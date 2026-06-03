import json
import socket
import threading
from typing import Callable, Optional

DISCOVERY_PORT = 15000

DISCOVERY = "discovery"
DISCOVERY_RESPONSE = "discovery_response"

class DiscoveryService:

    def __init__(
        self,
        username: str,
        listen_port: int
    ):

        self.username = username
        self.listen_port = listen_port

        self.running = False

        self.socket: Optional[socket.socket] = None

        self.listener_thread: Optional[
            threading.Thread
        ] = None

        self.on_peer_found: Optional[
            Callable[[dict, tuple[str, int]], None]
        ] = None

    def start(self):

        if self.running:
            return

        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.socket.settimeout(1.0)

        self.socket.bind(
            ("", DISCOVERY_PORT)
        )

        self.running = True

        self.listener_thread = threading.Thread(
            target=self.listen_loop,
            daemon=True
        )

        self.listener_thread.start()

    def listen_loop(self):

        if self.socket is None:
            return

        while self.running:

            try:

                data, address = self.socket.recvfrom(4096)

                packet = json.loads(
                    data.decode("utf-8")
                )

                self.handle_packet(
                    packet,
                    address
                )

            except socket.timeout:
                continue

            except (
                json.JSONDecodeError,
                UnicodeDecodeError
            ):
                continue

            except OSError:

                if not self.running:
                    break

                continue

    def handle_packet(self, packet: dict, address: tuple[str, int]):

        packet_type = packet.get("type")

        if packet_type == DISCOVERY:
            self.send_response(address)

        elif packet_type == DISCOVERY_RESPONSE:

            if self.on_peer_found is not None:
                self.on_peer_found(packet, address)

    def send_response(self, address: tuple[str, int]):

        if self.socket is None:
            return

        response = {
            "type": DISCOVERY_RESPONSE,
            "username": self.username,
            "port": self.listen_port
        }

        try:

            self.socket.sendto(
                json.dumps(response).encode("utf-8"),
                address
            )

        except OSError:
            pass

    def discover(self):

        sender = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        try:

            sender.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_BROADCAST,
                1
            )

            packet = {
                "type": DISCOVERY,
                "username": self.username,
                "port": self.listen_port
            }

            sender.sendto(
                json.dumps(packet).encode("utf-8"),
                (
                    "255.255.255.255",
                    DISCOVERY_PORT
                )
            )

        finally:
            sender.close()

    def stop(self):

        self.running = False
        sock = self.socket
        self.socket = None

        if sock is not None:

            try:
                sock.close()

            except OSError:
                pass

        if (
            self.listener_thread is not None
            and self.listener_thread.is_alive()
        ):
            self.listener_thread.join(timeout=1)