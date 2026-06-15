"""JWT identity token for P2PChat."""

from datetime import datetime, timedelta

import jwt


class JWTHandler:
        
    @staticmethod
    def create_identity_token(
        peer_id: str,
        username: str,
        fingerprint: str,
        private_key_pem: str
    ) -> str:
        """
        Create signed identity token.
        Used by Discovery and Handshake.
        """
        payload = {
            "peer_id": peer_id,
            "username": username,
            "fingerprint": fingerprint,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=12)
        }

        return jwt.encode(
            payload,
            private_key_pem,
            algorithm="RS256"
        )


    @staticmethod
    def verify_identity_token(
        token: str,
        public_key_pem: str
    ) -> dict | None:
        """
        Verify signed identity token.
        """

        try:
            return jwt.decode(
                token,
                public_key_pem,
                algorithms=["RS256"]
            )

        except jwt.InvalidTokenError:
            return None