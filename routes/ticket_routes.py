"""Handle registrations, tickets, sales and attendance."""

from uuid import uuid4

from flask import Blueprint, flash, redirect, render_template, request, send_file, session, url_for

from models.event import Event
from models.registration import Registration
from routes.auth_routes import login_required, role_required
from services.ticket_service import export_attendees, registration_rows, sales_summary
from storage import append_log, load_json, save_json


ticket_bp = Blueprint("tickets", __name__)


def event_record(event_id):
    """Find one saved event."""
    return next((event for event in load_json("events.json", []) if event["id"] == event_id), None)


def registration_record(registration_id):
    """Find one saved registration."""
    return next(
        (item for item in load_json("registrations.json", []) if item["id"] == registration_id),
        None,
    )


@ticket_bp.post("/events/<event_id>/register")
@login_required
@role_required("participant")
def register_for_event(event_id):
    """Register a participant for an event."""
    event_data = event_record(event_id)
    records = load_json("registrations.json", [])
    existing = {(item["event_id"], item["participant_id"]) for item in records}
    event_count = sum(1 for item in records if item["event_id"] == event_id)

    if not event_data:
        flash("Event not found.", "error")
    elif (event_id, session["user_id"]) in existing:
        flash("You already registered for this event.", "error")
    elif Event.from_dict(event_data).current_status() != "upcoming":
        flash("This event is unavailable.", "error")
    elif Event.from_dict(event_data).is_full(event_count):
        flash("This event is full.", "error")
    else:
        price = float(event_data["price"])
        payment_status = "Free" if price == 0 else "Paid"
        registration = Registration(
            uuid4().hex,
            event_id,
            session["user_id"],
            price,
            payment_status,
        )
        records.append(registration.to_dict())
        save_json("registrations.json", records)
        append_log(f"Registered participant for event: {event_data['title']}")
        flash("Registration successful. Your ticket is ready.", "success")
        return redirect(url_for("tickets.ticket_detail", registration_id=registration.registration_id))

    return redirect(url_for("events.event_detail", event_id=event_id))


@ticket_bp.get("/my-tickets")
@login_required
@role_required("participant")
def my_tickets():
    """Show the participant's tickets."""
    events = {event["id"]: event for event in load_json("events.json", [])}
    registrations = [
        {**item, "event": events.get(item["event_id"], {})}
        for item in load_json("registrations.json", [])
        if item["participant_id"] == session["user_id"]
    ]
    return render_template("my_tickets.html", registrations=registrations)


@ticket_bp.get("/tickets/<registration_id>")
@login_required
def ticket_detail(registration_id):
    """Show one ticket to its owner or organizer."""
    registration = registration_record(registration_id)
    if not registration:
        flash("Ticket not found.", "error")
        return redirect(url_for("auth.dashboard"))
    event = event_record(registration["event_id"])
    allowed = registration["participant_id"] == session["user_id"]
    allowed = allowed or bool(event and event["organizer_id"] == session["user_id"])
    if not allowed:
        flash("You cannot view that ticket.", "error")
        return redirect(url_for("auth.dashboard"))
    return render_template("ticket_detail.html", registration=registration, event=event)


@ticket_bp.get("/events/<event_id>/sales")
@login_required
@role_required("organizer")
def sales_report(event_id):
    """Show ticket sales for an organizer's event."""
    event = event_record(event_id)
    if not event or event["organizer_id"] != session["user_id"]:
        flash("You cannot view that report.", "error")
        return redirect(url_for("auth.dashboard"))
    return render_template("sales_report.html", event=event, summary=sales_summary(event))


@ticket_bp.route("/events/<event_id>/attendance", methods=["GET", "POST"])
@login_required
@role_required("organizer")
def attendance(event_id):
    """Check tickets and show the attendee list."""
    event = event_record(event_id)
    if not event or event["organizer_id"] != session["user_id"]:
        flash("You cannot manage that attendance list.", "error")
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        code = request.form.get("ticket_code", "").strip()
        records = load_json("registrations.json", [])
        record = next((item for item in records if item["ticket_code"] == code), None)
        if not record:
            flash("Ticket not found.", "error")
        elif record["event_id"] != event_id:
            flash("That ticket belongs to another event.", "error")
        else:
            registration = Registration.from_dict(record)
            if not registration.ticket.mark_used():
                flash("That ticket has already been checked in.", "error")
            else:
                records[records.index(record)] = registration.to_dict()
                save_json("registrations.json", records)
                append_log(f"Checked in ticket: {code}")
                flash("Ticket checked in.", "success")

    return render_template(
        "attendance.html",
        event=event,
        attendees=registration_rows(event_id),
        summary=sales_summary(event),
    )


@ticket_bp.get("/events/<event_id>/attendees.csv")
@login_required
@role_required("organizer")
def attendee_export(event_id):
    """Download an event's attendee list."""
    event = event_record(event_id)
    if not event or event["organizer_id"] != session["user_id"]:
        flash("You cannot export that attendee list.", "error")
        return redirect(url_for("auth.dashboard"))
    return send_file(export_attendees(event_id), as_attachment=True, download_name=f"attendees-{event_id}.csv")
