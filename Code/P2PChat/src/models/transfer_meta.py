"""Transfer metadata data model for P2PChat."""

from dataclasses import dataclass

@dataclass(slots=True)
class TransferMeta:
    """Data model representing metadata of a file transfer."""
    transfer_id: str
    filename: str
    filesize: int
    sender_id: str
    receiver_id: str
    status: str
