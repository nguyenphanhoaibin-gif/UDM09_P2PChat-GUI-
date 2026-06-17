import customtkinter as ctk

from gui.statusbar import StatusBar


def create_statusbar():

    root = ctk.CTk()
    root.withdraw()

    bar = StatusBar(root)

    return root, bar


def test_default_labels():

    root, bar = create_statusbar()

    assert (
        bar.status_label.cget("text")
        ==
        "🔄 Initializing..."
    )

    assert (
        bar.stats_label.cget("text")
        ==
        "Peers: 0"
    )

    root.destroy()


def test_set_status():

    root, bar = create_statusbar()

    bar.set_status(
        "Online",
        "#ffffff"
    )

    assert (
        bar.status_label.cget("text")
        ==
        "Online"
    )

    root.destroy()


def test_set_stats():

    root, bar = create_statusbar()

    bar.set_stats(
        peers=5,
        contacts=2,
        connected=1
    )

    assert (
        bar.stats_label.cget("text")
        ==
        "Peers:5  Contacts:2  Connected:1"
    )

    root.destroy()


def test_set_initializing():

    root, bar = create_statusbar()

    bar.set_initializing()

    assert (
        bar.status_label.cget("text")
        ==
        "🔄 Initializing..."
    )

    root.destroy()


def test_set_discovery_running():

    root, bar = create_statusbar()

    bar.set_discovery_running()

    assert (
        bar.status_label.cget("text")
        ==
        "🔍 Discovering peers..."
    )

    root.destroy()


def test_set_connected():

    root, bar = create_statusbar()

    bar.set_connected(
        "Tai"
    )

    assert (
        bar.status_label.cget("text")
        ==
        "🔗 Connected: Tai"
    )

    root.destroy()


def test_set_handshake():

    root, bar = create_statusbar()

    bar.set_handshake()

    assert (
        bar.status_label.cget("text")
        ==
        "🤝 Performing handshake..."
    )

    root.destroy()


def test_set_encrypted():

    root, bar = create_statusbar()

    bar.set_encrypted()

    assert (
        bar.status_label.cget("text")
        ==
        "🔐 Encrypted session active"
    )

    root.destroy()


def test_set_disconnected():

    root, bar = create_statusbar()

    bar.set_disconnected()

    assert (
        bar.status_label.cget("text")
        ==
        "❌ Disconnected"
    )

    root.destroy()


def test_set_error():

    root, bar = create_statusbar()

    bar.set_error(
        "Socket failed"
    )

    assert (
        bar.status_label.cget("text")
        ==
        "⚠ Socket failed"
    )

    root.destroy()