"""Fingerprint generation for P2PChat."""

import hashlib

def generate_fingerprint(public_key_pem: str | bytes) -> str:
    """
    Human readable fingerprint.
    Example:
    AA:BB:CC:DD:EE...
    """
    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode( "utf-8")
    digest = hashlib.sha256(public_key_pem).hexdigest().upper()
    return ":".join(
        digest[i:i + 2]
        for i in range(0,len(digest),2)
    )
