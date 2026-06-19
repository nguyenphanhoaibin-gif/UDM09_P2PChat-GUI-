import pytest
import customtkinter as ctk

from gui.statusbar import StatusBar


@pytest.fixture
def root():
    root = ctk.CTk()
    root.withdraw()

    yield root

    try:
        root.destroy()
    except Exception:
        pass


def create_statusbar(root):
    return StatusBar(root)


def test_default_labels(root):

    bar = create_statusbar(root)

    assert (
        bar._status_label.cget("text")
        ==
        "🔄 Initializing..."
    )

    assert (
        bar._stats_label.cget("text")
        ==
        "Peers: 0"
    )


def test_set_status(root):

    bar = create_statusbar(root)

    bar.set_status(
        "Online",
        "#ffffff"
    )

    assert (
        bar._status_label.cget("text")
        ==
        "Online"
    )


def test_set_stats(root):

    bar = create_statusbar(root)

    bar.set_stats(
        peers=5,
        connected=1,
        contacts=2,
    )

    assert (
        bar._stats_label.cget("text")
        ==
        "Peers:5 | Connected:1 | Contacts:2  "
    )