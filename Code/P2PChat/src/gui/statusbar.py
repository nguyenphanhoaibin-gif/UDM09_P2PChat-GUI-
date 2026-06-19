"""StatusBar: bottom bar with status message, identity, and peer stats."""
from __future__ import annotations

import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """One-line bar at the bottom of the window."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=32,
            corner_radius=0,
            fg_color="#11111b",
            **kwargs,
        )
        self.grid_columnconfigure(1, weight=1)

        # Left: identity
        self._id_label = ctk.CTkLabel(
            self, text="",
            anchor="w",
            font=("Consolas", 10),
            text_color="#45475a",
        )
        self._id_label.grid(row=0, column=0, sticky="w", padx=(10, 0))

        # Centre: status message
        self._status_label = ctk.CTkLabel(
            self, text="🔄 Initializing...",
            anchor="center",
            font=("Consolas", 11),
            text_color="#6c7086",
        )
        self._status_label.grid(row=0, column=1, sticky="ew")

        # Right: peer stats
        self._stats_label = ctk.CTkLabel(
            self,
            text="Peers: 0",
            anchor="e",
            font=("Consolas", 10),
            text_color="#45475a",
        )
        self._stats_label.grid(row=0, column=2, sticky="e", padx=(0, 10))

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def set_status(self, text: str, color: str = "#6c7086") -> None:
        self._status_label.configure(text=text, text_color=color)

    def set_identity(self, peer_id: str, fingerprint: str) -> None:
        self._id_label.configure(
            text=f"🆔 {peer_id}  🔑 {fingerprint}"
        )

    def set_stats(
        self,
        peers: int = 0,
        connected: int = 0,
        contacts: int = 0,
    ) -> None:
        self._stats_label.configure(
            text=(
                f"Peers:{peers} | "
                f"Connected:{connected} | "
                f"Contacts:{contacts}  "
            )
        )

    # ── Named convenience methods ──────────────────────────────────────

    def set_initializing(self)   -> None: 
        self.set_status("🔄 Initializing...", "#6c7086")
    def set_discovery_running(self) -> None: 
        self.set_status("🔍 Discovering peers...", "#89b4fa")
    def set_connected(self, peer: str)  -> None: 
        self.set_status(f"🔗 Connected: {peer}", "#a6e3a1")
    def set_handshake(self)      -> None: 
        self.set_status("🤝 Performing handshake...", "#f9e2af")
    def set_encrypted(self)      -> None: 
        self.set_status("🔐 Encrypted session active", "#a6e3a1")
    def set_disconnected(self)   -> None: 
        self.set_status("❌ Disconnected", "#f38ba8")
    def set_error(self, msg: str) -> None: 
        self.set_status(f"⚠ {msg}", "#f38ba8")

