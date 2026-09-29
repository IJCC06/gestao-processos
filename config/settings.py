import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    ENVIRONMENT = os.environ.get("FLASK_ENVIRONMENT", "development")
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-change-this-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'flask.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in {
        "1", "true", "yes", "on",
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get(
        "FLASK_SESSION_COOKIE_SECURE",
        "False",
    ).lower() in {"1", "true", "yes", "on"}

    @classmethod
    def validate_security(cls):
        if cls.ENVIRONMENT.lower() in {"production", "prod"}:
            if not os.environ.get("FLASK_SECRET_KEY"):
                raise RuntimeError(
                    "FLASK_SECRET_KEY deve ser configurada em produção."
                )
            if cls.DEBUG:
                raise RuntimeError(
                    "FLASK_DEBUG não pode estar habilitado em produção."
                )

    @staticmethod
    def local_date():
        return datetime.now(ZoneInfo("America/Sao_Paulo")).date()
