"""Chat bubbles — Telegram/Zalo-style message rendering."""
from __future__ import annotations

from datetime import datetime
import customtkinter as ctk
from gui import theme as T


def _now() -> str:
    return datetime.now().strftime("%H:%M")


# Max bubble width as fraction of chat area — bubbles never fill full width
_WRAP = 360


def add_chat_bubble(parent, message: str, sender: str = "me",
                    is_me: bool = False) -> None:
    """Append one message bubble to *parent* (a CTkScrollableFrame).
    Layout mirrors Telegram:
    - Sent  : right-aligned, blue, no sender name, double-tick
    - Received: left-aligned, dark, sender name in accent colour
    Both sides have consistent 8px vertical spacing and a timestamp footer.
    """
    ts = _now()

    outer = ctk.CTkFrame(parent, fg_color="transparent")
    outer.pack(fill="x", padx=16, pady=(3, 3))

    if is_me:
        # ── Sent bubble (right) ───────────────────────────────────
        bubble = ctk.CTkFrame(
            outer, fg_color=T.BG_BUBBLE_ME, corner_radius=18,
            # Flat bottom-right corner like Telegram
        )
        bubble.pack(anchor="e")

        ctk.CTkLabel(
            bubble, text=message,
            justify="left", wraplength=_WRAP,
            text_color="#dbeafe", font=("Segoe UI", 13),
        ).pack(anchor="w", padx=(14, 14), pady=(10, 2))

        # Footer row: spacer + timestamp + ticks
        foot = ctk.CTkFrame(bubble, fg_color="transparent")
        foot.pack(fill="x", padx=(14, 10), pady=(0, 8))
        ctk.CTkLabel(
            foot, text=f"{ts}  ✓✓",
            text_color="#93c5fd", font=("Segoe UI", 9),
        ).pack(side="right")

    else:
        # ── Received bubble (left) ────────────────────────────────
        bubble = ctk.CTkFrame(
            outer, fg_color=T.BG_BUBBLE_IN, corner_radius=18,
        )
        bubble.pack(anchor="w")

        # Sender name
        ctk.CTkLabel(
            bubble, text=sender, anchor="w",
            text_color=T.TEXT_LINK, font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(10, 0))

        # Message text
        ctk.CTkLabel(
            bubble, text=message,
            justify="left", wraplength=_WRAP,
            text_color=T.TEXT_PRI, font=("Segoe UI", 13),
        ).pack(anchor="w", padx=14, pady=(2, 2))

        # Timestamp footer
        ctk.CTkLabel(
            bubble, text=ts,
            text_color=T.TEXT_TIME, font=("Segoe UI", 9),
        ).pack(anchor="e", padx=12, pady=(0, 8))
