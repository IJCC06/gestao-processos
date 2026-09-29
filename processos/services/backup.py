from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


BACKUP_FILENAME_PREFIX = "flask_"
BACKUP_FILENAME_SUFFIX = ".db"
LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class BackupError(RuntimeError):
    """Erro controlado durante a criação ou manutenção de backups."""


def _database_path(database_path: str | Path) -> Path:
    path = Path(database_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def backup_sqlite(
    database_path: str | Path,
    backup_dir: str | Path,
    retention_days: int = 30,
    now: datetime | None = None,
) -> Path:
    """Cria um backup consistente do SQLite e remove backups antigos."""
    if retention_days < 1:
        raise BackupError("retention_days deve ser maior ou igual a 1.")

    source_path = _database_path(database_path)
    if not source_path.exists():
        raise BackupError(f"Banco de dados não encontrado: {source_path}")

    if source_path.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise BackupError("O backup automático está configurado apenas para SQLite.")

    destination_dir = Path(backup_dir).expanduser()
    if not destination_dir.is_absolute():
        destination_dir = Path.cwd() / destination_dir
    destination_dir = destination_dir.resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)

    current_time = now or datetime.now(LOCAL_TIMEZONE)
    timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    destination = destination_dir / (
        f"{BACKUP_FILENAME_PREFIX}{timestamp}{BACKUP_FILENAME_SUFFIX}"
    )
    temporary = destination.with_suffix(".tmp")

    try:
        source = sqlite3.connect(str(source_path), timeout=30)
        target = sqlite3.connect(str(temporary))
        try:
            source.backup(target)
            target.commit()
            integrity = target.execute("PRAGMA integrity_check").fetchone()
        finally:
            target.close()
            source.close()

        if not integrity or integrity[0] != "ok":
            raise BackupError(
                "O backup foi criado, mas falhou na verificação de integridade."
            )

        temporary.replace(destination)
        _remove_old_backups(destination_dir, retention_days, current_time)
        return destination
    except BackupError:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass
        raise
    except (OSError, sqlite3.Error) as exc:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass
        raise BackupError(f"Não foi possível criar o backup: {exc}") from exc

def _remove_old_backups(
    backup_dir: Path,
    retention_days: int,
    now: datetime,
) -> None:
    cutoff = now - timedelta(days=retention_days)
    for backup in backup_dir.glob(
        f"{BACKUP_FILENAME_PREFIX}*{BACKUP_FILENAME_SUFFIX}"
    ):
        if not backup.is_file():
            continue
        modified_at = datetime.fromtimestamp(
            backup.stat().st_mtime,
            tz=LOCAL_TIMEZONE,
        )
        if modified_at < cutoff:
            try:
                backup.unlink()
            except OSError:
                # A criação do backup atual não deve falhar porque um
                # backup antigo não pôde ser removido.
                continue
