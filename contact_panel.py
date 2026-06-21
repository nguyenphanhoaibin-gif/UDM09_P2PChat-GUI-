
from __future__ import annotations

import threading
from typing import Callable, Optional

import customtkinter as ctk


_TRUST_COLORS: dict[str, str] = {
    "NEW":      "#f9e2af",
    "TRUSTED":  "#89b4fa",
    "VERIFIED": "#a6e3a1",
    "MISMATCH": "#f38ba8",
    "BLOCKED":  "#6c7086",
}

# ContactCard  —  one saved contact

class ContactCard(ctk.CTkFrame):
    """Visual card for a saved contact.

    Shows: online badge, alias, short peer_id, short fingerprint,
    trust-state badge, IP:port when online, Remove button.
    Clicking the card fires ``on_select(contact, ip, port)``.
    """

    def __init__(
        self,
        master,
        contact:   dict,
        is_online: bool                  = False,
        peer_info: Optional[dict]        = None,
        on_select: Optional[Callable]    = None,
        on_remove: Optional[Callable]    = None,
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=10, fg_color="#313244", **kwargs)

        self.contact   = contact
        self.is_online = is_online
        self.peer_info = peer_info or {}
        self._on_select = on_select
        self._on_remove = on_remove

        self.grid_columnconfigure(0, weight=1)

        peer_id     = contact.get("peer_id",     "")
        alias       = contact.get("alias",       "Unknown")
        trust_state = contact.get("trust_state", "NEW")
        fingerprint = contact.get("fingerprint", "")

        # ── row 0: badge + alias ─────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="🟢" if is_online else "⚪",
            width=20, anchor="w",
        ).grid(row=0, column=0, padx=(0, 4))

        ctk.CTkLabel(
            header,
            text=alias,
            anchor="w",
            font=("Arial", 13, "bold"),
        ).grid(row=0, column=1, sticky="ew")

        # ── row 1: short peer_id ────────────────────────────────────
        short_id = (peer_id[:20] + "…") if len(peer_id) > 20 else peer_id
        ctk.CTkLabel(
            self, text=short_id, anchor="w",
            text_color="#a6adc8", font=("Consolas", 10),
        ).grid(row=1, column=0, sticky="ew", padx=8)

        # ── row 2: short fingerprint ─────────────────────────────────
        fp_short = (fingerprint[:20] + "…") if len(fingerprint) > 20 else fingerprint
        ctk.CTkLabel(
            self, text=f"fp: {fp_short}" if fp_short else "fp: —",
            anchor="w", text_color="#6c7086", font=("Consolas", 9),
        ).grid(row=2, column=0, sticky="ew", padx=8)

        # ── row 3: trust badge ───────────────────────────────────────
        trust_color = _TRUST_COLORS.get(trust_state, "#a6adc8")
        ctk.CTkLabel(
            self, text=trust_state,
            text_color=trust_color,
            font=("Consolas", 10, "bold"), anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=8, pady=(0, 2))

        # ── row 4: IP:port if online ─────────────────────────────────
        _next_row = 4
        if is_online:
            ip   = self.peer_info.get("ip",   "")
            port = self.peer_info.get("port", "")
            if ip and port:
                ctk.CTkLabel(
                    self, text=f"  {ip}:{port}",
                    anchor="w", text_color="#89b4fa",
                    font=("Consolas", 9),
                ).grid(row=_next_row, column=0, sticky="w", padx=8, pady=(0, 2))
                _next_row += 1

        # ── Remove button ────────────────────────────────────────────
        ctk.CTkButton(
            self, text="Remove", width=70, height=22,
            fg_color="#45475a", hover_color="#585b70",
            font=("Arial", 10),
            command=self._handle_remove,
        ).grid(row=_next_row, column=0, sticky="w", padx=8, pady=(2, 8))

        # make the whole card clickable (except the button)
        for w in (self, header):
            w.bind("<Button-1>", self._handle_click)

    def _handle_click(self, _event=None) -> None:
        if self._on_select:
            ip   = self.peer_info.get("ip",   "")
            port = str(self.peer_info.get("port", ""))
            self._on_select(self.contact, ip, port)

    def _handle_remove(self) -> None:
        if self._on_remove:
            self._on_remove(self.contact.get("peer_id", ""))


# DiscoveredPeerCard  —  online peer not yet saved

class DiscoveredPeerCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        peer_id:  str,
        peer_info: dict,
        on_add:   Optional[Callable] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, corner_radius=10, fg_color="#1e1e2e", **kwargs)

        self.peer_id   = peer_id
        self.peer_info = peer_info
        self._on_add   = on_add

        self.grid_columnconfigure(0, weight=1)

        username    = peer_info.get("username",    peer_id[:12])
        ip          = peer_info.get("ip",          "?")
        port        = peer_info.get("port",        "?")
        trust_state = peer_info.get("trust_state", "NEW")
        trust_color = _TRUST_COLORS.get(trust_state, "#a6adc8")

        ctk.CTkLabel(
            self, text=f"🟢 {username}",
            anchor="w", font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        ctk.CTkLabel(
            self, text=f"  {ip}:{port}",
            anchor="w", text_color="#89b4fa", font=("Consolas", 10),
        ).grid(row=1, column=0, sticky="ew", padx=8)

        short_id = (peer_id[:18] + "…") if len(peer_id) > 18 else peer_id
        ctk.CTkLabel(
            self, text=short_id,
            anchor="w", text_color="#6c7086", font=("Consolas", 9),
        ).grid(row=2, column=0, sticky="ew", padx=8)

        ctk.CTkLabel(
            self, text=trust_state,
            text_color=trust_color, anchor="w", font=("Consolas", 10),
        ).grid(row=3, column=0, sticky="w", padx=8, pady=(0, 2))

        ctk.CTkButton(
            self, text="+ Add to Contacts", height=26,
            fg_color="#313244", hover_color="#45475a",
            border_width=1, border_color="#89b4fa",
            text_color="#89b4fa", font=("Arial", 10, "bold"),
            command=self._handle_add,
        ).grid(row=4, column=0, sticky="w", padx=8, pady=(2, 8))

    def _handle_add(self) -> None:
        if self._on_add:
            self._on_add(self.peer_id, self.peer_info)


# ══════════════════════════════════════════════════════════════════════════════
# ContactPanel
# ══════════════════════════════════════════════════════════════════════════════

class ContactPanel(ctk.CTkFrame):
    """Full contact panel — Sprint 3.

    Parameters
    ----------
    contact_book:
        A ``ContactBook`` instance (or *None*).
    on_contact_select:
        ``(contact: dict, ip: str, port: str) -> None``
        Fired when a contact card is clicked; *ip* / *port* are non-empty
        only when the contact is currently online.
    on_add_contact:
        ``(peer_id: str, peer_info: dict) -> None``
        Fired after a new contact has been persisted.
    on_remove_contact:
        ``(peer_id: str) -> None``
        Fired after a contact has been removed.
    """

    def __init__(
        self,
        master,
        contact_book=None,
        on_contact_select: Optional[Callable] = None,
        on_add_contact:    Optional[Callable] = None,
        on_remove_contact: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="#181825", **kwargs)

        self._contact_book       = contact_book
        self._on_contact_select  = on_contact_select
        self._on_add_contact     = on_add_contact
        self._on_remove_contact  = on_remove_contact

        self._online_peers: dict[str, dict] = {}
        self._lock = threading.Lock()

        self._build_ui()
        self._refresh()

    # ── build ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="⭐ Contacts",
            font=("Arial", 14, "bold"), anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self._scroll.grid_columnconfigure(0, weight=1)

    # ── public API ────────────────────────────────────────────────────

    def load_contacts(self, contacts: list) -> None:
        """Refresh display with an explicit list (thread-safe via after)."""
        self.after(0, lambda: self._render(contacts))

    def set_online_peers(self, peers: dict) -> None:
        """Replace the full online-peer dict and refresh.

        ``peers`` → ``{ peer_id: {"username", "ip", "port", ...} }``
        """
        with self._lock:
            self._online_peers = dict(peers)
        self.after(0, self._refresh)

    def on_peer_discovered(self, peer_address: str, info: dict) -> None:
        """Compatible with ``ChatController.on_peer_discovered`` signature."""
        peer_id = info.get("peer_id", peer_address)
        with self._lock:
            self._online_peers[peer_id] = {**info, "peer_id": peer_id}
        self.after(0, self._refresh)

    def mark_peer_offline(self, peer_id: str) -> None:
        """Remove a peer from the online set and refresh."""
        with self._lock:
            self._online_peers.pop(peer_id, None)
        self.after(0, self._refresh)

    # ── internal ─────────────────────────────────────────────────────

    def _refresh(self) -> None:
        contacts: list = []
        if self._contact_book is not None:
            contacts = self._contact_book.get_all_contacts()
        self._render(contacts)

    def _render(self, contacts: list) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        with self._lock:
            online = dict(self._online_peers)

        saved_ids = {c.get("peer_id", "") for c in contacts}

        # ── saved contacts ────────────────────────────────────────────
        if contacts:
            for contact in contacts:
                pid = contact.get("peer_id", "")
                ContactCard(
                    self._scroll,
                    contact   = contact,
                    is_online = pid in online,
                    peer_info = online.get(pid, {}),
                    on_select = self._handle_select,
                    on_remove = self._handle_remove,
                ).grid(sticky="ew", padx=4, pady=3)
        else:
            ctk.CTkLabel(
                self._scroll, text="No contacts yet",
                text_color="#6c7086",
            ).grid(pady=10)

        # ── online peers not yet saved ────────────────────────────────
        new_peers = {pid: info for pid, info in online.items()
                     if pid not in saved_ids}
        if new_peers:
            ctk.CTkLabel(
                self._scroll, text="──── Online ────",
                text_color="#6c7086", font=("Consolas", 10),
            ).grid(sticky="ew", padx=8, pady=(8, 2))
            for pid, info in new_peers.items():
                DiscoveredPeerCard(
                    self._scroll,
                    peer_id   = pid,
                    peer_info = info,
                    on_add    = self._handle_add,
                ).grid(sticky="ew", padx=4, pady=3)

    # ── event handlers ────────────────────────────────────────────────

    def _handle_select(self, contact: dict, ip: str, port: str) -> None:
        if self._on_contact_select:
            self._on_contact_select(contact, ip, port)

    def _handle_add(self, peer_id: str, peer_info: dict) -> None:
        if self._contact_book is not None:
            self._contact_book.add_contact(
                peer_id,
                alias       = peer_info.get("username", peer_id[:12]),
                trust_state = peer_info.get("trust_state", "NEW"),
                fingerprint = peer_info.get("fingerprint", ""),
            )
        if self._on_add_contact:
            self._on_add_contact(peer_id, peer_info)
        self.after(0, self._refresh)

    def _handle_remove(self, peer_id: str) -> None:
        if self._contact_book is not None:
            self._contact_book.remove_contact(peer_id)
        if self._on_remove_contact:
            self._on_remove_contact(peer_id)
        self.after(0, self._refresh)
