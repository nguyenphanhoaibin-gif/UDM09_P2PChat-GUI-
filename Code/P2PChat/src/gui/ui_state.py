from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIState:

    # ==================================
    # Discovery
    # ==================================

    discovered_peers: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ==================================
    # Connected
    # ==================================

    connected_peers: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ==================================
    # Contacts
    # ==================================

    contacts: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ==================================
    # Selection
    # ==================================

    active_peer_id: str | None = None

    active_contact_id: str | None = None

    # ==================================
    # Session
    # ==================================

    connection_status: str = "offline"

    encryption_status: str = "disabled"

    last_status_message: str = ""

    # ==================================
    # Discovery
    # ==================================

    def update_discovered_peer(
        self,
        peer_id: str,
        peer_info: dict[str, Any]
    ):
        self.discovered_peers[peer_id] = peer_info

    def remove_discovered_peer(
        self,
        peer_id: str
    ):
        self.discovered_peers.pop(
            peer_id,
            None
        )

    # ==================================
    # Connected
    # ==================================

    def set_connected_peer(
        self,
        peer_id: str,
        peer_info: dict[str, Any]
    ):
        self.connected_peers[peer_id] = (
            peer_info
        )

    def remove_connected_peer(
        self,
        peer_id: str
    ):
        self.connected_peers.pop(
            peer_id,
            None
        )

    # ==================================
    # Contacts
    # ==================================

    def add_contact(
        self,
        peer_id: str,
        contact_info: dict[str, Any]
    ):
        self.contacts[peer_id] = contact_info

    def remove_contact(
        self,
        peer_id: str
    ):
        self.contacts.pop(
            peer_id,
            None
        )

    # ==================================
    # Selection
    # ==================================

    def select_peer(
        self,
        peer_id: str | None
    ):
        self.active_peer_id = peer_id

    def select_contact(
        self,
        contact_id: str | None
    ):
        self.active_contact_id = contact_id

    # ==================================
    # Session
    # ==================================

    def set_connection_status(
        self,
        status: str
    ):
        self.connection_status = status

    def set_encryption_status(
        self,
        status: str
    ):
        self.encryption_status = status

    def set_status_message(
        self,
        message: str
    ):
        self.last_status_message = message

    # ==================================
    # Queries
    # ==================================

    def get_selected_peer(self):

        if self.active_peer_id is None:
            return None

        return self.discovered_peers.get(
            self.active_peer_id
        )

    @property
    def peer_count(self):

        return len(
            self.discovered_peers
        )

    @property
    def connected_count(self):

        return len(
            self.connected_peers
        )

    @property
    def contact_count(self):

        return len(
            self.contacts
        )