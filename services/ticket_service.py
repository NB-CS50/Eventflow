"""Prepare ticket sales, attendance and CSV data."""

import csv
from pathlib import Path

from flask import current_app

from storage import load_json


def registration_rows(event_id):
    """Join users to their registrations."""
    users = {user["id"]: user for user in load_json("users.json", [])}
    rows = []
    for registration in load_json("registrations.json", []):
        if registration["event_id"] == event_id:
            user = users.get(registration["participant_id"], {})
            rows.append(
                {
                    "name": user.get("name", "Unknown"),
                    "email": user.get("email", "Unknown"),
                    **registration,
                }
            )
    return rows


def sales_summary(event):
    """Count tickets, attendance and sales."""
    rows = registration_rows(event["id"])
    paid = [row for row in rows if row["payment_status"] == "Paid"]
    checked_in = [row for row in rows if row.get("checked_in")]
    return {
        "tickets_sold": len(rows),
        "remaining": max(0, int(event["capacity"]) - len(rows)),
        "revenue": sum(float(row["price"]) for row in paid),
        "checked_in": len(checked_in),
        "absent": len(rows) - len(checked_in),
    }


def export_attendees(event_id):
    """Save the attendee list as a CSV file."""
    directory = Path(current_app.config["EXPORT_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"attendees-{event_id}.csv"
    fields = ["name", "email", "ticket_code", "payment_status", "checked_in"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in registration_rows(event_id):
            writer.writerow({field: row.get(field) for field in fields})
    return path
