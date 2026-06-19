"""ChatBox: scrollable chat display with bubble-style messages."""
from __future__ import annotations

from datetime import datetime
import customtkinter as ctk
from gui.chat_bubble import add_chat_bubble


class ChatBox(ctk.CTkFrame):
    """Scrollable message area.  Thread-safe via after(0, ...)."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="#1e1e2e")
        self._scroll.grid(row=0, column=0, sticky="nsew")

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

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _scroll_bottom(self) -> None:
        self.after(60, lambda: self._scroll._parent_canvas.yview_moveto(1.0))
