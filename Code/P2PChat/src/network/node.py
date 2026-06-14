"""P2PNode: Manages TCP connections, peer state, and the custom message protocol."""

import logging
import socket
import threading
import time
from cryptography.fernet import Fernet, InvalidToken

from security.crypto import CryptoHandler
from security.rsa_utils import RSAUtils
from message.protocol import PacketType, ProtocolHandler
from network.discovery import DiscoveryService, PEER_TIMEOUT
from identity.identity_manager import IdentityManager
from trust.tofu_engine import TOFUEngine


logger = logging.getLogger(__name__)

HANDSHAKE_TIMEOUT = 5  # seconds before a pending peer is dropped
_AddressMap = dict[int, str] # id(socket) -> address string

class P2PNode:
    """Manages TCP connections, peer state, and the custom message protocol."""
    def __init__(
        self,
        host: str,
        port: int,
        username: str = "Anonymous",
        on_message=None,
        on_disconnect=None,
        on_connected=None,
        on_peer_discovered=None,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username

        # ── GUI callbacks ──────────────────────────────────────────────
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.on_connected = on_connected
        # Called with (addr, info_dict) when a new LAN peer appears/disappears.
        self.on_peer_discovered = on_peer_discovered

        self.server_socket: socket.socket | None = None

        # ── Connected-peer state ────────────────────────────────────────
        self.peers_lock = threading.RLock()
        self.peers: dict[str, socket.socket] = {}
        self.peer_sessions: dict[str, dict] = {}

        self._sock_to_addr: _AddressMap = {}

        # ── Protocol / crypto ──────────────────────────────────────────
        self.protocol_handler = ProtocolHandler()
        self.identity_manager = IdentityManager()
        self.identity_manager.load_identity()
        self.private_key = self.identity_manager.get_private_key()
        self.public_key = self.identity_manager.get_public_key()
        self.tofu = TOFUEngine()
        
        # Replay-attack mitigation: store recently seen message IDs.
        self.seen_messages: set[str] = set()

        # ── Discovery ──────────────────────────────────────────────────
        self.discovery_lock     = threading.RLock()
        # key: peer_id → {"username", "ip", "port", "status", "last_seen"}
        self.discovered_peers:  dict[str, dict] = {}
        self.discovery = DiscoveryService(
            username=self.username,
            listen_port=self.port,
            peer_id=self.identity_manager.get_peer_id(),
            fingerprint=self.identity_manager.get_fingerprint()
        )
        self.discovery.on_peer_found = self._handle_discovered_peer

        # ── Misc ───────────────────────────────────────────────────────
        self.receive_threads: list[threading.Thread] = []
        self.expiration_thread: threading.Thread | None = None
        self.is_running = False

    # ------------------------------------------------------------------ #
    # Server lifecycle #
    def start_server(self) -> None:
        """Bind the TCP server, start discovery, and begin accepting connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.is_running = True

        self.discovery.start()

        self.expiration_thread = threading.Thread(
            target=self._cleanup_expired_peers,
            daemon=True,
            name="DiscoveryExpiration",
        )
        self.expiration_thread.start()

        threading.Thread(
            target=self._accept_connections,
            daemon=True,
            name="AcceptThread",
        ).start()

        logger.info("[INFO] Listening on %s:%d", self.host, self.port)

    def stop_server(self) -> None:
        """Gracefully shut down the server and all peer connections."""
        self.is_running = False
        self.discovery.stop()

        with self.peers_lock:

            for sock in self.peers.values():

                try:
                    sock.close()

                except OSError:
                    pass

            self.peers.clear()
            self.peer_sessions.clear()
            self._sock_to_addr.clear()

        if self.server_socket is not None:

            try:
                self.server_socket.close()
            except OSError:
                pass

            logger.info("[INFO] Server stopped.")

        for thread in self.receive_threads:
            thread.join(timeout=1)

        self.receive_threads.clear()

    # ------------------------------------------------------------------ #
    # Public networking interface (used by controller / GUI) #
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to another peer and initiate the handshake."""
        peer_id = f"{host}:{port}"

        with self.peers_lock:

            if peer_id in self.peers:
                logger.info("[INFO] Already connected to %s", peer_id)
                return False

        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(10)
            peer_socket.connect((host, port))
            peer_socket.settimeout(None)

            logger.info("[INFO] Connected to %s", peer_id)

            if not self._register_peer(peer_id, peer_socket, is_initiator=True):
                logger.info("[INFO] Already connected to %s", peer_id)
                peer_socket.close()
                return False

            if not self._send_handshake(peer_socket):
                self._remove_peer(peer_socket)
                return False

            self._start_receive_thread(peer_id, peer_socket)
            self._schedule_handshake_timeout(peer_id)
            return True

        except OSError as exc:
            logger.error("[ERROR] Failed to connect to %s: %s", peer_id, exc)
            return False

    def send_message(self, message: str, peer_id: str) -> bool:
        """Send an encrypted message to a connected, active peer."""
        with self.peers_lock:
            session     = self.peer_sessions.get(peer_id)
            peer_socket = self.peers.get(peer_id)

        if session is None or session["state"] != "active":
            logger.warning("[WARNING] Peer not ready: %s", peer_id)
            return False

        if peer_socket is None:
            return False

        crypto: CryptoHandler | None = session.get("crypto")

        try:
            packet = self.protocol_handler.create_packet(
                PacketType.MESSAGE,
                self.username,
                message,
                crypto=crypto,
            )
            peer_socket.sendall(self.protocol_handler.serialize(packet))
            return True

        except (BrokenPipeError, OSError) as exc:
            logger.error("[ERROR] Send failed: %s", exc)
            self._remove_peer(peer_socket)
            return False

    def broadcast_message(self, message: str) -> tuple[int, int]:
        """Send *message* to every active peer. Returns (sent, failed)."""
        with self.peers_lock:
            active = [
                addr
                for addr, session in self.peer_sessions.items()
                if session["state"] == "active"
            ]

        sent = failed = 0
        for peer_id in active:
            if self.send_message(message, peer_id):
                sent += 1
            else:
                failed += 1

        return sent, failed

    def discover_peers(self) -> None:
        """Trigger an immediate discovery broadcast."""
        self.discovery.discover()

    def get_discovered_peers(self) -> dict[str, dict]:
        """Return a snapshot of the current discovered-peer table."""
        with self.discovery_lock:
            return dict(self.discovered_peers)
       
    def get_trust_state(self, peer_id: str) -> str:
        """Return trust state."""
        return self.tofu.get_trust_state(peer_id)

    def trust_peer(self, peer_id: str) -> None:
        """Trust peer."""
        self.tofu.trust_peer(peer_id)

    def block_peer(self, peer_id: str) -> None:
        """Block peer."""
        self.tofu.block_peer(peer_id)

    # ------------------------------------------------------------------ #
    # Accept loop #
    def _accept_connections(self) -> None:
        if self.server_socket is None:
            return

        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                peer_id = f"{address[0]}:{address[1]}"
                logger.info("[INFO] Incoming connection from %s", peer_id)

                if not self._register_peer(peer_id, client_socket, is_initiator=False):
                    logger.info("[INFO] Already connected: %s", peer_id)
                    client_socket.close()
                    continue

                self._start_receive_thread(peer_id, client_socket)
                self._schedule_handshake_timeout(peer_id)

            except socket.timeout:
                continue

            except OSError:
                if self.is_running:
                    logger.error("[ERROR] Accept connection failed")
                break

    # ------------------------------------------------------------------ #
    # Receive loop #

    def _receive_messages(self, peer_socket: socket.socket) -> None:
        """Per-peer receive loop — dispatches packets to handlers. Never raises."""
        while self.is_running:
            try:
                packet = self.protocol_handler.receive_packet(peer_socket)

                if packet is None:
                    self._remove_peer(peer_socket)
                    break

                if not isinstance(packet, dict):
                    logger.warning("[WARNING] Non-dict packet received — dropping")
                    continue

                msg_type = packet.get("type", "")

                if msg_type == PacketType.HANDSHAKE:
                    self._handle_handshake(packet, peer_socket)

                elif msg_type == PacketType.HANDSHAKE_ACK:
                    self._handle_handshake_ack(packet, peer_socket)

                elif msg_type == PacketType.SESSION_KEY:
                    self._handle_session_key(packet, peer_socket)

                elif msg_type == PacketType.MESSAGE:
                    self._handle_message(packet, peer_socket)

                else:
                    logger.warning("[WARNING] Unknown packet type '%s' — dropping", msg_type)

            except (ConnectionResetError, BrokenPipeError):
                logger.info("[INFO] Connection reset by peer")
                self._remove_peer(peer_socket)
                break

            except (OSError, ValueError, KeyError, InvalidToken) as exc:
                if self.is_running:
                    logger.error("[ERROR] Receive error: %s", exc)
                self._remove_peer(peer_socket)
                break

    # ------------------------------------------------------------------ #
    # Packet handlers #

    def _handle_handshake(self, packet: dict, peer_socket: socket.socket) -> None:
        if not self.protocol_handler.validate_packet(packet):
            logger.warning("[WARNING] Malformed handshake — disconnecting peer")
            self._remove_peer(peer_socket)
            return

        peer_id = self._get_peer_id(peer_socket)
        if peer_id is None:
            return

        # Remap the address to the peer's *listening* port so we can
        # later connect back (the ephemeral port is not useful).
        real_peer_id = f"{peer_id.split(':')[0]}:{packet['listen_port']}"

        with self.peers_lock:

            if real_peer_id != peer_id and real_peer_id in self.peers:
                logger.info(
                    "[INFO] Duplicate connection: %s → %s",
                    peer_id, real_peer_id,
                )
                self._remove_peer(peer_socket)
                return

        logger.info(
            "[HANDSHAKE] Received from %s (user: %s)",
            peer_id, packet.get("username"),
        )

        # Validate the public key before proceeding.
        try:
            RSAUtils.load_public_key(packet["public_key"])
        except Exception:
            logger.warning("[WARNING] Invalid public key — disconnecting")
            self._remove_peer(peer_socket)
            return

        with self.peers_lock:
            session = self.peer_sessions.get(peer_id)
            if session is None:
                return
            session["public_key"]  = packet["public_key"]
            session["username"]    = packet.get("username", "Unknown")
            session["listen_port"] = packet.get("listen_port")

        ack = {
            "type":       PacketType.HANDSHAKE_ACK,
            "status":     "ok",
            "public_key": RSAUtils.serialize_public_key(self.public_key),
        }
        try:
            peer_socket.sendall(self.protocol_handler.serialize(ack))
        except OSError as exc:
            logger.error("[ERROR] Failed to send handshake_ack: %s", exc)
            self._remove_peer(peer_socket)

    def _handle_handshake_ack(self, packet: dict, peer_socket: socket.socket) -> None:
        if not self.protocol_handler.validate_packet(packet):
            logger.warning("[WARNING] Malformed handshake_ack — disconnecting peer")
            self._remove_peer(peer_socket)
            return

        peer_id = self._get_peer_id(peer_socket)
        if peer_id is None:
            return

        if packet.get("status") != "ok":
            logger.warning("[WARNING] Handshake_ack rejected by %s", peer_id)
            self._remove_peer(peer_socket)
            return

        raw_key = packet.get("public_key", "")
        try:
            RSAUtils.load_public_key(raw_key)

        except Exception:
            logger.warning("[WARNING] Invalid RSA public key in handshake_ack — disconnecting")
            self._remove_peer(peer_socket)
            return

        is_initiator = False

        with self.peers_lock:
            session = self.peer_sessions.get(peer_id)

            if session is None:
                return
            session["public_key"] = raw_key
            is_initiator = session["is_initiator"]

        if is_initiator:
            self._send_session_key(peer_socket, peer_id)

    def _handle_session_key(self, packet: dict, peer_socket: socket.socket) -> None:
        """Decrypt the RSA-wrapped Fernet session key and activate the session."""
        peer_id = self._get_peer_id(peer_socket)
        if peer_id is None:
            return

        if not self.protocol_handler.validate_packet(packet):
            logger.warning("[WARNING] Invalid session_key packet from %s", peer_id)
            self._remove_peer(peer_socket)
            return

        encrypted_key_hex = packet.get("payload", "")
        if not encrypted_key_hex:
            logger.warning("[WARNING] Empty session_key payload from %s", peer_id)
            self._remove_peer(peer_socket)
            return

        try:
            encrypted_key = bytes.fromhex(encrypted_key_hex)
            fernet_key    = RSAUtils.decrypt(self.private_key, encrypted_key)
            crypto        = CryptoHandler(key=fernet_key)

        except Exception as exc:
            logger.warning(
                "[WARNING] Failed to decrypt session key from %s: %s", peer_id, exc
            )
            self._remove_peer(peer_socket)
            return

        with self.peers_lock:
            session = self.peer_sessions.get(peer_id)

            if session is None:
                return
            session["crypto"] = crypto
            session["state"]  = "active"
            count = len(self.peers)

        logger.info(
            "[INFO] Session key received — peer active: %s (peers: %d)",
            peer_id, count,
        )
        self._fire_callback(self.on_connected, peer_id)

    def _handle_message(self, packet: dict, peer_socket: socket.socket) -> None:
        peer_id = self._get_peer_id(peer_socket)

        if peer_id is None:
            return

        with self.peers_lock:
            session = self.peer_sessions.get(peer_id)

        if session is None or session["state"] != "active":
            logger.warning("[WARNING] Message from non-active peer %s", peer_id)
            return

        if not self.protocol_handler.validate_packet(packet):
            logger.warning("[WARNING] Invalid message packet from %s — dropping", peer_id)
            return

        message_id = packet["message_id"]
        with self.peers_lock:

            if message_id in self.seen_messages:
                logger.warning("[WARNING] Replay packet dropped")
                return   
            self.seen_messages.add(message_id)

            if len(self.seen_messages) > 5000:
                self.seen_messages.clear()

        crypto: CryptoHandler | None = session.get("crypto")
        try:
            payload = self.protocol_handler.decrypt_payload(packet, crypto=crypto)

        except (InvalidToken, ValueError) as exc:
            logger.warning("[WARNING] Decryption failed from %s: %s", peer_id, exc)
            return

        sender = packet.get("sender", "Unknown")
        self._fire_callback(self.on_message, sender, payload)

    # ------------------------------------------------------------------ #
    # Discovery handlers #
    def _handle_discovered_peer(self, packet: dict, address: tuple[str, int]) -> None:
        """Called by DiscoveryService when a discovery_response is received."""
        peer_ip = address[0]
        peer_id = packet.get("peer_id")        
        if not peer_id:
            return
        trust_state = (
            self.tofu.verify_peer(
                peer_id,
                packet.get(
                    "fingerprint",
                    ""
                )
            )
        )
        peer_port = packet.get("port")

        if peer_port is None:
            return

        # Skip peers we are already connected to via TCP.
        with self.peers_lock:
            already_connected = peer_id in self.peers

        now = time.time()

        with self.discovery_lock:
            existing = self.discovered_peers.get(peer_id)

            if existing is not None:
                # Refresh the heartbeat.
                existing["last_seen"] = now
                existing["trust_state"] = trust_state
                existing["fingerprint"] = packet.get("fingerprint")

                if existing["status"] != "online":
                    existing["status"] = "online"
                    logger.info("[DISCOVERY] Peer back online: %s", peer_id)
                    self._fire_callback(
                        self.on_peer_discovered,
                        peer_id,
                        dict(existing),
                    )
                return

            info = {
                "username":  packet.get("username", "Unknown"),
                "ip":        peer_ip,
                "port":      peer_port,
                "status":    "online",
                "connected": already_connected,
                "peer_id": peer_id,
                "last_seen": now,              
                "fingerprint": packet.get("fingerprint"),
                "trust_state": trust_state,
            }

            self.discovered_peers[peer_id] = info
            logger.info("[DISCOVERY] New peer: %s (%s)", peer_id, info["username"])

        self._fire_callback(self.on_peer_discovered, peer_id, dict(info))

    def _cleanup_expired_peers(self) -> None:
        """Background loop: mark peers offline when they stop broadcasting."""
        while self.is_running:
            now = time.time()

            with self.discovery_lock:

                for peer_id, peer in list(self.discovered_peers.items()):

                    if peer["status"] == "online" and now - peer["last_seen"] > PEER_TIMEOUT:
                        peer["status"] = "offline"
                        peer["connected"] = False
                        logger.info("[DISCOVERY] Peer went offline: %s", peer_id)
                        self._fire_callback(
                            self.on_peer_discovered,
                            peer_id,
                            dict(peer),
                        )

            time.sleep(2)

    # ------------------------------------------------------------------ #
    # Peer registration / removal #
    def _register_peer(
        self, peer_id: str, sock: socket.socket, is_initiator: bool
    ) -> bool:
        """Atomically register *peer_id*. Returns False if already known."""
        with self.peers_lock:
            if peer_id in self.peers:
                return False

            self.peers[peer_id] = sock
            self._sock_to_addr[id(sock)] = peer_id
            self.peer_sessions[peer_id] = {
                "state":        "pending",
                "public_key":   None,
                "session_key":  None,
                "crypto":       None,
                "username":     None,
                "listen_port":  None,
                "is_initiator": is_initiator,
            }
            count = len(self.peers)

        logger.info("[INFO] Peer registered: %s — active peers: %d", peer_id, count)
        return True

    def _remove_peer(self, peer_socket: socket.socket) -> None:
        peer_id   = self._get_peer_id(peer_socket)
        remaining = 0

        with self.peers_lock:
            if peer_id is not None:
                self.peers.pop(peer_id, None)
                self.peer_sessions.pop(peer_id, None)
                self._sock_to_addr.pop(id(peer_socket), None)
                remaining = len(self.peers)

        try:
            peer_socket.close()

        except OSError:
            pass

        if peer_id is not None:
            logger.info(
                "[INFO] Peer disconnected: %s — remaining: %d",
                peer_id, remaining,
            )
            self._fire_callback(self.on_disconnect, peer_id)

    # ------------------------------------------------------------------ #
    # Handshake helpers #
    def _send_handshake(self, peer_socket: socket.socket) -> bool:
        handshake = {
            "type":        PacketType.HANDSHAKE,
            "username":    self.username,
            "version":     "1.0",
            "listen_port": self.port,
            "public_key":  RSAUtils.serialize_public_key(self.public_key),
        }

        try:
            peer_socket.sendall(self.protocol_handler.serialize(handshake))
            return True
        except (BrokenPipeError, OSError) as exc:
            logger.error("[ERROR] Failed to send handshake: %s", exc)
            return False

    def _send_session_key(self, peer_socket: socket.socket, peer_id: str) -> None:
        """Generate a Fernet session key, encrypt with peer's RSA public key, send."""
        with self.peers_lock:
            session = self.peer_sessions.get(peer_id)

            if session is None:
                return        
            raw_peer_key = session.get("public_key")

        if not raw_peer_key:
            logger.warning("[WARNING] No peer public key for %s — cannot send session key", peer_id)
            return
        try:
            peer_pub = RSAUtils.load_public_key(raw_peer_key)

        except Exception as exc:
            logger.error("[ERROR] Cannot load peer public key for %s: %s", peer_id, exc)
            self._remove_peer(peer_socket)
            return

        fernet_key = Fernet.generate_key()

        try:
            encrypted_key = RSAUtils.encrypt(peer_pub, fernet_key)

        except Exception as exc:
            logger.error("[ERROR] RSA encrypt failed for %s: %s", peer_id, exc)
            self._remove_peer(peer_socket)
            return

        session_key_packet = {
            "type":    PacketType.SESSION_KEY,
            "payload": encrypted_key.hex(),
        }

        try:
            peer_socket.sendall(self.protocol_handler.serialize(session_key_packet))

        except (BrokenPipeError, OSError) as exc:
            logger.error("[ERROR] Failed to send session key to %s: %s", peer_id, exc)
            self._remove_peer(peer_socket)
            return

        crypto = CryptoHandler(key=fernet_key)

        with self.peers_lock:
            session = self.peer_sessions.get(peer_id)

            if session is not None:
                session["session_key"] = fernet_key
                session["crypto"]      = crypto
                session["state"]       = "active"

        logger.info("[INFO] Session key sent to %s — session active", peer_id)
        self._fire_callback(self.on_connected, peer_id)

    def _schedule_handshake_timeout(self, peer_id: str) -> None:
        """Disconnect *peer_id* if still pending after HANDSHAKE_TIMEOUT."""
        def _check() -> None:
            with self.peers_lock:
                session = self.peer_sessions.get(peer_id)

                if session is None or session["state"] != "pending":
                    return
                peer_socket = self.peers.get(peer_id)

            if peer_socket is None:
                return

            logger.warning("[WARNING] Handshake timeout — disconnecting %s", peer_id)
            self._remove_peer(peer_socket)

        timer = threading.Timer(HANDSHAKE_TIMEOUT, _check)
        timer.daemon = True
        timer.start()

    # ------------------------------------------------------------------ #
    # Utility #
    def _get_peer_id(self, peer_socket: socket.socket) -> str | None:
        """O(1) reverse lookup: socket → address string."""
        with self.peers_lock:
            return self._sock_to_addr.get(id(peer_socket))

    def _start_receive_thread(self, peer_id: str, sock: socket.socket) -> None:
        thread = threading.Thread(
            target=self._receive_messages,
            args=(sock,),
            daemon=True,
            name=f"Recv-{peer_id}",
        )
        thread.start()
        self.receive_threads.append(thread)

    def _fire_callback(self, callback, *args) -> None:
        if callback is None:
            return
        try:
            callback(*args)
        except Exception as exc:
            logger.exception("[ERROR] Callback raised: %s", exc)