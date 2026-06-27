"""UIState: lightweight value object for GUI-side application state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIState:
    """Holds all transient GUI state in one place.
    This is a pure data class — no business logic.  The ChatApp reads and
    writes these fields to keep the GUI consistent across callbacks fired
    from different threads (all via after(0, ...)).
    """

    # ── Discovery ──────────────────────────────────────────────────────
    discovered_peers: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ── Connected ──────────────────────────────────────────────────────
    connected_peers: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ── Contacts ───────────────────────────────────────────────────────
    contacts: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ── Selection ──────────────────────────────────────────────────────
    active_peer_id:    str | None = None
    active_contact_id: str | None = None

    # ── Session ────────────────────────────────────────────────────────
    connection_status:   str = "offline"
    encryption_status:   str = "disabled"
    last_status_message: str = ""

    # ------------------------------------------------------------------ #
    # Discovery                                                            #
    # ------------------------------------------------------------------ #

    def update_discovered_peer(self, peer_id: str, peer_info: dict[str, Any]) -> None:
        """Insert or replace *peer_id* in the discovered-peers registry."""
        self.discovered_peers[peer_id] = peer_info

    def remove_discovered_peer(self, peer_id: str) -> None:
        """Remove *peer_id* from the discovered-peers registry, if present."""
        self.discovered_peers.pop(peer_id, None)

    # ------------------------------------------------------------------ #
    # Connected                                                            #
    # ------------------------------------------------------------------ #

    def set_connected_peer(self, peer_id: str, peer_info: dict[str, Any]) -> None:
        """Record *peer_id* as actively connected."""
        self.connected_peers[peer_id] = peer_info

    def remove_connected_peer(self, peer_id: str) -> None:
        """Remove *peer_id* from the connected-peers set."""
        self.connected_peers.pop(peer_id, None)

    # ------------------------------------------------------------------ #
    # Contacts                                                             #
    # ------------------------------------------------------------------ #

    def add_contact(self, peer_id: str, contact_info: dict[str, Any]) -> None:
        """Add or update a saved contact."""
        self.contacts[peer_id] = contact_info

    def remove_contact(self, peer_id: str) -> None:
        """Remove a saved contact, if present."""
        self.contacts.pop(peer_id, None)

    # ------------------------------------------------------------------ #
    # Selection                                                            #
    # ------------------------------------------------------------------ #

    def select_peer(self, peer_id: str | None) -> None:
        """Set the currently-selected peer ID."""
        self.active_peer_id = peer_id

    def select_contact(self, contact_id: str | None) -> None:
        """Set the currently-selected contact ID."""
        self.active_contact_id = contact_id

    # ------------------------------------------------------------------ #
    # Session                                                              #
    # ------------------------------------------------------------------ #

    def set_connection_status(self, status: str) -> None:
        """Update the overall connection status string."""
        self.connection_status = status

    def set_encryption_status(self, status: str) -> None:
        """Update the encryption status string."""
        self.encryption_status = status

    def set_status_message(self, message: str) -> None:
        """Store the last status message shown to the user."""
        self.last_status_message = message

    # ------------------------------------------------------------------ #
    # Queries                                                              #
    # ------------------------------------------------------------------ #

    def get_selected_peer(self) -> dict[str, Any] | None:
        """Return the info dict for the active peer, or None."""
        if self.active_peer_id is None:
            return None
        return self.discovered_peers.get(self.active_peer_id)

    @property
    def peer_count(self) -> int:
        """Total number of discovered peers."""
        return len(self.discovered_peers)

    @property
    def connected_count(self) -> int:
        """Number of currently-connected peers."""
        return len(self.connected_peers)

    @property
    def contact_count(self) -> int:
        """Number of saved contacts."""
        return len(self.contacts)
