from trust.trust_store import (TrustStore)
from trust.trust_state import (TrustState)


class TOFUEngine:

    def __init__(self):

        self.store = TrustStore()

    # ------------------------------
    # FREEZE API
    # ------------------------------

    def verify_peer(
        self,
        peer_id: str,
        fingerprint: str
    ) -> str:
        
        peer = self.store.get_peer(
            peer_id
        )

        if peer is None:

            return TrustState.NEW

        stored_fingerprint = (
            peer["fingerprint"]
        )

        trust_state = (
            peer["trust_state"]
        )

        if trust_state == TrustState.BLOCKED:

            return TrustState.BLOCKED

        if (
            stored_fingerprint
            ==
            fingerprint
        ):

            return TrustState.VERIFIED

        return TrustState.MISMATCH

    def add_peer(
        self,
        peer_id: str,
        fingerprint: str
    ):

        self.store.add_peer(
            peer_id,
            fingerprint,
            TrustState.TRUSTED
        )

    def update_peer(
        self,
        peer_id: str,
        fingerprint: str,
        trust_state: str
    ):

        self.store.update_peer(
            peer_id,
            fingerprint,
            trust_state
        )
        
    def block_peer(
        self,
        peer_id: str
    ):
        """Block peer."""

        peer = self.store.get_peer(
            peer_id
        )

        if not peer:
            return

        self.store.update_peer(
            peer_id,
            peer["fingerprint"],
            TrustState.BLOCKED
        )


    def trust_peer(
        self,
        peer_id: str
    ):
        """Mark peer as trusted."""

        peer = self.store.get_peer(
            peer_id
        )

        if not peer:
            return

        self.store.update_peer(
            peer_id,
            peer["fingerprint"],
            TrustState.TRUSTED
        )


    def get_trust_state(
        self,
        peer_id: str
    ) -> str:
        """Get current trust state."""

        peer = self.store.get_peer(
            peer_id
        )

        if not peer:
            return TrustState.NEW

        return peer[
            "trust_state"
        ]
