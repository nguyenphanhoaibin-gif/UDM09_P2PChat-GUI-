from models.contact import Contact
from models.history_record import HistoryRecord
from models.peer_info import PeerInfo
from models.transfer_meta import TransferMeta


def test_contact_model():

    contact = Contact(
        peer_id="peer1",
        alias="Tai",
        trust_state="TRUSTED",
        fingerprint="ABC123"
    )

    assert contact.peer_id == "peer1"
    assert contact.alias == "Tai"
    assert contact.trust_state == "TRUSTED"
    assert contact.fingerprint == "ABC123"


def test_history_record_model():

    record = HistoryRecord(
        message_id="msg1",
        peer_id="peer1",
        direction="OUTGOING",
        content="Hello",
        timestamp=123.45
    )

    assert record.message_id == "msg1"
    assert record.peer_id == "peer1"
    assert record.direction == "OUTGOING"
    assert record.content == "Hello"
    assert record.timestamp == 123.45


def test_peer_info_model():

    peer = PeerInfo(
        peer_id="peer1",
        username="Tai",
        fingerprint="FP123",
        ip="127.0.0.1",
        tcp_port=5000,
        status="online",
        last_seen=100.0
    )

    assert peer.peer_id == "peer1"
    assert peer.username == "Tai"
    assert peer.fingerprint == "FP123"
    assert peer.ip == "127.0.0.1"
    assert peer.tcp_port == 5000
    assert peer.status == "online"
    assert peer.last_seen == 100.0


def test_transfer_meta_model():

    transfer = TransferMeta(
        transfer_id="file1",
        filename="test.txt",
        filesize=1024,
        sender_id="peer1",
        receiver_id="peer2",
        status="PENDING"
    )

    assert transfer.transfer_id == "file1"
    assert transfer.filename == "test.txt"
    assert transfer.filesize == 1024
    assert transfer.sender_id == "peer1"
    assert transfer.receiver_id == "peer2"
    assert transfer.status == "PENDING"