import datetime
import json
import struct
import uuid
from typing import Any, Optional
from cryptography.fernet import InvalidToken
from security.crypto import CryptoHandler

class PacketType:
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    SESSION_KEY = "session_key" # Sprint 3: RSA-wrapped Fernet key exchange
    MESSAGE = "message"
    SYSTEM = "system"
    ERROR = "error"
    FILE_OFFER   = "file_offer"    # metadata: name, size, checksum
    FILE_ACCEPT  = "file_accept"
    FILE_REJECT  = "file_reject"
    FILE_CHUNK   = "file_chunk"    # index, total_chunks, data (base64)
    FILE_DONE    = "file_done"     # checksum verify
    FILE_CANCEL  = "file_cancel"

# Thêm "sender" vào tất cả các gói tin liên quan đến trao đổi giữa các peer
_HANDSHAKE_REQUIRED: frozenset[str] = frozenset({
    "type", "username", "version","listen_port", "public_key",
})

_HANDSHAKE_ACK_REQUIRED: frozenset[str] = frozenset({
    "type", "status", "public_key",
})

_MESSAGE_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "payload", "timestamp", "message_id",
})

_SESSION_KEY_REQUIRED: frozenset[str] = frozenset({
    "type", "payload",
})

_MESSAGE_STRING_FIELDS: frozenset[str] = frozenset({
    "type", "sender", "message_id", "timestamp",
})

_FILE_OFFER_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "name", "size", "checksum", "message_id", "timestamp"
})

_FILE_ACCEPT_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "message_id", "timestamp"
})

_FILE_REJECT_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "message_id", "reason", "timestamp"
})

_FILE_CHUNK_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "message_id", "index", "total_chunks", "data", "timestamp"
})

_FILE_DONE_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "message_id", "checksum", "timestamp"
})

_FILE_CANCEL_REQUIRED: frozenset[str] = frozenset({
    "type", "sender", "message_id", "timestamp"
})


