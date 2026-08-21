"""Run the simple EventFlow website."""

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for

from helpers import copy_categories, get_city_weather, get_weather, load_data, make_reminders, save_data
from models import Event, Organizer, Participant, Registration, event_from_dict, user_from_dict


BASE_FOLDER = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_FOLDER / "templates"),
    static_folder=str(BASE_FOLDER / "static"),
)
app.secret_key = os.environ.get("EVENTFLOW_SECRET_KEY", "eventflow-student-project")


CATEGORIES = [
    "Academic",
    "Technology",
    "Business",
    "Arts",
    "Sports",
    "Music",
    "Community",
    "Food",
    "Health",
    "Networking",
    "Other",
]


def get_current_user():
    """Get the logged-in user."""
    user_id = session.get("user_id")
    users = load_data("users.json")
    for record in users:
        if record["id"] == user_id:
            return user_from_dict(record)
    return None


def find_event(event_id):
    """Find one event."""
    events = load_data("events.json")
    for record in events:
        if record["id"] == event_id:
            return event_from_dict(record)
    return None


@app.get("/")
def home():
    """Show the home page."""
    return render_template(
        "home.html",
        categories=CATEGORIES[:8],
        city_weather=get_city_weather(),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Create a user account."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "")
        users = load_data("users.json")

        email_exists = False
        for saved_user in users:
            if saved_user["email"] == email:
                email_exists = True

        if not name or not email or not password or not confirm_password:
            flash("Complete every field.", "error")
        elif len(password) < 6:
            flash("Password must have at least 6 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif role not in {"organizer", "participant"}:
            flash("Choose a valid role.", "error")
        elif email_exists:
            flash("That email is already registered.", "error")
        else:
            user = Organizer(uuid4().hex, name, email) if role == "organizer" else Participant(uuid4().hex, name, email)
            user.set_password(password)
            users.append(user.to_dict())
            save_data("users.json", users)
            flash("Account created. You can log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in a user."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        record = None
        users = load_data("users.json")
        for saved_user in users:
            if saved_user["email"] == email:
                record = saved_user

        if record and user_from_dict(record).check_password(password):
            session["user_id"] = record["id"]
            session["role"] = record["role"]
            return redirect(url_for("dashboard"))
        else:
            flash("Email or password is incorrect.", "error")

    return render_template("login.html")


@app.get("/logout")
def logout():
    """Log out the user."""
    session.clear()
    return redirect(url_for("home"))


@app.get("/dashboard")
def dashboard():
    """Show the correct dashboard for the user role."""
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    events = load_data("events.json")
    registrations = load_data("registrations.json")

    dashboard_items = []
    tickets = []

    if user.role == "organizer":
        for event in events:
            if event["organizer_id"] == user.user_id:
                card = event.copy()
                card["tickets_sold"] = 0
                card["sales"] = 0
                for registration in registrations:
                    if registration["event_id"] == event["id"]:
                        card["tickets_sold"] += 1
                        card["sales"] += registration["price"]
                dashboard_items.append(card)
        reminders = []
    else:
        event_lookup = {}
        for event in events:
            event_lookup[event["id"]] = event
        for registration in registrations:
            if registration["participant_id"] == user.user_id:
                ticket_details = registration.copy()
                ticket_details["event"] = event_lookup.get(registration["event_id"], {})
                tickets.append(ticket_details)
        reminders = make_reminders(user.user_id)

    return render_template(
        "dashboard.html",
        user=user,
        created_events=dashboard_items,
        tickets=tickets,
        reminders=reminders,
    )


@app.get("/events")
def events():
    """Show and search events."""
    search = request.args.get("search", "").lower()
    results = []
    for record in load_data("events.json"):
        if not search or search in record["title"].lower() or search in record["category"].lower() or search in record["location"].lower():
            results.append(record)
    return render_template("events.html", events=results)


@app.route("/events/create", methods=["GET", "POST"])
def create_event():
    """Create an event."""
    user = get_current_user()
    if not user:
        flash("Log in to create an event.", "error")
        return redirect(url_for("login"))
    if user.role != "organizer":
        flash("Only organizers can create events.", "error")
        return redirect(url_for("dashboard"))

    categories = copy_categories(CATEGORIES)
    if request.method == "POST":
        try:
            category = request.form.get("category", "")
            if category == "Other":
                category = request.form.get("custom_category", "").strip()
            event = Event(
                uuid4().hex,
                user.user_id,
                request.form.get("title", "").strip(),
                category,
                request.form.get("date_time", ""),
                request.form.get("location", "").strip(),
                request.form.get("capacity", 1),
                request.form.get("price", 0),
                request.form.get("reminder_hours", 24),
            )
            datetime.fromisoformat(event.date_time)
            if not event.title or not event.category or not event.location:
                raise ValueError
        except (TypeError, ValueError):
            flash("Enter valid event details.", "error")
        else:
            records = load_data("events.json")
            records.append(event.to_dict())
            save_data("events.json", records)
            return redirect(url_for("event_details", event_id=event.event_id))

    return render_template("event_form.html", categories=categories)


@app.get("/events/<event_id>")
def event_details(event_id):
    """Show one event."""
    event = find_event(event_id)
    if not event:
        return redirect(url_for("events"))

    registrations = load_data("registrations.json")
    event_registrations = []
    registered_ids = set()
    for registration in registrations:
        if registration["event_id"] == event_id:
            event_registrations.append(registration)
            registered_ids.add(registration["participant_id"])
    weather = get_weather(event.location)
    return render_template(
        "event_details.html",
        event=event,
        weather=weather,
        spaces=max(0, event.capacity - len(event_registrations)),
        registered=session.get("user_id") in registered_ids,
        attendees=event_registrations,
    )


@app.post("/events/<event_id>/register")
def register_for_event(event_id):
    """Register for an event and create a ticket."""
    user = get_current_user()
    event = find_event(event_id)
    if not user:
        flash("Log in to register for an event.", "error")
        return redirect(url_for("login"))
    if user.role != "participant":
        flash("Only participants can register for events.", "error")
        return redirect(url_for("event_details", event_id=event_id))

    registrations = load_data("registrations.json")
    registered_pairs = set()
    event_count = 0
    for registration in registrations:
        pair = (registration["event_id"], registration["participant_id"])
        registered_pairs.add(pair)
        if registration["event_id"] == event_id:
            event_count += 1

    if not event:
        flash("Event not found.", "error")
    elif (event_id, user.user_id) in registered_pairs:
        flash("You already registered for this event.", "error")
    elif not event.is_upcoming():
        flash("This event has already started.", "error")
    elif event.is_full(event_count):
        flash("This event is full.", "error")
    else:
        registration = Registration(
            uuid4().hex,
            event_id,
            user.user_id,
            user.name,
            event.price,
        )
        registrations.append(registration.to_dict())
        save_data("registrations.json", registrations)
        flash("Registration complete. Your ticket is ready.", "success")
        return redirect(url_for("ticket", registration_id=registration.registration_id))

    return redirect(url_for("event_details", event_id=event_id))


@app.get("/ticket/<registration_id>")
def ticket(registration_id):
    """Show one digital ticket."""
    record = None
    registrations = load_data("registrations.json")
    for registration in registrations:
        if registration["id"] == registration_id:
            record = registration
    if not record or record["participant_id"] != session.get("user_id"):
        return redirect(url_for("dashboard"))
    event = find_event(record["event_id"])
    return render_template("ticket.html", ticket=record, event=event)


@app.post("/events/<event_id>/check-in")
def check_in(event_id):
    """Check in one ticket."""
    user = get_current_user()
    event = find_event(event_id)
    if not user or not event or user.user_id != event.organizer_id:
        return redirect(url_for("login"))

    code = request.form.get("ticket_code", "").strip()
    registrations = load_data("registrations.json")
    record = None
    for registration in registrations:
        if registration["ticket_code"] == code:
            record = registration

    if not record:
        flash("Ticket not found.", "error")
    elif record["event_id"] != event_id:
        flash("That ticket is for another event.", "error")
    elif record["checked_in"]:
        flash("That ticket was already used.", "error")
    else:
        record["checked_in"] = True
        save_data("registrations.json", registrations)
        flash("Participant checked in.", "success")

    return redirect(url_for("event_details", event_id=event_id))


if __name__ == "__main__":
    app.run(debug=True)
