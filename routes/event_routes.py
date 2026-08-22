"""Handle event pages and forms."""

from uuid import uuid4

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.event import Event
from routes.auth_routes import login_required, role_required
from services.category_service import flatten_categories
from services.weather_service import planning_data
from storage import append_log, load_json, save_json


event_bp = Blueprint("events", __name__)


def event_record(event_id):
    """Find one saved event."""
    return next((event for event in load_json("events.json", []) if event["id"] == event_id), None)


def event_status_label(status):
    """Make an event status easy to read."""
    match status:
        case "upcoming":
            return "Upcoming"
        case "ongoing":
            return "Ongoing"
        case "completed":
            return "Completed"
        case "cancelled":
            return "Cancelled"
        case _:
            return "Unknown"


def category_options():
    """Get all category choices."""
    tree = load_json("categories.json", {})
    return flatten_categories(tree)


@event_bp.get("/events")
def list_events():
    """Show events that match the filters."""
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip()
    price_type = request.args.get("price", "").strip()
    results = []

    for record in load_json("events.json", []):
        event = Event.from_dict(record)
        record["display_status"] = event_status_label(event.current_status())
        title_match = not query or query in record["title"].lower()
        category_match = not category or record["category"] == category
        price_match = not price_type
        if price_type == "free":
            price_match = float(record["price"]) == 0
        elif price_type == "paid":
            price_match = float(record["price"]) > 0
        if title_match and category_match and price_match:
            results.append(record)

    return render_template(
        "events.html",
        events=results,
        categories=category_options(),
        selected_category=category,
    )


@event_bp.route("/events/create", methods=["GET", "POST"])
@login_required
@role_required("organizer")
def create_event():
    """Create and save an event."""
    if request.method == "POST":
        try:
            category = request.form.get("custom_category", "").strip()
            if not category:
                category = request.form.get("category", "")
            event = Event(
                uuid4().hex,
                session["user_id"],
                request.form.get("title", ""),
                category,
                request.form.get("description", ""),
                request.form.get("date_time", ""),
                request.form.get("location", ""),
                request.form.get("capacity", 1),
                request.form.get("price", 0),
                reminder_hours=request.form.get("reminder_hours", 24),
            )
            if not event.title or not event.category or not event.date_time or not event.location:
                raise ValueError
        except (TypeError, ValueError):
            flash("Enter valid event details.", "error")
        else:
            records = load_json("events.json", [])
            records.append(event.to_dict())
            save_json("events.json", records)
            append_log(f"Created event: {event.title}")
            flash("Event created.", "success")
            return redirect(url_for("events.event_detail", event_id=event.event_id))

    return render_template("event_form.html", event=None, categories=category_options())


@event_bp.get("/events/<event_id>")
def event_detail(event_id):
    """Show an event with weather information."""
    record = event_record(event_id)
    if not record:
        flash("Event not found.", "error")
        return redirect(url_for("events.list_events"))

    registrations = load_json("registrations.json", [])
    registration_count = sum(1 for item in registrations if item["event_id"] == event_id)
    event = Event.from_dict(record)
    return render_template(
        "event_detail.html",
        event=record,
        display_status=event_status_label(event.current_status()),
        spaces=event.available_spaces(registration_count),
        weather=planning_data(record["location"]),
    )


@event_bp.route("/events/<event_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("organizer")
def edit_event(event_id):
    """Edit an event owned by the organizer."""
    records = load_json("events.json", [])
    record = next((event for event in records if event["id"] == event_id), None)
    if not record or record["organizer_id"] != session["user_id"]:
        flash("You cannot edit that event.", "error")
        return redirect(url_for("events.list_events"))

    if request.method == "POST":
        try:
            category = request.form.get("custom_category", "").strip()
            if not category:
                category = request.form.get("category", "")
            updated = Event(
                event_id,
                session["user_id"],
                request.form.get("title", ""),
                category,
                request.form.get("description", ""),
                request.form.get("date_time", ""),
                request.form.get("location", ""),
                request.form.get("capacity", 1),
                request.form.get("price", 0),
                request.form.get("status", "upcoming"),
                request.form.get("reminder_hours", 24),
            )
            if not updated.title or not updated.date_time or not updated.location:
                raise ValueError
        except (TypeError, ValueError):
            flash("Enter valid event details.", "error")
        else:
            records[records.index(record)] = updated.to_dict()
            save_json("events.json", records)
            append_log(f"Updated event: {updated.title}")
            flash("Event updated.", "success")
            return redirect(url_for("events.event_detail", event_id=event_id))

    return render_template("event_form.html", event=record, categories=category_options())


@event_bp.post("/events/<event_id>/delete")
@login_required
@role_required("organizer")
def delete_event(event_id):
    """Delete an event owned by the organizer."""
    records = load_json("events.json", [])
    record = next((event for event in records if event["id"] == event_id), None)
    if not record or record["organizer_id"] != session["user_id"]:
        flash("You cannot delete that event.", "error")
    else:
        save_json("events.json", [event for event in records if event["id"] != event_id])
        save_json(
            "registrations.json",
            [item for item in load_json("registrations.json", []) if item["event_id"] != event_id],
        )
        save_json(
            "notifications.json",
            [item for item in load_json("notifications.json", []) if item["event_id"] != event_id],
        )
        append_log(f"Deleted event: {record['title']}")
        flash("Event deleted.", "success")
    return redirect(url_for("events.list_events"))
