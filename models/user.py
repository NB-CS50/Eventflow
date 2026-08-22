"""Create the user classes."""

from abc import ABC, abstractmethod

from werkzeug.security import check_password_hash, generate_password_hash


class User(ABC):
    """Store details shared by every user."""

    def __init__(self, user_id, name, email, password_hash):
        """Set up a user."""
        self.user_id = user_id
        self.name = name.strip()
        self.email = email.strip().lower()
        self.__password_hash = password_hash

    def set_password(self, password):
        """Save a password safely."""
        self.__password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if a password is correct."""
        return check_password_hash(self.__password_hash, password)

    @property
    @abstractmethod
    def role(self):
        """Return the user role."""
        raise NotImplementedError

    @abstractmethod
    def dashboard_template(self):
        """Choose the dashboard for this user type."""
        raise NotImplementedError

    def to_dict(self):
        """Turn the user into data that can be saved."""
        return {
            "id": self.user_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.__password_hash,
            "role": self.role,
        }


class Organizer(User):
    """Represent a person who creates events."""

    @property
    def role(self):
        """Return the organizer role."""
        return "organizer"

    def dashboard_template(self):
        """Return the organizer dashboard template."""
        return "organizer_dashboard.html"


class Participant(User):
    """Represent a person who joins events."""

    @property
    def role(self):
        """Return the participant role."""
        return "participant"

    def dashboard_template(self):
        """Return the participant dashboard template."""
        return "participant_dashboard.html"


def user_from_dict(data):
    """Create the right user type from saved data."""
    user_class = Organizer if data["role"] == "organizer" else Participant
    return user_class(data["id"], data["name"], data["email"], data["password_hash"])
