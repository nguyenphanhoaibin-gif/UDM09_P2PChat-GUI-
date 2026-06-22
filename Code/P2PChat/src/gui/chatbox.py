"""ChatBox: scrollable chat display with bubble-style messages."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Callable, Optional

import customtkinter as ctk
from gui.chat_bubble import add_chat_bubble


def _fmt_size(n: int) -> str:
    if n < 1_024:
        return f"{n} B"
    if n < 1_048_576:
        return f"{n / 1_024:.1f} KB"
    return f"{n / 1_048_576:.2f} MB"


class ChatBox(ctk.CTkFrame):
  
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="#1e1e2e")
        self._scroll.grid(row=0, column=0, sticky="nsew")

        # transfer_id → widget refs for in-place updates
        self._transfer_registry: dict[str, dict] = {}

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def add_sent(self, sender: str, recipient: str, message: str) -> None:
        add_chat_bubble(self._scroll, message, sender=sender, is_me=True)
        self._scroll_bottom()

    def add_received(self, sender: str, message: str) -> None:
        add_chat_bubble(self._scroll, message, sender=sender, is_me=False)
        self._scroll_bottom()

    def add_system(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(
            row,
            text=f"── {ts}  {text} ──",
            text_color="#6c7086",
            font=("Consolas", 10),
        ).pack()
        self._scroll_bottom()

    def clear(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        self._transfer_registry.clear()

    # ------------------------------------------------------------------ #
    # Sprint 3 — file transfer & trust                                    #
    # ------------------------------------------------------------------ #

    def add_file_offer(
        self,
        sender:    str,
        filename:  str,
        size:      int,
        on_accept: Optional[Callable[[str], None]] = None,
        on_reject: Optional[Callable[[str], None]] = None,
    ) -> str:
        
        transfer_id = uuid.uuid4().hex[:8]
        ts          = datetime.now().strftime("%H:%M")
        size_str    = _fmt_size(size)

        # ── outer row ────────────────────────────────────────────────
        outer = ctk.CTkFrame(self._scroll, fg_color="transparent")
        outer.pack(fill="x", padx=10, pady=3)

        bubble = ctk.CTkFrame(outer, fg_color="#2a2a3e", corner_radius=18)
        bubble.pack(anchor="w", padx=(0, 80))

        # sender name
        ctk.CTkLabel(
            bubble,
            text=sender,
            text_color="#89b4fa",
            font=("Arial", 10, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(8, 0))

        # file info
        info_lbl = ctk.CTkLabel(
            bubble,
            text=f"📎  {filename}   ({size_str})",
            font=("Consolas", 11),
            anchor="w",
        )
        info_lbl.pack(anchor="w", padx=14, pady=(4, 0))

        # progress row (hidden until accepted)
        prog_row = ctk.CTkFrame(bubble, fg_color="transparent")
        prog_bar = ctk.CTkProgressBar(
            prog_row, width=200, height=10,
            progress_color="#89b4fa", fg_color="#313145",
        )
        prog_bar.set(0)
        pct_lbl = ctk.CTkLabel(
            prog_row,
            text="0%",
            text_color="#a6adc8",
            font=("Consolas", 9),
            width=36,
        )

        # button row
        btn_row = ctk.CTkFrame(bubble, fg_color="transparent")
        btn_row.pack(anchor="w", padx=10, pady=(6, 4))

        _done = {"v": False}

        def do_accept() -> None:
            if _done["v"]:
                return
            _done["v"] = True
            accept_btn.configure(state="disabled", text="Accepted ✓", fg_color="#4a7c59")
            reject_btn.configure(state="disabled")
            prog_row.pack(anchor="w", padx=14, pady=(4, 2))
            prog_bar.pack(side="left", padx=(0, 6))
            pct_lbl.pack(side="left")
            if on_accept:
                on_accept(transfer_id)

        def do_reject() -> None:
            if _done["v"]:
                return
            _done["v"] = True
            reject_btn.configure(state="disabled", text="Rejected ✗", fg_color="#7c3f3f")
            accept_btn.configure(state="disabled")
            if on_reject:
                on_reject(transfer_id)

        accept_btn = ctk.CTkButton(
            btn_row, text="Accept", width=82, height=28,
            fg_color="#a6e3a1", hover_color="#7bc49c", text_color="#11111b",
            font=("Arial", 10, "bold"), command=do_accept,
        )
        accept_btn.pack(side="left", padx=(0, 6))

        reject_btn = ctk.CTkButton(
            btn_row, text="Reject", width=82, height=28,
            fg_color="#f38ba8", hover_color="#c96f85", text_color="#11111b",
            font=("Arial", 10, "bold"), command=do_reject,
        )
        reject_btn.pack(side="left")

        # timestamp
        ctk.CTkLabel(
            bubble, text=ts,
            text_color="#6c7086", font=("Consolas", 9), anchor="e",
        ).pack(anchor="e", padx=14, pady=(2, 6))

        self._transfer_registry[transfer_id] = {
            "info_lbl":   info_lbl,
            "prog_row":   prog_row,
            "prog_bar":   prog_bar,
            "pct_lbl":    pct_lbl,
            "accept_btn": accept_btn,
            "reject_btn": reject_btn,
            "done":       _done,
        }

        self._scroll_bottom()
        return transfer_id

    def update_file_progress(self, transfer_id: str, pct: int) -> None:
        """Update the progress bar for *transfer_id* (0 – 100).

        Safe to call from Tk main thread only; wrap in ``after(0, ...)``
        when calling from a worker thread.
        """
        entry = self._transfer_registry.get(transfer_id)
        if entry is None:
            return

        prog_row: ctk.CTkFrame       = entry["prog_row"]
        prog_bar: ctk.CTkProgressBar = entry["prog_bar"]
        pct_lbl:  ctk.CTkLabel       = entry["pct_lbl"]

        if not prog_row.winfo_ismapped():
            prog_row.pack(anchor="w", padx=14, pady=(4, 2))
            prog_bar.pack(side="left", padx=(0, 6))
            pct_lbl.pack(side="left")

        pct = max(0, min(100, pct))
        prog_bar.set(pct / 100)
        pct_lbl.configure(text=f"{pct}%")

    def add_file_progress(
        self, transfer_id: str, filename: str, pct: int
    ) -> None:
        """Compatibility alias for ``update_file_progress``."""
        self.update_file_progress(transfer_id, pct)

    def add_file_done(
        self,
        transfer_id: str,
        filename:   str,
        save_path:  Optional[str] = None,
    ) -> None:
        """Mark a transfer complete, update the bubble in-place."""
        entry = self._transfer_registry.get(transfer_id)
        if entry is None:
            self.add_system(f"✅ {filename} received")
            return

        # hide action buttons
        entry["accept_btn"].pack_forget()
        entry["reject_btn"].pack_forget()

        # fill bar to 100 %
        prog_row: ctk.CTkFrame = entry["prog_row"]
        if not prog_row.winfo_ismapped():
            prog_row.pack(anchor="w", padx=14, pady=(4, 2))
            entry["prog_bar"].pack(side="left", padx=(0, 6))
            entry["pct_lbl"].pack(side="left")
        entry["prog_bar"].set(1.0)
        entry["pct_lbl"].configure(text="100%")

        # update label
        loc = f"  →  {save_path}" if save_path else ""
        entry["info_lbl"].configure(
            text=f"✅  {filename} received{loc}",
            text_color="#a6e3a1",
        )

        entry["done"]["v"] = True
        self._transfer_registry.pop(transfer_id, None)
        self._scroll_bottom()

    def add_trust_notice(
        self, peer_id: str, fingerprint: str, status: str
    ) -> None:
        """Render a coloured trust-state banner."""
        _ICONS = {
            "new":      "🔑",
            "trusted":  "✅",
            "verified": "🛡️",
            "mismatch": "⚠️",
            "blocked":  "🚫",
        }
        icon     = _ICONS.get(status.lower(), "🔑")
        ts       = datetime.now().strftime("%H:%M:%S")
        short_id = (peer_id[:14]     + "…") if len(peer_id)     > 14 else peer_id
        short_fp = (fingerprint[:20] + "…") if len(fingerprint) > 20 else fingerprint

        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(
            row,
            text=f"── {ts}  {icon} {short_id} [{status.upper()}]  fp: {short_fp} ──",
            text_color="#cba6f7",
            font=("Consolas", 10),
        ).pack()
        self._scroll_bottom()

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _scroll_bottom(self) -> None:
        self.after(60, lambda: self._scroll._parent_canvas.yview_moveto(1.0))
