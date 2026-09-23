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
    elif command == "verificar_movimentacoes":
        with app.app_context():
            from processos.services.movimentacoes import verificar_movimentacoes
            print(verificar_movimentacoes())
    else:
        print("Comandos: runserver, init-db, test, verificar_movimentacoes")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
