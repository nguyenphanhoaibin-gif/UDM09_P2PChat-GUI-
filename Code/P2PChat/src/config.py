"""Application configuration."""

import logging

# =========================
# Network
# =========================

DEFAULT_HOST = "0.0.0.0"

DEFAULT_LISTEN_PORT = 12000
DISCOVERY_PORT = 15000

MAX_PACKET_SIZE = 65536
SOCKET_TIMEOUT = 1

# =========================
# Discovery 
# =========================

PRESENCE_INTERVAL = 5
PEER_TIMEOUT = 15

# =========================
# Security
# =========================

JWT_EXPIRE_HOURS = 12

# =========================
# GUI
# =========================

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# =========================
# Logging
# =========================

LOG_FORMAT = (
    "%(asctime)s "
    "%(levelname)s "
    "%(name)s: "
    "%(message)s"
)

LOG_LEVEL = logging.INFO


def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )