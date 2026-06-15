"""Main window container for P2PChat Sprint 3."""

from __future__ import annotations

import customtkinter as ctk

from gui.chatbox import ChatBox
from gui.sidebar import Sidebar
from gui.contact_panel import ContactPanel
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

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        self._build_chat_area()

        self._build_sidebar(
            on_peer_select,
            on_peer_connect,
            on_contact_select
        )

    # ==================================================
    # BUILD UI
    # ==================================================

    def _build_chat_area(self):

        self.chat_frame = ctk.CTkFrame(self)

        self.chat_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )

        self.chat_frame.grid_rowconfigure(1, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # ------------------------------------------------
        # Chat Header
        # ------------------------------------------------

        self.chat_header = ctk.CTkFrame(
            self.chat_frame,
            height=60
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

        self.chat_target_label = ctk.CTkLabel(
            self.chat_header,
            text="No peer selected",
            font=("Arial", 14, "bold"),
            anchor="w"
        )

        self.chat_target_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=(6, 0)
        )

        self.chat_info_label = ctk.CTkLabel(
            self.chat_header,
            text="Status: Offline | Trust: NEW",
            anchor="w",
            text_color="#a6adc8",
            font=("Consolas", 11)
        )

        self.chat_info_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=10,
            pady=(0, 6)
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
            placeholder_text="Enter message..."
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
            text="Send",
            width=100
        )

        self.send_button.grid(
            row=0,
            column=1,
            padx=(0, 5),
            pady=10
        )

        self.broadcast_button = ctk.CTkButton(
            self.input_frame,
            text="Broadcast",
            width=100
        )

        self.broadcast_button.grid(
            row=0,
            column=2,
            padx=(0, 10),
            pady=10
        )

    def _build_sidebar(
        self,
        on_peer_select,
        on_peer_connect,
        on_contact_select
    ):

        self.right_panel = ctk.CTkFrame(
            self,
            width=320
        )

        self.right_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )

        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=0)

        self.sidebar = Sidebar(
            self.right_panel,
            on_peer_select=on_peer_select,
            on_peer_connect=on_peer_connect
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.contact_panel = ContactPanel(
            self.right_panel,
            on_contact_select=on_contact_select
        )

        self.contact_panel.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.status_bar = StatusBar(
            self.right_panel
        )

        self.status_bar.grid(
            row=2,
            column=0,
            sticky="ew"
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

    # ==================================================
    # DISCOVERY API
    # ==================================================

    def update_discovered_peers(
        self,
        peers: dict
    ):
        self.sidebar.update_peers(peers)

    # ==================================================
    # CONTACT API
    # ==================================================

    def update_contacts(
        self,
        contacts: list
    ):
        if hasattr(
            self.contact_panel,
            "load_contacts"
        ):
            self.contact_panel.load_contacts(
                contacts
            )

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
        self.chat_target_label.configure(
            text=username
        )

        self.chat_info_label.configure(
            text=(
                f"Status: {status.upper()} | "
                f"Trust: {trust_state}"
            )
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
