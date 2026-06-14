import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class CryptoHandler:
    """Handles Fernet symmetric encryption/decryption and RSA key operations."""
    
    def __init__(self, key: bytes | None = None) -> None:
        # Khởi tạo phần mã hóa đối xứng (Symmetric)
        self._fernet_key = key or Fernet.generate_key()
        self._fernet_instance = Fernet(self._fernet_key)

    def encrypt(self, data: str) -> str:
        """Encrypt *data* using Fernet and return the result as a base64-encoded string."""
        if not isinstance(data, str):
            raise ValueError("Data to encrypt must be a string.")
        return self._fernet_instance.encrypt(data.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_data: str, ttl: int | None = 300) -> str:
        """Decrypt *encrypted_data* using Fernet and return the original string.
        
        Raises:
            cryptography.fernet.InvalidToken: if decryption fails.
        """
        if not isinstance(encrypted_data, str):
            raise ValueError("Data to decrypt must be a string.")
        return self._fernet_instance.decrypt(encrypted_data.encode("utf-8"), ttl=ttl).decode("utf-8")

    def get_key(self) -> bytes:
        """Return the current Fernet encryption key."""
        return self._fernet_key

    @staticmethod
    def generate_rsa_keys():
        """Generate a new RSA private and public key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key

    # =========================================================================
    # BỔ SUNG: MÃ HÓA / GIẢI MÃ KHÓA BẰNG RSA (Cho tính năng Session Key Exchange)
    # =========================================================================
    @staticmethod
    def rsa_encrypt_key(plain_key: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        """Dùng Public Key của đối phương để mã hóa khóa Fernet trước khi gửi qua mạng."""
        return public_key.encrypt(
            plain_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def rsa_decrypt_key(encrypted_key: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        """Dùng Private Key của mình để giải mã khóa Fernet nhận được từ đối phương."""
        return private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    # =========================================================================
    # SERIALIZATION & DESERIALIZATION (Giữ nguyên logic chuẩn của bạn)
    # =========================================================================
    @staticmethod
    def serialize_public_key(public_key: rsa.RSAPublicKey) -> bytes:
        """Serialize an RSA public key to PEM format."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def deserialize_public_key(pem_bytes: bytes) -> rsa.RSAPublicKey:
        """Deserialize an RSA public key from PEM format."""
        return serialization.load_pem_public_key(pem_bytes)

    @staticmethod
    def serialize_private_key(private_key: rsa.RSAPrivateKey, password: Optional[str] = None) -> bytes:
        """Serialize an RSA private key to PEM format, optionally encrypted."""
        encryption_algorithm = serialization.NoEncryption()
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
                
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )

    @staticmethod
    def deserialize_private_key(pem_bytes: bytes, password: Optional[str] = None) -> rsa.RSAPrivateKey:
        """Deserialize an RSA private key from PEM format, optionally with a password."""
        return serialization.load_pem_private_key(
            pem_bytes,
            password=password.encode() if password else None
        )