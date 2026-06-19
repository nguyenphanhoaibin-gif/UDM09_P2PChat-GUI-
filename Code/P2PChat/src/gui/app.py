"""ChatApp: main application entry point and controller bridge (Sprint 3)."""
from __future__ import annotations

import socket
import customtkinter as ctk

from config import configure_logging, WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_LISTEN_PORT
from controllers.controller import ChatController
from gui.main_window import MainWindow
from gui.ui_state import UIState
from trust.trust_state import TrustState

configure_logging()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ChatApp(ctk.CTk):
    """Root Tk window.  Owns the controller and wires all callbacks."""

    def __init__(self, listen_port: int = DEFAULT_LISTEN_PORT) -> None:
        super().__init__()

        self.listen_port = listen_port
        self.title("P2P Chat — UDM_09")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(960, 600)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── State ─────────────────────────────────────────────────────
        self.ui_state = UIState()
        # selected_peer_id is the SHA-256 hash key used in discovered_peers
        self.selected_peer_id: str | None = None

        # ── Controller ────────────────────────────────────────────────
        self.controller = ChatController(
            on_system          = self._on_system,
            on_message         = self._on_message,
            on_connected       = self._on_connected,
            on_disconnect      = self._on_disconnect,
            on_peers_update    = self._on_peers_update,
            on_peer_discovered = self._on_peer_discovered,
        )

        # ── Main window ───────────────────────────────────────────────
        self.main_window = MainWindow(
            self,
            on_peer_select    = self._handle_peer_selected,
            on_peer_connect   = self._handle_peer_connect,
            on_contact_select = self._handle_contact_selected,
            on_trust          = self._handle_trust,
            on_block          = self._handle_block,
            on_manual_connect = self._handle_manual_connect,
            on_broadcast      = self._handle_broadcast,
        )
        self.main_window.set_send_callback(self._handle_send_message)

        # ── Start node ────────────────────────────────────────────────
        username = socket.gethostname()
        ok, msg  = self.controller.start_node("0.0.0.0", listen_port, username)
        self.main_window.set_status(msg, "#a6e3a1" if ok else "#f38ba8")

        if ok:
            # Show own identity in status bar
            pid = self.controller.get_local_peer_id()
            fp  = self.controller.get_local_fingerprint()
            self.main_window.set_identity(pid[:16] + "…", fp[:23] + "…")
            self.controller.discover_peers()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # Controller → GUI callbacks (always marshalled to Tk thread)         #
    # ------------------------------------------------------------------ #

    def _on_system(self, message: str) -> None:
        self.after(0, lambda: self.main_window.add_system_message(message))

    def _on_message(self, sender: str, payload: str) -> None:
        self.after(0, lambda: self.main_window.add_received_message(sender, payload))

    def _on_connected(self, tcp_addr: str) -> None:
        def _upd():
            self.ui_state.set_connection_status("connected")
            # Find which peer_id maps to this tcp_addr and mark connected
            for pid, info in self.ui_state.discovered_peers.items():
                if info.get("tcp_address") == tcp_addr:
                    info["connected"] = True
                    info["status"]    = "connected"
                    self.ui_state.discovered_peers[pid] = info
                    break
            self.main_window.update_discovered_peers(self.ui_state.discovered_peers)
            self.main_window.set_status(f"🔗 Connected: {tcp_addr}", "#a6e3a1")
            self._refresh_stats()
        self.after(0, _upd)

    def _on_disconnect(self, tcp_addr: str) -> None:
        def _upd():
            self.ui_state.set_connection_status("offline")
            for pid, info in self.ui_state.discovered_peers.items():
                if info.get("tcp_address") == tcp_addr:
                    info["connected"] = False
                    info["status"]    = "online"
                    break
            # If the disconnected peer was selected, clear chat header
            if self.selected_peer_id:
                sel_info = self.ui_state.discovered_peers.get(self.selected_peer_id, {})
                if sel_info.get("tcp_address") == tcp_addr:
                    self.main_window.set_active_chat(
                        username    = sel_info.get("username", "?"),
                        status      = "offline",
                        trust_state = sel_info.get("trust_state", TrustState.NEW),
                    )
            self.main_window.update_discovered_peers(self.ui_state.discovered_peers)
            self.main_window.set_status(f"❌ Disconnected: {tcp_addr}", "#f38ba8")
            self._refresh_stats()
        self.after(0, _upd)

    def _on_peers_update(self) -> None:
        self.after(0, self._refresh_stats)

    def _on_peer_discovered(self, peer_id: str, info: dict) -> None:
        def _upd():
            self.ui_state.update_discovered_peer(peer_id,info)
            self.main_window.update_discovered_peers(
                self.ui_state.discovered_peers
            )
            status = info.get(
                "status",
                "online"
            )
            uname = info.get(
                "username",
                peer_id[:8]
            )
            if status == "online":
                self.main_window.set_status(
                    f"📡 Discovered: {uname}"
                )
            if peer_id == self.selected_peer_id:
                self.main_window.update_peer_details(info)
                self.main_window.set_active_chat(
                    username=info.get(
                        "username",
                        peer_id
                    ),
                    status=info.get(
                        "status",
                        "online"
                    ),
                    trust_state=info.get(
                        "trust_state",
                        TrustState.NEW
                    ),
                )
            self._refresh_stats()
        self.after(0, _upd)

    # ------------------------------------------------------------------ #
    # GUI → Controller callbacks                                           #
    # ------------------------------------------------------------------ #

    def _handle_peer_selected(self, peer_id: str, peer_info: dict) -> None:
        """User clicked a peer card in the sidebar."""
        self.selected_peer_id = peer_id
        self.ui_state.select_peer(peer_id)
        self.main_window.update_peer_details(peer_info)
        self.main_window.set_active_chat(
            username    = peer_info.get("username", peer_id),
            status      = peer_info.get("status", "offline"),
            trust_state = peer_info.get("trust_state", TrustState.NEW),
        )

    def _handle_peer_connect(self, peer_id: str, peer_info: dict) -> None:
        """User clicked Connect on a peer card."""
        ip   = peer_info.get("ip")
        port = peer_info.get("port")
        if not ip or not port:
            self.main_window.set_status("Missing IP/port for peer.", "#f38ba8")
            return
        self.main_window.set_status(f"Connecting to {ip}:{port}…", "#f9e2af")
        ok = self.controller.connect_to_peer(ip, int(port))
        if not ok:
            self.main_window.set_status(f"Connection failed: {ip}:{port}", "#f38ba8")

    def _handle_contact_selected(self, contact: dict) -> None:
        pass  # reserved

    def _handle_trust(self, peer_id: str) -> None:
        self.controller.trust_peer(peer_id)
        self._refresh_peer_info(peer_id)
        self.main_window.set_status(f"✅ Trusted: {peer_id[:12]}…", "#a6e3a1")

    def _handle_block(self, peer_id: str) -> None:
        self.controller.block_peer(peer_id)
        self._refresh_peer_info(peer_id)
        self.main_window.set_status(f"🚫 Blocked: {peer_id[:12]}…", "#f38ba8")

    def _handle_manual_connect(self, ip: str, port_str: str) -> None:
        """Manual IP/port connect from the sidebar."""
        from network.validation import validate_ip, validate_port
        if not validate_ip(ip):
            self.main_window.set_status("Invalid IP address.", "#f38ba8")
            return
        if not validate_port(port_str):
            self.main_window.set_status("Invalid port number.", "#f38ba8")
            return
        self.main_window.set_status(f"Connecting to {ip}:{port_str}…", "#f9e2af")
        ok = self.controller.connect_to_peer(ip, int(port_str))
        if not ok:
            self.main_window.set_status(f"Connection failed: {ip}:{port_str}", "#f38ba8")

    def _handle_broadcast(self) -> None:
        message = self.main_window.get_message_text().strip()
        if not message:
            return
        sent, failed = self.controller.broadcast_message(message)
        if sent > 0:
            self.main_window.add_sent_message("Me", "Everyone", message)
            self.main_window.clear_message_text()
            self.main_window.set_status(f"📢 Broadcast sent to {sent} peer(s).")
        if failed:
            self.main_window.set_status(f"⚠ Broadcast failed for {failed} peer(s).", "#f9e2af")

    def _handle_send_message(self) -> None:
        if self.selected_peer_id is None:
            self.main_window.set_status("Select a peer first.", "#f9e2af")
            return
        message = self.main_window.get_message_text().strip()
        if not message:
            return
        ok = self.controller.send_message(message, self.selected_peer_id)
        if ok:
            sel_info = self.ui_state.discovered_peers.get(self.selected_peer_id, {})
            self.main_window.add_sent_message(
                "Me", sel_info.get("username", self.selected_peer_id[:8]), message
            )
            self.main_window.clear_message_text()
        else:
            self.main_window.set_status("Send failed — peer not connected.", "#f38ba8")

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _refresh_peer_info(self, peer_id: str) -> None:
        """Re-read trust state from node and update UI."""
        info = self.ui_state.discovered_peers.get(peer_id)
        if info is None:
            return
        ts = self.controller.get_trust_state(peer_id)
        info["trust_state"] = ts
        self.ui_state.discovered_peers[peer_id] = info
        self.main_window.update_discovered_peers(self.ui_state.discovered_peers)
        if peer_id == self.selected_peer_id:
            self.main_window.update_peer_details(info)
            self.main_window.set_active_chat(
                username    = info.get("username", peer_id),
                status      = info.get("status", "online"),
                trust_state = ts,
            )

    def _refresh_stats(self) -> None:
        peers     = len(self.ui_state.discovered_peers)
        connected = sum(
            1 for i in self.ui_state.discovered_peers.values()
            if i.get("connected") or i.get("status") == "connected"
        )
        self.main_window.update_stats(
            peers=peers,
            connected=connected,
            contacts=len(self.controller.contact_book.get_all_contacts()),
        )

    def _on_close(self) -> None:
        try:
            self.controller.stop()
        finally:
            self.destroy()
