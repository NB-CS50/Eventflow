"""Create the registration class."""

from datetime import datetime

from models.ticket import Ticket


class Registration:
    """Connect a participant to an event and ticket."""

    def __init__(
        self,
        registration_id,
        event_id,
        participant_id,
        price,
        payment_status,
        ticket_code=None,
        checked_in=False,
        checked_in_at=None,
        created_at=None,
    ):
        """Set up a registration."""
        self.registration_id = registration_id
        self.event_id = event_id
        self.participant_id = participant_id
        self.price = float(price)
        self.payment_status = payment_status
        self.ticket = Ticket(ticket_code, checked_in, checked_in_at)
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")

    @property
    def ticket_type(self):
        """Show if the ticket is free or paid."""
        return "Free" if self.price == 0 else "Paid"

    def to_dict(self):
        """Turn the registration into data that can be saved."""
        return {
            "id": self.registration_id,
            "event_id": self.event_id,
            "participant_id": self.participant_id,
            "price": self.price,
            "payment_status": self.payment_status,
            "ticket_code": self.ticket.code,
            "ticket_type": self.ticket_type,
            "checked_in": self.ticket.checked_in,
            "checked_in_at": self.ticket.checked_in_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a registration from saved data."""
        return cls(
            data["id"],
            data["event_id"],
            data["participant_id"],
            data.get("price", 0),
            data.get("payment_status", "Free"),
            data.get("ticket_code"),
            data.get("checked_in", False),
            data.get("checked_in_at"),
            data.get("created_at"),
        )
