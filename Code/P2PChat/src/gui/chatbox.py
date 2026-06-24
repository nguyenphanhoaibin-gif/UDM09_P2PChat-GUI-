"""ChatBox: scrollable message area with date dividers and system notices."""
from __future__ import annotations

from datetime import datetime
import customtkinter as ctk
from gui import theme as T
from gui.chat_bubble import add_chat_bubble


class ChatBox(ctk.CTkFrame):
    """Scrollable area that holds message bubbles, date dividers, and notices."""

    def __init__(self, master, **kw) -> None:
        super().__init__(master, fg_color="transparent", **kw)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=T.BG_MAIN,
            scrollbar_button_color=T.BORDER,
            scrollbar_button_hover_color=T.BORDER_LIGHT)
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._last_date: str = ""

    # ------------------------------------------------------------------ #

    def add_sent(self, sender: str, _recipient: str, message: str) -> None:
        """Append an outbound message bubble.
        Args:
            sender: Display name of the local user.
            _recipient: Unused; kept for API compatibility.
            message: Plaintext message body.
        """
        self._maybe_date_divider()
        add_chat_bubble(self._scroll, message, sender=sender, is_me=True)
        self._scroll_bottom()

    def add_received(self, sender: str, message: str) -> None:
        """Append an inbound message bubble.
        Args:
            sender: Display name of the remote peer.
            message: Plaintext message body.
        """
        self._maybe_date_divider()
        add_chat_bubble(self._scroll, message, sender=sender, is_me=False)
        self._scroll_bottom()

    def add_system(self, text: str) -> None:
        """Add a centred system notice — pill style like Telegram."""
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", pady=6)
        pill = ctk.CTkFrame(row, fg_color=T.BG_FIELD, corner_radius=10)
        pill.pack()
        ctk.CTkLabel(pill, text=text,
                     text_color=T.TEXT_MUTED, font=("Segoe UI", 9),
                     ).pack(padx=12, pady=4)
        self._scroll_bottom()

    def clear(self) -> None:
        """Remove all messages and reset the date-divider state."""
        for w in self._scroll.winfo_children():
            w.destroy()
        self._last_date = ""

    # ------------------------------------------------------------------ #

    def _maybe_date_divider(self) -> None:
        today = datetime.now().strftime("%d %B %Y")
        if today != self._last_date:
            self._last_date = today
            self._date_divider(today)

    def _date_divider(self, label: str) -> None:
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", pady=10)
        # Left line
        ctk.CTkFrame(row, height=1, fg_color=T.BORDER).pack(
            side="left", fill="x", expand=True, padx=(20, 6))
        ctk.CTkLabel(row, text=label, fg_color=T.BG_FIELD,
                     corner_radius=8, text_color=T.TEXT_MUTED,
                     font=("Segoe UI", 9),
                     ).pack(side="left", padx=4, pady=2)
        ctk.CTkFrame(row, height=1, fg_color=T.BORDER).pack(
            side="left", fill="x", expand=True, padx=(6, 20))

    def _scroll_bottom(self) -> None:
        """Scroll to bottom — two-stage to ensure widget layout is complete."""
        def _do() -> None:
            # pylint: disable=protected-access
            canvas = self._scroll._parent_canvas
            canvas.update_idletasks()
            canvas.yview_moveto(1.0)
        self.after(100, _do)
