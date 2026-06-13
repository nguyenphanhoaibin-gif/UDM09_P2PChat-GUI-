
from crypto import CryptoHandler
from rsa_utils import RSAUtils
from jwt_handler import JWTHandler
import time

def test_jwt_hs256():
    print("--- Testing HS256 ---")
    crypto = CryptoHandler()
    jwt_h = JWTHandler(crypto_handler=crypto, algorithm="HS256")
    
    payload = {"user_id": 123, "username": "manus_user"}
    
    # Test Normal Token
    token = jwt_h.create_access_token(payload)
    print(f"HS256 Token: {token[:20]}...")
    decoded = jwt_h.decode_jwt(token)
    print(f"Decoded Payload: {decoded}")
    assert decoded["user_id"] == 123

    # Test Encrypted Payload
    enc_token = jwt_h.create_access_token(payload, encrypt_payload=True)
    print(f"HS256 Encrypted Token: {enc_token[:20]}...")
    decoded_enc = jwt_h.decode_jwt(enc_token)
    print(f"Decoded Encrypted Payload: {decoded_enc}")
    assert decoded_enc["user_id"] == 123
    print("HS256 tests passed!\n")

def test_jwt_rs256():
    print("--- Testing RS256 ---")
    crypto = CryptoHandler()
    private_key, public_key = RSAUtils.generate_key_pair()
    jwt_h = JWTHandler(crypto_handler=crypto, rsa_private_key=private_key, rsa_public_key=public_key, algorithm="RS256")
    
    payload = {"user_id": 456, "username": "rsa_user"}
    
    token = jwt_h.create_access_token(payload)
    print(f"RS256 Token: {token[:20]}...")
    decoded = jwt_h.decode_jwt(token)
    print(f"Decoded Payload: {decoded}")
    assert decoded["user_id"] == 456
    print("RS256 tests passed!\n")

def test_refresh_token():
    print("--- Testing Refresh Token ---")
    crypto = CryptoHandler()
    jwt_h = JWTHandler(crypto_handler=crypto)
    
    payload = {"user_id": 789}
    refresh_token = jwt_h.create_refresh_token(payload)
    print(f"Refresh Token: {refresh_token[:20]}...")
    
    new_access_token = jwt_h.refresh_access_token(refresh_token, {"user_id": 789, "new": "data"})
    print(f"New Access Token: {new_access_token[:20]}...")
    
    decoded = jwt_h.decode_jwt(new_access_token)
    assert decoded["new"] == "data"
    print("Refresh token tests passed!\n")

if __name__ == "__main__":
    try:
        test_jwt_hs256()
        test_jwt_rs256()
        test_refresh_token()
        print("All integration tests passed successfully!")
    except Exception as e:
        print(f"Tests failed: {e}")
        import traceback
        traceback.print_exc()