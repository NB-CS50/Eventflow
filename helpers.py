"""Keep the small helper functions used by EventFlow."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import requests


DATA_FOLDER = Path(__file__).resolve().parent / "data"


def load_data(filename):
    """Read a JSON file."""
    path = DATA_FOLDER / filename
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_data(filename, data):
    """Save data in a JSON file."""
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    with (DATA_FOLDER / filename).open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def copy_categories(categories, index=0):
    """Copy the categories using recursion."""
    if index == len(categories):
        return []
    return [categories[index]] + copy_categories(categories, index + 1)


def weather_word(code):
    """Turn a weather code into a simple word."""
    match code:
        case 0:
            return "Clear"
        case 1 | 2 | 3:
            return "Cloudy"
        case 45 | 48:
            return "Foggy"
        case 51 | 53 | 55 | 61 | 63 | 65 | 80 | 81 | 82:
            return "Rainy"
        case 95 | 96 | 99:
            return "Stormy"
        case _:
            return "Unknown"


def get_weather(location):
    """Get live weather for a city."""
    city = location.split(",")[0].strip()
    try:
        place_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        )
        place_response.raise_for_status()
        places = place_response.json().get("results", [])
        if not places:
            return {"error": "Location not found. Use a city such as Accra."}

        place = places[0]
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,precipitation,weather_code",
            },
            timeout=10,
        )
        weather_response.raise_for_status()
        current = weather_response.json().get("current", {})
        return {
            "place": place.get("name", city),
            "country": place.get("country", ""),
            "temperature": current.get("temperature_2m"),
            "rain": current.get("precipitation"),
            "condition": weather_word(current.get("weather_code")),
        }
    except requests.RequestException:
        return {"error": "Weather could not load. Check your internet."}


def make_reminders(participant_id):
    """Create reminders for the participant's upcoming events."""
    events = {}
    saved_events = load_data("events.json")
    for event in saved_events:
        events[event["id"]] = event
    registrations = load_data("registrations.json")
    reminders = []
    now = datetime.now()

    for registration in registrations:
        if registration["participant_id"] != participant_id:
            continue
        event = events.get(registration["event_id"])
        if not event:
            continue
        event_time = datetime.fromisoformat(event["date_time"])
        reminder_hours = event.get("reminder_hours", 24)
        if now <= event_time <= now + timedelta(hours=reminder_hours):
            reminders.append(
                {
                    "participant_id": participant_id,
                    "event_id": event["id"],
                    "message": f"Reminder: {event['title']} starts at {event['date_time'].replace('T', ' ')}.",
                }
            )
    return reminders
