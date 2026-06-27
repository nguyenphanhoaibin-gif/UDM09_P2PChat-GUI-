"""ContactPanel: scrollable list of saved contacts."""
from __future__ import annotations

import customtkinter as ctk


class ContactPanel(ctk.CTkFrame):
    """Scrollable panel showing saved contacts with click-to-select."""

    def __init__(
        self,
        master,
        on_contact_select=None,
        **kwargs,
    ) -> None:
        """Create the contact panel.
        Args:
            master: Parent widget.
            on_contact_select: Callback (contact_dict) on selection.
        """
        super().__init__(master, fg_color="#1a1b2e", **kwargs)

        self._on_contact_select = on_contact_select
        self.contacts: list[dict] = []

        ctk.CTkLabel(
            self, text="CONTACTS",
            font=("Arial", 10, "bold"),
            text_color="#64748b", anchor="w",
        ).pack(anchor="w", padx=14, pady=(14, 6))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=6, pady=4)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def load_contacts(self, contacts: list[dict]) -> None:
        """Populate the panel with *contacts*.
        Args:
            contacts: List of contact info dicts.
        """
        self.contacts = contacts
        self.refresh()

    def refresh(self) -> None:
        """Rebuild the list from the current self.contacts."""
        for w in self._scroll.winfo_children():
            w.destroy()

        if not self.contacts:
            ctk.CTkLabel(
                self._scroll,
                text="No contacts saved",
                text_color="#475569",
                font=("Arial", 11),
            ).pack(pady=20)
            return

        for contact in self.contacts:
            name = contact.get("alias") or contact.get("username", "Unknown")
            btn = ctk.CTkButton(
                self._scroll,
                text=f"⭐  {name}",
                anchor="w",
                fg_color="#1e2035",
                hover_color="#252637",
                text_color="#e2e8f0",
                font=("Arial", 12),
                corner_radius=8,
                command=lambda c=contact: self._select(c),
            )
            btn.pack(fill="x", padx=4, pady=3)

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _select(self, contact: dict) -> None:
        if self._on_contact_select:
            self._on_contact_select(contact)
