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
    monkeypatch.setattr(
        app_file,
        "get_city_weather",
        lambda: [
            {"city": "Accra", "temperature": 28, "condition": "Clear"},
            {"city": "Kumasi", "temperature": 27, "condition": "Cloudy"},
            {"city": "Tamale", "temperature": 31, "condition": "Clear"},
            {"city": "Cape Coast", "temperature": 27, "condition": "Rainy"},
            {"city": "Takoradi", "temperature": 27, "condition": "Cloudy"},
        ],
    )
    app_file.app.config.update(TESTING=True, SECRET_KEY="test")
    return app_file.app.test_client()


def create_account(client, name, email, role):
    """Create a test account."""
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": "secret12",
            "confirm_password": "secret12",
            "role": role,
        },
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
    home = client.get("/")
    assert b"Your events. Your plans. One simple place." in home.data
    assert b"Plan before you go" in home.data
    assert b"Participants and organizers" in home.data
    assert b"How to use EventFlow" in home.data
    assert b"Takoradi" in home.data
    wrong_password = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "secret12",
            "confirm_password": "different",
            "role": "participant",
        },
        follow_redirects=True,
    )
    assert b"Passwords do not match" in wrong_password.data
    create_account(client, "Ama Organizer", "organizer@example.com", "organizer")
    create_account(client, "Kojo Participant", "participant@example.com", "participant")
    log_in(client, "organizer@example.com")

    organizer_dashboard = client.get("/dashboard")
    assert b"Your events" in organizer_dashboard.data
    assert b"Your tickets" not in organizer_dashboard.data

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

    blocked_registration = client.post(
        f"/events/{helpers.load_data('events.json')[0]['id']}/register",
        follow_redirects=True,
    )
    assert b"Only participants can register for events" in blocked_registration.data

    event_id = helpers.load_data("events.json")[0]["id"]
    client.get("/logout")
    log_in(client, "participant@example.com")
    ticket_page = client.post(f"/events/{event_id}/register", follow_redirects=True)
    assert b"EVENTFLOW TICKET" in ticket_page.data

    dashboard = client.get("/dashboard")
    assert b"Reminder" in dashboard.data
    assert b"alert(" in dashboard.data
    assert b"Your tickets" in dashboard.data
    assert b"Your events" not in dashboard.data

    blocked_event = client.post(
        "/events/create",
        data={
            "title": "Study Session",
            "category": "Academic",
            "date_time": event_time,
            "location": "Accra, Ghana",
            "capacity": "10",
            "price": "0",
            "reminder_hours": "3",
        },
        follow_redirects=True,
    )
    assert b"Only organizers can create events" in blocked_event.data
    assert len(helpers.load_data("events.json")) == 1

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
