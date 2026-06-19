"""Telegram-style chat bubble with sender name and timestamp."""
from __future__ import annotations

from datetime import datetime
import customtkinter as ctk


def add_chat_bubble(
    parent,
    message: str,
    sender:  str  = "me",
    is_me:   bool = False,
) -> None:
    """Append a chat bubble to *parent* (a CTkScrollableFrame)."""

    ts = datetime.now().strftime("%H:%M")

    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="x", padx=10, pady=3)

    if is_me:
        bubble = ctk.CTkFrame(outer, fg_color="#1d4ed8", corner_radius=18)
        bubble.pack(anchor="e", padx=(80, 0))

        ctk.CTkLabel(
            bubble,
            text=message,
            justify="left",
            wraplength=420,
            text_color="#f0f9ff",
            font=("Arial", 13),
        ).pack(padx=14, pady=(8, 2))

        ctk.CTkLabel(
            bubble,
            text=f"You  {ts}",
            text_color="#93c5fd",
            font=("Consolas", 9),
            anchor="e",
        ).pack(anchor="e", padx=14, pady=(0, 6))

    else:
        bubble = ctk.CTkFrame(outer, fg_color="#313244", corner_radius=18)
        bubble.pack(anchor="w", padx=(0, 80))

        ctk.CTkLabel(
            bubble,
            text=sender,
            text_color="#89b4fa",
            font=("Arial", 10, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(8, 0))

        ctk.CTkLabel(
            bubble,
            text=message,
            justify="left",
            wraplength=420,
            font=("Arial", 13),
        ).pack(padx=14, pady=(2, 2))

        ctk.CTkLabel(
            bubble,
            text=ts,
            text_color="#6c7086",
            font=("Consolas", 9),
            anchor="e",
        ).pack(anchor="e", padx=14, pady=(0, 6))
