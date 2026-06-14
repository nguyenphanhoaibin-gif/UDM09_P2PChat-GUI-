"""Status bar for displaying application state information."""

import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """Global application status bar.
    States:
        Initializing
        Discovery
        Connected
        Handshake
        Encrypted
        Error
    """
    def __init__(self, master, **kwargs):
        super().__init__(master,
            height=30,
            corner_radius=0,
            fg_color="#11111b",
            **kwargs
        )

        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self,
            text="🔄 Initializing...",
            anchor="w",
            font=("Consolas", 12),
            text_color="#6c7086"
        )

        self.label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=4
        )

    # ------------------------------------------------------------------ #
    # Generic API
    # ------------------------------------------------------------------ #

    def set_status(self, text: str, color: str = "#6c7086") -> None:
        """Set status text and color."""
        self.label.configure( text=text, text_color=color )

    # ------------------------------------------------------------------ #
    # Convenience Helpers
    # ------------------------------------------------------------------ #

    def set_initializing(self) -> None:
        """Set status to initializing."""
        self.set_status(
            "🔄 Initializing...",
            "#6c7086"
        )

    def set_discovery_running(self) -> None:
        """Set status to discovery running."""
        self.set_status(
            "🔍 Discovering peers...",
            "#89b4fa"
        )

    def set_connected(self, peer: str) -> None:
        """Set status to connected."""
        self.set_status(
            f"🔗 Connected: {peer}",
            "#a6e3a1"
        )

    def set_handshake(self) -> None:
        """Set status to handshake."""
        self.set_status(
            "🤝 Performing handshake...",
            "#f9e2af"
        )

    def set_encrypted(self) -> None:
        """Set status to encrypted."""
        self.set_status(
            "🔐 Encrypted session active",
            "#a6e3a1"
        )

    def set_disconnected(self) -> None:
        """Set status to disconnected."""
        self.set_status(
            "❌ Disconnected",
            "#f38ba8"
        )

    def set_error(self, message: str) -> None:
        """Set status to error."""
        self.set_status(
            f"⚠️ {message}",
            "#f38ba8"
        )
