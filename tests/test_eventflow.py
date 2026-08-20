"""Test the simple EventFlow website."""

from datetime import datetime, timedelta

import app as app_file
import helpers
from models import Organizer, Participant


def setup_client(tmp_path, monkeypatch):
    """Create a test website with empty files."""
    monkeypatch.setattr(helpers, "DATA_FOLDER", tmp_path)
    monkeypatch.setattr(
        app_file,
        "get_weather",
        lambda location: {
            "place": "Accra",
            "country": "Ghana",
            "temperature": 28,
            "rain": 0,
            "condition": "Clear",
        },
    )
    app_file.app.config.update(TESTING=True, SECRET_KEY="test")
    return app_file.app.test_client()


def create_account(client, name, email, role):
    """Create a test account."""
    return client.post(
        "/register",
        data={"name": name, "email": email, "password": "secret12", "role": role},
        follow_redirects=True,
    )


def log_in(client, email):
    """Log in a test account."""
    return client.post(
        "/login",
        data={"email": email, "password": "secret12"},
        follow_redirects=True,
    )


def test_oop_and_recursion():
    """Test the user classes and recursive category function."""
    organizer = Organizer("1", "Ama", "ama@example.com")
    participant = Participant("2", "Kojo", "kojo@example.com")
    organizer.set_password("secret12")
    categories = ["Academic", "Technology", "Other"]

    assert organizer.check_password("secret12")
    assert organizer.role != participant.role
    assert organizer.welcome_message() != participant.welcome_message()
    assert helpers.copy_categories(categories) == categories
    assert helpers.weather_word(63) == "Rainy"


def test_full_event_journey(tmp_path, monkeypatch):
    """Test accounts, events, weather, tickets, reminders and check-in."""
    client = setup_client(tmp_path, monkeypatch)
    create_account(client, "Ama Organizer", "organizer@example.com", "organizer")
    create_account(client, "Kojo Participant", "participant@example.com", "participant")
    log_in(client, "organizer@example.com")

    event_time = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
    created = client.post(
        "/events/create",
        data={
            "title": "Robotics Workshop",
            "category": "Other",
            "custom_category": "Robotics",
            "date_time": event_time,
            "location": "Accra, Ghana",
            "capacity": "5",
            "price": "20",
            "reminder_hours": "3",
        },
        follow_redirects=True,
    )
    assert b"Robotics Workshop" in created.data
    assert b"Robotics" in created.data
    assert helpers.load_data("events.json")[0]["reminder_hours"] == 3
    assert b"28" in created.data

    event_id = helpers.load_data("events.json")[0]["id"]
    client.get("/logout")
    log_in(client, "participant@example.com")
    ticket_page = client.post(f"/events/{event_id}/register", follow_redirects=True)
    assert b"EVENTFLOW TICKET" in ticket_page.data

    dashboard = client.get("/dashboard")
    assert b"Reminder" in dashboard.data
    assert b"alert(" in dashboard.data
    registration = helpers.load_data("registrations.json")[0]

    client.get("/logout")
    log_in(client, "organizer@example.com")
    checked_in = client.post(
        f"/events/{event_id}/check-in",
        data={"ticket_code": registration["ticket_code"]},
        follow_redirects=True,
    )
    assert b"Participant checked in" in checked_in.data
    assert helpers.load_data("registrations.json")[0]["checked_in"] is True
