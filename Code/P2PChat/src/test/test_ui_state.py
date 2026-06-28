"""Tests for UIState — the GUI-side peer registry and selection state."""
from gui.ui_state import UIState


# ── Initial state ──────────────────────────────────────────────────────────

def test_default_state():
    state = UIState()
    assert state.discovered_peers    == {}
    assert state.active_peer_id      is None
    assert state.connection_status   == "offline"


# ── Peer registry ──────────────────────────────────────────────────────────

def test_update_discovered_peer():
    state = UIState()
    state.update_discovered_peer("peer1", {"username": "Tai"})
    assert state.discovered_peers["peer1"]["username"] == "Tai"


def test_update_discovered_peer_overwrites():
    state = UIState()
    state.update_discovered_peer("peer1", {"username": "Old"})
    state.update_discovered_peer("peer1", {"username": "New"})
    assert state.discovered_peers["peer1"]["username"] == "New"


def test_direct_dict_access():
    """app.py reads discovered_peers directly — verify dict is writable."""
    state = UIState()
    state.discovered_peers["peer1"] = {"connected": True}
    assert state.discovered_peers["peer1"]["connected"] is True


def test_dict_iteration():
    """app.py iterates discovered_peers.items() in several places."""
    state = UIState()
    state.update_discovered_peer("p1", {"username": "A"})
    state.update_discovered_peer("p2", {"username": "B"})
    names = [info["username"] for info in state.discovered_peers.values()]
    assert sorted(names) == ["A", "B"]


# ── Selection ──────────────────────────────────────────────────────────────

def test_select_peer():
    state = UIState()
    state.select_peer("peer1")
    assert state.active_peer_id == "peer1"


def test_select_peer_none():
    state = UIState()
    state.select_peer("peer1")
    state.select_peer(None)
    assert state.active_peer_id is None


# ── Connection status ──────────────────────────────────────────────────────

def test_set_connection_status():
    state = UIState()
    state.set_connection_status("connected")
    assert state.connection_status == "connected"


def test_set_connection_status_offline():
    state = UIState()
    state.set_connection_status("connected")
    state.set_connection_status("offline")
    assert state.connection_status == "offline"
