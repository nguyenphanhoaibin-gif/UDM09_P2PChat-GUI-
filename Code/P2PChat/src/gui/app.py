import customtkinter as ctk
from gui.chatbox import ChatBox
from gui.validation import validate_ip, validate_port
from controllers.controller import ChatController
from app.config import configure_logging, DEFAULT_LISTEN_PORT
import threading

configure_logging()

class ChatApp(ctk.CTk):
    def __init__(self, listen_port: int = DEFAULT_LISTEN_PORT) -> None:
        super().__init__()

        self._peers_lock = threading.Lock()
        self.connected_peers: list[str] = []
        self.selected_peer: str | None = None

        self.controller: ChatController | None = None
        self._listen_port = listen_port

        self.setup_window()
        self.setup_layout()

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

    # Layout and event handlers
    def setup_window(self) -> None:
        """Configure the main application window."""

        self.title("UDM_09 · P2P Chat GUI")
        self.geometry("1000x600")
        self.minsize(900, 500)

    def setup_layout(self) -> None:
        """Create the main application layout."""

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_chat_section()
        self.create_sidebar()

    def create_chat_section(self) -> None:
        """Create the chat display section."""

        self.chat_frame = ctk.CTkFrame(self)

        self.chat_frame.grid(
            row=0,
            column=0,
            padx=(10, 5),
            pady=10,
            sticky="nsew"
        )

        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Chat display
        self.chat_box = ChatBox(self.chat_frame, corner_radius=10)

        self.chat_box.grid(
            row=0,
            column=0,
            padx=10,
            pady=(10, 5),
            sticky="nsew"
        )

        # Message input
        self.message_entry = ctk.CTkEntry(
            self.chat_frame,
            placeholder_text="Enter message..."
        )

        self.broadcast_button = ctk.CTkButton(
            self.chat_frame,
            text="📡 Broadcast",
            command=self.broadcast_message
        )

        self.broadcast_button.grid(
            row=1,
            column=1,
            padx=(5, 10),
            pady=(5, 10),
            sticky="ew"
        )

        self.message_entry.grid(
            row=1,
            column=0,
            padx=10,
            pady=(5, 10),
            sticky="ew"
        )

        self.message_entry.bind(
            "<Return>",
            self.handle_enter
        )

    def create_sidebar(self) -> None:
        """Create the peer management sidebar."""

        self.sidebar_frame = ctk.CTkFrame(self)

        self.sidebar_frame.grid(
            row=0,
            column=1,
            padx=(5, 10),
            pady=10,
            sticky="nsew"
        )

        ctk.CTkLabel(
            self.sidebar_frame, text="P2P Chat", font=("Arial", 18, "bold")
        ).pack(pady=(15, 4))

        ctk.CTkLabel(
            self.sidebar_frame, text="Your name", font=("Arial", 11)
        ).pack(padx=10, anchor="w")

        self.username_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Enter your name"
        )

        self.username_entry.pack(padx=10, pady=(2, 2), fill="x")

        ctk.CTkLabel(
            self.sidebar_frame, text="Listen port", font=("Arial", 11)
        ).pack(padx=10, anchor="w")

        self.listen_port_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text=str(self._listen_port)
        )

        self.listen_port_entry.insert(0, str(self._listen_port))
        self.listen_port_entry.pack(padx=10, pady=(2, 4), fill="x")

        self.start_button = ctk.CTkButton(
            self.sidebar_frame, text="Start", command=self.start_node
        )

        self.start_button.pack(padx=10, pady=(2, 12), fill="x")

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color="gray40").pack(
            fill="x", padx=10, pady=(0, 8)
        )

        # Connected peers section
        ctk.CTkLabel(
            self.sidebar_frame, text="Connected Peers", font=("Arial", 13, "bold")
        ).pack(pady=(0, 4))

        self.peer_listbox = ctk.CTkTextbox(
            self.sidebar_frame, width=250, height=200
        )

        self.peer_listbox.pack(
            padx=10, pady=5, fill="both", expand=True
        )

        self.peer_listbox.bind("<ButtonRelease-1>", self.select_peer)
        
        # New connection section
        ctk.CTkLabel(
            self.sidebar_frame, text="Peer IP", font=("Arial", 11)
        ).pack(padx=10, anchor="w")

        # Peer IP input
        self.ip_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="Peer IP"
        )

        self.ip_entry.pack(
            padx=10,
            pady=(2, 2),
            fill="x"
        )

        ctk.CTkLabel(
            self.sidebar_frame, text="Peer Port", font=("Arial", 11)
        ).pack(padx=10, anchor="w")

        # Peer port input
        self.port_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Port"
        )

        self.port_entry.pack(
            padx=10, pady=(2, 4), fill="x"
        )

        self.connect_button = ctk.CTkButton(
            self.sidebar_frame, text="Connect", command=self.connect_to_peer
        )

        self.connect_button.pack(
            padx=10, pady=(2,4), fill="x"
        )

        self.send_button = ctk.CTkButton(
            self.sidebar_frame, text="Send", command=self.send_message
        )

        self.send_button.pack(
            padx=10, pady=(2, 15), fill="x"
        )

        self.discover_button = ctk.CTkButton(self.sidebar_frame, text="Discover", command=self.discover_peers)
        self.discover_button.pack( fill="x", padx=10, pady=5)
    
    # Controller / node management
    def start_node(self) -> None:
        """Start the node via the ChatController."""

        if self.controller is not None:
            self.add_system_message("Node already started.")
            return

        username = self.username_entry.get().strip()

        if not username:
            self.add_system_message("Please enter your name before starting.")
            return

        port_text = self.listen_port_entry.get().strip()

        if not validate_port(port_text):
            self.add_system_message("Invalid listen port. Must be 1–65535.")
            return

        listen_port = int(port_text)

        # create controller with GUI callbacks
        self.controller = ChatController(
            on_system=self.add_system_message,
            on_message=self.handle_peer_message,
            on_connected=self.handle_connected,
            on_disconnect=self.handle_disconnect,
            on_peers_update=self.update_peer_list,
        )

        success, msg = self.controller.start_node("0.0.0.0", listen_port, username)

        if not success:
            self.add_system_message(f"Could not start on port {listen_port}: {msg}")
            self.controller = None
            return

        self.start_button.configure(state="disabled")
        self.username_entry.configure(state="disabled")
        self.listen_port_entry.configure(state="disabled")
        self.add_system_message(msg)

    # Event handlers
    def connect_to_peer(self) -> None:
        """Handle the Connect button."""
        if self.controller is None:
            self.add_system_message("Start the node first.")
            return

        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()

        if not ip or not port:
            self.add_system_message("Please enter peer IP and port.")
            return

        if not validate_ip(ip):
            self.add_system_message("Invalid IP address format.")
            return

        if not validate_port(port):
            self.add_system_message("Invalid port number. Must be 1 - 65535.")
            return

        self.add_system_message(f"Connecting to {ip}:{port}…")

        if not self.controller.connect_to_peer(ip, int(port)):
            self.add_system_message(f"Could not connect to {ip}:{port}.")
            return

        self.add_system_message("TCP connected — waiting for handshake…")

    def send_message(self) -> None:
        """Handle the Send button."""
        if self.controller is None:
            self.add_system_message("Start the node first.")
            return

        message = self.message_entry.get().strip()

        if not message:
            return
        
        with self._peers_lock:
            selected = self.selected_peer
            has_peers = bool(self.connected_peers)

        if not has_peers:
            self.add_system_message("No connected peers.")
            return

        if selected is None:
            self.add_system_message("No peer selected.")
            return
        
        sent = self.controller.send_message(message, selected)

        if sent:
            me = username = self.username_entry.get().strip() or "me"
            self.chat_box.add_sent(me, selected, message)
            self.message_entry.delete(0, "end")

        else:
            self.add_system_message(
                f"Failed to send — {selected} may have disconnected."
            )

    def broadcast_message(self) -> None:
        """Handle the Broadcast button."""
        if self.controller is None:
            self.add_system_message("Start the node first.")
            return
        
        message = self.message_entry.get().strip()

        if not message:
            return

        with self._peers_lock:
            has_peers = bool(self.connected_peers)

        if not has_peers:
            self.add_system_message("No connected peers.")
            return

        sent, failed = self.controller.broadcast_message(message)

        if sent > 0:
            me = self.username_entry.get().strip() or "me"
            self.chat_box.add_sent(me, "everyone", message)
            self.message_entry.delete(0, "end")

        if failed > 0:
            self.add_system_message(f"Broadcast failed for {failed} peer(s).")
        
        if sent == 0:
            self.add_system_message("Broadcast failed. No peer received the message.")
        
    def handle_enter(self, _event) -> str:
        self.send_message()
        return "break"  # prevent Enter from propagating to the widget

    def update_peer_list(self) -> None:
        """Refresh the connected-peers display in the sidebar."""

        self.peer_listbox.delete("1.0", "end")

        with self._peers_lock:
            peers = list(self.connected_peers)
            selected = self.selected_peer

        for peer in peers:
            marker = "▶ " if peer == selected else "  "
            self.peer_listbox.insert("end", f"{marker}{peer}\n")

    def select_peer(self, event) -> None:  
        """Handle peer selection in the listbox."""

        raw = self.peer_listbox.get("insert linestart", "insert lineend").strip()

        # Strip the selection marker if present.
        candidate = raw.lstrip("▶ ").strip()

        with self._peers_lock:
            is_valid = candidate in self.connected_peers

        if is_valid:
            with self._peers_lock:
                self.selected_peer = candidate
            self.update_peer_list()  # refresh markers
            self.add_system_message(f"Selected peer: {candidate}")

    def discover_peers(self):
        if self.controller is None:
            self.add_system_message("Start the node first.")
            return
        self.add_system_message("Discovering peers on the local network…")
        self.controller.discover_peers()
        self.after(1000, self.refresh_discovered_peers)

    def refresh_discovered_peers(self):
        if self.controller is None:
            return
        
        peers = (self.controller.get_discovered_peers())
        self.add_system_message(f"Discovered {len(peers)} peer(s) on the local network.")
        
        for addr, info in peers.items():
            username = info.get("username", "unknown")
            self.add_system_message(f" - {username} at {addr}")

    # Message handling (called from networking thread via controller)
    def add_system_message(self, message: str) -> None:
        """Display a system message. Safe to call from any thread."""
        self.chat_box.add_system(message)

    def handle_peer_message(self, sender: str, payload: str) -> None:
        self.chat_box.add_received(sender, payload)

    def handle_connected(self, peer_address: str) -> None:
        """Handle a new peer connection event (called from networking thread)."""
        def _update() -> None:
            with self._peers_lock:

                if peer_address not in self.connected_peers:
                    self.connected_peers.append(peer_address)

            self.update_peer_list()
            self.add_system_message(f"Peer connected and ready: {peer_address}")

        self.after(0, _update)

    def handle_disconnect(self, peer_address: str) -> None:
        """Handle a peer disconnection event (called from networking thread)."""

        def update() -> None:
            with self._peers_lock:

                if peer_address in self.connected_peers:
                    self.connected_peers.remove(peer_address)

                if self.selected_peer == peer_address:
                    self.selected_peer = None

            self.update_peer_list()
            self.add_system_message(f"Connection lost: {peer_address}")

        self.after(0, update)
    
    def handle_close(self) -> None:
        if self.controller is not None:
            self.controller.stop()
        self.destroy()
