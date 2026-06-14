"""History record data model for P2PChat."""

from dataclasses import dataclass

@dataclass(slots=True)
class HistoryRecord:
    """Data model representing a chat history record."""
    message_id: str
    peer_id: str
    direction: str
    content: str
    timestamp: float
   