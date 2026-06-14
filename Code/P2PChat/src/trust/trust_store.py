"""Trust store for managing known peers and their trust states in P2PChat."""

from pathlib import Path
import json
import threading


class TrustStore:
    """
    Persistent storage for known peers.

    known_peers.json

    {
        peer_id: {
            "fingerprint": "...",
            "trust_state": "VERIFIED"
        }
    }
    """

    def __init__(self):

        self.data_dir = Path(
            "data/trust"
        )

        self.store_file = (
            self.data_dir /
            "known_peers.json"
        )

        self._lock = threading.RLock()

        self.peers = {}

        self.load()

    # --------------------------------
    # Persistence
    # --------------------------------

    def load(self):
        """Load known peers from disk."""
        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.store_file.exists():

            self.peers = {}

            return

        try:

            with open(
                self.store_file,
                "r",
                encoding="utf-8"
            ) as f:

                self.peers = json.load(f)

        except Exception:

            self.peers = {}

    def save(self):
        """Save known peers to disk."""
        temp_file = (
            self.store_file
            .with_suffix(".tmp")
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.peers,
                f,
                indent=4
            )

        temp_file.replace(
            self.store_file
        )

    # --------------------------------
    # CRUD
    # --------------------------------

    def get_peer(
        self,
        peer_id: str
    ):
        """Get peer info by peer ID."""
        with self._lock:

            return self.peers.get(
                peer_id
            )

    def add_peer(
        self,
        peer_id: str,
        fingerprint: str,
        trust_state: str
    ):
        """Add a new peer to the trust store."""
        with self._lock:

            self.peers[peer_id] = {
                "fingerprint":
                    fingerprint,

                "trust_state":
                    trust_state
            }

            self.save()

    def update_peer(
        self,
        peer_id: str,
        fingerprint: str,
        trust_state: str
    ):
        """Update an existing peer's info in the trust store."""
        with self._lock:

            self.peers[peer_id] = {
                "fingerprint":
                    fingerprint,

                "trust_state":
                    trust_state
            }

            self.save()

    def remove_peer(
        self,
        peer_id: str
    ):
        """Remove a peer from the trust store."""
        with self._lock:

            if peer_id in self.peers:

                del self.peers[
                    peer_id
                ]

                self.save()

    def get_all_peers(self):
        """Return a copy of all known peers."""
        with self._lock:

            return dict(
                self.peers
            )
