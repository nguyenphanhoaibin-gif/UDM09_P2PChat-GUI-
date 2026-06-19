"""Sidebar: peer list with connect button and manual IP/port entry."""
from __future__ import annotations

from typing import Callable, Optional
import customtkinter as ctk

from trust.trust_state import TrustState

TRUST_COLORS = {
    TrustState.NEW:      "#f9e2af",
    TrustState.TRUSTED:  "#89b4fa",
    TrustState.VERIFIED: "#a6e3a1",
    TrustState.MISMATCH: "#f38ba8",
    TrustState.BLOCKED:  "#6c7086",
}

STATUS_ICONS = {
    "online":     "🟢",
    "connected":  "🔗",
    "offline":    "⚪",
    "connecting": "🟡",
}


class PeerCard(ctk.CTkFrame):
    """One row in the peer list."""

    def __init__(
        self,
        master,
        peer_id:   str,
        peer_info: dict,
        on_select:  Optional[Callable] = None,
        on_connect: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master, corner_radius=12,
            fg_color="#313244", height=80, **kwargs
        )

        self.peer_id   = peer_id
        self.peer_info = peer_info
        self._on_select  = on_select
        self._on_connect = on_connect

        self.grid_columnconfigure(1, weight=1)

        username    = peer_info.get("username", "Unknown")
        status      = peer_info.get("status", "offline")
        trust_state = peer_info.get("trust_state", TrustState.NEW)
        connected   = peer_info.get("connected", False)
        ip          = peer_info.get("ip", "")
        port        = peer_info.get("port", "")

        icon        = STATUS_ICONS.get(status, "⚪")
        trust_color = TRUST_COLORS.get(trust_state, "#a6adc8")

        # Avatar
        ctk.CTkLabel(
            self, text="👤", font=("Segoe UI Emoji", 20),
        ).grid(row=0, column=0, rowspan=3, padx=(10, 6), pady=8)

        # Username
        self.username_label = ctk.CTkLabel(
            self, text=f"{icon} {username}",
            anchor="w", font=("Arial", 13, "bold"),
        )
        self.username_label.grid(row=0, column=1, sticky="w", pady=(8, 0))

        # Trust badge + IP
        self.trust_label = ctk.CTkLabel(
            self,
            text=f"🔑 {trust_state}  ·  {ip}:{port}",
            text_color=trust_color,
            anchor="w", font=("Consolas", 9),
        )
        self.trust_label.grid(row=1, column=1, sticky="w")

        # Connect / Connected button
        btn_text  = "🔗 Connected" if connected else "Connect"
        btn_color = "#45475a" if connected else "#89b4fa"
        btn_hover = "#585b70" if connected else "#74c7ec"

        self._connect_btn = ctk.CTkButton(
            self, text=btn_text,
            width=90, height=26,
            fg_color=btn_color, hover_color=btn_hover,
            font=("Arial", 11),
            command=self._do_connect,
            state="disabled" if connected else "normal",
        )
        self._connect_btn.grid(row=2, column=1, sticky="w", pady=(2, 8))

        # Click anywhere on card → select
        for widget in (self, self._connect_btn):
            widget.bind("<Button-1>", self._do_select)

    def _do_select(self, _e=None) -> None:
        if self._on_select:
            self._on_select(self.peer_id, self.peer_info)

    def _do_connect(self) -> None:
        if self._on_connect:
            self._on_connect(self.peer_id, self.peer_info)

    def set_selected(self, selected: bool) -> None:
        self.configure(fg_color="#45475a" if selected else "#313244")
        
    def update_info(self, peer_info: dict):
        self.peer_info = peer_info
        username = peer_info.get(
            "username",
            "Unknown"
        )
        status = peer_info.get(
            "status",
            "offline"
        )
        trust_state = peer_info.get(
            "trust_state",
            TrustState.NEW
        )
        trust_color = TRUST_COLORS.get(
            trust_state,
            "#a6adc8"
        )
        ip = peer_info.get(
            "ip",
            ""
        )
        port = peer_info.get(
            "port",
            ""
        )
        icon = STATUS_ICONS.get(
            status,
            "⚪"
        )
        self.username_label.configure(
            text=f"{icon} {username}"
        )
        self.trust_label.configure(
            text=f"🔑 {trust_state} · {ip}:{port}",
            text_color=trust_color
        )
        connected = peer_info.get(
            "connected",
            False
        )
        btn_text = (
            "🔗 Connected"
            if connected
            else "Connect"
        )
        btn_color = (
            "#45475a"
            if connected
            else "#89b4fa"
        )
        btn_hover = (
            "#585b70"
            if connected
            else "#74c7ec"
        )
        self._connect_btn.configure(
            text=btn_text,
            fg_color=btn_color,
            hover_color=btn_hover,
            state="disabled" if connected else "normal",
        )

