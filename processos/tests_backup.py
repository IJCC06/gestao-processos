import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from processos.services.backup import BackupError, backup_sqlite


class BackupTests(unittest.TestCase):
    def test_backup_sqlite_cria_copia_integra(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "flask.db"
            backup_dir = root / "backups"

            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE teste (id INTEGER PRIMARY KEY, nome TEXT)")
                connection.execute("INSERT INTO teste (nome) VALUES (?)", ("registro",))
                connection.commit()

            destino = backup_sqlite(
                database,
                backup_dir,
                retention_days=30,
                now=datetime(2026, 9, 29, 12, 0, 0),
            )

            self.assertTrue(destino.exists())
            self.assertEqual(destino.parent, backup_dir)

            with sqlite3.connect(destino) as connection:
                self.assertEqual(
                    connection.execute("SELECT nome FROM teste").fetchone()[0],
                    "registro",
                )
                self.assertEqual(
                    connection.execute("PRAGMA integrity_check").fetchone()[0],
                    "ok",
                )

    def test_backup_sqlite_rejeita_banco_inexistente(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(BackupError):
                backup_sqlite(
                    Path(temp_dir) / "nao-existe.db",
                    Path(temp_dir) / "backups",
                )


if __name__ == "__main__":
    unittest.main()
