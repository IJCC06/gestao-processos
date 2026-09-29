from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "launcher.log"


def log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp} | {message}\n")


def find_python() -> Path:
    candidates = [
        PROJECT_DIR / "venv" / "Scripts" / "python.exe",
        PROJECT_DIR / ".venv" / "Scripts" / "python.exe",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Ambiente virtual nao encontrado em venv ou .venv."
    )


def is_server_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((HOST, PORT)) == 0


def start_server(python: Path) -> subprocess.Popen:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    return subprocess.Popen(
        [
            str(python),
            "-m",
            "flask",
            "--app",
            "app",
            "run",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=PROJECT_DIR,
        creationflags=creationflags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


def wait_for_server(timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if is_server_running():
            return True
        time.sleep(0.25)

    return False


def main() -> None:
    if is_server_running():
        log("Servidor ja estava em execucao; navegador aberto.")
        webbrowser.open(URL)
        return

    python = find_python()
    process = start_server(python)

    if not wait_for_server():
        try:
            process.terminate()
        except OSError:
            pass
        raise RuntimeError(
            "O sistema nao iniciou dentro do tempo esperado."
        )

    log(f"Servidor iniciado com PID {process.pid}.")
    webbrowser.open(URL)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"ERRO: {exc}")
        # Nao exibe console. O erro fica registrado em logs/launcher.log.
