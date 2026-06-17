from __future__ import annotations

import customtkinter as ctk

class ContactPanel(ctk.CTkFrame):

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

        self._on_contact_select = (
            on_contact_select
        )

        self.contacts = []

        self.title = ctk.CTkLabel(
            self,
            text="⭐ Contacts",
            font=("Arial", 14, "bold")
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

    # ==================================
    # Public API
    # ==================================

    def load_contacts(
        self,
        contacts
    ):

        self.contacts = contacts

        self.refresh()

    def refresh(self):

        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not self.contacts:

            empty = ctk.CTkLabel(
                self.scroll,
                text="No contacts",
                text_color="#6c7086"
            )

            empty.pack(
                pady=10
            )

            return

        for contact in self.contacts:

            name = contact.get(
                "username",
                "Unknown"
            )

            btn = ctk.CTkButton(
                self.scroll,
                text=f"⭐ {name}",
                anchor="w",
                fg_color="#313244",
                hover_color="#45475a",
                command=lambda c=contact:
                    self._select(c)
            )

            btn.pack(
                fill="x",
                padx=4,
                pady=2
            )

    # ==================================
    # Internal
    # ==================================

    def _select(
        self,
        contact
    ):

        if self._on_contact_select:

            self._on_contact_select(
                contact
            )