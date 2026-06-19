"""Trust-On-First-Use engine for P2PChat."""

from trust.trust_store import TrustStore
from trust.trust_state import TrustState


class TOFUEngine:
    """TOFU: automatically trusts new peers on first contact, warns on mismatch."""

    def __init__(self):
        self.store = TrustStore()

    # ------------------------------------------------------------------ #
    # Core TOFU API                                                        #
    # ------------------------------------------------------------------ #

    def verify_peer(self, peer_id: str, fingerprint: str) -> str:
        """Check and update trust state for *peer_id* with *fingerprint*.

        State machine:
          unknown          → NEW       (stored as TRUSTED on first sight)
          stored + match   → VERIFIED
          stored + BLOCKED → BLOCKED
          stored + mismatch → MISMATCH
        """
        peer = self.store.get_peer(peer_id)

        if peer is None:
            # First time seeing this peer: auto-trust (TOFU).
            self.store.add_peer(peer_id, fingerprint, TrustState.TRUSTED)
            return TrustState.NEW

        stored_fp    = peer["fingerprint"]
        trust_state  = peer["trust_state"]

        if trust_state == TrustState.BLOCKED:
            return TrustState.BLOCKED

        if stored_fp == fingerprint:
            # Fingerprint matches — promote to VERIFIED if not already.
            return trust_state

        # Fingerprint changed — potential key rotation or MITM.
        return TrustState.MISMATCH

    def add_peer(self, peer_id: str, fingerprint: str):
        """Explicitly add a peer as TRUSTED."""
        self.store.add_peer(peer_id, fingerprint, TrustState.TRUSTED)

    def update_peer(self, peer_id: str, fingerprint: str, trust_state: str):
        """Update a peer's record."""
        self.store.update_peer(peer_id, fingerprint, trust_state)

    def trust_peer(self, peer_id: str) -> bool:
        """Mark *peer_id* as TRUSTED. Returns False if peer unknown."""
        peer = self.store.get_peer(peer_id)
        if not peer:
            return False
        self.store.update_peer(peer_id, peer["fingerprint"], TrustState.TRUSTED)
        return True

    def block_peer(self, peer_id: str) -> bool:
        """Mark *peer_id* as BLOCKED. Returns False if peer unknown."""
        peer = self.store.get_peer(peer_id)
        if not peer:
            return False
        self.store.update_peer(peer_id, peer["fingerprint"], TrustState.BLOCKED)
        return True

    def accept_mismatch(self, peer_id: str, new_fingerprint: str) -> None:
        """Accept a fingerprint change (key rotation) and trust the new key."""
        self.store.update_peer(peer_id, new_fingerprint, TrustState.TRUSTED)

    def get_trust_state(self, peer_id: str) -> str:
        """Return current trust state string, or TrustState.NEW if unknown."""
        peer = self.store.get_peer(peer_id)
        if not peer:
            return TrustState.NEW
        return peer["trust_state"]
