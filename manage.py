#!/usr/bin/env python
import getpass
import sys
import unittest

from app import create_app

app = create_app()


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "runserver"

    if command == "runserver":
        app.run(debug=app.config["DEBUG"])

    elif command == "init-db":
        print("Banco inicializado.")

    elif command == "createuser":
        from processos.extensions import db
        from processos.models import Usuario

        username = input("Usuário: ").strip()
        password = getpass.getpass("Senha: ")

        with app.app_context():
            if Usuario.query.filter_by(username=username).first():
                print("Usuário já existe.")
                raise SystemExit(1)

            usuario = Usuario(username=username)
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            print("Usuário criado.")

    elif command == "test":
        suite = unittest.defaultTestLoader.discover(
            "processos", pattern="test*.py"
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(not result.wasSuccessful())

    elif command == "verificar_movimentacoes":
        with app.app_context():
            from processos.services.movimentacoes import verificar_movimentacoes

            print(verificar_movimentacoes())

    else:
        print(
            "Comandos: runserver, init-db, createuser, "
            "test, verificar_movimentacoes"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
