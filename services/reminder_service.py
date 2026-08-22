"""Create reminders for events that are close."""

from datetime import datetime, timedelta

from storage import load_json, save_json


def check_upcoming_events(app, user_id=None):
    """Create reminders for events happening soon."""
    with app.app_context():
        events = {event["id"]: event for event in load_json("events.json", [])}
        notifications = load_json("notifications.json", [])
        existing = {(item["user_id"], item["event_id"]) for item in notifications}
        now = datetime.now()
        new_count = 0

        for registration in load_json("registrations.json", []):
            event = events.get(registration["event_id"])
            key = (registration["participant_id"], registration["event_id"])
            if user_id and registration["participant_id"] != user_id:
                continue
            if not event or event.get("status") == "cancelled" or key in existing:
                continue
            event_time = datetime.fromisoformat(event["date_time"])
            limit = now + timedelta(hours=event.get("reminder_hours", app.config["REMINDER_HOURS"]))
            if now <= event_time <= limit:
                notifications.append(
                    {
                        "id": f"{registration['participant_id']}-{registration['event_id']}",
                        "user_id": registration["participant_id"],
                        "event_id": registration["event_id"],
                        "message": f"Reminder: {event['title']} starts at {event['date_time']}.",
                        "sent_at": now.isoformat(timespec="seconds"),
                        "read": False,
                    }
                )
                existing.add(key)
                new_count += 1

        save_json("notifications.json", notifications)
        return new_count
