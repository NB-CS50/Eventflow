"""Read and save the app files."""

import json
from datetime import datetime
from pathlib import Path

from flask import current_app


def data_path(filename):
    """Get a safe path in the data folder."""
    directory = Path(current_app.config["DATA_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    return directory / Path(filename).name


def load_json(filename, default=None):
    """Load JSON data or return a default value."""
    fallback = [] if default is None else default
    try:
        with data_path(filename).open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def save_json(filename, data):
    """Save data in a JSON file."""
    with data_path(filename).open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def append_log(message):
    """Add an action to the text log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with data_path("activity_log.txt").open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")
