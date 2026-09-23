#!/usr/bin/env python
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
    elif command == "test":
        suite = unittest.defaultTestLoader.discover("processos", pattern="test*.py")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(not result.wasSuccessful())
    elif command == "createuser":\n        from processos.extensions import db\n        from processos.models import Usuario\n        username = input("Usuário: ").strip()\n        password = getpass.getpass("Senha: ")\n        with app.app_context():\n            if Usuario.query.filter_by(username=username).first():\n                print("Usuário já existe.")\n                raise SystemExit(1)\n            usuario = Usuario(username=username)\n            usuario.set_password(password)\n            db.session.add(usuario)\n            db.session.commit()\n            print("Usuário criado.")\n    elif command == "verificar_movimentacoes":
        with app.app_context():
            from processos.services.movimentacoes import verificar_movimentacoes
            print(verificar_movimentacoes())
    else:
        print("Comandos: runserver, init-db, createuser, test, verificar_movimentacoes")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
