"""Trust state constants for TOFU model."""


class TrustState:
    """Enumeration of peer trust states.

    State machine:
        NEW       — first discovery, not yet in store
        TRUSTED   — manually trusted by the user
        VERIFIED  — fingerprint confirmed on repeated contact
        MISMATCH  — fingerprint changed since last contact (possible MITM)
        BLOCKED   — explicitly blocked; all traffic rejected
    """

    NEW      = "NEW"
    TRUSTED  = "TRUSTED"
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    BLOCKED  = "BLOCKED"

    _ALL: frozenset[str] = frozenset({NEW, TRUSTED, VERIFIED, MISMATCH, BLOCKED})

    @classmethod
    def is_valid(cls, state: str) -> bool:
        """Return True if *state* is a known trust state string."""
        return state in cls._ALL
