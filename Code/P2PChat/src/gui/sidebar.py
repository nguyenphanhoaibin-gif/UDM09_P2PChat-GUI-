"""Sidebar module for P2PChat Sprint 3."""

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
    """Visual representation of a discovered peer."""
    def __init__(
        self,
        master,
        peer_id: str,
        peer_info: dict,
        on_select=None,
        on_connect=None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=8,
            fg_color="#313145",
            **kwargs
        )

        self.peer_id = peer_id
        self.peer_info = peer_info

        self._on_select = on_select
        self._on_connect = on_connect

        self.grid_columnconfigure(
            0,
            weight=1
        )

        username = peer_info.get(
            "username",
            "Unknown"
        )

        ip = peer_info.get(
            "ip",
            "?"
        )

        port = peer_info.get(
            "port",
            "?"
        )

        status = peer_info.get(
            "status",
            "offline"
        )

        trust_state = peer_info.get(
            "trust_state",
            "NEW"
        )

        status_icon = {
            "online": "🟢",
            "connected": "🔗",
            "offline": "⚪",
            "connecting": "🟡"
        }.get(
            status,
            "⚪"
        )

        self.title_label = ctk.CTkLabel(
            self,
            text=f"{status_icon} {username}",
            anchor="w",
            font=("Arial", 13, "bold")
        )

        self.title_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=8,
            pady=(6, 0)
        )

        self.addr_label = ctk.CTkLabel(
            self,
            text=f"{ip}:{port}",
            anchor="w",
            text_color="#a6adc8",
            font=("Consolas", 10)
        )

        self.addr_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=8
        )

        trust_color = TRUST_COLORS.get(
            trust_state,
            "#a6adc8"
        )

        self.trust_label = ctk.CTkLabel(
            self,
            text=f"Trust: {trust_state}",
            anchor="w",
            text_color=trust_color,
            font=("Consolas", 10)
        )

        self.trust_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=8,
            pady=(0, 4)
        )

        short_id = (
            peer_id[:12] + "..."
            if len(peer_id) > 12
            else peer_id
        )

        self.peer_id_label = ctk.CTkLabel(
            self,
            text=short_id,
            anchor="w",
            text_color="#6c7086",
            font=("Consolas", 9)
        )

        self.peer_id_label.grid(
            row=3,
            column=0,
            sticky="w",
            padx=8
        )

        self.button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.button_frame.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=6,
            pady=(0, 6)
        )

        self.select_button = ctk.CTkButton(
            self.button_frame,
            text="Select",
            width=70,
            command=self._handle_select
        )

        self.select_button.pack(
            side="left",
            padx=(0, 4)
        )

        self.connect_button = ctk.CTkButton(
            self.button_frame,
            text="Connect",
            width=80,
            fg_color="#89b4fa",
            command=self._handle_connect
        )

        self.connect_button.pack(
            side="left"
        )

    def _handle_select(self):
        if self._on_select:
            self._on_select(
                self.peer_id,
                self.peer_info
            )

    def _handle_connect(self):
        if self._on_connect:
            self._on_connect(
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
            else "#313145"
        )


class Sidebar(ctk.CTkFrame):
    """Discovery sidebar."""

    def __init__(
        self,
        master,
        on_peer_select=None,
        on_peer_connect=None,
        **kwargs
    ):
        super().__init__(
            master,
            width=260,
            corner_radius=0,
            fg_color="#181825",
            **kwargs
        )

        self._on_peer_select = on_peer_select
        self._on_peer_connect = on_peer_connect

        self.selected_peer_id = None
        self.peer_cards = {}

        self.title = ctk.CTkLabel(
            self,
            text="🌐 Nearby Users",
            font=("Consolas", 14, "bold")
        )

        self.title.pack(
            pady=(15, 5),
            padx=10,
            anchor="w"
        )

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

        self.info_label = ctk.CTkLabel(
            self,
            text="── No peer selected ──",
            text_color="#6c7086",
            font=("Consolas", 11)
        )

        self.info_label.pack(
            side="bottom",
            pady=15
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
                peer_id=peer_id,
                peer_info=peer_info,
                on_select=self._select_peer,
                on_connect=self._connect_peer
            )

            card.pack(
                fill="x",
                padx=4,
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

        self.info_label.configure(
            text=f"Selected: {username}"
        )

        if self._on_peer_select:

            self._on_peer_select(
                peer_id,
                peer_info
            )

    def _connect_peer(
        self,
        peer_id,
        peer_info
    ):
        if self._on_peer_connect:

            self._on_peer_connect(
                peer_id,
                peer_info
            )