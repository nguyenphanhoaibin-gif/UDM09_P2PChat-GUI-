"""Identity management for P2PChat, including key generation, storage, and retrieval."""

from pathlib import Path
import json

from security.rsa_utils import RSAUtils

from identity.peer_id import ( generate_peer_id)

from identity.fingerprint import ( generate_fingerprint )


class IdentityManager:
    """Manages the user's identity, including key generation, storage, and retrieval."""
    
    def __init__(self):

        self.identity_dir = Path(
            "data/identity"
        )

        self.identity_file = (
            self.identity_dir /
            "identity.json"
        )

        self.private_key = None
        self.public_key = None
        self.private_key_pem: str = ""
        self.public_key_pem: str = ""
        self.peer_id = ""
        self.fingerprint = ""

    # --------------------------------
    # FREEZE API
    # --------------------------------

    def load_identity(self):
        """Load existing identity or create a new one if not found."""

        self.identity_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if self.identity_file.exists():

            with open(
                self.identity_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            self.private_key_pem = data["private_key"]
            self.public_key_pem = data["public_key"]                   
            self.private_key = (
                RSAUtils.load_private_key(self.private_key_pem)
            )
            self.public_key = (
                RSAUtils.load_public_key(
                    self.public_key_pem
                )
            )

        else:
            (
                self.private_key,
                self.public_key
            ) = RSAUtils.generate_key_pair()

            self.public_key_pem = (
                RSAUtils.serialize_public_key(
                    self.public_key
                )
            )

            self.save_identity()

        self.peer_id = generate_peer_id(
            self.public_key_pem
        )

        self.fingerprint = (
            generate_fingerprint(
                self.public_key_pem
            )
        )

    def save_identity(self):
        """Save the current identity to disk."""
        data = {
            "private_key":
                RSAUtils.serialize_private_key(
                    self.private_key
                ),                 
            "public_key":
                self.public_key_pem
        }

        temp_file = (
            self.identity_file
            .with_suffix(".tmp")
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

        temp_file.replace(
            self.identity_file
        )

    def get_peer_id(self):
        """Return the stable Peer ID derived from the public key."""
        return self.peer_id

    def get_fingerprint(self):
        """Return the fingerprint of the public key."""
        return self.fingerprint

    def get_public_key(self):
        return self.public_key


    def get_private_key(self):
        return self.private_key

    def get_public_key_pem(self):
        return self.public_key_pem
