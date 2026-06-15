"""Main GUI application for the P2P Chat."""

from __future__ import annotations

import threading
import customtkinter as ctk

from gui.main_window import MainWindow
from gui.validation import validate_ip, validate_port
from controllers.controller import ChatController
from config import configure_logging, DEFAULT_LISTEN_PORT  # ← fixed import
from gui.ui_state import UIState

configure_logging()

class ChatApp(ctk.CTk):
    """Main GUI window.  All networking callbacks are marshalled back to the
    Tk main thread via ``self.after(0, ...)`` before touching any widget.
    """

    def __init__(self, listen_port: int = DEFAULT_LISTEN_PORT) -> None:
        super().__init__()

        self._peers_lock     = threading.Lock()
        self.connected_peers: list[str] = []
        self.selected_peer:  str | None = None

        # Discovered LAN peers: addr → info dict
        self._disc_lock      = threading.Lock()
        self.discovered_peers: dict[str, dict] = {}

        self.controller: ChatController | None = None
        self.ui_state = UIState()
        self._listen_port = listen_port

        self._setup_window()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_window = MainWindow(
            self,
            on_peer_select=self._handle_peer_selected,
            on_peer_connect=self._handle_peer_connect
        )
        self.main_window.set_send_callback(self._send_message)
        self.main_window.set_broadcast_callback(self._broadcast_message)
        
        self.protocol("WM_DELETE_WINDOW", self._handle_close)

    # ------------------------------------------------------------------ #
    # UI setup and event handlers #
    def _setup_window(self) -> None:
        self.title("UDM_09 · P2P Chat")
        self.geometry("1100x640")
        self.minsize(900, 520)
        self.sidebar_frame = ctk.CTkFrame(self)
        self.sidebar_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.sidebar_frame, text="P2P Chat", font=("Arial", 18, "bold")
        ).pack(pady=(15, 4))

        # ── Identity ──────────────────────────────────────────────────
        ctk.CTkLabel(self.sidebar_frame, text="Your name", font=("Arial", 11)).pack(
            padx=10, anchor="w"
        )
        self.username_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Enter your name"
        )
        self.username_entry.pack(padx=10, pady=(2, 2), fill="x")

        ctk.CTkLabel(self.sidebar_frame, text="Listen port", font=("Arial", 11)).pack(
            padx=10, anchor="w"
        )
        self.listen_port_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text=str(self._listen_port)
        )
        self.listen_port_entry.insert(0, str(self._listen_port))
        self.listen_port_entry.pack(padx=10, pady=(2, 4), fill="x")

        self.start_button = ctk.CTkButton(
            self.sidebar_frame, text="Start", command=self._start_node
        )
        self.start_button.pack(padx=10, pady=(2, 10), fill="x")

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color="gray40").pack(
            fill="x", padx=10, pady=(0, 8)
        )

        # ── Connected peers ────────────────────────────────────────────
        ctk.CTkLabel(
            self.sidebar_frame, text="Connected Peers", font=("Arial", 13, "bold")
        ).pack(pady=(0, 4))

        self.peer_listbox = ctk.CTkTextbox(self.sidebar_frame, width=250, height=120)
        self.peer_listbox.pack(padx=10, pady=(0, 4), fill="x")
        self.peer_listbox.bind("<ButtonRelease-1>", self._select_peer)

        # ── Manual connect ─────────────────────────────────────────────
        ctk.CTkLabel(self.sidebar_frame, text="Peer IP", font=("Arial", 11)).pack(
            padx=10, anchor="w"
        )
        self.ip_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Peer IP")
        self.ip_entry.pack(padx=10, pady=(2, 2), fill="x")

        ctk.CTkLabel(self.sidebar_frame, text="Peer Port", font=("Arial", 11)).pack(
            padx=10, anchor="w"
        )
        self.port_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Port")
        self.port_entry.pack(padx=10, pady=(2, 4), fill="x")

        self.connect_button = ctk.CTkButton(
            self.sidebar_frame, text="Connect", command=self._connect_to_peer
        )
        self.connect_button.pack(padx=10, pady=(2, 4), fill="x")

        self.send_button = ctk.CTkButton(
            self.sidebar_frame, text="Send", command=self._send_message
        )
        self.send_button.pack(padx=10, pady=(2, 8), fill="x")

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color="gray40").pack(
            fill="x", padx=10, pady=(0, 8)
        )

        # ── LAN Discovery ─────────────────────────────────────────────
        ctk.CTkLabel(
            self.sidebar_frame, text="LAN Peers", font=("Arial", 13, "bold")
        ).pack(pady=(0, 4))

        self.discovery_listbox = ctk.CTkTextbox(
            self.sidebar_frame, width=250, height=120
        )
        self.discovery_listbox.pack(padx=10, pady=(0, 4), fill="x")
        self.discovery_listbox.bind("<ButtonRelease-1>", self._select_discovered_peer)

        btn_row = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        btn_row.pack(padx=10, pady=(2, 10), fill="x")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        self.discover_button = ctk.CTkButton(
            btn_row, text="🔍 Scan", command=self._discover_peers
        )
        self.discover_button.grid(row=0, column=0, padx=(0, 2), sticky="ew")

        self.connect_disc_button = ctk.CTkButton(
            btn_row, text="⚡ Connect", command=self._connect_discovered_peer
        )
        self.connect_disc_button.grid(row=0, column=1, padx=(2, 0), sticky="ew")

        self._selected_discovered: str | None = None

    # ------------------------------------------------------------------ #
    # Node lifecycle #
    def _start_node(self) -> None:
        if self.controller is not None:
            self._add_system("Node already started.")
            return

        username = self.username_entry.get().strip()
        if not username:
            self._add_system("Please enter your name before starting.")
            return

        port_text = self.listen_port_entry.get().strip()
        if not validate_port(port_text):
            self._add_system("Invalid listen port. Must be 1–65535.")
            return

        listen_port = int(port_text)

        self.controller = ChatController(
            on_system          = self._add_system,
            on_message         = self._handle_peer_message,
            on_connected       = self._handle_connected,
            on_disconnect      = self._handle_disconnect,
            on_peers_update    = self._update_peer_list,
            on_peer_discovered = self._handle_peer_discovered,
        )

        ok, msg = self.controller.start_node("0.0.0.0", listen_port, username)
        if not ok:
            self._add_system(f"Could not start on port {listen_port}: {msg}")
            self.controller = None
            return

        self.start_button.configure(state="disabled")
        self.main_window.disable_input()
        self.main_window.set_status(
            "Ready - Waiting for connections",
            "#89b4fa"
        )
        self.username_entry.configure(state="disabled")
        self.listen_port_entry.configure(state="disabled")
        self._add_system(msg)
        self.main_window.set_active_chat(
            username="No peer selected",
            status="offline",
            trust_state="NEW"
        )
        self.main_window.disable_input()

    # ------------------------------------------------------------------ #
    # Messaging actions #
    def _connect_to_peer(self) -> None:
        if self.controller is None:
            self._add_system("Start the node first.")
            return

        ip   = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()

        if not ip or not port:
            self._add_system("Please enter peer IP and port.")
            return
        if not validate_ip(ip):
            self._add_system("Invalid IP address format.")
            return
        if not validate_port(port):
            self._add_system("Invalid port number. Must be 1–65535.")
            return

        self._add_system(f"Connecting to {ip}:{port}…")

        if not self.controller.connect_to_peer(ip, int(port)):
            self._add_system(f"Could not connect to {ip}:{port}.")
            return

        self._add_system("TCP connected — waiting for handshake…")

    def _send_message(self) -> None:
        if self.controller is None:
            self._add_system("Start the node first.")
            return

        message = self.main_window.get_message_text().strip()
        
        if not message:
            return

        with self._peers_lock:
            selected  = self.selected_peer
            has_peers = bool(self.connected_peers)

        if not has_peers:
            self._add_system("No connected peers.")
            return
        if selected is None:
            self._add_system("No peer selected — click a peer in the list.")
            return

        if self.controller.send_message(message, selected):
            me = self.username_entry.get().strip() or "me"
            self.main_window.add_sent_message(me, selected, message)
            self.main_window.clear_message_text()
        else:
            self._add_system(f"Failed to send — {selected} may have disconnected.")

    def _broadcast_message(self) -> None:
        if self.controller is None:
            self._add_system("Start the node first.")
            return

        message = self.main_window.get_message_text().strip()
        if not message:
            return

        with self._peers_lock:
            has_peers = bool(self.connected_peers)

        if not has_peers:
            self._add_system("No connected peers.")
            return

        sent, failed = self.controller.broadcast_message(message)

        if sent > 0:
            me = self.username_entry.get().strip() or "me"
            self.main_window.add_sent_message(me, "everyone", message)
            self.main_window.clear_message_text()

        if failed > 0:
            self._add_system(f"Broadcast failed for {failed} peer(s).")

        if sent == 0:
            self._add_system("Broadcast failed — no peer received the message.")

    def _handle_enter(self, _event) -> str:
        self._send_message()
        return "break"

    # ------------------------------------------------------------------ #
    # LAN Discovery #

    def _discover_peers(self) -> None:
        if self.controller is None:
            self._add_system(
                "Start the node first."
            )
            return
        self.main_window.set_status(
            "🔍 Discovering peers...",
            "#89b4fa"
        )
        self._add_system(
            "Scanning LAN for peers…"
        )
        self.controller.discover_peers()
        self.after(
            1500,
            lambda: self.main_window.update_discovered_peers(
                self.discovered_peers
            )
        )

    def _refresh_discovery_panel(self) -> None:
        """Repaint the LAN-peers listbox from the current snapshot."""
        if self.controller is None:
            return

        with self._disc_lock:
            peers = dict(self.discovered_peers)

        self.discovery_listbox.configure(state="normal")
        self.discovery_listbox.delete("1.0", "end")

        if not peers:
            self.discovery_listbox.insert("end", "  (none found)\n")
        else:
            for addr, info in peers.items():
                status  = "●" if info.get("status") == "online" else "○"
                uname   = info.get("username", "?")
                connected_tag = " [connected]" if addr in self._get_connected_set() else ""
                marker  = "▶ " if addr == self._selected_discovered else "  "
                self.discovery_listbox.insert(
                    "end", f"{marker}{status} {uname} @ {addr}{connected_tag}\n"
                )

        self.discovery_listbox.configure(state="disabled")

    def _get_connected_set(self) -> set[str]:
        with self._peers_lock:
            return set(self.connected_peers)

    def _select_discovered_peer(self, _event) -> None:
        raw = self.discovery_listbox.get("insert linestart", "insert lineend").strip()
        # Lines look like: "▶ ● Alice @ 192.168.1.5:12000 [connected]"
        # We need the "ip:port" part.
        if " @ " not in raw:
            return
        addr_part = raw.split(" @ ")[-1].replace("[connected]", "").strip()

        with self._disc_lock:
            valid = addr_part in self.discovered_peers

        if valid:
            self._selected_discovered = addr_part
            self._refresh_discovery_panel()
            self._add_system(f"Selected LAN peer: {addr_part}")
            # Pre-fill the manual connect fields for convenience.
            parts = addr_part.rsplit(":", 1)
            if len(parts) == 2:
                self.ip_entry.delete(0, "end")
                self.ip_entry.insert(0, parts[0])
                self.port_entry.delete(0, "end")
                self.port_entry.insert(0, parts[1])

    def _connect_discovered_peer(self) -> None:
        """Connect to whichever LAN peer is currently selected."""
        if self._selected_discovered is None:
            self._add_system("Select a LAN peer first.")
            return

        addr = self._selected_discovered
        parts = addr.rsplit(":", 1)
        if len(parts) != 2 or not validate_port(parts[1]):
            self._add_system(f"Invalid peer address: {addr}")
            return

        ip, port = parts[0], int(parts[1])

        if self.controller is None:
            self._add_system("Start the node first.")
            return

        with self._peers_lock:
            if addr in self.connected_peers:
                self._add_system(f"Already connected to {addr}.")
                return

        self._add_system(f"Connecting to LAN peer {addr}…")
        if not self.controller.connect_to_peer(ip, port):
            self._add_system(f"Could not connect to {addr}.")

    # ------------------------------------------------------------------ #
    # Connected-peer actions #
    def _update_peer_list(self) -> None:
        """Refresh the connected-peers listbox. Safe to call from any thread."""
        self.after(0, self._repaint_peer_list)

    def _repaint_peer_list(self) -> None:
        self.peer_listbox.configure(state="normal")
        self.peer_listbox.delete("1.0", "end")

        with self._peers_lock:
            peers    = list(self.connected_peers)
            selected = self.selected_peer

        for peer in peers:
            marker = "▶ " if peer == selected else "  "
            self.peer_listbox.insert("end", f"{marker}{peer}\n")

        self.peer_listbox.configure(state="disabled")

    def _select_peer(self, _event) -> None:
        raw       = self.peer_listbox.get("insert linestart", "insert lineend").strip()
        candidate = raw.lstrip("▶ ").strip()

        with self._peers_lock:
            is_valid = candidate in self.connected_peers

        if is_valid:
            with self._peers_lock:
                self.selected_peer = candidate
            self._repaint_peer_list()
            self._add_system(f"Selected peer: {candidate}")

    # ------------------------------------------------------------------ #
    # System messages and callbacks #
    def _add_system(self, message: str) -> None:
        """Display a system message. Thread-safe via ChatBox queue."""
        self.main_window.add_system_message(message)

    def _handle_peer_message(self, sender: str, payload: str) -> None:
        self.main_window.add_received_message(sender, payload)

    def _handle_connected(self, peer_address: str) -> None:
        def _update() -> None:
            with self._peers_lock:
                if peer_address not in self.connected_peers:
                    self.connected_peers.append(peer_address)

            self._repaint_peer_list()
            self.main_window.set_status(
                f"Connected: {peer_address}",
                "#a6e3a1"
            )

            if self.selected_peer == peer_address:
                self.main_window.enable_input()

            self._add_system(f"Peer connected and ready: {peer_address}")
            
            with self._disc_lock:
                if peer_address in self.discovered_peers:
                    self.discovered_peers[peer_address]["connected"] = True
                    self.discovered_peers[peer_address]["status"] = "connected"

            self.main_window.update_discovered_peers(self.discovered_peers)
            self._refresh_discovery_panel()
            
        self.after(0, _update)

    def _handle_disconnect(self,peer_address: str) -> None:
        def _update() -> None:
            with self._peers_lock:
                if peer_address in self.connected_peers:
                    self.connected_peers.remove(peer_address)

                if self.selected_peer == peer_address:
                    self.selected_peer = None
                    self.main_window.set_active_chat(
                        username="No peer selected",
                        status="offline",
                        trust_state="NEW"
                    )
                    self.main_window.disable_input()

            self._repaint_peer_list()
            self.main_window.set_status(
                f"Disconnected: {peer_address}",
                "#f38ba8"
            )

            self._add_system(f"Connection lost: {peer_address}")

            with self._disc_lock:
                if peer_address in self.discovered_peers:
                    self.discovered_peers[peer_address]["connected"] = False
                    self.discovered_peers[peer_address]["status"] = "online"

            self.main_window.update_discovered_peers(
                self.discovered_peers
            )
            self._refresh_discovery_panel()

        self.after(0, _update)

    def _handle_peer_discovered(self, peer_address: str, info: dict) -> None:
        """
        Called from networking thread when a peer is discovered or updated.
        """
        def _update() -> None:
            with self._disc_lock:
                self.discovered_peers[peer_address] = info
                
            self.main_window.update_discovered_peers(self.discovered_peers)
            username = info.get("username", peer_address)
            status = info.get("status", "online")
            # Refresh header if selected peer changed
            if self.selected_peer == peer_address:
                self.main_window.set_active_chat(
                    username=username,
                    status=status,
                    trust_state=info.get(
                        "trust_state",
                        "NEW"
                    )
                )

            self.main_window.set_status(
                f"Discovery: {len(self.discovered_peers)} peer(s)"
            )

        self.after(0, _update)

    def _handle_close(self) -> None:
        if self.controller is not None:
            self.controller.stop()
        self.destroy()
        
    def _handle_peer_selected(self, peer_id, peer_info):
        """
        Called when a peer is selected from Sidebar.
        Updates chat header, status bar and loads history.
        """
        self.selected_peer = peer_id
        self.main_window.clear_chat()
        username = peer_info.get("username", peer_id)
        status = peer_info.get("status", "online")
        trust_state = peer_info.get("trust_state", "NEW")
        self.main_window.set_active_chat(
            username=username,
            status=status,
            trust_state=trust_state
        )
        self.main_window.enable_input()
        self.main_window.focus_message_box()
        self.main_window.set_status(
            f"Selected peer: {username}"
        )
        self._add_system(
            f"Selected peer: {username}"
        )
        """ Todo: Future update
        # --------------------------------------------------
        # Future MessageHistory Integration
        # --------------------------------------------------
        if (hasattr(self.controller, "load_history")and callable(self.controller.load_history)):
            try:
                history = self.controller.load_history(peer_id)
                self.main_window.clear_chat()
                
                for record in history:
                    direction = record.get("direction")
                    sender = record.get("sender", username)
                    content = record.get("content", "")
                    
                    if direction == "sent":
                        self.main_window.add_sent_message(
                            "me",
                            username,
                            content
                        )

                    else:
                        self.main_window.add_received_message(
                            sender,
                            content
                        )

            except Exception as exc:
                self._add_system(f"History load failed: {exc}")
        """

    def _handle_peer_connect(self, peer_id, peer_info):
        if self.controller is None:
            return
        ip = peer_info.get("ip")
        port = peer_info.get("port")
        if not ip or not port:
            return
        self.controller.connect_to_peer(ip, int(port))
