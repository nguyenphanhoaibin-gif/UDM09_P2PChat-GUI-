"""Peer ID generation — SHA-256 hash of the public key PEM."""

import hashlib


def generate_peer_id(public_key_pem: str | bytes) -> str:
    """Generate a stable, collision-resistant peer ID from *public_key_pem*.
    The peer ID is the lower-hex SHA-256 digest of the PEM bytes.  Using the
    full PEM (including headers) ensures uniqueness across different key sizes
    and encoding variants.
    Args:
        public_key_pem: PEM-encoded RSA public key, as str or bytes.
    Returns:
        64-character lowercase hex string (SHA-256 digest).
    """
    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode("utf-8")
    return hashlib.sha256(public_key_pem).hexdigest()
