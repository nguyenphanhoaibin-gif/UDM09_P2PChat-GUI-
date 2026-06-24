"""Centralised design tokens — single source of truth for all GUI colours/fonts."""
from __future__ import annotations

# ── Background layers ──────────────────────────────────────────────────
BG_APP      = "#0d0e1a"   # root window
BG_SIDEBAR  = "#111220"   # left panel
BG_MAIN     = "#13141f"   # chat column
BG_HEADER   = "#181929"   # chat / sidebar headers
BG_INPUT    = "#181929"   # bottom input bar
BG_CARD     = "#1c1d2e"   # peer card normal
BG_CARD_HOV = "#21223a"   # peer card hover
BG_CARD_SEL = "#1e2f58"   # peer card selected
BG_BUBBLE_ME= "#1d4ed8"   # sent bubble
BG_BUBBLE_IN= "#1c1d2e"   # received bubble
BG_FIELD    = "#1a1b2c"   # detail info rows
BG_DETAILS  = "#111220"   # right panel
BG_TOAST    = "#1e2035"   # toast notification
BG_ENTRY    = "#1a1b2c"   # text entry

# ── Borders / separators ───────────────────────────────────────────────
BORDER      = "#232438"
BORDER_LIGHT= "#2a2b45"

# ── Text ───────────────────────────────────────────────────────────────
TEXT_PRI    = "#e8eaf6"
TEXT_SEC    = "#8892b0"
TEXT_MUTED  = "#4a5080"
TEXT_TIME   = "#3d4060"
TEXT_LINK   = "#60a5fa"

# ── Accents ────────────────────────────────────────────────────────────
ACCENT      = "#3b82f6"
ACCENT_HOV  = "#2563eb"
ACCENT_DIM  = "#1e3a5f"

SUCCESS     = "#10b981"
WARNING     = "#f59e0b"
DANGER      = "#ef4444"
DANGER_DIM  = "#2d1a1a"

# ── Trust colours ──────────────────────────────────────────────────────
TRUST_NEW      = "#f59e0b"
TRUST_TRUSTED  = "#3b82f6"
TRUST_VERIFIED = "#10b981"
TRUST_MISMATCH = "#ef4444"
TRUST_BLOCKED  = "#6b7280"

TRUST_BG: dict[str, str] = {
    "NEW":      "#201a0a",
    "TRUSTED":  "#0f1a30",
    "VERIFIED": "#0a1f16",
    "MISMATCH": "#200a0a",
    "BLOCKED":  "#151618",
}

TRUST_FG: dict[str, str] = {
    "NEW":      TRUST_NEW,
    "TRUSTED":  TRUST_TRUSTED,
    "VERIFIED": TRUST_VERIFIED,
    "MISMATCH": TRUST_MISMATCH,
    "BLOCKED":  TRUST_BLOCKED,
}

# ── Status dot colours ─────────────────────────────────────────────────
STATUS_DOT: dict[str, str] = {
    "online":     SUCCESS,
    "connected":  ACCENT,
    "offline":    "#2d3350",
    "connecting": WARNING,
}

# ── Avatar palette ─────────────────────────────────────────────────────
AVATAR_PALETTE: list[str] = [
    "#3b82f6", "#8b5cf6", "#10b981",
    "#f59e0b", "#ef4444", "#06b6d4",
    "#ec4899", "#14b8a6",
]

# ── Typography ─────────────────────────────────────────────────────────
FONT_TITLE   = ("Segoe UI", 14, "bold")
FONT_BODY    = ("Segoe UI", 12)
FONT_SMALL   = ("Segoe UI", 10)
FONT_MONO    = ("Consolas", 10)
FONT_MONO_SM = ("Consolas", 9)
FONT_BADGE   = ("Segoe UI", 9, "bold")


def avatar_color(name: str) -> str:
    """Return a stable avatar colour from the username string."""
    return AVATAR_PALETTE[sum(ord(c) for c in name) % len(AVATAR_PALETTE)]
