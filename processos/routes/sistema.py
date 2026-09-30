from __future__ import annotations

import os
import threading

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required, logout_user

from processos.extensions import db
from processos.services.auditoria import registrar_auditoria


sistema_bp = Blueprint("sistema", __name__, url_prefix="/sistema")


def _encerrar_servidor(shutdown) -> None:
    if shutdown is not None:
        shutdown()
        return

    os._exit(0)


@sistema_bp.post("/encerrar/")
@login_required
def encerrar():
    shutdown = request.environ.get("werkzeug.server.shutdown")
    registrar_auditoria(
        "ENCERRAR",
        "Sistema",
        None,
        "Servidor local encerrado pelo usuário.",
    )
    db.session.commit()
    logout_user()

    # Devolve a resposta ao navegador antes de encerrar o processo.
    threading.Timer(0.25, _encerrar_servidor, args=(shutdown,)).start()

    return render_template("sistema/encerrando.html"), 200
