"""Enhanced Status Bar."""

from __future__ import annotations

import customtkinter as ctk


class StatusBar(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            height=34,
            corner_radius=0,
            fg_color="#11111b",
            **kwargs
        )

        self.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self,
            text="🔄 Initializing...",
            anchor="w",
            font=("Consolas", 11),
            text_color="#6c7086"
        )

        self.status_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(10, 0)
        )

        self.stats_label = ctk.CTkLabel(
            self,
            text="Peers: 0",
            anchor="e",
            font=("Consolas", 11),
            text_color="#6c7086"
        )

        self.stats_label.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(0, 10)
        )

    def set_status(
        self,
        text: str,
        color: str = "#6c7086"
    ):
        self.status_label.configure(
            text=text,
            text_color=color
        )

    def set_stats(
        self,
        peers: int = 0,
        contacts: int = 0,
        connected: int = 0
    ):
        self.stats_label.configure(
            text=(
                f"Peers:{peers}  "
                f"Contacts:{contacts}  "
                f"Connected:{connected}"
            )
        )

    def set_initializing(self):
        self.set_status(
            "🔄 Initializing...",
            "#6c7086"
        )

    def set_discovery_running(self):
        self.set_status(
            "🔍 Discovering peers...",
            "#89b4fa"
        )

    def set_connected(self, peer: str):
        self.set_status(
            f"🔗 Connected: {peer}",
            "#a6e3a1"
        )

    def set_handshake(self):
        self.set_status(
            "🤝 Performing handshake...",
            "#f9e2af"
        )

    def set_encrypted(self):
        self.set_status(
            "🔐 Encrypted session active",
            "#a6e3a1"
        )

    def set_disconnected(self):
        self.set_status(
            "❌ Disconnected",
            "#f38ba8"
        )

    def set_error(self, message: str):
        self.set_status(
            f"⚠ {message}",
            "#f38ba8"
        )