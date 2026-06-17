from __future__ import annotations

import customtkinter as ctk


TRUST_COLORS = {
    "NEW": "#f9e2af",
    "TRUSTED": "#89b4fa",
    "VERIFIED": "#a6e3a1",
    "MISMATCH": "#f38ba8",
    "BLOCKED": "#6c7086",
}


class PeerDetails(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color="#181825",
            width=280,
            corner_radius=14,
            **kwargs
        )

        self.grid_columnconfigure(0, weight=1)

        self._trust_callback = None
        self._block_callback = None
        self.current_peer_id = None

        # ======================================
        # Header
        # ======================================

        self.title_label = ctk.CTkLabel(
            self,
            text="Peer Details",
            font=("Arial", 18, "bold")
        )

        self.title_label.pack(
            anchor="w",
            padx=15,
            pady=(15, 10)
        )

        # ======================================
        # Username
        # ======================================

        self.username_label = ctk.CTkLabel(
            self,
            text="No peer selected",
            anchor="w",
            font=("Arial", 15, "bold")
        )

        self.username_label.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        # ======================================
        # Info
        # ======================================

        self.peer_id_label = ctk.CTkLabel(
            self,
            text="Peer ID: -",
            anchor="w"
        )

        self.peer_id_label.pack(
            fill="x",
            padx=15,
            pady=3
        )

        self.ip_label = ctk.CTkLabel(
            self,
            text="IP: -",
            anchor="w"
        )

        self.ip_label.pack(
            fill="x",
            padx=15,
            pady=3
        )

        self.trust_label = ctk.CTkLabel(
            self,
            text="Trust: NEW",
            anchor="w"
        )

        self.trust_label.pack(
            fill="x",
            padx=15,
            pady=3
        )

        # ======================================
        # Fingerprint
        # ======================================

        self.fp_title = ctk.CTkLabel(
            self,
            text="Fingerprint",
            anchor="w",
            font=("Arial", 13, "bold")
        )

        self.fp_title.pack(
            fill="x",
            padx=15,
            pady=(15, 5)
        )

        self.fingerprint_box = ctk.CTkTextbox(
            self,
            height=120
        )

        self.fingerprint_box.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.fingerprint_box.insert(
            "1.0",
            "No fingerprint available"
        )

        self.fingerprint_box.configure(
            state="disabled"
        )

        # ======================================
        # Buttons
        # ======================================

        self.trust_button = ctk.CTkButton(
            self,
            text="✓ Trust Peer",
            command=self._on_trust
        )

        self.trust_button.pack(
            fill="x",
            padx=15,
            pady=(0, 8)
        )

        self.block_button = ctk.CTkButton(
            self,
            text="🚫 Block Peer",
            fg_color="#f38ba8",
            hover_color="#eba0ac",
            command=self._on_block
        )

        self.block_button.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

    # ======================================
    # Public API
    # ======================================

    def set_trust_callback(self, callback):
        self._trust_callback = callback

    def set_block_callback(self, callback):
        self._block_callback = callback

    def update_peer(
        self,
        peer_info: dict
    ):

        self.current_peer_id = peer_info.get(
            "peer_id"
        )

        username = peer_info.get(
            "username",
            "Unknown"
        )

        trust_state = peer_info.get(
            "trust_state",
            "NEW"
        )

        self.username_label.configure(
            text=username
        )

        self.peer_id_label.configure(
            text=f"Peer ID: {peer_info.get('peer_id', '-')}"
        )

        self.ip_label.configure(
            text=f"IP: {peer_info.get('ip', '-')}"
        )

        self.trust_label.configure(
            text=f"Trust: {trust_state}",
            text_color=TRUST_COLORS.get(
                trust_state,
                "#a6adc8"
            )
        )

        self.fingerprint_box.configure(
            state="normal"
        )

        self.fingerprint_box.delete(
            "1.0",
            "end"
        )

        self.fingerprint_box.insert(
            "1.0",
            peer_info.get(
                "fingerprint",
                "Unknown"
            )
        )

        self.fingerprint_box.configure(
            state="disabled"
        )

    # ======================================
    # Events
    # ======================================

    def _on_trust(self):

        if (
            self.current_peer_id
            and self._trust_callback
        ):
            self._trust_callback(
                self.current_peer_id
            )

    def _on_block(self):

        if (
            self.current_peer_id
            and self._block_callback
        ):
            self._block_callback(
                self.current_peer_id
            )