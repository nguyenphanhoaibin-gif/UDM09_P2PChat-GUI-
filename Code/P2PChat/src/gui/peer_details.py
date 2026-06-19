"""PeerDetails: right panel showing selected peer's info, fingerprint, and trust actions."""
from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from trust.trust_state import TrustState

TRUST_COLORS = {
    TrustState.NEW:      "#f9e2af",
    TrustState.TRUSTED:  "#89b4fa",
    TrustState.VERIFIED: "#a6e3a1",
    TrustState.MISMATCH: "#f38ba8",
    TrustState.BLOCKED:  "#6c7086",
}

TRUST_ICONS = {
    TrustState.NEW:      "🔑",
    TrustState.TRUSTED:  "🔐",
    TrustState.VERIFIED: "✅",
    TrustState.MISMATCH: "⚠️",
    TrustState.BLOCKED:  "⛔",
}


class PeerDetails(ctk.CTkFrame):
    """Right-hand panel: peer metadata, fingerprint box, trust / block buttons."""

    def __init__(
        self,
        master,
        on_trust: Optional[Callable[[str], None]] = None,
        on_block: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color="#181825",
            width=270,
            corner_radius=14,
            **kwargs,
        )
        self.grid_propagate(False)

        self._on_trust  = on_trust
        self._on_block  = on_block
        self.current_peer_id: Optional[str] = None

        self._build_ui()

    # ------------------------------------------------------------------ #
    # Construction                                                         #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        # Title
        ctk.CTkLabel(
            self, text="Peer Details",
            font=("Arial", 17, "bold"),
        ).pack(anchor="w", padx=14, pady=(14, 6))

        # Avatar + username row
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(0, 8))

        self._avatar = ctk.CTkLabel(
            top, text="👤", font=("Segoe UI Emoji", 36),
        )
        self._avatar.pack(side="left", padx=(0, 10))

        name_col = ctk.CTkFrame(top, fg_color="transparent")
        name_col.pack(side="left", fill="x", expand=True)

        self._username_label = ctk.CTkLabel(
            name_col, text="No peer selected",
            font=("Arial", 14, "bold"), anchor="w",
        )
        self._username_label.pack(anchor="w")

        self._status_label = ctk.CTkLabel(
            name_col, text="⚪ Offline",
            text_color="#6c7086", font=("Consolas", 10), anchor="w",
        )
        self._status_label.pack(anchor="w")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#313244").pack(fill="x", padx=10, pady=4)

        # Info grid
        self._peer_id_label  = self._info_row("Peer ID",     "—")
        self._ip_label       = self._info_row("Address",     "—")
        self._trust_label    = self._info_row("Trust",       "NEW")

        # Fingerprint
        ctk.CTkLabel(
            self, text="Fingerprint",
            font=("Arial", 12, "bold"), anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        self._fp_box = ctk.CTkTextbox(
            self, height=110,
            font=("Consolas", 10),
        )
        self._fp_box.pack(fill="x", padx=14, pady=(0, 10))
        self._fp_box.insert("1.0", "No peer selected.")
        self._fp_box.configure(state="disabled")

        # Buttons
        self._trust_btn = ctk.CTkButton(
            self, text="✅  Trust Peer",
            fg_color="#1e6f40", hover_color="#165c34",
            command=self._do_trust,
        )
        self._trust_btn.pack(fill="x", padx=14, pady=(0, 6))

        self._block_btn = ctk.CTkButton(
            self, text="⛔  Block Peer",
            fg_color="#7f1d1d", hover_color="#6b1a1a",
            command=self._do_block,
        )
        self._block_btn.pack(fill="x", padx=14, pady=(0, 14))

    def _info_row(self, label: str, value: str) -> ctk.CTkLabel:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=2)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text=f"{label}:",
            font=("Arial", 11, "bold"),
            anchor="w", width=72,
        ).grid(row=0, column=0, sticky="w")

        val_label = ctk.CTkLabel(
            row, text=value,
            font=("Consolas", 10),
            anchor="w", text_color="#cdd6f4",
        )
        val_label.grid(row=0, column=1, sticky="w")
        return val_label

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def update_peer(self, peer_info: dict) -> None:
        self.current_peer_id = peer_info.get("peer_id")

        username    = peer_info.get("username", "Unknown")
        trust_state = peer_info.get("trust_state", TrustState.NEW)
        status      = peer_info.get("status", "offline")
        ip          = peer_info.get("ip", "—")
        port        = peer_info.get("port", "")
        fingerprint = peer_info.get("fingerprint", "No fingerprint available")
        pid         = peer_info.get("peer_id", "—")

        trust_color = TRUST_COLORS.get(trust_state, "#a6adc8")
        trust_icon  = TRUST_ICONS.get(trust_state, "🔑")
        status_icon = {"online": "🟢", "connected": "🔗", "offline": "⚪"}.get(status, "⚪")

        self._username_label.configure(text=username)
        self._status_label.configure(text=f"{status_icon} {status.capitalize()}")

        # Truncate peer_id for display
        pid_display = (pid[:24] + "…") if len(pid) > 24 else pid
        self._peer_id_label.configure(text=pid_display)
        self._ip_label.configure(text=f"{ip}:{port}" if port else ip)
        self._trust_label.configure(
            text=f"{trust_icon} {trust_state}",
            text_color=trust_color,
        )

        # Format fingerprint: one pair per group of 8, each line 4 groups
        fp_formatted = self._format_fingerprint(fingerprint)
        self._fp_box.configure(state="normal")
        self._fp_box.delete("1.0", "end")
        self._fp_box.insert("1.0", fp_formatted)
        self._fp_box.configure(state="disabled")

        # Button states
        if trust_state == TrustState.BLOCKED:
            self._trust_btn.configure(text="✅  Unblock Peer")
            self._block_btn.configure(state="disabled")
        else:
            self._trust_btn.configure(text="✅  Trust Peer")
            self._block_btn.configure(state="normal")

    # Compat shims (older app.py calls)
    def set_trust_callback(self, cb: Callable) -> None:
        self._on_trust = cb

    def set_block_callback(self, cb: Callable) -> None:
        self._on_block = cb

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _do_trust(self) -> None:
        if self.current_peer_id and self._on_trust:
            self._on_trust(self.current_peer_id)

    def _do_block(self) -> None:
        if self.current_peer_id and self._on_block:
            self._on_block(self.current_peer_id)

    @staticmethod
    def _format_fingerprint(fp: str) -> str:
        """Split a long colon-separated fingerprint into 4-group lines."""
        if not fp or ":" not in fp:
            return fp or "—"
        pairs  = fp.split(":")
        groups = [":".join(pairs[i:i+8]) for i in range(0, len(pairs), 8)]
        return "\n".join(groups)
