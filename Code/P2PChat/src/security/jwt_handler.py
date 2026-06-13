import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from crypto import CryptoHandler
from rsa_utils import RSAUtils

class JWTHandler:
    """Handles JWT creation, encoding, decoding, and optional payload encryption."""

    def __init__(self, 
                 crypto_handler: CryptoHandler, 
                 rsa_private_key = None, 
                 rsa_public_key = None, 
                 algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7) -> None:
        
        self.crypto_handler = crypto_handler
        self.rsa_private_key = rsa_private_key
        self.rsa_public_key = rsa_public_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

        if self.algorithm.startswith("RS") and (rsa_private_key is None or rsa_public_key is None):
            raise ValueError("RSA private and public keys are required for RS-algorithms.")
        elif self.algorithm.startswith("HS") and not isinstance(self.crypto_handler.get_key(), bytes):
            raise ValueError("CryptoHandler key must be bytes for HS-algorithms.")

    def create_access_token(self, data: Dict[str, Any], encrypt_payload: bool = False) -> str:
        """Creates an access token with an optional encrypted payload."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        if encrypt_payload:
            import json
            # Convert datetime to ISO string for JSON serialization
            json_payload = json.dumps(to_encode, default=str)
            encrypted_data = self.crypto_handler.encrypt(json_payload)
            return self._encode_jwt({"encrypted_payload": encrypted_data})
        
        return self._encode_jwt(to_encode)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Creates a refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return self._encode_jwt(to_encode)

    def _encode_jwt(self, payload: Dict[str, Any]) -> str:
        """Internal method to encode the JWT based on the configured algorithm."""
        if self.algorithm.startswith("HS"):
            return jwt.encode(payload, self.crypto_handler.get_key(), algorithm=self.algorithm)
        elif self.algorithm.startswith("RS"):
            return jwt.encode(payload, self.rsa_private_key, algorithm=self.algorithm)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def decode_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Decodes and verifies the JWT, decrypting the payload if necessary."""
        try:
            if self.algorithm.startswith("HS"):
                decoded_payload = jwt.decode(token, self.crypto_handler.get_key(), algorithms=[self.algorithm])
            elif self.algorithm.startswith("RS"):
                decoded_payload = jwt.decode(token, self.rsa_public_key, algorithms=[self.algorithm])
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")

            if "encrypted_payload" in decoded_payload:
                decrypted_str = self.crypto_handler.decrypt(decoded_payload["encrypted_payload"])
                import json
                return json.loads(decrypted_str)
            
            return decoded_payload
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None
        except Exception as e:
            print(f"An error occurred during token decoding: {e}")
            return None

    def refresh_access_token(self, refresh_token: str, data: Dict[str, Any], encrypt_payload: bool = False) -> Optional[str]:
        """Refreshes an access token using a valid refresh token."""
        decoded_refresh_token = self.decode_jwt(refresh_token)
        if decoded_refresh_token and decoded_refresh_token.get("type") == "refresh":
            # You might want to add more checks here, e.g., against a database of valid refresh tokens
            return self.create_access_token(data, encrypt_payload)
        return None