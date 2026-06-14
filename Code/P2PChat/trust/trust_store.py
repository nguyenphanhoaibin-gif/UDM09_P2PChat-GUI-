
import json
import threading
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

class TrustResult(Enum):
    NEW                  = "new"
    TRUSTED_UNVERIFIED   = "trusted_unverified"
    VERIFIED             = "verified"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    BLOCKED              = "blocked"

class TrustStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.trust_file = self.data_dir / "trust.json"
        self._lock = threading.RLock() # Use RLock for re-entrant locking
        self._trust_data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        with self._lock:
            if self.trust_file.exists():
                try:
                    with open(self.trust_file, "r") as f:
                        self._trust_data = json.load(f)
                except json.JSONDecodeError:
                    # Handle corrupted JSON file by starting with an empty store
                    self._trust_data = {}
            else:
                self._trust_data = {}

    def _save(self) -> None:
        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.trust_file, "w") as f:
                json.dump(self._trust_data, f, indent=4)

    def get_peer_info(self, peer_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._trust_data.get(peer_id)

    def update_peer_info(self, peer_id: str, fingerprint: str, status: TrustResult) -> None:
        with self._lock:
            now = datetime.now().isoformat()
            peer_info = self._trust_data.get(peer_id)
            if peer_info:
                peer_info["fingerprint"] = fingerprint
                peer_info["status"] = status.value
                peer_info["last_seen"] = now
            else:
                self._trust_data[peer_id] = {
                    "fingerprint": fingerprint,
                    "status": status.value,
                    "first_seen": now,
                    "last_seen": now,
                }
            self._save()

    def set_peer_status(self, peer_id: str, status: TrustResult) -> None:
        with self._lock:
            peer_info = self._trust_data.get(peer_id)
            if peer_info:
                peer_info["status"] = status.value
                peer_info["last_seen"] = datetime.now().isoformat()
                self._save()

    def get_all_peers(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return self._trust_data.copy()