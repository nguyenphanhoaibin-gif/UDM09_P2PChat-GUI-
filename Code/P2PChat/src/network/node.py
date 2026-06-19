"""P2PNode: Manages TCP connections, peer state, and the custom message protocol."""

import logging
import socket
import threading
import time
from cryptography.fernet import Fernet, InvalidToken

from security.crypto import CryptoHandler
from security.rsa_utils import RSAUtils
from security.jwt_handler import JWTHandler
from message.protocol import PacketType, ProtocolHandler
from network.discovery import DiscoveryService, PEER_TIMEOUT
from identity.identity_manager import IdentityManager
from trust.tofu_engine import TOFUEngine
from config import SOCKET_TIMEOUT

logger = logging.getLogger(__name__)

HANDSHAKE_TIMEOUT = 5
_AddressMap = dict[int, str]  # id(socket) -> "IP:PORT"


class P2PNode:
    """Manages TCP connections, peer state, and the custom message protocol.

    Peer identity note
    ------------------
    * ``node.peers`` and ``node.peer_sessions`` are keyed by **"IP:PORT"** strings
      (the TCP connection address).
    * ``node.discovered_peers`` is keyed by the **peer_id SHA-256 hash** that comes
      from the discovery JWT.
    * Each entry in ``discovered_peers`` carries a ``"tcp_address"`` field that maps
      back to the TCP key used by ``peers`` / ``peer_sessions``.
    * The controller / GUI must use the ``tcp_address`` field when calling
      ``send_message``; the ``peer_id`` hash is only for identity / trust purposes.
    """

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
        self.host     = host
        self.port     = port
        self.username = username

        # GUI callbacks
        self.on_message         = on_message
        self.on_disconnect      = on_disconnect
        self.on_connected       = on_connected
        self.on_peer_discovered = on_peer_discovered

        self.server_socket: socket.socket | None = None

        # ── Connected-peer state (keyed by "IP:PORT") ──────────────────
        self.peers_lock    = threading.RLock()
        self.peers:         dict[str, socket.socket] = {}
        self.peer_sessions: dict[str, dict]          = {}
        self._sock_to_addr: _AddressMap              = {}

        # ── Protocol / crypto ──────────────────────────────────────────
        self.protocol_handler = ProtocolHandler()
        self.identity_manager = IdentityManager()
        self.identity_manager.load_identity()
        self.private_key = self.identity_manager.get_private_key()
        self.public_key  = self.identity_manager.get_public_key()
        self.tofu        = TOFUEngine()

        # Replay-attack mitigation
        self.seen_messages: set[str] = set()

        # ── Discovery (keyed by peer_id SHA-256 hash) ──────────────────
        self.discovery_lock    = threading.RLock()
        self.discovered_peers: dict[str, dict] = {}

        self.discovery = DiscoveryService(
            username        = self.username,
            listen_port     = self.port,
            peer_id         = self.identity_manager.get_peer_id(),
            fingerprint     = self.identity_manager.get_fingerprint(),
            public_key_pem  = self.identity_manager.public_key_pem,
            private_key_pem = self.identity_manager.private_key_pem,
        )
        self.discovery.on_peer_found = self._handle_discovered_peer

        # ── Misc ───────────────────────────────────────────────────────
        self.receive_threads: list[threading.Thread] = []
        self.expiration_thread: threading.Thread | None = None
        self.is_running = False

    # ------------------------------------------------------------------ #
    # Server lifecycle                                                     #
    # ------------------------------------------------------------------ #

    def start_server(self) -> None:
        """Bind the TCP server, start discovery, and begin accepting connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(SOCKET_TIMEOUT)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.is_running = True

        self.discovery.start()

        self.expiration_thread = threading.Thread(
            target=self._cleanup_expired_peers,
            daemon=True, name="DiscoveryExpiration",
        )
        self.expiration_thread.start()

        threading.Thread(
            target=self._accept_connections,
            daemon=True, name="AcceptThread",
        ).start()

        logger.info("[NODE] Listening on %s:%d", self.host, self.port)

    def stop_server(self) -> None:
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

        for t in self.receive_threads:
            t.join(timeout=1)
        self.receive_threads.clear()
        logger.info("[NODE] Server stopped.")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to another peer and initiate the handshake.

        The TCP connection key is always "IP:PORT" (ephemeral port of the
        *outgoing* socket → we remap after handshake to the peer's *listen* port).
        """
        tcp_addr = f"{host}:{port}"

        with self.peers_lock:
            if tcp_addr in self.peers:
                return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            sock.settimeout(None)

            if not self._register_peer(tcp_addr, sock, is_initiator=True):
                sock.close()
                return False

            if not self._send_handshake(sock):
                self._remove_peer(sock)
                return False

            self._start_receive_thread(tcp_addr, sock)
            self._schedule_handshake_timeout(tcp_addr)
            return True

        except OSError as exc:
            logger.error("[NODE] Connect failed %s: %s", tcp_addr, exc)
            return False

    def send_message(self, message: str, tcp_addr: str) -> bool:
        """Send an encrypted message to the peer at *tcp_addr* ("IP:PORT")."""
        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
            sock    = self.peers.get(tcp_addr)

        if session is None or session["state"] != "active" or sock is None:
            logger.warning("[NODE] Peer not active: %s", tcp_addr)
            return False

        crypto: CryptoHandler | None = session.get("crypto")
        try:
            packet = self.protocol_handler.create_packet(
                PacketType.MESSAGE, self.username, message, crypto=crypto
            )
            sock.sendall(self.protocol_handler.serialize(packet))
            return True
        except OSError as exc:
            logger.error("[NODE] Send failed: %s", exc)
            self._remove_peer(sock)
            return False

    def broadcast_message(self, message: str) -> tuple[int, int]:
        with self.peers_lock:
            active = [a for a, s in self.peer_sessions.items() if s["state"] == "active"]
        sent = failed = 0
        for addr in active:
            if self.send_message(message, addr):
                sent += 1
            else:
                failed += 1
        return sent, failed

    def discover_peers(self) -> None:
        self.discovery.discover()

    def get_discovered_peers(self) -> dict[str, dict]:
        with self.discovery_lock:
            return dict(self.discovered_peers)

    def get_trust_state(self, peer_id: str) -> str:
        return self.tofu.get_trust_state(peer_id)

    def trust_peer(self, peer_id: str) -> bool:
        try:
            self.tofu.trust_peer(peer_id)
            return True
        except Exception:
            logger.exception(
                "[NODE] Failed to trust peer %s",
                peer_id,
            )
            return False


    def block_peer(self, peer_id: str) -> bool:
        try:
            self.tofu.block_peer(peer_id)
            return True
        except Exception:
            logger.exception(
                "[NODE] Failed to block peer %s",
                peer_id,
            )
            return False

    # ------------------------------------------------------------------ #
    # Accept loop                                                          #
    # ------------------------------------------------------------------ #

    def _accept_connections(self) -> None:
        if self.server_socket is None:
            return
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                tcp_addr = f"{address[0]}:{address[1]}"
                logger.info("[NODE] Incoming: %s", tcp_addr)
                if not self._register_peer(tcp_addr, client_socket, is_initiator=False):
                    client_socket.close()
                    continue
                self._start_receive_thread(tcp_addr, client_socket)
                self._schedule_handshake_timeout(tcp_addr)
            except socket.timeout:
                continue
            except OSError:
                if self.is_running:
                    logger.error("[NODE] Accept error")
                break

    # ------------------------------------------------------------------ #
    # Receive loop                                                         #
    # ------------------------------------------------------------------ #

    def _receive_messages(self, peer_socket: socket.socket) -> None:
        while self.is_running:
            try:
                packet = self.protocol_handler.receive_packet(peer_socket)
                if packet is None:
                    self._remove_peer(peer_socket)
                    break

                msg_type = packet.get("type", "")

                if   msg_type == PacketType.HANDSHAKE:
                    self._handle_handshake(packet, peer_socket)
                elif msg_type == PacketType.HANDSHAKE_ACK:
                    self._handle_handshake_ack(packet, peer_socket)
                elif msg_type == PacketType.SESSION_KEY:
                    self._handle_session_key(packet, peer_socket)
                elif msg_type == PacketType.MESSAGE:
                    self._handle_message(packet, peer_socket)
                else:
                    logger.debug("[NODE] Unknown packet '%s'", msg_type)

            except (ConnectionResetError, BrokenPipeError):
                self._remove_peer(peer_socket)
                break
            except (OSError, ValueError, KeyError, InvalidToken) as exc:
                if self.is_running:
                    logger.error("[NODE] Receive error: %s", exc)
                self._remove_peer(peer_socket)
                break

    # ------------------------------------------------------------------ #
    # Packet handlers                                                      #
    # ------------------------------------------------------------------ #

    def _handle_handshake(self, packet: dict, peer_socket: socket.socket) -> None:
        if not self.protocol_handler.validate_packet(packet):
            self._remove_peer(peer_socket)
            return

        tcp_addr = self._get_peer_id(peer_socket)
        if tcp_addr is None:
            return

        try:
            RSAUtils.load_public_key(packet["public_key"])
        except Exception:
            logger.warning("[NODE] Invalid public key — dropping")
            self._remove_peer(peer_socket)
            return

        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
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
            logger.error("[NODE] ACK send failed: %s", exc)
            self._remove_peer(peer_socket)

    def _handle_handshake_ack(self, packet: dict, peer_socket: socket.socket) -> None:
        if not self.protocol_handler.validate_packet(packet):
            self._remove_peer(peer_socket)
            return

        tcp_addr = self._get_peer_id(peer_socket)
        if tcp_addr is None:
            return

        if packet.get("status") != "ok":
            self._remove_peer(peer_socket)
            return

        raw_key = packet.get("public_key", "")
        try:
            RSAUtils.load_public_key(raw_key)
        except Exception:
            self._remove_peer(peer_socket)
            return

        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
            if session is None:
                return
            session["public_key"] = raw_key
            is_initiator = session["is_initiator"]

        if is_initiator:
            self._send_session_key(peer_socket, tcp_addr)

    def _handle_session_key(self, packet: dict, peer_socket: socket.socket) -> None:
        tcp_addr = self._get_peer_id(peer_socket)
        if tcp_addr is None:
            return

        if not self.protocol_handler.validate_packet(packet):
            self._remove_peer(peer_socket)
            return

        encrypted_key_hex = packet.get("payload", "")
        try:
            fernet_key = RSAUtils.decrypt(self.private_key, bytes.fromhex(encrypted_key_hex))
            crypto     = CryptoHandler(key=fernet_key)
        except Exception as exc:
            logger.warning("[NODE] Session key decrypt failed from %s: %s", tcp_addr, exc)
            self._remove_peer(peer_socket)
            return

        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
            if session is None:
                return
            session["crypto"] = crypto
            session["state"]  = "active"

        logger.info("[NODE] Session active: %s", tcp_addr)
        self._fire_callback(self.on_connected, tcp_addr)

    def _handle_message(self, packet: dict, peer_socket: socket.socket) -> None:
        tcp_addr = self._get_peer_id(peer_socket)
        if tcp_addr is None:
            return

        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
        if session is None or session["state"] != "active":
            return
        if not self.protocol_handler.validate_packet(packet):
            return

        message_id = packet["message_id"]
        with self.peers_lock:
            if message_id in self.seen_messages:
                return
            self.seen_messages.add(message_id)
            if len(self.seen_messages) > 5000:
                self.seen_messages.clear()

        crypto = session.get("crypto")
        try:
            payload = self.protocol_handler.decrypt_payload(packet, crypto=crypto)
        except (InvalidToken, ValueError) as exc:
            logger.warning("[NODE] Decrypt failed: %s", exc)
            return

        self._fire_callback(self.on_message, packet.get("sender", "Unknown"), payload)

    # ------------------------------------------------------------------ #
    # Discovery handlers                                                   #
    # ------------------------------------------------------------------ #

    def _handle_discovered_peer(self, packet: dict, address: tuple[str, int]) -> None:
        """Called by DiscoveryService when a valid discovery_response arrives."""
        peer_ip  = address[0]
        peer_id  = packet.get("peer_id")
        token    = packet.get("identity_token")
        pub_key  = packet.get("public_key")

        if not token or not pub_key:
            logger.warning("[DISCOVERY] Missing JWT identity")
            return

        claims = JWTHandler.verify_identity_token(token, pub_key)
        if claims is None:
            logger.warning("[DISCOVERY] Invalid JWT from %s", peer_ip)
            return

        # Cross-validate claims against packet fields
        if claims.get("fingerprint") != packet.get("fingerprint"):
            logger.warning("[DISCOVERY] Fingerprint mismatch in JWT vs packet")
            return
        if claims.get("peer_id") != peer_id:
            logger.warning("[DISCOVERY] Peer ID mismatch in JWT vs packet")
            return
        if not peer_id:
            return

        peer_port = packet.get("port")
        if peer_port is None:
            return

        # tcp_address is the key used in node.peers / peer_sessions
        tcp_address = f"{peer_ip}:{peer_port}"

        trust_state = self.tofu.verify_peer(peer_id, packet.get("fingerprint", ""))
        now = time.time()

        with self.discovery_lock:
            existing = self.discovered_peers.get(peer_id)

            if existing is not None:
                existing["last_seen"]   = now
                existing["trust_state"] = trust_state
                existing["fingerprint"] = packet.get("fingerprint")
                existing["tcp_address"] = tcp_address

                if existing["status"] != "online":
                    existing["status"] = "online"
                    self._fire_callback(self.on_peer_discovered, peer_id, dict(existing))
                else:
                    # Always refresh GUI so trust_state stays current
                    self._fire_callback(self.on_peer_discovered, peer_id, dict(existing))
                return

            info = {
                "username":    packet.get("username", "Unknown"),
                "ip":          peer_ip,
                "port":        peer_port,
                "tcp_address": tcp_address,    # ← KEY FIX: for send_message routing
                "status":      "online",
                "connected":   tcp_address in self.peers,
                "peer_id":     peer_id,
                "last_seen":   now,
                "fingerprint": packet.get("fingerprint"),
                "trust_state": trust_state,
            }
            self.discovered_peers[peer_id] = info

        logger.info("[DISCOVERY] New peer: %s (%s)", peer_id[:12], info["username"])
        self._fire_callback(self.on_peer_discovered, peer_id, dict(info))

    def _cleanup_expired_peers(self) -> None:
        while self.is_running:
            now = time.time()
            with self.discovery_lock:
                for peer_id, peer in list(self.discovered_peers.items()):
                    if peer["status"] == "online" and now - peer["last_seen"] > PEER_TIMEOUT:
                        peer["status"]    = "offline"
                        peer["connected"] = False
                        self._fire_callback(self.on_peer_discovered, peer_id, dict(peer))
            time.sleep(2)

    # ------------------------------------------------------------------ #
    # Peer registration / removal                                          #
    # ------------------------------------------------------------------ #

    def _register_peer(self, tcp_addr: str, sock: socket.socket, is_initiator: bool) -> bool:
        with self.peers_lock:
            if tcp_addr in self.peers:
                return False
            self.peers[tcp_addr]         = sock
            self._sock_to_addr[id(sock)] = tcp_addr
            self.peer_sessions[tcp_addr] = {
                "state":        "pending",
                "public_key":   None,
                "session_key":  None,
                "crypto":       None,
                "username":     None,
                "listen_port":  None,
                "is_initiator": is_initiator,
            }
        return True

    def _remove_peer(self, peer_socket: socket.socket) -> None:
        tcp_addr = self._get_peer_id(peer_socket)
        with self.peers_lock:
            if tcp_addr is not None:
                self.peers.pop(tcp_addr, None)
                self.peer_sessions.pop(tcp_addr, None)
                self._sock_to_addr.pop(id(peer_socket), None)
        try:
            peer_socket.close()
        except OSError:
            pass
        if tcp_addr is not None:
            # Mark as disconnected in discovery table
            with self.discovery_lock:
                for info in self.discovered_peers.values():
                    if info.get("tcp_address") == tcp_addr:
                        info["connected"] = False
                        info["status"]    = "offline"
                        break
            self._fire_callback(self.on_disconnect, tcp_addr)

    # ------------------------------------------------------------------ #
    # Handshake helpers                                                    #
    # ------------------------------------------------------------------ #

    def _send_handshake(self, peer_socket: socket.socket) -> bool:
        packet = {
            "type":        PacketType.HANDSHAKE,
            "username":    self.username,
            "version":     "1.0",
            "listen_port": self.port,
            "public_key":  RSAUtils.serialize_public_key(self.public_key),
        }
        try:
            peer_socket.sendall(self.protocol_handler.serialize(packet))
            return True
        except OSError as exc:
            logger.error("[NODE] Handshake send failed: %s", exc)
            return False

    def _send_session_key(self, peer_socket: socket.socket, tcp_addr: str) -> None:
        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
            if session is None:
                return
            raw_peer_key = session.get("public_key")

        if not raw_peer_key:
            return
        try:
            peer_pub = RSAUtils.load_public_key(raw_peer_key)
        except Exception as exc:
            logger.error("[NODE] Cannot load peer pub key: %s", exc)
            self._remove_peer(peer_socket)
            return

        fernet_key    = Fernet.generate_key()
        encrypted_key = RSAUtils.encrypt(peer_pub, fernet_key)

        pkt = {"type": PacketType.SESSION_KEY, "payload": encrypted_key.hex()}
        try:
            peer_socket.sendall(self.protocol_handler.serialize(pkt))
        except OSError as exc:
            logger.error("[NODE] Session key send failed: %s", exc)
            self._remove_peer(peer_socket)
            return

        crypto = CryptoHandler(key=fernet_key)
        with self.peers_lock:
            session = self.peer_sessions.get(tcp_addr)
            if session is not None:
                session["session_key"] = fernet_key
                session["crypto"]      = crypto
                session["state"]       = "active"

        logger.info("[NODE] Session key sent → %s active", tcp_addr)
        self._fire_callback(self.on_connected, tcp_addr)

    def _schedule_handshake_timeout(self, tcp_addr: str) -> None:
        def _check() -> None:
            with self.peers_lock:
                session = self.peer_sessions.get(tcp_addr)
                if session is None or session["state"] != "pending":
                    return
                sock = self.peers.get(tcp_addr)
            if sock is None:
                return
            logger.warning("[NODE] Handshake timeout — dropping %s", tcp_addr)
            self._remove_peer(sock)

        t = threading.Timer(HANDSHAKE_TIMEOUT, _check)
        t.daemon = True
        t.start()

    # ------------------------------------------------------------------ #
    # Utility                                                              #
    # ------------------------------------------------------------------ #

    def _get_peer_id(self, peer_socket: socket.socket) -> str | None:
        with self.peers_lock:
            return self._sock_to_addr.get(id(peer_socket))

    def _start_receive_thread(self, tcp_addr: str, sock: socket.socket) -> None:
        t = threading.Thread(
            target=self._receive_messages, args=(sock,),
            daemon=True, name=f"Recv-{tcp_addr}",
        )
        t.start()
        self.receive_threads.append(t)

    def _fire_callback(self, callback, *args) -> None:
        if callback is None:
            return
        try:
            callback(*args)
        except Exception as exc:
            logger.exception("[NODE] Callback raised: %s", exc)