class ProtocolHandler:
    """Central packet creation, framing, validation, and socket I/O."""

    HEADER_SIZE = 4  
    MAX_PACKET_SIZE = 1024 * 1024  # 1 MB max packet size to prevent abuse

    def __init__(self) -> None:
        pass

    def create_packet(self, msg_type: str, sender: str, crypto: Optional[CryptoHandler] = None, **kwargs) -> dict[str, Any]:
        """Build and return a complete packet dict supporting both chat and file transfer operations."""
        
        packet = {
            "type": msg_type,
            "sender": sender,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        packet["message_id"] = kwargs.pop("message_id", str(uuid.uuid4()))
        packet.update(kwargs)

        if crypto is not None:
            if "payload" in packet and isinstance(packet["payload"], str):
                packet["payload"] = crypto.encrypt(packet["payload"])
            elif "data" in packet and isinstance(packet["data"], str):
                packet["data"] = crypto.encrypt(packet["data"])

        return packet

    def serialize(self, packet: dict[str, Any]) -> bytes:
        """Serialize *packet* into a 4-byte length-prefixed byte stream."""
        json_data = json.dumps(packet).encode('utf-8')
        return struct.pack("!I", len(json_data)) + json_data
    
    def validate_packet(self, packet: dict[str, Any]) -> bool:
        """Return True only if *packet* carries all required fields with correct types."""
        if not isinstance(packet, dict):
            print("[WARNING] validate_packet: not a dict")
            return False
        
        packet_type = packet.get("type")

        if packet_type == PacketType.HANDSHAKE:
            required = _HANDSHAKE_REQUIRED

        elif packet_type == PacketType.HANDSHAKE_ACK:
            required = _HANDSHAKE_ACK_REQUIRED
        
        elif packet_type == PacketType.MESSAGE:
            required = _MESSAGE_REQUIRED
            for field in _MESSAGE_STRING_FIELDS:
                if not isinstance(packet.get(field), str):
                    print(f"[WARNING] validate_packet: '{field}' must be a string")
                    return False
        
        elif packet_type == PacketType.SESSION_KEY:
            required = _SESSION_KEY_REQUIRED
            if not isinstance(packet.get("payload"), str):
                print("[WARNING] validate_packet: 'payload' must be a string")
                return False
        
        elif packet_type == PacketType.FILE_OFFER:
            required = _FILE_OFFER_REQUIRED
            if not isinstance(packet.get("name"), str):
                print("[WARNING] validate_packet: 'name' must be a string")
                return False
            if not isinstance(packet.get("size"), int) or packet.get("size") < 0:
                print("[WARNING] validate_packet: 'size' must be a non-negative integer")
                return False
            if not isinstance(packet.get("checksum"), str):
                print("[WARNING] validate_packet: 'checksum' must be a string")
                return False

        elif packet_type == PacketType.FILE_ACCEPT:
            required = _FILE_ACCEPT_REQUIRED

        elif packet_type == PacketType.FILE_REJECT:
            required = _FILE_REJECT_REQUIRED
            if not isinstance(packet.get("reason"), str):
                print("[WARNING] validate_packet: 'reason' must be a string")
                return False

        elif packet_type == PacketType.FILE_CHUNK:
            required = _FILE_CHUNK_REQUIRED
            if not isinstance(packet.get("index"), int) or packet.get("index") < 0:
                print("[WARNING] validate_packet: 'index' must be a non-negative integer")
                return False
            if not isinstance(packet.get("total_chunks"), int) or packet.get("total_chunks") <= 0:
                print("[WARNING] validate_packet: 'total_chunks' must be a positive integer")
                return False
            if not isinstance(packet.get("data"), str):
                print("[WARNING] validate_packet: 'data' must be a string")
                return False

        elif packet_type == PacketType.FILE_DONE:
            required = _FILE_DONE_REQUIRED
            if not isinstance(packet.get("checksum"), str):
                print("[WARNING] validate_packet: 'checksum' must be a string")
                return False

        elif packet_type == PacketType.FILE_CANCEL:
            required = _FILE_CANCEL_REQUIRED

        else:
            print(f"[WARNING] validate_packet: unknown type '{packet_type}'")
            return False

        # Kiểm tra chung cho tất cả các gói tin: message_id và sender (nếu nằm trong required) phải là string
        if "message_id" in packet and not isinstance(packet.get("message_id"), str):
            print("[WARNING] validate_packet: 'message_id' must be a string")
            return False
        if "sender" in packet and not isinstance(packet.get("sender"), str):
            print("[WARNING] validate_packet: 'sender' must be a string")
            return False

        for field in required:
            if field not in packet:
                print(f"[WARNING] validate_packet: missing field '{field}'")
                return False

        return True
    
    def decrypt_payload(self, packet: dict[str, Any], crypto: Optional[CryptoHandler] = None) -> str:
        """Decrypt packet payload or file chunk data. Raises InvalidToken if decryption fails."""
        # Xác định trường chứa dữ liệu cần giải mã (ưu tiên 'payload', sau đó tới 'data' của file_chunk)
        target_field = "payload" if "payload" in packet else "data"
        
        if target_field not in packet:
            return ""

        if crypto is not None:
            return crypto.decrypt(packet[target_field])
        
        return packet[target_field]
    
    def validate_and_decrypt(self, packet: dict[str, Any], crypto: Optional[CryptoHandler] = None) -> Optional[str]:
        """Convenience: validate then decrypt. Returns None on any failure."""
        if not self.validate_packet(packet):
            return None
        try:
            decrypted_message = self.decrypt_payload(packet, crypto)
            return decrypted_message
        except (InvalidToken, ValueError) as exc:
            print(f"[WARNING] Decryption failed: {exc}")
            return None

    def receive_exact(self, peer_socket: Any, size: int) -> bytes:
        """Read exactly *size* bytes from *peer_socket*. Returns b"" when closed."""
        received_data = bytearray()
        while len(received_data) < size:
            data = peer_socket.recv(size - len(received_data))
            if not data:
                return b""
            received_data.extend(data)
        return bytes(received_data)
    
    def receive_packet(self, peer_socket: Any) -> Optional[dict[str, Any]]:
        """Read one framed packet from *peer_socket*."""
        try:
            header = self.receive_exact(peer_socket, self.HEADER_SIZE)
            if not header:
                return None

            (packet_length,) = struct.unpack("!I", header)

            if packet_length > self.MAX_PACKET_SIZE:
                print(f"[WARNING] Oversized packet ({packet_length} bytes) — dropping")
                return None

            packet_data = self.receive_exact(peer_socket, packet_length)
            if not packet_data:
                return None
            
            packet = json.loads(packet_data.decode("utf-8"))
            return packet

        except OSError as error:
            print(f"[ERROR] Socket receive failed: {error}")
            return None
        except (json.JSONDecodeError, UnicodeDecodeError, struct.error) as error:
            print(f"[WARNING] receive_packet: malformed data — {error}")
            return None