"""MainWindow: layout container and public API for all GUI subsystems."""
from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from gui.chatbox import ChatBox
from gui.sidebar import Sidebar
from gui.peer_details import PeerDetails
from gui.statusbar import StatusBar


class MainWindow(ctk.CTkFrame):
    """Three-column layout: Sidebar | ChatArea | PeerDetails."""

    def __init__(
        self,
        master,
        on_peer_select:    Optional[Callable] = None,
        on_peer_connect:   Optional[Callable] = None,
        on_contact_select: Optional[Callable] = None,
        on_trust:          Optional[Callable] = None,
        on_block:          Optional[Callable] = None,
        on_manual_connect: Optional[Callable] = None,
        on_broadcast:      Optional[Callable] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0)  # sidebar — fixed
        self.grid_columnconfigure(1, weight=1)  # chat    — flex
        self.grid_columnconfigure(2, weight=0)  # details — fixed

        self._build_sidebar(on_peer_select, on_peer_connect, on_manual_connect)
        self._build_chat_area()
        self._build_peer_details(on_trust, on_block)
        self._build_statusbar()

        # Wire broadcast button
        if on_broadcast:
            self.broadcast_button.configure(command=on_broadcast)

    # ------------------------------------------------------------------ #
    # Construction                                                         #
    # ------------------------------------------------------------------ #

    def _build_sidebar(self, on_peer_select, on_peer_connect, on_manual_connect) -> None:
        self.sidebar = Sidebar(
            self,
            on_peer_select    = on_peer_select,
            on_peer_connect   = on_peer_connect,
            on_manual_connect = on_manual_connect,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=10)

    def _build_chat_area(self) -> None:
        chat_frame = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=14)
        chat_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=10)
        chat_frame.grid_rowconfigure(1, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────
        header = ctk.CTkFrame(chat_frame, height=64, fg_color="#181825", corner_radius=14)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        header.grid_columnconfigure(1, weight=1)

        self.avatar_label = ctk.CTkLabel(
            header, text="💬", font=("Segoe UI Emoji", 26)
        )
        self.avatar_label.grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=6)

        self.chat_target_label = ctk.CTkLabel(
            header, text="No peer selected",
            font=("Arial", 15, "bold"), anchor="w",
        )
        self.chat_target_label.grid(row=0, column=1, sticky="w", pady=(8, 0))

        self.chat_info_label = ctk.CTkLabel(
            header, text="⚪ Offline  |  🔑 NEW",
            text_color="#6c7086", font=("Consolas", 11), anchor="w",
        )
        self.chat_info_label.grid(row=1, column=1, sticky="w", pady=(0, 8))

        # ── Chat box ──────────────────────────────────────────────────
        self.chat_box = ChatBox(chat_frame)
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)

        # Empty-state overlay
        self.empty_label = ctk.CTkLabel(
            chat_frame,
            text="💬\n\nSelect a peer from the sidebar\nto start chatting",
            text_color="#6c7086", font=("Arial", 16),
        )
        self.empty_label.place(relx=0.5, rely=0.45, anchor="center")

        # ── Input row ────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Type a message…",
            height=42, corner_radius=21, font=("Arial", 13),
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=8)

        self.send_button = ctk.CTkButton(
            input_frame, text="➤", width=48, height=42,
            corner_radius=21, font=("Arial", 15, "bold"),
        )
        self.send_button.grid(row=0, column=1, padx=(0, 4), pady=8)

        self.broadcast_button = ctk.CTkButton(
            input_frame, text="📢", width=48, height=42,
            corner_radius=21, fg_color="#45475a", hover_color="#585b70",
            font=("Segoe UI Emoji", 16),
        )
        self.broadcast_button.grid(row=0, column=2, padx=(0, 8), pady=8)

    def _build_peer_details(self, on_trust, on_block) -> None:
        self.details_panel = PeerDetails(
            self,
            on_trust = on_trust,
            on_block = on_block,
        )
        self.details_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 10), pady=10)

    def _build_statusbar(self) -> None:
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, columnspan=3, sticky="ew")

    # ------------------------------------------------------------------ #
    # Send callback                                                        #
    # ------------------------------------------------------------------ #

    def set_send_callback(self, callback: Callable) -> None:
        self.send_button.configure(command=callback)
        self.message_entry.bind("<Return>", lambda _e: callback())

    # ------------------------------------------------------------------ #
    # Chat API                                                             #
    # ------------------------------------------------------------------ #

    def add_system_message(self, message: str) -> None:
        self.chat_box.add_system(message)

    def add_received_message(self, sender: str, message: str) -> None:
        self.chat_box.add_received(sender, message)

    def add_sent_message(self, sender: str, recipient: str, message: str) -> None:
        self.chat_box.add_sent(sender, recipient, message)

    def clear_chat(self) -> None:
        self.chat_box.clear()

    def get_message_text(self) -> str:
        return self.message_entry.get()

    def clear_message_text(self) -> None:
        self.message_entry.delete(0, "end")

    def focus_message_box(self) -> None:
        self.message_entry.focus_set()

    # ------------------------------------------------------------------ #
    # Peer list API                                                        #
    # ------------------------------------------------------------------ #

    def update_discovered_peers(self, peers: dict) -> None:
        self.sidebar.update_peers(peers)

    # ------------------------------------------------------------------ #
    # Details panel API                                                    #
    # ------------------------------------------------------------------ #

    def update_peer_details(self, peer_info: dict) -> None:
        self.details_panel.update_peer(peer_info)

    # ------------------------------------------------------------------ #
    # Chat header API                                                      #
    # ------------------------------------------------------------------ #

    def set_active_chat(
        self,
        username:    str,
        status:      str = "offline",
        trust_state: str = "NEW",
    ) -> None:
        # Hide empty-state overlay
        self.empty_label.place_forget()

        status_icon = {
            "online": "🟢", "connected": "🔗",
            "offline": "⚪", "connecting": "🟡",
        }.get(status, "⚪")

        trust_color = {
            "NEW": "#f9e2af", "TRUSTED": "#89b4fa",
            "VERIFIED": "#a6e3a1", "MISMATCH": "#f38ba8", "BLOCKED": "#6c7086",
        }.get(trust_state, "#a6adc8")

        self.chat_target_label.configure(text=username)
        self.chat_info_label.configure(
            text  = f"{status_icon} {status.capitalize()}  |  🔑 {trust_state}",
            text_color = trust_color,
        )

    # ------------------------------------------------------------------ #
    # Status / stats API                                                   #
    # ------------------------------------------------------------------ #

    def set_status(self, text: str, color: str = "#a6adc8") -> None:
        self.status_bar.set_status(text, color)

    def set_identity(self, peer_id: str, fingerprint: str) -> None:
        self.status_bar.set_identity(peer_id, fingerprint)

    def update_stats(self, peers: int = 0, connected: int = 0, contacts: int = 0) -> None:
        self.status_bar.set_stats(peers=peers, connected=connected, contacts=contacts)

    # ------------------------------------------------------------------ #
    # Deprecated / compat shims                                            #
    # ------------------------------------------------------------------ #

    def set_trust_callback(self, cb) -> None:
        self.details_panel.set_trust_callback(cb)

    def set_block_callback(self, cb) -> None:
        self.details_panel.set_block_callback(cb)
