"""Create the event class."""

from datetime import datetime, timedelta


class Event:
    """Store the details of one event."""

    def __init__(
        self,
        event_id,
        organizer_id,
        title,
        category,
        description,
        date_time,
        location,
        capacity,
        price,
        status="upcoming",
        reminder_hours=24,
    ):
        """Set up an event."""
        self.event_id = event_id
        self.organizer_id = organizer_id
        self.title = title.strip()
        self.category = category.strip()
        self.description = description.strip()
        self.date_time = date_time
        datetime.fromisoformat(self.date_time)
        self.location = location.strip()
        self.__capacity = max(1, int(capacity))
        self.price = max(0.0, float(price))
        self.status = status
        self.reminder_hours = max(1, int(reminder_hours))

    @property
    def capacity(self):
        """Get the event capacity."""
        return self.__capacity

    @capacity.setter
    def capacity(self, new_capacity):
        """Change the event capacity."""
        self.__capacity = max(1, int(new_capacity))

    def available_spaces(self, registration_count):
        """Count the spaces that are left."""
        return max(0, self.capacity - registration_count)

    def is_full(self, registration_count):
        """Check if the event is full."""
        return registration_count >= self.capacity

    def current_status(self):
        """Work out the event status."""
        if self.status in {"cancelled", "completed", "ongoing"}:
            return self.status
        event_time = datetime.fromisoformat(self.date_time)
        now = datetime.now()
        if event_time <= now <= event_time + timedelta(hours=2):
            return "ongoing"
        return "completed" if now > event_time else "upcoming"

    def to_dict(self):
        """Turn the event into data that can be saved."""
        return {
            "id": self.event_id,
            "organizer_id": self.organizer_id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "date_time": self.date_time,
            "location": self.location,
            "capacity": self.capacity,
            "price": self.price,
            "status": self.status,
            "reminder_hours": self.reminder_hours,
        }

    @classmethod
    def from_dict(cls, data):
        """Create an event from saved data."""
        return cls(
            data["id"],
            data["organizer_id"],
            data["title"],
            data["category"],
            data["description"],
            data["date_time"],
            data["location"],
            data["capacity"],
            data["price"],
            data.get("status", "upcoming"),
            data.get("reminder_hours", 24),
        )
