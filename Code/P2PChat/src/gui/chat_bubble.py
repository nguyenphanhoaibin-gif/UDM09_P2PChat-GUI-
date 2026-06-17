from __future__ import annotations

import customtkinter as ctk


def add_chat_bubble(
    parent,
    message: str,
    is_me: bool = False
):
    """
    Telegram-style message bubble.
    """

    row = ctk.CTkFrame(
        parent,
        fg_color="transparent"
    )

    row.pack(
        fill="x",
        padx=8,
        pady=4
    )

    if is_me:

        container = ctk.CTkFrame(
            row,
            fg_color="#89b4fa",
            corner_radius=18
        )

        container.pack(
            anchor="e",
            padx=(120, 5)
        )

        label = ctk.CTkLabel(
            container,
            text=message,
            justify="left",
            wraplength=500,
            text_color="#11111b",
            font=("Arial", 13)
        )

        label.pack(
            padx=12,
            pady=8
        )

    else:

        container = ctk.CTkFrame(
            row,
            fg_color="#313244",
            corner_radius=18
        )

        container.pack(
            anchor="w",
            padx=(5, 120)
        )

        label = ctk.CTkLabel(
            container,
            text=message,
            justify="left",
            wraplength=500,
            font=("Arial", 13)
        )

        label.pack(
            padx=12,
            pady=8
        )