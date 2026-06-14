"""Contact panel module for P2PChat."""

import customtkinter as ctk


class ContactCard(ctk.CTkFrame):
    """Visual representation of a contact.
    Data format: {
        "alias": str,
        "peer_id": str,
        "trust_state": str
    }"""
    TRUST_COLORS = {
        "NEW": "#f9e2af",
        "TRUSTED": "#89b4fa",
        "VERIFIED": "#a6e3a1",
        "MISMATCH": "#f38ba8",
        "BLOCKED": "#6c7086"
    }

    def __init__(
        self,
        master,
        contact: dict,
        on_select=None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=8,
            fg_color="#313145",
            **kwargs
        )

        self.contact = contact
        self.on_select = on_select

        self.grid_columnconfigure(0, weight=1)

        alias = contact.get(
            "alias",
            "Unknown"
        )

        peer_id = contact.get(
            "peer_id",
            ""
        )

        trust_state = contact.get(
            "trust_state",
            "NEW"
        )

        color = self.TRUST_COLORS.get(
            trust_state,
            "#a6adc8"
        )

        self.alias_label = ctk.CTkLabel(
            self,
            text=alias,
            anchor="w",
            font=("Arial", 13, "bold")
        )

        self.alias_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=8,
            pady=(6, 0)
        )

        self.peer_label = ctk.CTkLabel(
            self,
            text=peer_id[:16],
            anchor="w",
            text_color="#a6adc8",
            font=("Consolas", 10)
        )

        self.peer_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=8
        )

        self.state_label = ctk.CTkLabel(
            self,
            text=trust_state,
            text_color=color
        )

        self.state_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=8,
            pady=(0, 6)
        )

        self.bind(
            "<Button-1>",
            self._handle_click
        )

    def _handle_click(self, _event):

        if self.on_select:
            self.on_select(self.contact)


class ContactPanel(ctk.CTkFrame):
    """Panel to display list of contacts."""
    def __init__(
        self,
        master,
        on_contact_select=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color="#181825",
            **kwargs
        )

        self.on_contact_select = (
            on_contact_select
        )

        self.contacts = []

        self.title = ctk.CTkLabel(
            self,
            text="📒 Contacts",
            font=("Consolas", 14, "bold")
        )

        self.title.pack(
            anchor="w",
            padx=10,
            pady=(10, 5)
        )

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.scroll.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

    def load_contacts(
        self,
        contacts: list
    ):
        """Load and display contacts in the panel."""
        self.contacts = contacts

        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not contacts:

            empty = ctk.CTkLabel(
                self.scroll,
                text="No contacts"
            )

            empty.pack(
                pady=20
            )

            return

        for contact in contacts:

            card = ContactCard(
                self.scroll,
                contact,
                on_select=self.on_contact_select
            )

            card.pack(
                fill="x",
                padx=4,
                pady=4
            )
