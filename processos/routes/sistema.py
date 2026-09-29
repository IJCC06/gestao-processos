from __future__ import annotations

import os
import threading

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required, logout_user

from processos.extensions import db
from processos.services.auditoria import registrar_auditoria


sistema_bp = Blueprint("sistema", __name__, url_prefix="/sistema")


def _encerrar_servidor() -> None:
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if shutdown is not None:
        shutdown()
        return

    # O servidor atual e iniciado pelo inicializador local como processo separado.
    # O encerramento do proprio processo evita deixar o Flask rodando em segundo plano.
    os._exit(0)


@sistema_bp.post("/encerrar/")
@login_required
def encerrar():
    usuario_id = current_user.id
    registrar_auditoria(
        "ENCERRAR",
        "Sistema",
        None,
        "Servidor local encerrado pelo usuário.",
    )
    db.session.commit()
    logout_user()

    # Devolve a resposta ao navegador antes de encerrar o processo.
    threading.Timer(0.25, _encerrar_servidor).start()

    return render_template("sistema/encerrando.html"), 200
