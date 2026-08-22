"""Keep the main app settings."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Keep the settings used by the app."""

    SECRET_KEY = os.environ.get("EVENTFLOW_SECRET_KEY", "change-this-before-submission")
    DATA_DIR = BASE_DIR / "data"
    EXPORT_DIR = BASE_DIR / "exports"
    REMINDER_HOURS = 24
