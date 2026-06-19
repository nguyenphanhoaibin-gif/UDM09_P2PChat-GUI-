"""ChatController: thin adapter between P2PNode and the GUI layer."""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional, Tuple

from network.node import P2PNode
from storage.contact_book import ContactBook
from storage.message_history import MessageHistory
from trust.trust_state import TrustState

logger = logging.getLogger(__name__)


class ChatController:
    """Thin wrapper around P2PNode that exposes a clean interface for the GUI.

    Key design decision: the GUI works with **peer_id** (SHA-256 hash) for
    display and selection, but all networking calls (send_message, connect)
    use **tcp_address** ("IP:PORT"). This controller translates between them.
    """

    def __init__(
        self,
        on_system:          Callable[[str], None],
        on_message:         Callable[[str, str], None],
        on_connected:       Callable[[str], None],
        on_disconnect:      Callable[[str], None],
        on_peers_update:    Callable[[], None],
        on_peer_discovered: Optional[Callable[[str, dict], None]] = None,
    ) -> None:
        self.on_system          = on_system
        self.on_message         = on_message
        self.on_connected       = on_connected
        self.on_disconnect      = on_disconnect
        self.on_peers_update    = on_peers_update
        self.on_peer_discovered = on_peer_discovered

        self.node: Optional[P2PNode] = None

        # Storage
        self.contact_book    = ContactBook()
        self.message_history = MessageHistory()

        # Mapping peer_id → tcp_address for routing send_message
        self._peer_to_tcp:  dict[str, str] = {}
        # Mapping tcp_address → peer_id
        self._tcp_to_peer:  dict[str, str] = {}
        self._map_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Node lifecycle                                                       #
    # ------------------------------------------------------------------ #

    def start_node(self, host: str, port: int, username: str) -> Tuple[bool, str]:
        """Start the P2PNode. Returns (success, message)."""
        if self.node is not None:
            return False, "Node already started."

        self.node = P2PNode(
            host               = host,
            port               = port,
            username           = username,
            on_message         = self._on_message,
            on_disconnect      = self._on_disconnect,
            on_connected       = self._on_connected,
            on_peer_discovered = self._on_peer_discovered,
        )

        try:
            self.node.start_server()
        except OSError:
            logger.exception("Failed to start node")
            self.node = None
            return False, f"Could not bind to port {port}."

        peer_id = self.get_local_peer_id()
        fp      = self.get_local_fingerprint()
        return True, (
            f"Started as '{username}' on port {port}. "
            f"ID: {peer_id[:8]}… | FP: {fp[:11]}…"
        )

    def stop(self) -> None:
        if self.node is not None:
            self.node.stop_server()
            self.node = None

    # ------------------------------------------------------------------ #
    # Networking actions                                                   #
    # ------------------------------------------------------------------ #

    def connect_to_peer(self, ip: str, port: int) -> bool:
        """Connect to peer at ip:port. Returns success flag."""
        if self.node is None:
            self.on_system("Start the node first.")
            return False

        # Prevent self-connect
        if (
            ip in ("127.0.0.1", "localhost")
            and port == self.node.port
        ):
            self.on_system(
                "Cannot connect to yourself."
            )
            return False

        return self.node.connect_to_peer(ip,port)

    def send_message(self, payload: str, peer_id: str) -> bool:
        """Send message to *peer_id*.

        Translates peer_id → tcp_address before forwarding to node.
        """
        if self.node is None:
            self.on_system("Start the node first.")
            return False

        tcp_addr = self._peer_id_to_tcp(peer_id)
        if tcp_addr is None:
            logger.warning("No tcp_address for peer_id %s — cannot send", peer_id[:12])
            self.on_system(f"Peer not connected: {peer_id[:8]}…")
            return False

        ok = self.node.send_message(payload, tcp_addr)
        if ok:
            try:
                self.message_history.append_message(peer_id, {
                    "message_id": "",
                    "peer_id":    peer_id,
                    "direction":  "sent",
                    "content":    payload,
                    "timestamp":  __import__("time").time(),
                })
            except Exception:
                pass
        return ok

    def broadcast_message(self, payload: str) -> Tuple[int, int]:
        if self.node is None:
            self.on_system("Start the node first.")
            return 0, 0
        return self.node.broadcast_message(payload)

    def discover_peers(self) -> None:
        if self.node is not None:
            self.node.discover_peers()

    def get_discovered_peers(self) -> dict[str, dict]:
        if self.node is not None:
            return self.node.get_discovered_peers()
        return {}

    # ------------------------------------------------------------------ #
    # Identity / trust                                                     #
    # ------------------------------------------------------------------ #

    def get_local_peer_id(self) -> str:
        if self.node is None:
            return ""
        return self.node.identity_manager.get_peer_id()

    def get_local_fingerprint(self) -> str:
        if self.node is None:
            return ""
        return self.node.identity_manager.get_fingerprint()

    def get_trust_state(self, peer_id: str) -> str:
        if self.node is None:
            return TrustState.NEW
        return self.node.get_trust_state(peer_id)

    def trust_peer(self, peer_id: str) -> None:
        if self.node is not None:
            ok = self.node.trust_peer(peer_id)
            if not ok:
                self.on_system(f"Peer {peer_id[:8]}… not found in trust store.")

    def block_peer(self, peer_id: str) -> None:
        if self.node is not None:
            ok = self.node.block_peer(peer_id)
            if not ok:
                self.on_system(f"Peer {peer_id[:8]}… not found in trust store.")

    def get_peer_info(self, peer_id: str) -> Optional[dict]:
        return self.get_discovered_peers().get(peer_id)

    # ------------------------------------------------------------------ #
    # Address translation helpers                                         #
    # ------------------------------------------------------------------ #

    def register_peer_tcp(self, peer_id: str, tcp_addr: str) -> None:
        """Register the peer_id → tcp_address mapping."""
        with self._map_lock:
            self._peer_to_tcp[peer_id] = tcp_addr
            self._tcp_to_peer[tcp_addr] = peer_id

    def _peer_id_to_tcp(self, peer_id: str) -> Optional[str]:
        """Return tcp_address for peer_id, or None."""
        with self._map_lock:
            tcp = self._peer_to_tcp.get(peer_id)
        if tcp:
            return tcp
        # Fallback: look in discovered_peers which carries tcp_address
        peers = self.get_discovered_peers()
        info  = peers.get(peer_id)
        if info:
            return info.get("tcp_address")
        return None

    def _tcp_to_peer_id(self, tcp_addr: str) -> Optional[str]:
        with self._map_lock:
            return self._tcp_to_peer.get(tcp_addr)

    # ------------------------------------------------------------------ #
    # Internal callbacks                                                   #
    # ------------------------------------------------------------------ #

    def _safe_fire(self, cb: Optional[Callable], *args) -> None:
        if cb is None:
            return
        try:
            cb(*args)
        except Exception:
            logger.exception("Controller callback raised an exception")

    def _on_message(self, sender: str, payload: str) -> None:
        self._safe_fire(self.on_message, sender, payload)

    def _on_connected(self, tcp_addr: str) -> None:
        """node fires connected with tcp_addr; translate to peer_id for GUI."""
        # Register mapping if we can find the peer_id from discovered_peers
        peer_id = self._tcp_to_peer_id(tcp_addr)
        if peer_id is None:
            # Try to find from discovered_peers by tcp_address
            for pid, info in self.get_discovered_peers().items():
                if info.get("tcp_address") == tcp_addr:
                    peer_id = pid
                    self.register_peer_tcp(pid, tcp_addr)
                    break

        display = peer_id[:12] + "…" if peer_id else tcp_addr
        self._safe_fire(self.on_connected,display)
        self._safe_fire(self.on_peers_update)

    def _on_disconnect(self, tcp_addr: str) -> None:
        with self._map_lock:
            peer_id = self._tcp_to_peer.pop(tcp_addr, None)
            if peer_id:
                self._peer_to_tcp.pop(peer_id, None)
        self._safe_fire(self.on_disconnect, tcp_addr)
        self._safe_fire(self.on_peers_update)

    def _on_peer_discovered(self, peer_id: str, info: dict) -> None:
        # Keep tcp mapping fresh whenever we get a discovery update
        print(
            "[CTRL] peer discovered:",
            peer_id,
            info.get("username"),
        )
        tcp_addr = info.get("tcp_address")
        if tcp_addr:
            self.register_peer_tcp(peer_id, tcp_addr)
        self._safe_fire(self.on_peer_discovered, peer_id, info)
        self._safe_fire(self.on_peers_update)
