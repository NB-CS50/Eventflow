"""Keep the classes used by EventFlow."""

from abc import ABC, abstractmethod
from datetime import datetime
from secrets import token_urlsafe

from werkzeug.security import check_password_hash, generate_password_hash


class User(ABC):
    """Keep details shared by every user."""

    role = "user"

    def __init__(self, user_id, name, email, password_hash=""):
        """Create a user."""
        self.user_id = user_id
        self.name = name
        self.email = email.lower()
        self.__password_hash = password_hash

    def set_password(self, password):
        """Save a safe version of the password."""
        self.__password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the password is correct."""
        return check_password_hash(self.__password_hash, password)

    @abstractmethod
    def welcome_message(self):
        """Give the correct dashboard message."""
        raise NotImplementedError

    def to_dict(self):
        """Turn the user into saved data."""
        return {
            "id": self.user_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.__password_hash,
            "role": self.role,
        }


class Organizer(User):
    """Represent a user who creates events."""

    role = "organizer"

    def welcome_message(self):
        """Give the organizer message."""
        return "Create events and manage participants."


class Participant(User):
    """Represent a user who joins events."""

    role = "participant"

    def welcome_message(self):
        """Give the participant message."""
        return "Browse events and view your tickets."


def user_from_dict(data):
    """Create the correct user type from saved data."""
    user_class = Organizer if data["role"] == "organizer" else Participant
    return user_class(data["id"], data["name"], data["email"], data["password_hash"])


class Event:
    """Keep the details of one event."""

    def __init__(
        self,
        event_id,
        organizer_id,
        title,
        category,
        date_time,
        location,
        capacity,
        price,
        reminder_hours=24,
    ):
        """Create an event."""
        self.event_id = event_id
        self.organizer_id = organizer_id
        self.title = title
        self.category = category
        self.date_time = date_time
        self.location = location
        self.capacity = max(1, int(capacity))
        self.price = max(0, float(price))
        self.reminder_hours = max(1, int(reminder_hours))

    def is_full(self, number_registered):
        """Check if the event is full."""
        return number_registered >= self.capacity

    def is_upcoming(self):
        """Check if the event has not started."""
        return datetime.fromisoformat(self.date_time) > datetime.now()

    def to_dict(self):
        """Turn the event into saved data."""
        return {
            "id": self.event_id,
            "organizer_id": self.organizer_id,
            "title": self.title,
            "category": self.category,
            "date_time": self.date_time,
            "location": self.location,
            "capacity": self.capacity,
            "price": self.price,
            "reminder_hours": self.reminder_hours,
        }


def event_from_dict(data):
    """Create an event from saved data."""
    return Event(
        data["id"],
        data["organizer_id"],
        data["title"],
        data["category"],
        data["date_time"],
        data["location"],
        data["capacity"],
        data["price"],
        data.get("reminder_hours", 24),
    )


class Ticket:
    """Create a secure ticket code."""

    def __init__(self, code=None):
        """Create a ticket."""
        self.code = code or f"TKT-{token_urlsafe(8)}"


class Registration:
    """Connect a participant, event and ticket."""

    def __init__(
        self,
        registration_id,
        event_id,
        participant_id,
        participant_name,
        price,
        ticket_code=None,
        checked_in=False,
    ):
        """Create a registration."""
        self.registration_id = registration_id
        self.event_id = event_id
        self.participant_id = participant_id
        self.participant_name = participant_name
        self.price = float(price)
        self.ticket = Ticket(ticket_code)
        self.checked_in = checked_in

    def ticket_type(self):
        """Show if the ticket is free or paid."""
        return "Free" if self.price == 0 else "Paid"

    def to_dict(self):
        """Turn the registration into saved data."""
        return {
            "id": self.registration_id,
            "event_id": self.event_id,
            "participant_id": self.participant_id,
            "participant_name": self.participant_name,
            "price": self.price,
            "ticket_code": self.ticket.code,
            "ticket_type": self.ticket_type(),
            "checked_in": self.checked_in,
        }