class Sidebar(ctk.CTkFrame):
    """Left sidebar: title, search, peer cards, manual connect form."""

    def __init__(
        self,
        master,
        on_peer_select:    Optional[Callable] = None,
        on_peer_connect:   Optional[Callable] = None,
        on_manual_connect: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="#181825", width=290, **kwargs)
        self.grid_propagate(False)

        self._on_peer_select    = on_peer_select
        self._on_peer_connect   = on_peer_connect
        self._on_manual_connect = on_manual_connect
        self.selected_peer_id   = None
        self.peer_cards:        dict[str, PeerCard] = {}

        self._build_ui()

    # ------------------------------------------------------------------ #
    # Construction                                                         #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        # Title
        ctk.CTkLabel(
            self, text="Peers", font=("Arial", 18, "bold"),
        ).pack(anchor="w", padx=14, pady=(14, 4))

        # Search
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            self, textvariable=self._search_var,
            placeholder_text="Search peers…", height=32,
        ).pack(fill="x", padx=10, pady=(0, 6))

        # Peer scroll area
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#313244").pack(fill="x", padx=10)

        # Manual connect section
        self._build_manual_connect()

        # Footer
        self._footer = ctk.CTkLabel(
            self, text="No peer selected",
            text_color="#6c7086", font=("Consolas", 10),
        )
        self._footer.pack(pady=(4, 8))

    def _build_manual_connect(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            frame, text="Manual Connect",
            font=("Arial", 11, "bold"), anchor="w",
        ).pack(anchor="w")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", pady=(2, 0))
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=1)

        self._ip_entry = ctk.CTkEntry(
            row, placeholder_text="IP address", height=30, font=("Consolas", 11),
        )
        self._ip_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self._port_entry = ctk.CTkEntry(
            row, placeholder_text="Port", height=30,
            font=("Consolas", 11), width=70,
        )
        self._port_entry.grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            frame, text="Connect", height=30,
            command=self._do_manual_connect,
        ).pack(fill="x", pady=(4, 0))

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def update_peers(self, peers: dict):
        existing = set(self.peer_cards.keys())
        current = set(peers.keys())
        removed = existing - current
        for peer_id in removed:
            self.peer_cards[peer_id].destroy()
            del self.peer_cards[peer_id]
        self._all_peers = peers
        for peer_id, peer_info in peers.items():
            if peer_id in self.peer_cards:
                self.peer_cards[peer_id].update_info(peer_info)

            else:
                card = PeerCard(
                    self._scroll,
                    peer_id,
                    peer_info,
                    on_select=self._select_peer,
                    on_connect=self._connect_peer,
                )
                card.pack(
                    fill="x",
                    padx=4,
                    pady=3
                )
                self.peer_cards[peer_id] = card

    def _apply_filter(self) -> None:
        query = getattr(self, "_search_var", None)
        q     = query.get().lower().strip() if query else ""
        peers = getattr(self, "_all_peers", {})

        for widget in self._scroll.winfo_children():
            widget.destroy()
        self.peer_cards.clear()

        filtered = {
            pid: info for pid, info in peers.items()
            if not q
            or q in info.get("username", "").lower()
            or q in info.get("ip", "")
        }

        if not filtered:
            ctk.CTkLabel(
                self._scroll,
                text="No peers found" if q else "No peers discovered",
                text_color="#6c7086",
            ).pack(pady=20)
            return

        # Sort: connected first, then online, then offline
        def _sort_key(item):
            info = item[1]
            order = {"connected": 0, "online": 1, "offline": 2}
            return order.get(info.get("status", "offline"), 2)

        for peer_id, peer_info in sorted(filtered.items(), key=_sort_key):
            card = PeerCard(
                self._scroll,
                peer_id,
                peer_info,
                on_select  = self._select_peer,
                on_connect = self._connect_peer,
            )
            card.pack(fill="x", padx=4, pady=3)
            if peer_id == self.selected_peer_id:
                card.set_selected(True)
            self.peer_cards[peer_id] = card

    # ------------------------------------------------------------------ #
    # Internal actions                                                     #
    # ------------------------------------------------------------------ #

    def _select_peer(self, peer_id: str, peer_info: dict) -> None:
        self.selected_peer_id = peer_id
        for pid, card in self.peer_cards.items():
            card.set_selected(pid == peer_id)
        uname = peer_info.get("username", peer_id[:8])
        self._footer.configure(text=f"Selected: {uname}")
        if self._on_peer_select:
            self._on_peer_select(peer_id, peer_info)

    def _connect_peer(self, peer_id: str, peer_info: dict) -> None:
        if self._on_peer_connect:
            self._on_peer_connect(peer_id, peer_info)

    def _do_manual_connect(self) -> None:
        ip       = self._ip_entry.get().strip()
        port_str = self._port_entry.get().strip()
        if self._on_manual_connect:
            self._on_manual_connect(ip, port_str)
