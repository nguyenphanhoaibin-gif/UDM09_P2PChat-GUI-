"""Design tokens — single source of truth for all GUI colours, fonts, and sizes.

Inspired by the Lumina P2P design system:
- Indigo primary (closer to the reference #4648D4, adapted for dark context)
- Tighter, more intentional palette — fewer shades, stronger hierarchy
- Generous rounding for a "secure but approachable" feel
"""
from __future__ import annotations

# ── Background layers (dark → light hierarchy) ────────────────────────────
BG_APP      = "#0f1117"   # root window — deepest layer
BG_SIDEBAR  = "#13151e"   # left panel
BG_MAIN     = "#0f1117"   # chat column
BG_HEADER   = "#1a1d2b"   # chat / sidebar headers
BG_INPUT    = "#1a1d2b"   # bottom input bar
BG_CARD     = "#1e2235"   # peer card normal
BG_CARD_HOV = "#252a42"   # peer card hover
BG_CARD_SEL = "#1e3163"   # peer card selected (indigo tinted)
BG_BUBBLE_ME= "#3730a3"   # sent bubble — deep indigo (matches Lumina primary)
BG_BUBBLE_IN= "#1e2235"   # received bubble
BG_FIELD    = "#1a1d2b"   # detail info rows
BG_DETAILS  = "#13151e"   # right panel
BG_TOAST    = "#1e2235"   # toast notification
BG_ENTRY    = "#1a1d2b"   # text entry
BG_BADGE    = "#1e3163"   # unread badge background

# ── Borders / separators ──────────────────────────────────────────────────
BORDER       = "#252a42"
BORDER_LIGHT = "#2e3452"

# ── Text ──────────────────────────────────────────────────────────────────
TEXT_PRI    = "#e8eaf6"   # primary — slightly warm white
TEXT_SEC    = "#8892b0"   # secondary
TEXT_MUTED  = "#4a5180"   # muted / placeholder
TEXT_TIME   = "#363b5e"   # timestamps
TEXT_LINK   = "#818cf8"   # links / accent labels (indigo-300)

# ── Accents — indigo-first palette ────────────────────────────────────────
ACCENT      = "#4f46e5"   # indigo-600 — primary action
ACCENT_HOV  = "#4338ca"   # indigo-700
ACCENT_DIM  = "#1e1b4b"   # indigo-950 — subtle background tint
ACCENT_GLOW = "#312e81"   # indigo-900 — border on focus

# ── Semantic colours ──────────────────────────────────────────────────────
SUCCESS     = "#10b981"   # emerald
WARNING     = "#f59e0b"   # amber
DANGER      = "#ef4444"   # red
DANGER_DIM  = "#2d1a1a"   # dark red tint

# ── Trust palette ─────────────────────────────────────────────────────────
TRUST_NEW      = "#f59e0b"
TRUST_TRUSTED  = "#818cf8"   # indigo-300
TRUST_VERIFIED = "#10b981"
TRUST_MISMATCH = "#ef4444"
TRUST_BLOCKED  = "#6b7280"

TRUST_BG: dict[str, str] = {
    "NEW":      "#22190a",
    "TRUSTED":  "#1e1b4b",
    "VERIFIED": "#0a1f16",
    "MISMATCH": "#2d0a0a",
    "BLOCKED":  "#151618",
}

TRUST_FG: dict[str, str] = {
    "NEW":      TRUST_NEW,
    "TRUSTED":  TRUST_TRUSTED,
    "VERIFIED": TRUST_VERIFIED,
    "MISMATCH": TRUST_MISMATCH,
    "BLOCKED":  TRUST_BLOCKED,
}

# ── Status dot colours ────────────────────────────────────────────────────
STATUS_DOT: dict[str, str] = {
    "online":     SUCCESS,
    "connected":  ACCENT,
    "offline":    "#2d3350",
    "connecting": WARNING,
}

# ── Avatar palette ────────────────────────────────────────────────────────
AVATAR_PALETTE: list[str] = [
    "#4f46e5",  # indigo
    "#7c3aed",  # violet
    "#0891b2",  # cyan
    "#059669",  # emerald
    "#d97706",  # amber
    "#dc2626",  # red
    "#db2777",  # pink
    "#0284c7",  # sky
]

# ── Typography — closer to Inter rhythm ───────────────────────────────────
FONT        = "Segoe UI"     # Windows; Inter if available
FONT_MONO   = "Consolas"
FONT_TITLE  = (FONT, 14, "bold")
FONT_BODY   = (FONT, 13)
FONT_SMALL  = (FONT, 11)
FONT_BADGE  = (FONT, 9, "bold")
FONT_MONO_S = (FONT_MONO, 9)


def avatar_color(name: str) -> str:
    """Return a stable avatar colour for *name*."""
    return AVATAR_PALETTE[sum(ord(c) for c in name) % len(AVATAR_PALETTE)]
