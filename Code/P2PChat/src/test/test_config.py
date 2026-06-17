"""Tests for config module."""

import logging

from config import (
    DEFAULT_HOST,
    DEFAULT_LISTEN_PORT,
    DISCOVERY_PORT,
    MAX_PACKET_SIZE,
    SOCKET_TIMEOUT,
    PRESENCE_INTERVAL,
    PEER_TIMEOUT,
    JWT_EXPIRE_HOURS,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    LOG_LEVEL,
    LOG_FORMAT,
    configure_logging
)


def test_network_constants():

    assert DEFAULT_HOST == "0.0.0.0"
    assert DEFAULT_LISTEN_PORT == 12000
    assert DISCOVERY_PORT == 15000
    assert SOCKET_TIMEOUT == 1
    assert MAX_PACKET_SIZE == 65536


def test_discovery_constants():

    assert PRESENCE_INTERVAL == 5
    assert PEER_TIMEOUT == 15


def test_security_constants():

    assert JWT_EXPIRE_HOURS == 12


def test_gui_constants():

    assert WINDOW_WIDTH == 1200
    assert WINDOW_HEIGHT == 800


def test_logging_constants():

    assert LOG_LEVEL == logging.INFO

    assert isinstance(
        LOG_FORMAT,
        str
    )

    assert "%(asctime)s" in LOG_FORMAT
    assert "%(levelname)s" in LOG_FORMAT
    assert "%(message)s" in LOG_FORMAT


def test_configure_logging():

    configure_logging()

    root_logger = logging.getLogger()

    assert root_logger is not None