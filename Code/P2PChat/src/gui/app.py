"""ChatApp: root window — owns the controller and wires all callbacks."""
from __future__ import annotations

import socket
import threading
import time
import uuid
import customtkinter as ctk

from config import (
    configure_logging, WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_LISTEN_PORT,
)
from controllers.controller import ChatController
from gui import theme as T
from gui.main_window import MainWindow
from gui.ui_state import UIState
from trust.trust_state import TrustState

configure_logging()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ChatApp(ctk.CTk):
    """Root Tk window — owns the controller and wires all GUI callbacks."""

    def __init__(self, listen_port: int = DEFAULT_LISTEN_PORT) -> None:
        super().__init__()

        self.listen_port = listen_port
        self.title("P2PChat")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(960, 620)
        self.configure(fg_color=T.BG_APP)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.ui_state = UIState()
        self.selected_peer_id: str | None = None
        self._peers_update_pending = False
        self._closing = False          # guard against double-close
        self._toast_after: str | None = None   # pending after() id for toast

        # Per-conversation message log, keyed by peer_id.
        # Each entry: list of (direction, sender, text) tuples.
        # "direction" is "in" or "out". Lets us show only the selected
        # peer's messages and reload history when switching peers.
        self._conversations: dict[str, list[tuple[str, str, str]]] = {}
        # Unread counts per peer_id (cleared when the peer is selected).
        self._unread: dict[str, int] = {}

        # ── Controller ────────────────────────────────────────────────
        self.controller = ChatController(
            on_system = self._on_system,
            on_message = self._on_message,
            on_connected = self._on_connected,
            on_disconnect = self._on_disconnect,
            on_peers_update = self._on_peers_update,
            on_peer_discovered = self._on_peer_discovered,
        )

        # ── Main window ───────────────────────────────────────────────
        self.main_window = MainWindow(
            self,
            on_peer_select = self._handle_peer_selected,
            on_peer_connect = self._handle_peer_connect,
            on_contact_select = self._handle_contact_selected,
            on_trust = self._handle_trust,
            on_block = self._handle_block,
            on_manual_connect = self._handle_manual_connect,
            on_broadcast = self._handle_broadcast,
            on_disconnect = self._handle_disconnect,
        )
        self.main_window.set_send_callback(self._handle_send_message)

        # ── Toast overlay (created once, hidden by default) ───────────
        self._toast = ctk.CTkLabel(
            self, text="", height=32, corner_radius=10,
            fg_color=T.BG_TOAST, text_color=T.TEXT_PRI,
            font=("Segoe UI", 11), padx=16)
        # Not placed until first toast

        # ── Start node (in background thread so UI appears immediately) ─
        self._boot_ui()
        threading.Thread(target=self._start_node_bg,
                         daemon=True, name="NodeBoot").start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # Boot sequence                                                        #
    # ------------------------------------------------------------------ #

    def _boot_ui(self) -> None:
        """Show the 'starting…' state while the node initialises."""
        self.main_window.set_status("Starting node…", T.WARNING)

    def _start_node_bg(self) -> None:
        """Start the P2P node in a background thread, then update UI."""
        username = socket.gethostname()
        ok, msg  = self.controller.start_node("0.0.0.0", self.listen_port, username)

        def _done() -> None:
            if ok:
                pid = self.controller.get_local_peer_id()
                fp  = self.controller.get_local_fingerprint()
                self.main_window.set_identity(pid[:16] + "…", fp[:23] + "…")
                self.main_window.set_status(
                    f"Online · port {self.listen_port}", T.SUCCESS)
                self.controller.discover_peers()
            else:
                self.main_window.set_status(msg, T.DANGER)
                self._toast_show(f"⚠  {msg}", T.DANGER)

        self.after(0, _done)

    # ------------------------------------------------------------------ #
    # Toast helper                                                         #
    # ------------------------------------------------------------------ #

    def _toast_show(self, text: str, color: str = T.TEXT_PRI,
                    duration_ms: int = 3000) -> None:
        """Show a transient toast at the bottom-centre for *duration_ms* ms."""
        self._toast.configure(text=text, text_color=color)
        self._toast.place(relx=0.5, rely=0.96, anchor="s")
        self._toast.lift()
        if self._toast_after:
            try:
                self.after_cancel(self._toast_after)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        self._toast_after = self.after(duration_ms, self._toast_hide)

    def _toast_hide(self) -> None:
        self._toast.place_forget()
        self._toast_after = None

    # ------------------------------------------------------------------ #
    # Controller → GUI (always marshalled to Tk thread via after(0, …))  #
    # ------------------------------------------------------------------ #

    def _on_system(self, message: str) -> None:
        self.after(0, lambda: self.main_window.add_system_message(message))

    def _on_message(self, peer_id: str, sender: str, payload: str) -> None:
        # Persist received message immediately (happens on the callback thread,
        # before marshalling to Tk — avoids losing messages if the UI thread
        # is busy). append_message does an atomic write, safe from any thread.
        self.controller.message_history.append_message(peer_id, {
            "message_id": str(uuid.uuid4()),
            "peer_id":    peer_id,
            "direction":  "received",
            "content":    payload,
            "timestamp":  time.time(),
        })

        def _upd() -> None:
            # Store in that peer's in-memory conversation log.
            self._conversations.setdefault(peer_id, []).append(("in", sender, payload))

            if peer_id == self.selected_peer_id:
                self.main_window.add_received_message(sender, payload)
            else:
                self._unread[peer_id] = self._unread.get(peer_id, 0) + 1
                preview = payload[:38] + "…" if len(payload) > 38 else payload
                self._toast_show(f"💬  {sender}: {preview}")
                self._apply_unread_badges()
                self._schedule_peers_redraw()
        self.after(0, _upd)

    def _on_connected(self, peer_id: str, tcp_addr: str) -> None:
        def _upd() -> None:
            self.ui_state.set_connection_status("connected")
            # Use peer_id directly — no fragile tcp_address search loop.
            info = self.ui_state.discovered_peers.get(peer_id, {})
            info["connected"] = True
            info["status"]    = "connected"
            self.ui_state.discovered_peers[peer_id] = info
            peer_name = info.get("username", tcp_addr)

            self.main_window.status_bar.set_connected_peer(peer_name)
            self.main_window.set_status(f"Connected: {peer_name}", T.ACCENT)
            self._toast_show(f"🔗 Connected to {peer_name}", T.SUCCESS)

            # If this peer is currently selected, refresh header + details.
            if peer_id == self.selected_peer_id:
                self.main_window.set_active_chat(
                    username    = peer_name,
                    status      = "connected",
                    trust_state = info.get("trust_state", TrustState.NEW))
                self.main_window.update_peer_details(info)
            self._schedule_peers_redraw()
        self.after(0, _upd)

    def _on_disconnect(self, tcp_addr: str) -> None:
        def _upd() -> None:
            self.ui_state.set_connection_status("offline")
            peer_name = tcp_addr
            for pid, info in self.ui_state.discovered_peers.items():
                if info.get("tcp_address") == tcp_addr:
                    info["connected"] = False
                    info["status"]    = "online"
                    peer_name = info.get("username", tcp_addr)
                    self.ui_state.discovered_peers[pid] = info
                    break
            self.main_window.status_bar.set_disconnected()
            self.main_window.set_status(
                f"Disconnected: {peer_name}", T.WARNING)
            self._toast_show(f"🔌 {peer_name} disconnected", T.WARNING)
            if self.selected_peer_id:
                sel = self.ui_state.discovered_peers.get(
                    self.selected_peer_id, {})
                if sel.get("tcp_address") == tcp_addr:
                    self.main_window.set_active_chat(
                        username    = sel.get("username", "?"),
                        status      = "online",
                        trust_state = sel.get("trust_state", TrustState.NEW))
                    self.main_window.update_peer_details(sel)
            self._schedule_peers_redraw()
        self.after(0, _upd)

    def _on_peers_update(self) -> None:
        self.after(0, self._refresh_stats)

    def _on_peer_discovered(self, peer_id: str, info: dict) -> None:
        def _upd() -> None:
            self.ui_state.update_discovered_peer(peer_id, info)
            status = info.get("status", "online")
            if status == "online":
                self.main_window.status_bar.set_discovery(True)
            if peer_id == self.selected_peer_id:
                self.main_window.update_peer_details(info)
                self.main_window.set_active_chat(
                    username    = info.get("username", peer_id),
                    status      = status,
                    trust_state = info.get("trust_state", TrustState.NEW))
            self._schedule_peers_redraw()
        self.after(0, _upd)

    # ------------------------------------------------------------------ #
    # Throttled sidebar rebuild                                            #
    # ------------------------------------------------------------------ #

    def _schedule_peers_redraw(self) -> None:
        """Coalesce sidebar rebuilds to at most one per 300 ms."""
        if not self._peers_update_pending:
            self._peers_update_pending = True
            self.after(300, self._do_peers_redraw)

    def _do_peers_redraw(self) -> None:
        self._peers_update_pending = False
        self.main_window.update_discovered_peers(self.ui_state.discovered_peers)
        self._refresh_stats()

    # ------------------------------------------------------------------ #
    # GUI → Controller                                                     #
    # ------------------------------------------------------------------ #

    def _handle_peer_selected(self, peer_id: str, peer_info: dict) -> None:
        self.selected_peer_id = peer_id
        self.ui_state.select_peer(peer_id)

        # Clear unread badge for this peer.
        if self._unread.pop(peer_id, 0):
            self._apply_unread_badges()

        self.main_window.update_peer_details(peer_info)
        self.main_window.set_active_chat(
            username    = peer_info.get("username", peer_id),
            status      = peer_info.get("status", "offline"),
            trust_state = peer_info.get("trust_state", TrustState.NEW))

        # Reload this peer's conversation into the chat area.
        # On first select (or after restart), the in-memory log is empty — load
        # from MessageHistory on disk so previous sessions are visible.
        self.main_window.clear_chat()
        if peer_id not in self._conversations:
            records = self.controller.message_history.load_history(peer_id)
            if records:
                uname = peer_info.get("username", peer_id[:8])
                loaded: list[tuple[str, str, str]] = []
                for rec in records:
                    if rec.get("direction") == "sent":
                        loaded.append(("out", "Me", rec.get("content", "")))
                    else:
                        loaded.append(("in", uname, rec.get("content", "")))
                self._conversations[peer_id] = loaded

        for direction, sender, msg in self._conversations.get(peer_id, []):
            if direction == "out":
                self.main_window.add_sent_message(
                    "Me", peer_info.get("username", peer_id), msg)
            else:
                self.main_window.add_received_message(sender, msg)

        self.main_window.focus_message_box()

    def _apply_unread_badges(self) -> None:
        """Push unread counts into discovered_peers so the sidebar shows them."""
        for pid, info in self.ui_state.discovered_peers.items():
            info["unread"] = self._unread.get(pid, 0)

    def _handle_peer_connect(self, peer_id: str, peer_info: dict) -> None:  # pylint: disable=unused-argument
        # peer_id unused here — connect uses IP/port; peer_id is for dedup in node.
        ip   = peer_info.get("ip")
        port = peer_info.get("port")
        if not ip or not port:
            self._toast_show("⚠  Missing IP/port for peer.", T.DANGER)
            return
        self.main_window.set_status(f"Connecting to {ip}:{port}…", T.WARNING)
        # Run connect in background so UI doesn't freeze on timeout
        def _connect() -> None:
            ok = self.controller.connect_to_peer(ip, int(port))
            if not ok:
                self.after(0, lambda: (
                    self.main_window.set_status(
                        f"Connection failed: {ip}:{port}", T.DANGER),
                    self._toast_show(f"⚠  Could not reach {ip}:{port}", T.DANGER),
                ))
        threading.Thread(target=_connect, daemon=True, name="Connect").start()

    def _handle_disconnect(self, peer_id: str) -> None:
        """Close the active session with *peer_id* (user pressed Disconnect)."""
        info = self.ui_state.discovered_peers.get(peer_id, {})
        name = info.get("username", peer_id[:8])
        ok = self.controller.disconnect_peer(peer_id)
        if ok:
            self._toast_show(f"🔌 Disconnected from {name}", T.WARNING)
        else:
            self._toast_show("Not connected.", T.TEXT_MUTED)
        # The node fires on_disconnect which will refresh the UI.

    def _handle_contact_selected(self, _contact: dict) -> None:
        """Reserved for contacts panel."""

    def _handle_trust(self, peer_id: str) -> None:
        """Trust or Unblock the peer, depending on current state."""
        info = self.ui_state.discovered_peers.get(peer_id, {})
        if info.get("trust_state") == "BLOCKED":
            # "Trust / Verify" button acts as Unblock when peer is blocked.
            self.controller.unblock_peer(peer_id)
            self._toast_show("↩  Peer unblocked", T.SUCCESS)
        else:
            self.controller.trust_peer(peer_id)
            self._toast_show("✓  Peer trusted", T.SUCCESS)
        self._refresh_peer_info(peer_id)

    def _handle_block(self, peer_id: str) -> None:
        """Block the peer and immediately disconnect them."""
        self.controller.block_peer(peer_id)
        self._refresh_peer_info(peer_id)
        self._toast_show("⊘  Peer blocked — connection closed", T.DANGER)
        # If we were chatting with this peer, update the header.
        if peer_id == self.selected_peer_id:
            info = self.ui_state.discovered_peers.get(peer_id, {})
            self.main_window.set_active_chat(
                username    = info.get("username", peer_id),
                status      = "offline",
                trust_state = "BLOCKED")

    def _handle_manual_connect(self, ip: str, port_str: str) -> None:
        from network.validation import validate_ip, validate_port  # pylint: disable=import-outside-toplevel
        if not validate_ip(ip):
            self._toast_show("⚠  Invalid IP address.", T.DANGER)
            return
        if not validate_port(port_str):
            self._toast_show("⚠  Invalid port number.", T.DANGER)
            return
        self.main_window.set_status(f"Connecting to {ip}:{port_str}…", T.WARNING)
        def _connect() -> None:
            ok = self.controller.connect_to_peer(ip, int(port_str))
            if not ok:
                self.after(0, lambda: self._toast_show(
                    f"⚠  Could not reach {ip}:{port_str}", T.DANGER))
        threading.Thread(target=_connect, daemon=True, name="ManualConnect").start()

    def _handle_broadcast(self) -> None:
        msg = self.main_window.get_message_text().strip()
        if not msg:
            return
        sent, failed = self.controller.broadcast_message(msg)
        if sent:
            self.main_window.add_sent_message("Me", "Everyone", msg)
            self.main_window.clear_message_text()
            self._toast_show(f"📢 Sent to {sent} peer(s)", T.SUCCESS)
        if failed:
            self._toast_show(f"⚠  Failed for {failed} peer(s)", T.WARNING)

    def _handle_send_message(self) -> None:
        if self.selected_peer_id is None:
            self._toast_show("Select a peer first.", T.WARNING)
            return
        msg = self.main_window.get_message_text().strip()
        if not msg:
            return

        # Guard: don't allow sending to a BLOCKED peer.
        sel = self.ui_state.discovered_peers.get(self.selected_peer_id, {})
        if sel.get("trust_state") == TrustState.BLOCKED:
            self._toast_show("⊘  Peer is blocked — unblock to chat.", T.DANGER)
            return

        ok = self.controller.send_message(msg, self.selected_peer_id)
        if ok:
            # Store in conversation log + render.
            self._conversations.setdefault(self.selected_peer_id, []).append(
                ("out", "Me", msg))
            self.main_window.add_sent_message(
                "Me", sel.get("username", self.selected_peer_id[:8]), msg)
            self.main_window.clear_message_text()
        else:
            self._toast_show("⚠  Not connected — press Connect first.", T.DANGER)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _refresh_peer_info(self, peer_id: str) -> None:
        info = self.ui_state.discovered_peers.get(peer_id)
        if info is None:
            return
        info["trust_state"] = self.controller.get_trust_state(peer_id)
        self.ui_state.discovered_peers[peer_id] = info
        self._schedule_peers_redraw()
        if peer_id == self.selected_peer_id:
            self.main_window.update_peer_details(info)
            self.main_window.set_active_chat(
                username    = info.get("username", peer_id),
                status      = info.get("status", "online"),
                trust_state = info.get("trust_state", TrustState.NEW))

    def _refresh_stats(self) -> None:
        peers     = len(self.ui_state.discovered_peers)
        connected = sum(
            1 for i in self.ui_state.discovered_peers.values()
            if i.get("connected") or i.get("status") == "connected")
        self.main_window.update_stats(
            peers     = peers,
            connected = connected,
            contacts  = len(self.controller.contact_book.get_all_contacts()))

    # ------------------------------------------------------------------ #
    # Graceful shutdown                                                    #
    # ------------------------------------------------------------------ #

    def _on_close(self) -> None:
        """Gracefully stop networking then destroy the window."""
        if self._closing:
            return
        self._closing = True

        self.main_window.set_status("Closing…", T.WARNING)
        self.update_idletasks()   # flush any pending redraws

        def _shutdown() -> None:
            try:
                self.controller.stop()
            finally:
                self.after(0, self.destroy)

        threading.Thread(target=_shutdown, daemon=True, name="Shutdown").start()
