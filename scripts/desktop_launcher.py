from __future__ import annotations

import os
import secrets
import sys
import threading
import webbrowser
from pathlib import Path


APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"


def _data_dir() -> Path:
    return Path(
        os.environ.get(
            "GESTAO_PROCESSOS_DATA_DIR",
            Path.home() / "AppData" / "Local" / "GestaoProcessos",
        )
    )


def _prepare_environment() -> None:
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    env_file = data_dir / ".env"

    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

    os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_urlsafe(48))
    os.environ.setdefault("FLASK_DEBUG", "False")

    if not env_file.exists():
        env_file.write_text(
            f"FLASK_SECRET_KEY={os.environ['FLASK_SECRET_KEY']}\n"
            "FLASK_DEBUG=False\n",
            encoding="utf-8",
        )


def main() -> None:
    os.environ.setdefault("GESTAO_PROCESSOS_DATA_DIR", str(_data_dir()))
    _prepare_environment()
    os.chdir(APP_DIR)

    from flask_migrate import upgrade
    from app import app

    with app.app_context():
        upgrade(directory=str(APP_DIR / "migrations"))

    threading.Timer(1.5, lambda: webbrowser.open(URL)).start()
    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_dir = _data_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "launcher.log").open("a", encoding="utf-8") as file:
            file.write(f"ERRO: {type(exc).__name__}: {exc}\n")
