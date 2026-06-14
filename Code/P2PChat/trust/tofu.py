from enum import Enum
from pathlib import Path
from typing import Optional

from trust.trust_store import TrustStore

class TrustResult(Enum):
    NEW                  = "new"
    TRUSTED_UNVERIFIED   = "trusted_unverified"
    VERIFIED             = "verified"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    BLOCKED              = "blocked"

class TOFUEngine:
    def __init__(self, data_dir: Path):
        self.trust_store = TrustStore(data_dir)

    def check(self, peer_id: str, current_fingerprint: str) -> TrustResult:
        peer_info = self.trust_store.get_peer_info(peer_id)

        # 1. TRƯỜNG HỢP PEER CHƯA TỒN TẠI (Lần đầu gặp peer)
        if peer_info is None:
            # Lưu fingerprint và ĐÁNH DẤU LÀ TRUSTED_UNVERIFIED vào Database luôn
            self.trust_store.update_peer_info(peer_id, current_fingerprint, TrustResult.TRUSTED_UNVERIFIED)
            # Trả về NEW để thông báo cho hệ thống biết đây là kết nối đầu tiên thành công
            return TrustResult.NEW
        
        # 2. TRƯỜNG HỢP PEER ĐÃ TỒN TẠI TRONG DB
        stored_fingerprint = peer_info["fingerprint"]
        stored_status = TrustResult(peer_info["status"])

        # Nếu bị chặn từ trước thì từ chối luôn
        if stored_status == TrustResult.BLOCKED:
            return TrustResult.BLOCKED

        # Nếu fingerprint khác với lần đầu lưu trữ -> CẢNH BÁO NGUY HIỂM!
        if stored_fingerprint != current_fingerprint:
            return TrustResult.FINGERPRINT_MISMATCH
        
        # Nếu fingerprint trùng khớp -> Cập nhật thời gian last_seen và giữ nguyên trạng thái cũ
        self.trust_store.update_peer_info(peer_id, current_fingerprint, stored_status)

        return stored_status

    def trust(self, peer_id: str) -> None:
        """
        Hàm này có thể giữ lại để kích hoạt thủ công từ các trạng thái khác nếu cần,
        hoặc dùng để 'Bỏ qua cảnh báo' (Overwrite) fingerprint cũ nếu bạn muốn thiết kế thêm.
        """
        peer_info = self.trust_store.get_peer_info(peer_id)
        if peer_info:
            self.trust_store.set_peer_status(peer_id, TrustResult.TRUSTED_UNVERIFIED)

    def verify(self, peer_id: str) -> None:
        # Chuyển trạng thái từ TRUSTED_UNVERIFIED lên VERIFIED (Xác thực thủ công nâng cao)
        peer_info = self.trust_store.get_peer_info(peer_id)
        if peer_info:
            self.trust_store.set_peer_status(peer_id, TrustResult.VERIFIED)

    def block(self, peer_id: str) -> None:
        # Đưa vào danh sách đen
        peer_info = self.trust_store.get_peer_info(peer_id)
        if peer_info:
            self.trust_store.set_peer_status(peer_id, TrustResult.BLOCKED)