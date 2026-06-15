"""Central GUI state for P2PChat Sprint 3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIState:
    """
    Centralized GUI state.

    GUI components should render from this object
    instead of maintaining duplicated state.
    """

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    discovered_peers: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    connected_peers: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    contacts: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Active Selection
    # ------------------------------------------------------------------

    active_peer_id: str | None = None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def update_discovered_peer(
        self,
        peer_id: str,
        peer_info: dict[str, Any]
    ) -> None:
        self.discovered_peers[peer_id] = peer_info

    def remove_discovered_peer(
        self,
        peer_id: str
    ) -> None:
        self.discovered_peers.pop(peer_id, None)

    def clear_discovered_peers(self) -> None:
        self.discovered_peers.clear()

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def set_connected_peer(
        self,
        peer_id: str,
        peer_info: dict[str, Any]
    ) -> None:
        self.connected_peers[peer_id] = peer_info

    def remove_connected_peer(
        self,
        peer_id: str
    ) -> None:
        self.connected_peers.pop(peer_id, None)

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def add_contact(
        self,
        peer_id: str,
        contact_info: dict[str, Any]
    ) -> None:
        self.contacts[peer_id] = contact_info

    def remove_contact(
        self,
        peer_id: str
    ) -> None:
        self.contacts.pop(peer_id, None)

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def select_peer(
        self,
        peer_id: str | None
    ) -> None:
        self.active_peer_id = peer_id

    def get_selected_peer(
        self
    ) -> dict[str, Any] | None:

        if self.active_peer_id is None:
            return None

        return self.discovered_peers.get(
            self.active_peer_id
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def peer_count(self) -> int:
        return len(self.discovered_peers)

    @property
    def connected_count(self) -> int:
        return len(self.connected_peers)

    @property
    def contact_count(self) -> int:
        return len(self.contacts)