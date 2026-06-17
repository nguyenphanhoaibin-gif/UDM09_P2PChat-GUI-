"""Modern Sidebar for P2PChat."""

from __future__ import annotations

import customtkinter as ctk

TRUST_COLORS = {
    "NEW": "#f9e2af",
    "TRUSTED": "#89b4fa",
    "VERIFIED": "#a6e3a1",
    "MISMATCH": "#f38ba8",
    "BLOCKED": "#6c7086"
}


class PeerCard(ctk.CTkFrame):

    def __init__(
        self,
        master,
        peer_id: str,
        peer_info: dict,
        on_select=None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color="#313244",
            height=72
        )

        self.peer_id = peer_id
        self.peer_info = peer_info
        self._on_select = on_select

        self.grid_columnconfigure(1, weight=1)

        username = peer_info.get(
            "username",
            "Unknown"
        )

        status = peer_info.get(
            "status",
            "offline"
        )

        trust_state = peer_info.get(
            "trust_state",
            "NEW"
        )

        icon = {
            "online": "🟢",
            "connected": "🔗",
            "offline": "⚪",
            "connecting": "🟡"
        }.get(
            status,
            "⚪"
        )

        # avatar
        self.avatar = ctk.CTkLabel(
            self,
            text="👤",
            font=("Segoe UI Emoji", 22)
        )

        self.avatar.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(10, 8),
            pady=8
        )

        # username
        self.name_label = ctk.CTkLabel(
            self,
            text=f"{icon} {username}",
            anchor="w",
            font=("Arial", 13, "bold")
        )

        self.name_label.grid(
            row=0,
            column=1,
            sticky="w",
            pady=(10, 0)
        )

        trust_color = TRUST_COLORS.get(
            trust_state,
            "#a6adc8"
        )

        self.info_label = ctk.CTkLabel(
            self,
            text=trust_state,
            text_color=trust_color,
            anchor="w",
            font=("Consolas", 10)
        )

        self.info_label.grid(
            row=1,
            column=1,
            sticky="w",
            pady=(0, 10)
        )

        self.bind(
            "<Button-1>",
            self._handle_select
        )

        self.avatar.bind(
            "<Button-1>",
            self._handle_select
        )

        self.name_label.bind(
            "<Button-1>",
            self._handle_select
        )

        self.info_label.bind(
            "<Button-1>",
            self._handle_select
        )

    def _handle_select(self, _event=None):

        if self._on_select:
            self._on_select(
                self.peer_id,
                self.peer_info
            )

    def set_selected(
        self,
        selected: bool
    ):
        self.configure(
            fg_color="#45475a"
            if selected
            else "#313244"
        )


class Sidebar(ctk.CTkFrame):

    def __init__(
        self,
        master,
        on_peer_select=None,
        on_peer_connect=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color="#181825",
            width=280,
            **kwargs
        )

        self._on_peer_select = on_peer_select
        self.selected_peer_id = None
        self.peer_cards = {}

        # title
        self.title = ctk.CTkLabel(
            self,
            text="Chats",
            font=("Arial", 18, "bold")
        )

        self.title.pack(
            anchor="w",
            padx=12,
            pady=(15, 5)
        )

        # search
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search..."
        )

        self.search_entry.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        # scroll area
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.scroll_frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        self.footer = ctk.CTkLabel(
            self,
            text="No peer selected",
            text_color="#6c7086",
            font=("Consolas", 10)
        )

        self.footer.pack(
            pady=8
        )

    def clear(self):

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.peer_cards.clear()

    def update_peers(
        self,
        peers: dict
    ):

        self.clear()

        if not peers:

            empty = ctk.CTkLabel(
                self.scroll_frame,
                text="No peers discovered",
                text_color="#6c7086"
            )

            empty.pack(
                pady=20
            )

            return

        for peer_id, peer_info in peers.items():

            card = PeerCard(
                self.scroll_frame,
                peer_id,
                peer_info,
                on_select=self._select_peer
            )

            card.pack(
                fill="x",
                padx=5,
                pady=4
            )

            self.peer_cards[
                peer_id
            ] = card

    def _select_peer(
        self,
        peer_id,
        peer_info
    ):

        self.selected_peer_id = peer_id

        for pid, card in self.peer_cards.items():

            card.set_selected(
                pid == peer_id
            )

        username = peer_info.get(
            "username",
            peer_id
        )

        self.footer.configure(
            text=f"Selected: {username}"
        )

        if self._on_peer_select:

            self._on_peer_select(
                peer_id,
                peer_info
            )