import json
import uuid
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import rsa
from security.crypto import CryptoHandler

# Đường dẫn mặc định trỏ thẳng vào ~/.p2pchat/ theo yêu cầu
DEFAULT_DATA_DIR = Path.home() / ".p2pchat"

class PeerID:
    def __init__(self, id: str, public_key: rsa.RSAPublicKey, private_key: rsa.RSAPrivateKey):
        self.id = id                  # UUID dạng chuỗi cố định
        self.public_key = public_key    # RSA public key (được persist)
        self.private_key = private_key  # RSA private key (được persist, encrypted)

    @classmethod
    def load_or_create(cls, data_dir: Path = DEFAULT_DATA_DIR, password: Optional[str] = None) -> "PeerID":
        """Hàm load_or_create bổ sung: Tự động kiểm tra file để load hoặc tạo mới."""
        identity_file = data_dir / "identity.json"
        if identity_file.exists():
            with open(identity_file, "r") as f:
                data = json.load(f)
            
            peer_id = data["id"]
            public_key_pem = data["public_key"].encode('utf-8')
            private_key_pem = data["private_key"].encode('utf-8')
            
            public_key = CryptoHandler.deserialize_public_key(public_key_pem)
            private_key = CryptoHandler.deserialize_private_key(private_key_pem, password)
            
            return cls(peer_id, public_key, private_key)
        else:
            peer_id = str(uuid.uuid4())
            private_key, public_key = CryptoHandler.generate_rsa_keys()
            new_peer_id = cls(peer_id, public_key, private_key)
            new_peer_id.save(data_dir, password)
            return new_peer_id

    @classmethod
    def generate(cls, data_dir: Path = DEFAULT_DATA_DIR, password: Optional[str] = None) -> "PeerID":
        """Tạo UUID cố định và cặp khóa RSA, sau đó lưu (persist) vào thư mục chỉ định."""
        peer_id = str(uuid.uuid4())
        private_key, public_key = CryptoHandler.generate_rsa_keys()
        
        new_peer = cls(peer_id, public_key, private_key)
        new_peer.save(data_dir, password)
        return new_peer

    @classmethod
    def load(cls, data_dir: Path = DEFAULT_DATA_DIR, password: Optional[str] = None) -> "PeerID":
        """Load danh tính từ file identity.json, TỰ ĐỘNG TẠO MỚI (generate) nếu chưa có."""
        identity_file = data_dir / "identity.json"
        
        # Nếu file CHƯA tồn tại -> Tiến hành tạo mới danh tính bằng cách gọi hàm load_or_create
        if not identity_file.exists():
            return cls.load_or_create(data_dir, password)
            
        # Nếu file ĐA tồn tại -> Đọc dữ liệu lên để tái cấu trúc lại object PeerID
        with open(identity_file, "r") as f:
            data = json.load(f)
        
        peer_id = data["id"]
        public_key_pem = data["public_key"].encode('utf-8')
        private_key_pem = data["private_key"].encode('utf-8')

        public_key = CryptoHandler.deserialize_public_key(public_key_pem)
        private_key = CryptoHandler.deserialize_private_key(private_key_pem, password)
        
        return cls(peer_id, public_key, private_key)

    def save(self, data_dir: Path = DEFAULT_DATA_DIR, password: Optional[str] = None) -> None:
        """Lưu trữ thông tin định danh (UUID và cặp khóa RSA) xuống đĩa cứng dưới dạng file JSON."""
        data_dir.mkdir(parents=True, exist_ok=True)
        identity_file = data_dir / "identity.json"

        public_key_pem = CryptoHandler.serialize_public_key(self.public_key).decode('utf-8')
        private_key_pem = CryptoHandler.serialize_private_key(self.private_key, password).decode('utf-8')

        data = {
            "id": self.id,
            "public_key": public_key_pem,
            "private_key": private_key_pem,
        }

        with open(identity_file, "w") as f:
            json.dump(data, f, indent=4)
            
        # Giới hạn quyền truy cập file identity.json (Chỉ chủ sở hữu máy mới được đọc/ghi)
        try:
            identity_file.chmod(0o600)  # Hoạt động tốt trên Unix/Linux/MacOS
        except OSError:
            pass  # Bỏ qua nếu chạy trên môi trường Windows không hỗ trợ chmod dạng này