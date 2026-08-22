"""Run the EventFlow website."""

from pathlib import Path

from flask import Flask, flash, render_template, session

from config import Config
from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from routes.ticket_routes import ticket_bp
from services.reminder_service import check_upcoming_events
from services.weather_service import major_city_weather


def create_app(test_config=None):
    """Create the EventFlow app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    Path(app.config["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["EXPORT_DIR"]).mkdir(parents=True, exist_ok=True)
    app.register_blueprint(auth_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(ticket_bp)

    @app.get("/")
    def home():
        """Show the home page."""
        return render_template("home.html", city_weather=major_city_weather())

    @app.before_request
    def update_reminders():
        """Check reminders when a user opens the website."""
        if session.get("user_id"):
            new_count = check_upcoming_events(app, session["user_id"])
            if new_count:
                word = "reminder" if new_count == 1 else "reminders"
                flash(f"You have {new_count} new event {word}.", "success")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
