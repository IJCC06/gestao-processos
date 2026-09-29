import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-change-this-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'flask.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in {
        "1", "true", "yes", "on",
    }

    @staticmethod
    def local_date():
        return datetime.now(ZoneInfo("America/Sao_Paulo")).date()
