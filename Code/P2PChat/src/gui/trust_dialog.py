"""Trust verification dialog — shown on first contact and fingerprint mismatch."""
from __future__ import annotations

import customtkinter as ctk


class TrustDialog(ctk.CTkToplevel):
    """Modal dialog for TOFU trust decisions.

    Modes
    -----
    ``new_peer``
        Shown on first contact.  Offers Trust, Block, Skip.
    ``warning``
        Shown when a known peer's fingerprint changed (possible MITM).
        Offers Update & Trust, Block.

    Callback results: ``"trust"`` | ``"block"`` | ``"skip"`` | ``"update"``
    """

    def __init__(
        self,
        master,
        mode: str,
        peer_info: dict,
        callback=None,
    ) -> None:
        """Show the dialog.

        Args:
            master: Parent Tk widget.
            mode: ``"new_peer"`` or ``"warning"``.
            peer_info: Dict with keys from PeerInfo DTO (plus
                ``known_fingerprint`` / ``current_fingerprint`` for
                ``"warning"`` mode).
            callback: Called with the result string when the user acts.
        """
        super().__init__(master)
        self.mode      = mode
        self.peer_info = peer_info
        self.callback  = callback

        self._setup_window()

        if mode == "new_peer":
            self._build_new_peer_ui()
        elif mode == "warning":
            self._build_warning_ui()
        else:
            raise ValueError(f"Unknown mode: {mode!r}")

    # ------------------------------------------------------------------ #
    # Window setup                                                         #
    # ------------------------------------------------------------------ #

    def _setup_window(self) -> None:
        """Configure the toplevel window."""
        self.title("Peer Trust Verification")
        self.geometry("520x320")
        self.resizable(False, False)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ #
    # new_peer mode                                                        #
    # ------------------------------------------------------------------ #

    def _build_new_peer_ui(self) -> None:
        """Build UI for first-contact trust decision."""
        ctk.CTkLabel(
            self, text="🔑  New Peer",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(20, 10))

        card = ctk.CTkFrame(self)
        card.pack(fill="x", padx=20)

        for label, key in (
            ("Username",    "username"),
            ("Peer ID",     "peer_id"),
            ("Fingerprint", "fingerprint"),
        ):
            ctk.CTkLabel(
                card,
                text=f"{label}:   {self.peer_info.get(key, '—')}",
                anchor="w",
            ).pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(
            self,
            text="Verify the fingerprint with the peer before trusting.",
            justify="center",
        ).pack(pady=20)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)

        for text, result in (
            ("Trust & Connect", "trust"),
            ("Block",           "block"),
            ("Skip",            "skip"),
        ):
            ctk.CTkButton(
                btn_row, text=text, width=130,
                command=lambda r=result: self._fire(r),
            ).pack(side="left", padx=5)

    # ------------------------------------------------------------------ #
    # warning mode                                                         #
    # ------------------------------------------------------------------ #

    def _build_warning_ui(self) -> None:
        """Build UI for fingerprint-mismatch warning."""
        ctk.CTkLabel(
            self, text="⚠️  Fingerprint Changed",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(20, 10))

        card = ctk.CTkFrame(self)
        card.pack(fill="x", padx=20)

        for label, key in (
            ("Known",   "known_fingerprint"),
            ("Current", "current_fingerprint"),
        ):
            ctk.CTkLabel(
                card,
                text=f"{label}:   {self.peer_info.get(key, '—')}",
                anchor="w",
            ).pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(
            self,
            text=(
                "This may indicate a man-in-the-middle attack.\n"
                "Verify the fingerprint out-of-band before trusting."
            ),
            justify="center",
        ).pack(pady=20)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)

        for text, result in (
            ("Update & Trust", "update"),
            ("Block",          "block"),
        ):
            ctk.CTkButton(
                btn_row, text=text, width=140,
                command=lambda r=result: self._fire(r),
            ).pack(side="left", padx=10)

    # ------------------------------------------------------------------ #
    # Result dispatch                                                      #
    # ------------------------------------------------------------------ #

    def _fire(self, result: str) -> None:
        """Call the callback with *result* and close the dialog."""
        if self.callback:
            self.callback(result)
        self.destroy()
