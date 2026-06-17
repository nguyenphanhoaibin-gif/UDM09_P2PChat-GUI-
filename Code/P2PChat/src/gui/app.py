from __future__ import annotations

import socket
import customtkinter as ctk

from controllers.controller import ChatController
from gui.main_window import MainWindow
from gui.ui_state import UIState


class ChatApp(ctk.CTk):

    def __init__(
        self,
        listen_port: int
    ):
        super().__init__()

        self.listen_port = listen_port

        self.title("P2P Chat")
        self.geometry("1200x800")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ==================================================
        # STATE
        # ==================================================

        self.ui_state = UIState()

        self.selected_peer_id: str | None = None

        # ==================================================
        # CONTROLLER
        # ==================================================

        self.controller = ChatController(
            on_system=self._on_system,
            on_message=self._on_message,
            on_connected=self._on_connected,
            on_disconnect=self._on_disconnect,
            on_peers_update=self._on_peers_update,
            on_peer_discovered=self._on_peer_discovered
        )

        # ==================================================
        # GUI
        # ==================================================

        self.main_window = MainWindow(
            self,
            on_peer_select=self._handle_peer_selected,
            on_peer_connect=self._handle_peer_connect,
            on_contact_select=self._handle_contact_selected
        )

        self.main_window.set_send_callback(
            self._handle_send_message
        )

        # ==================================================
        # START NODE
        # ==================================================

        username = socket.gethostname()

        success, message = self.controller.start_node(
            host="0.0.0.0",
            port=self.listen_port,
            username=username
        )

        self.main_window.set_status(message)

        if success:
            self.controller.discover_peers()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._on_close
        )

    # ==================================================
    # CONTROLLER CALLBACKS
    # ==================================================

    def _on_system(
        self,
        message: str
    ):
        self.after(
            0,
            lambda: self.main_window.add_system_message(
                message
            )
        )

    def _on_message(
        self,
        sender: str,
        payload: str
    ):
        self.after(
            0,
            lambda: self.main_window.add_received_message(
                sender,
                payload
            )
        )

    def _on_connected(
        self,
        peer_id: str
    ):
        self.ui_state.set_connection_status(
            "connected"
        )

        self.after(
            0,
            lambda: self.main_window.set_status(
                f"Connected: {peer_id}",
                "#a6e3a1"
            )
        )

    def _on_disconnect(
        self,
        peer_id: str
    ):
        self.ui_state.set_connection_status(
            "offline"
        )

        self.after(
            0,
            lambda: self.main_window.set_status(
                f"Disconnected: {peer_id}",
                "#f38ba8"
            )
        )

    def _on_peers_update(self):
        pass

    def _on_peer_discovered(
        self,
        peer_id: str,
        info: dict
    ):

        self.ui_state.update_discovered_peer(
            peer_id,
            info
        )

        def update():

            self.main_window.update_discovered_peers(
                self.ui_state.discovered_peers
            )

            self.main_window.set_status(
                f"Discovered: {info.get('username', peer_id)}"
            )

        self.after(
            0,
            update
        )

    # ==================================================
    # GUI CALLBACKS
    # ==================================================

    def _handle_peer_selected(
        self,
        peer_id: str,
        peer_info: dict
    ):

        self.selected_peer_id = peer_id

        self.ui_state.select_peer(
            peer_id
        )

        self.main_window.update_peer_details(
            peer_info
        )
        
        self.main_window.set_active_chat(
            username=peer_info.get(
                "username",
                peer_id
            ),
            status=peer_info.get(
                "status",
                "offline"
            ),
            trust_state=peer_info.get(
                "trust_state",
                "NEW"
            )
        )

    def _handle_peer_connect(
        self,
        peer_id: str,
        peer_info: dict
    ):

        ip = peer_info.get("ip")
        port = peer_info.get("port")

        if ip is None or port is None:
            return

        ok = self.controller.connect_to_peer(
            ip,
            int(port)
        )

        if not ok:

            self.main_window.set_status(
                "Connection failed",
                "#f38ba8"
            )

    def _handle_contact_selected(
        self,
        contact: dict
    ):
        pass

    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def _handle_send_message(self):

        if self.selected_peer_id is None:
            return

        message = (
            self.main_window.get_message_text()
            .strip()
        )

        if not message:
            return

        success = self.controller.send_message(
            message,
            self.selected_peer_id
        )

        if success:

            self.main_window.add_sent_message(
                "Me",
                self.selected_peer_id,
                message
            )

            self.main_window.clear_message_text()

    # ==================================================
    # CLOSE
    # ==================================================

    def _on_close(self):

        try:
            self.controller.stop()

        finally:
            self.destroy()