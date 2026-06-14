"""Contact data model for P2PChat."""

from dataclasses import dataclass

@dataclass(slots=True)
class Contact:
    """Data model representing a contact in the P2PChat application."""
    peer_id: str
    alias: str
    trust_state: str
    fingerprint: str
