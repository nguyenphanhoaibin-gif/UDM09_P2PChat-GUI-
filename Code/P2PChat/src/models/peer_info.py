"""Peer information data model for P2PChat."""

from dataclasses import dataclass

@dataclass(slots=True)
class PeerInfo:
    """Data model representing a peer in the P2PChat application."""
    peer_id: str
    username: str
    fingerprint: str
    ip: str
    tcp_port: int
    status: str
    last_seen: float
