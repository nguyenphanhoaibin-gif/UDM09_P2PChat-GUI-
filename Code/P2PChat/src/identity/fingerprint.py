import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
from security.crypto import CryptoHandler

class Fingerprint:
    def __init__(self, fingerprint_hex: str):
        self._fingerprint_hex = fingerprint_hex.lower()

    @classmethod
    def from_public_key(cls, public_key: rsa.RSAPublicKey) -> "Fingerprint":
        public_key_pem = CryptoHandler.serialize_public_key(public_key)
        sha256_hash = hashlib.sha256(public_key_pem).hexdigest()
        formatted_fingerprint = ":".join([sha256_hash[i:i+2] for i in range(0, len(sha256_hash), 2)])
        return cls(formatted_fingerprint)

    def short(self) -> str:
        return self._fingerprint_hex.replace(":", "")[:8]

    def __str__(self) -> str:
        return self._fingerprint_hex

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fingerprint):
            return NotImplemented
        return self._fingerprint_hex == other._fingerprint_hex

    def __hash__(self) -> int:
        return hash(self._fingerprint_hex)