"""UDP broadcast-based peer discovery service for P2PChat."""

import json
import logging
import socket
import threading
import time
from typing import Callable, Optional

from security.jwt_handler import JWTHandler

logger = logging.getLogger(__name__)

DISCOVERY_PORT    = 15000
PEER_TIMEOUT      = 15   # seconds before a peer is considered offline
PRESENCE_INTERVAL = 5    # seconds between broadcast announcements

# Packet type constants
DISCOVERY          = "discovery"
DISCOVERY_RESPONSE = "discovery_response"

class DiscoveryService:
    """UDP broadcast-based peer discovery service."""
    def __init__(
        self, 
        username: str, 
        listen_port: int, 
        peer_id: str, 
        fingerprint: str,
        public_key_pem: str, 
        private_key_pem: str
        ):
        self.username = username
        self.listen_port = listen_port
        self.peer_id = peer_id
        self.fingerprint = fingerprint
        self.public_key_pem = public_key_pem
        self.private_key_pem = private_key_pem
        # Unique ID that lets us discard our own broadcast echoes.
        self.instance_id  = f"{username}-{listen_port}"
        self.nearby_peers = {}

        self.running: bool = False
        self._socket: Optional[socket.socket] = None

        self._listener_thread:  Optional[threading.Thread] = None
        self._broadcast_thread: Optional[threading.Thread] = None

        # Assigned by the owning P2PNode; called with (packet, address) for
        # every valid discovery_response received.
        self.on_peer_found: Optional[Callable[[dict, tuple[str, int]], None]] = None

    # ------------------------------------------------------------------ #
    # Lifecycle #

    def start(self) -> None:
        """Open the UDP socket and start listener + broadcast threads."""
        if self.running:
            return
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)   # unblocks listen_loop so it can check self.running
        sock.bind(("", DISCOVERY_PORT))
        self._socket = sock
        self.running = True

        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="DiscoveryListener",
        )

        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop,
            daemon=True,
            name="DiscoveryBroadcast",
        )

        self._listener_thread.start()
        self._broadcast_thread.start()
        logger.info("[DISCOVERY] Service started (port=%d)", DISCOVERY_PORT)

    def stop(self) -> None:
        """Signal threads to stop and wait for them to finish."""
        self.running = False

        # Closing the socket unblocks any pending recvfrom immediately.
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()

            except OSError:
                pass

        for thread in (self._listener_thread, self._broadcast_thread):
            if thread is not None and thread.is_alive():
                thread.join(timeout=2)

        logger.info("[DISCOVERY] Service stopped.")

    # ------------------------------------------------------------------ #
    # Public actions #

    def discover(self) -> None:
        """Send a single broadcast discovery packet on the LAN."""
        sender: Optional[socket.socket] = None
        identity_token = (
            JWTHandler.create_identity_token(
                peer_id=self.peer_id,
                username=self.username,
                fingerprint=self.fingerprint,
                private_key_pem=self.private_key_pem
            )
        )
        try:
            sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            packet = {
                "type": DISCOVERY,
                "instance_id": self.instance_id,
                "peer_id": self.peer_id,
                "username": self.username,
                "fingerprint": self.fingerprint,
                "public_key": self.public_key_pem,
                "identity_token": identity_token,
                "port": self.listen_port,
                "status": "online",
                "timestamp": time.time()
            }

            sender.sendto(
                json.dumps(packet).encode("utf-8"),
                ("255.255.255.255", DISCOVERY_PORT),
            )

        except OSError as exc:
            logger.warning("[DISCOVERY] Broadcast error: %s", exc)

        finally:
            if sender is not None:
                try:
                    sender.close()

                except OSError:
                    pass

    # ------------------------------------------------------------------ #
    # Internal threads #

    def _listen_loop(self) -> None:
        """Receive UDP packets and dispatch to _handle_packet."""
        while self.running:
            sock = self._socket

            if sock is None:
                break

            try:
                data, address = sock.recvfrom(4096)
                packet = json.loads(data.decode("utf-8"))
                self._handle_packet(packet, address)

            except socket.timeout:
                continue

            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            except OSError:

                if not self.running:
                    break

                continue

    def _broadcast_loop(self) -> None:
        """Broadcast our presence every PRESENCE_INTERVAL seconds."""
        while self.running:
            self.discover()
            # Sleep in small increments so we respond to stop() quickly.
            for _ in range(PRESENCE_INTERVAL * 10):

                if not self.running:
                    break

                time.sleep(0.1)

    # ------------------------------------------------------------------ #
    # Packet handling #
    def _handle_packet(self, packet: dict, address: tuple[str, int]) -> None:
        """Dispatch an incoming discovery packet."""
        packet_type = packet.get("type")

        if packet_type == DISCOVERY:
            # Ignore our own echoes.

            if packet.get("instance_id") == self.instance_id:
                return
            
            self._send_response(address)

        elif packet_type == DISCOVERY_RESPONSE:
            self.update_peer_registry(packet, address)

            if self.on_peer_found is not None:
                try:
                    self.on_peer_found(packet, address)

                except Exception as exc:
                    logger.exception("[DISCOVERY] on_peer_found raised: %s", exc)

    def _send_response(self, address: tuple[str, int]) -> None:
        """Reply to a discovery broadcast with our own info."""
        identity_token = (
            JWTHandler.create_identity_token(
                peer_id=self.peer_id,
                username=self.username,
                fingerprint=self.fingerprint,
                private_key_pem=self.private_key_pem
            )
        )
        
        sock = self._socket
        if sock is None:
            return

        response = {
            "type": DISCOVERY_RESPONSE,
            "peer_id": self.peer_id,
            "username": self.username,
            "fingerprint": self.fingerprint,
            "public_key": self.public_key_pem,
            "identity_token": identity_token,
            "port": self.listen_port,
            "status": "online",
            "timestamp": time.time()
        }

        try:
            sock.sendto(json.dumps(response).encode("utf-8"), address)

        except OSError as exc:
            logger.debug("[DISCOVERY] send_response error: %s", exc)
            
    def update_peer_registry(
        self,
        packet: dict,
        address: tuple[str, int]
    ):
        """Update nearby peer registry."""
        peer_id = packet.get("peer_id")

        if not peer_id:
            return

        self.nearby_peers[
            peer_id
        ] = {
            "peer_id": peer_id,
            "username": packet.get("username"),
            "fingerprint": packet.get("fingerprint"),
            "ip": address[0],
            "tcp_port": packet.get("port"),
            "status": packet.get("status", "online"),
            "last_seen": time.time()
        }

    def get_nearby_peers(self) -> dict:
        """Return discovered peers."""
        return dict(self.nearby_peers)
  
    def cleanup_expired_peers(self):
        """Remove expired peers."""
        now = time.time()
        expired = []

        for peer_id, peer in (self.nearby_peers.items()):           
            if now - peer["last_seen"] > PEER_TIMEOUT:
                expired.append(peer_id)

        for peer_id in expired:
            del self.nearby_peers[peer_id]
