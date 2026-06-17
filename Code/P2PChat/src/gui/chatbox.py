from __future__ import annotations

import customtkinter as ctk

from gui.chat_bubble import add_chat_bubble

class ChatBox(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="#1e1e2e"
        )

        self.scroll.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

    # ==========================================
    # Messages
    # ==========================================

    def add_sent(
        self,
        sender: str,
        recipient: str,
        message: str
    ):

        add_chat_bubble(
            self.scroll,
            message,
            is_me=True
        )

        self.after(
            50,
            self.scroll_to_bottom
        )

    def add_received(
        self,
        sender: str,
        message: str
    ):

        add_chat_bubble(
            self.scroll,
            message,
            is_me=False
        )

        self.after(
            50,
            self.scroll_to_bottom
        )

    def add_system(
        self,
        text: str
    ):

        frame = ctk.CTkFrame(
            self.scroll,
            fg_color="transparent"
        )

        frame.pack(
            fill="x",
            pady=5
        )

        label = ctk.CTkLabel(
            frame,
            text=text,
            text_color="#6c7086",
            font=("Consolas", 11)
        )

        label.pack()

        self.after(
            50,
            self.scroll_to_bottom
        )

    # ==========================================
    # Helpers
    # ==========================================

    def clear(self):

        for widget in self.scroll.winfo_children():
            widget.destroy()

    def scroll_to_bottom(self):

        try:
            self.scroll._parent_canvas.yview_moveto(1.0)

        except Exception:
            pass