"""Peer ID generation utilities."""

import hashlib


def generate_peer_id(public_key_pem) -> str:
    """Generate stable peer id."""
    
    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode("utf-8")
        
    return hashlib.sha256(public_key_pem).hexdigest()
