from gui.ui_state import UIState


def test_default_state():

    state = UIState()

    assert state.discovered_peers == {}
    assert state.connected_peers == {}
    assert state.contacts == {}

    assert state.active_peer_id is None
    assert state.active_contact_id is None

    assert state.connection_status == "offline"
    assert state.encryption_status == "disabled"
    assert state.last_status_message == ""


def test_update_discovered_peer():

    state = UIState()

    state.update_discovered_peer(
        "peer1",
        {
            "username": "Tai"
        }
    )

    assert (
        state.discovered_peers["peer1"]["username"]
        ==
        "Tai"
    )


def test_remove_discovered_peer():

    state = UIState()

    state.update_discovered_peer(
        "peer1",
        {}
    )

    state.remove_discovered_peer(
        "peer1"
    )

    assert "peer1" not in state.discovered_peers


def test_remove_missing_discovered_peer():

    state = UIState()

    state.remove_discovered_peer(
        "unknown"
    )

    assert True


def test_set_connected_peer():

    state = UIState()

    state.set_connected_peer(
        "peer1",
        {
            "status": "online"
        }
    )

    assert (
        state.connected_peers["peer1"]["status"]
        ==
        "online"
    )


def test_remove_connected_peer():

    state = UIState()

    state.set_connected_peer(
        "peer1",
        {}
    )

    state.remove_connected_peer(
        "peer1"
    )

    assert "peer1" not in state.connected_peers


def test_add_contact():

    state = UIState()

    state.add_contact(
        "peer1",
        {
            "alias": "Tai"
        }
    )

    assert (
        state.contacts["peer1"]["alias"]
        ==
        "Tai"
    )


def test_remove_contact():

    state = UIState()

    state.add_contact(
        "peer1",
        {}
    )

    state.remove_contact(
        "peer1"
    )

    assert "peer1" not in state.contacts


def test_select_peer():

    state = UIState()

    state.select_peer(
        "peer1"
    )

    assert state.active_peer_id == "peer1"


def test_select_contact():

    state = UIState()

    state.select_contact(
        "contact1"
    )

    assert state.active_contact_id == "contact1"


def test_set_connection_status():

    state = UIState()

    state.set_connection_status(
        "online"
    )

    assert state.connection_status == "online"


def test_set_encryption_status():

    state = UIState()

    state.set_encryption_status(
        "enabled"
    )

    assert state.encryption_status == "enabled"


def test_set_status_message():

    state = UIState()

    state.set_status_message(
        "connected"
    )

    assert (
        state.last_status_message
        ==
        "connected"
    )


def test_get_selected_peer_none():

    state = UIState()

    assert (
        state.get_selected_peer()
        is None
    )


def test_get_selected_peer():

    state = UIState()

    state.update_discovered_peer(
        "peer1",
        {
            "username": "Tai"
        }
    )

    state.select_peer(
        "peer1"
    )

    peer = state.get_selected_peer()

    assert peer["username"] == "Tai" # type: ignore[arg-type]


def test_peer_count():

    state = UIState()

    state.update_discovered_peer(
        "peer1",
        {}
    )

    state.update_discovered_peer(
        "peer2",
        {}
    )

    assert state.peer_count == 2


def test_connected_count():

    state = UIState()

    state.set_connected_peer(
        "peer1",
        {}
    )

    state.set_connected_peer(
        "peer2",
        {}
    )

    assert state.connected_count == 2


def test_contact_count():

    state = UIState()

    state.add_contact(
        "peer1",
        {}
    )

    state.add_contact(
        "peer2",
        {}
    )

    assert state.contact_count == 2
    
