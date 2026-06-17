from security.rsa_utils import RSAUtils


def test_generate_key_pair():

    private_key, public_key = (
        RSAUtils.generate_key_pair()
    )

    assert private_key is not None
    assert public_key is not None
    
from security.rsa_utils import RSAUtils


def test_rsa_encrypt_decrypt_round_trip():

    private_key, public_key = (
        RSAUtils.generate_key_pair()
    )

    plaintext = b"hello"

    encrypted = RSAUtils.encrypt(
        public_key,
        plaintext
    )

    decrypted = RSAUtils.decrypt(
        private_key,
        encrypted
    )

    assert decrypted == plaintext
    
def test_public_key_serialization():

    _, public_key = (
        RSAUtils.generate_key_pair()
    )

    pem = RSAUtils.serialize_public_key(
        public_key
    )

    loaded = RSAUtils.load_public_key(
        pem
    )

    assert loaded is not None
    
def test_private_key_serialization():

    private_key, _ = (
        RSAUtils.generate_key_pair()
    )

    pem = RSAUtils.serialize_private_key(
        private_key
    )

    loaded = RSAUtils.load_private_key(
        pem
    )

    assert loaded is not None
    
