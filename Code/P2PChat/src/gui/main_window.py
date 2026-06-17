"""Main window container for P2PChat Sprint 3."""

from __future__ import annotations

import customtkinter as ctk

from gui.chatbox import ChatBox
from gui.sidebar import Sidebar
from gui.peer_details import PeerDetails
from gui.statusbar import StatusBar

class MainWindow(ctk.CTkFrame):
    """
    Main GUI coordinator.

    Responsibilities:
    - Layout management
    - Sidebar integration
    - Contact integration
    - Chat integration
    - Status integration
    """
    
    def __init__(
        self,
        master,
        on_peer_select=None,
        on_peer_connect=None,
        on_contact_select=None
    ):
        super().__init__(master)

        self.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=6)
        self.grid_columnconfigure(2, weight=2)

        self._build_chat_area()
        self._build_peer_details()
        self._build_sidebar(
            on_peer_select,
            on_peer_connect,
            on_contact_select
        )

    # ==================================================
    # BUILD UI
    # ==================================================

    def _build_chat_area(self):

        self.chat_frame = ctk.CTkFrame(
            self,
            fg_color="#1e1e2e"
        )

        self.chat_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=5,
            pady=10
        )

        self.chat_frame.grid_rowconfigure(1, weight=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # ------------------------------------------------
        # Chat Header
        # ------------------------------------------------

        self.chat_header = ctk.CTkFrame(
            self.chat_frame,
            height=64,
            fg_color="#181825",
            corner_radius=14
        )

        self.chat_header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=(10, 5)
        )

        self.chat_header.grid_columnconfigure(
            0,
            weight=1
        )

        # ==================================================
        # Peer Avatar
        # ==================================================

        self.avatar_label = ctk.CTkLabel(
            self.chat_header,
            text="👤",
            font=("Segoe UI Emoji", 26)
        )

        self.avatar_label.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(10, 10),
            pady=6
        )

        # ==================================================
        # Username
        # ==================================================

        self.chat_target_label = ctk.CTkLabel(
            self.chat_header,
            text="No peer selected",
            font=("Arial", 15, "bold"),
            anchor="w"
        )

        self.chat_target_label.grid(
            row=0,
            column=1,
            sticky="w",
            pady=(6, 0)
        )

        # ==================================================
        # Status
        # ==================================================

        self.chat_info_label = ctk.CTkLabel(
            self.chat_header,
            text="⚪ Offline | NEW",
            text_color="#a6adc8",
            font=("Consolas", 11),
            anchor="w"
        )

        self.chat_info_label.grid(
            row=1,
            column=1,
            sticky="w",
            pady=(0, 6)
        )

        self.chat_header.grid_columnconfigure(
            1,
            weight=1
        )

        # ------------------------------------------------
        # Chat Box
        # ------------------------------------------------

        self.chat_box = ChatBox(
            self.chat_frame
        )

        self.chat_box.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=5
        )
        
        self.empty_label = ctk.CTkLabel(
            self.chat_frame,
            text=(
                "💬\n\n"
                "Select a peer to start chatting"
            ),
            text_color="#6c7086",
            font=("Arial", 18)
        )

        self.empty_label.place(
            relx=0.5,
            rely=0.45,
            anchor="center"
        )

        # ------------------------------------------------
        # Input Area
        # ------------------------------------------------

        self.input_frame = ctk.CTkFrame(
            self.chat_frame
        )

        self.input_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=10,
            pady=(5, 10)
        )

        self.input_frame.grid_columnconfigure(
            0,
            weight=1
        )

        self.message_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type a message...",
            height=42,
            corner_radius=21,
            font=("Arial", 13)
        )

        self.message_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(10, 5),
            pady=10
        )

        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="➤",
            width=48,
            height=42,
            corner_radius=21,
            font=("Arial", 15, "bold")
        )

        self.send_button.grid(
            row=0,
            column=1,
            padx=(0, 5),
            pady=10
        )

        self.broadcast_button = ctk.CTkButton(
            self.input_frame,
            text="📢",
            width=48,
            height=42,
            corner_radius=21,
            fg_color="#45475a",
            hover_color="#585b70"
        )

        self.broadcast_button.grid_remove()

    def _build_sidebar(
        self,
        on_peer_select,
        on_peer_connect,
        on_contact_select
    ):

        self.sidebar = Sidebar(
            self,
            on_peer_select=on_peer_select,
            on_peer_connect=on_peer_connect
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )

        self.status_bar = StatusBar(
            self
        )

        self.status_bar.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew"
        )
    
    def _build_peer_details(self):

        self.details_panel = PeerDetails(
            self
        )

        self.details_panel.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )
        
    # ==================================================
    # CALLBACKS
    # ==================================================

    def set_send_callback(self, callback):

        self.send_button.configure(
            command=callback
        )

        self.message_entry.bind(
            "<Return>",
            lambda _e: callback()
        )

    def set_broadcast_callback(self, callback):

        self.broadcast_button.configure(
            command=callback
        )

    # ==================================================
    # CHAT API
    # ==================================================

    def add_system_message(self, message: str):
        self.chat_box.add_system(message)

    def add_received_message(
        self,
        sender: str,
        message: str
    ):
        self.chat_box.add_received(
            sender,
            message
        )

    def add_sent_message(
        self,
        sender: str,
        recipient: str,
        message: str
    ):
        self.chat_box.add_sent(
            sender,
            recipient,
            message
        )

    def clear_chat(self):
        self.chat_box.clear()
        
    def update_peer_details(
        self,
        peer_info: dict
    ):
        self.details_panel.update_peer(
            peer_info
        )

    # ==================================================
    # DISCOVERY API
    # ==================================================

    def update_discovered_peers(
        self,
        peers: dict
    ):
        self.sidebar.update_peers(peers)
        self.status_bar.set_stats(
            peers=len(peers),
            contacts=0,
            connected=0
        )
    # ==================================================
    # CONTACT API
    # ==================================================

    def update_contacts(
        self,
        contacts: list
    ):
        """
        Reserved for ContactBook integration.
        """
        pass

    # ==================================================
    # STATUS API
    # ==================================================

    def set_status(
        self,
        text: str,
        color: str = "#a6adc8"
    ):
        self.status_bar.set_status(
            text,
            color
        )

    # ==================================================
    # CHAT HEADER API
    # ==================================================

    def set_active_chat(
        self,
        username: str,
        status: str = "offline",
        trust_state: str = "NEW"
    ):
        
        if hasattr(self, "empty_label"):
            self.empty_label.place_forget()

        status_icon = {
            "online": "🟢",
            "connected": "🔗",
            "offline": "⚪",
            "connecting": "🟡"
        }.get(
            status,
            "⚪"
        )

        trust_color = {
            "NEW": "#f9e2af",
            "TRUSTED": "#89b4fa",
            "VERIFIED": "#a6e3a1",
            "MISMATCH": "#f38ba8",
            "BLOCKED": "#6c7086"
        }.get(
            trust_state,
            "#a6adc8"
        )

        self.chat_target_label.configure(
            text=username
        )

        self.chat_info_label.configure(
            text=f"{status_icon} {status.capitalize()} | 🔐 {trust_state}",
            text_color=trust_color
        )

    # ==================================================
    # INPUT API
    # ==================================================

    def get_message_text(self) -> str:
        return self.message_entry.get()

    def clear_message_text(self):
        self.message_entry.delete(0, "end")

    def focus_message_box(self):
        self.message_entry.focus_set()

    def enable_input(self):
        self.message_entry.configure(
            state="normal"
        )
        self.send_button.configure(
            state="normal"
        )

    def disable_input(self):
        self.message_entry.configure(
            state="disabled"
        )
        self.send_button.configure(
            state="disabled"
        )
        
    def set_trust_callback(
        self,
        callback
    ):
        self.details_panel.set_trust_callback(
            callback
        )


    def set_block_callback(
        self,
        callback
    ):
        self.details_panel.set_block_callback(
            callback
        )