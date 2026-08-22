"""Test the full EventFlow website."""

import csv
from datetime import datetime, timedelta

from app import create_app
from services.category_service import flatten_categories
from services.reminder_service import check_upcoming_events
from services.weather_service import geocode_location, get_weather, weather_label


def make_app(tmp_path):
    """Create an isolated test application."""
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test",
            "DATA_DIR": tmp_path / "data",
            "EXPORT_DIR": tmp_path / "exports",
            "REMINDER_HOURS": 24,
        }
    )


def register(client, name, email, role):
    """Register a test user."""
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


def login(client, email):
    """Log in a test user."""
    return client.post(
        "/login",
        data={"email": email, "password": "secret12"},
        follow_redirects=True,
    )


def logout(client):
    """Log out the current test user."""
    return client.get("/logout", follow_redirects=True)


def test_recursion():
    """Confirm nested event categories are flattened recursively."""
    tree = {"Academic": {"Workshop": {}, "Conference": {"Research": {}}}}
    assert flatten_categories(tree) == [
        "Academic",
        "Academic > Workshop",
        "Academic > Conference",
        "Academic > Conference > Research",
    ]


def test_weather_api(monkeypatch):
    """Check the location and weather API code."""

    class FakeResponse:
        """Act like a small API response."""

        def __init__(self, data):
            """Save the fake response data."""
            self.data = data

        def raise_for_status(self):
            """Act like a successful request."""
            return None

        def json(self):
            """Return the fake JSON data."""
            return self.data

    def fake_get(url, params, timeout):
        """Return fake data for each API address."""
        if "geocoding" in url:
            return FakeResponse(
                {
                    "results": [
                        {
                            "name": "Accra",
                            "country": "Ghana",
                            "latitude": 5.56,
                            "longitude": -0.2,
                        }
                    ]
                }
            )
        return FakeResponse(
            {"current": {"temperature_2m": 28, "precipitation": 0, "weather_code": 0}}
        )

    monkeypatch.setattr("services.weather_service.requests.get", fake_get)
    location = geocode_location("Accra")
    weather = get_weather(location["latitude"], location["longitude"])
    assert location["name"] == "Accra"
    assert weather == {"temperature": 28, "precipitation": 0, "condition": "Clear"}
    assert weather_label(63) == "Rainy"


def test_home_page(tmp_path, monkeypatch):
    """Check the full scrolling home page."""
    monkeypatch.setattr(
        "app.major_city_weather",
        lambda: [{"name": "Accra", "temperature": 28, "condition": "Clear"}],
    )
    client = make_app(tmp_path).test_client()
    page = client.get("/")
    assert page.status_code == 200
    assert page.data.count(b'class="home-page') == 5
    assert b"Your events. Your plans. One simple place." in page.data
    assert b"Weather around Ghana" in page.data
    assert b"For participants" in page.data
    assert b"For organizers" in page.data


def test_complete_event_journey(tmp_path, monkeypatch):
    """Test accounts, events, tickets, reminders, sales, export and check-in."""
    app = make_app(tmp_path)
    client = app.test_client()
    monkeypatch.setattr(
        "routes.event_routes.planning_data",
        lambda location: {
            "name": location,
            "temperature": 28,
            "condition": "Clear",
            "precipitation": 0,
        },
    )

    register(client, "Ama Organizer", "organizer@example.com", "organizer")
    register(client, "Kojo Participant", "participant@example.com", "participant")
    organizer_login = login(client, "organizer@example.com")
    assert b"Organizer dashboard" in organizer_login.data

    event_time = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
    created = client.post(
        "/events/create",
        data={
            "title": "Engineering Workshop",
            "category": "Technology > Engineering",
            "description": "A practical workshop.",
            "date_time": event_time,
            "location": "Accra",
            "capacity": "2",
            "price": "25",
            "reminder_hours": "6",
        },
        follow_redirects=False,
    )
    assert created.status_code == 302
    event_url = created.headers["Location"]
    event_id = event_url.rstrip("/").split("/")[-1]
    detail = client.get(event_url)
    assert b"Engineering Workshop" in detail.data
    assert b"28" in detail.data

    logout(client)
    participant_login = login(client, "participant@example.com")
    assert b"Participant dashboard" in participant_login.data
    registered = client.post(f"/events/{event_id}/register", follow_redirects=True)
    assert b"Digital ticket" in registered.data
    assert b"new event reminder" in registered.data

    with app.app_context():
        from storage import load_json

        registrations = load_json("registrations.json", [])
        assert len(registrations) == 1
        registration = registrations[0]
        assert registration["ticket_type"] == "Paid"
        assert len(registration["ticket_code"]) >= 12

    duplicate = client.post(f"/events/{event_id}/register", follow_redirects=True)
    assert b"already registered" in duplicate.data

    check_upcoming_events(app)
    reminders = client.get("/notifications")
    assert b"Engineering Workshop" in reminders.data

    logout(client)
    login(client, "organizer@example.com")
    report = client.get(f"/events/{event_id}/sales")
    assert b"GHS 25.00" in report.data

    exported = client.get(f"/events/{event_id}/attendees.csv")
    assert exported.status_code == 200
    rows = list(csv.DictReader(exported.data.decode("utf-8").splitlines()))
    assert rows[0]["email"] == "participant@example.com"

    checked_in = client.post(
        f"/events/{event_id}/attendance",
        data={"ticket_code": registration["ticket_code"]},
        follow_redirects=True,
    )
    assert b"Ticket checked in" in checked_in.data

    repeated = client.post(
        f"/events/{event_id}/attendance",
        data={"ticket_code": registration["ticket_code"]},
        follow_redirects=True,
    )
    assert b"already been checked in" in repeated.data
