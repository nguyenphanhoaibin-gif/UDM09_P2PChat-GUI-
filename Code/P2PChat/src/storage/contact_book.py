"""Contact book persistence."""

from pathlib import Path

from storage.storage_manager import StorageManager


class ContactBook:
    """
    Persistent contacts.

    contacts.json

    {
        peer_id: {
            "peer_id": "...",
            "alias": "...",
            "trust_state": "...",
            "fingerprint": "..."
        }
    }
    """

    def __init__(self):

        self.data_dir = Path(
            "data/storage"
        )

        StorageManager.ensure_dir(
            self.data_dir
        )

        self.contacts_file = (
            self.data_dir /
            "contacts.json"
        )

        self.contacts = {}

        self.load_contacts()

    # --------------------------------
    # FREEZE API
    # --------------------------------

    def load_contacts(self):
        """Load contacts from disk."""

        self.contacts = (
            StorageManager.load_json(
                self.contacts_file,
                {}
            )
        )

        return self.contacts

    def save_contacts(self):
        """Save contacts to disk."""

        StorageManager.save_json(
            self.contacts_file,
            self.contacts
        )

    def add_contact(
        self,
        peer_id: str,
        alias: str,
        trust_state: str,
        fingerprint: str
    ):
        """Add or update contact."""

        self.contacts[peer_id] = {
            "peer_id": peer_id,
            "alias": alias,
            "trust_state": trust_state,
            "fingerprint": fingerprint
        }

        self.save_contacts()

    def remove_contact(
        self,
        peer_id: str
    ):
        """Remove contact."""

        if peer_id not in self.contacts:
            return

        del self.contacts[peer_id]

        self.save_contacts()

    # --------------------------------
    # Helpers
    # --------------------------------

    def get_contact(
        self,
        peer_id: str
    ):

        return self.contacts.get(
            peer_id
        )

    def get_all_contacts(self):

        return list(
            self.contacts.values()
        )
        
    def update_contact(
        self,
        peer_id: str,
        alias: str | None = None,
        trust_state: str | None = None,
        fingerprint: str | None = None
    ):
        """Update existing contact."""

        contact = self.contacts.get(
            peer_id
        )

        if not contact:
            return

        if alias is not None:
            contact["alias"] = alias

        if trust_state is not None:
            contact["trust_state"] = trust_state

        if fingerprint is not None:
            contact["fingerprint"] = fingerprint

        self.save_contacts()
