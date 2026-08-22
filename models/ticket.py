"""Create secure ticket codes."""

from datetime import datetime
from secrets import token_urlsafe


class Ticket:
    """Represent one secure digital ticket."""

    def __init__(self, code=None, checked_in=False, checked_in_at=None):
        """Set up a ticket."""
        self.code = code or token_urlsafe(9)
        self.checked_in = checked_in
        self.checked_in_at = checked_in_at

    def is_valid(self):
        """Check if the ticket can be used."""
        return not self.checked_in

    def mark_used(self):
        """Mark the ticket as used once."""
        if not self.is_valid():
            return False
        self.checked_in = True
        self.checked_in_at = datetime.now().isoformat(timespec="seconds")
        return True
