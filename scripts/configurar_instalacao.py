from __future__ import annotations

import getpass
import secrets
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_DIR / ".env"


def _read_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}

    values: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _write_env(values: dict[str, str]) -> None:
    content = [
        "# Configuração local do Sistema de Gestão de Processos",
        f"FLASK_SECRET_KEY={values['FLASK_SECRET_KEY']}",
        "FLASK_DEBUG=False",
        f"DATAJUD_API_KEY={values.get('DATAJUD_API_KEY', '')}",
        "DATABASE_URL=sqlite:///flask.db",
        "",
        "# BACKUP_DIR=C:\\GestaoProcessos\\backups",
        "# LOG_LEVEL=INFO",
        "# LOG_FILE=C:\\GestaoProcessos\\logs\\app.log",
        "",
    ]
    ENV_FILE.write_text("\n".join(content), encoding="utf-8")


def configurar_ambiente() -> None:
    values = _read_env()

    if not values.get("FLASK_SECRET_KEY"):
        values["FLASK_SECRET_KEY"] = secrets.token_urlsafe(48)

    if "DATAJUD_API_KEY" not in values:
        print()
        print("Chave da API pública do DataJud (opcional nesta etapa).")
        print("Se você já possui a chave, cole-a agora.")
        print("Se deixar em branco, poderá configurar depois no arquivo .env.")
        values["DATAJUD_API_KEY"] = getpass.getpass("Chave DataJud: ").strip()

    _write_env(values)
    print()
    print(f"Configuração salva em: {ENV_FILE}")


def configurar_primeiro_administrador() -> None:
    from processos.extensions import db
    from processos.models import Usuario
    from app import app

    with app.app_context():
        if Usuario.query.filter_by(is_admin=True).first() is not None:
            print("Já existe um administrador. Nenhuma conta administrativa foi criada.")
            return

        print()
        print("=== Primeiro administrador ===")

        while True:
            username = input("Nome de usuário [admin]: ").strip() or "admin"
            if len(username) < 3:
                print("O nome de usuário deve ter pelo menos 3 caracteres.")
                continue

            existente = Usuario.query.filter_by(username=username).first()
            if existente is not None:
                existente.is_admin = True
                existente.is_active = True
                db.session.commit()
                print(f"Usuário '{username}' promovido a administrador.")
                return
            break

        while True:
            senha = getpass.getpass("Senha: ")
            confirmacao = getpass.getpass("Confirme a senha: ")

            if len(senha) < 8:
                print("A senha deve ter pelo menos 8 caracteres.")
                continue

            if senha != confirmacao:
                print("As senhas não coincidem.")
                continue
            break

        usuario = Usuario(username=username, is_admin=True, is_active=True)
        usuario.set_password(senha)
        db.session.add(usuario)
        db.session.commit()

        print(f"Administrador '{username}' criado com sucesso.")


def main() -> None:
    configurar_ambiente()
    configurar_primeiro_administrador()


if __name__ == "__main__":
    main()
