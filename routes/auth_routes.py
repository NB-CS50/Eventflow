"""Handle accounts, dashboards and reminders."""

from functools import wraps
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from models.user import Organizer, Participant, user_from_dict
from storage import append_log, load_json, save_json


auth_bp = Blueprint("auth", __name__)


def users():
    """Get all saved users."""
    return load_json("users.json", [])


def login_required(view):
    """Keep a page for logged-in users."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        """Run the route only when a user is logged in."""
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(role):
    """Keep a page for one user type."""
    def decorator(view):
        """Apply the role restriction to a route."""
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            """Run the route only for the required user role."""
            if session.get("role") != role:
                flash("You cannot access that page.", "error")
                return redirect(url_for("auth.dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create an organizer or participant account."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "")
        records = users()

        if not name or not email or not password:
            flash("Complete every field.", "error")
        elif len(password) < 6:
            flash("Password must contain at least six characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif role not in {"organizer", "participant"}:
            flash("Select a valid role.", "error")
        elif any(user["email"] == email for user in records):
            flash("That email is already registered.", "error")
        else:
            user_class = Organizer if role == "organizer" else Participant
            user = user_class(uuid4().hex, name, email, "")
            user.set_password(password)
            records.append(user.to_dict())
            save_json("users.json", records)
            append_log(f"Registered {role}: {email}")
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Log in a saved user."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        record = next((user for user in users() if user["email"] == email), None)
        if record and user_from_dict(record).check_password(password):
            session.clear()
            session["user_id"] = record["id"]
            session["role"] = record["role"]
            append_log(f"Logged in: {email}")
            return redirect(url_for("auth.dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@auth_bp.get("/dashboard")
@login_required
def dashboard():
    """Show the right dashboard for the user."""
    record = next((user for user in users() if user["id"] == session["user_id"]), None)
    if not record:
        session.clear()
        return redirect(url_for("auth.login"))
    user = user_from_dict(record)
    return render_template(user.dashboard_template(), user=user)


@auth_bp.get("/notifications")
@login_required
def notifications():
    """Show the user's event reminders."""
    items = [
        item
        for item in load_json("notifications.json", [])
        if item["user_id"] == session["user_id"]
    ]
    return render_template(
        "notifications.html",
        notifications=items,
        reminder_hours=current_app.config["REMINDER_HOURS"],
    )


@auth_bp.get("/logout")
def logout():
    """Log out the current user."""
    if "user_id" in session:
        append_log(f"Logged out user ID: {session['user_id']}")
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("home"))
