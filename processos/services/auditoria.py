from __future__ import annotations

from flask_login import current_user

from processos.extensions import db
from processos.models import Auditoria


def registrar_auditoria(acao, entidade, registro_id=None, detalhes=""):
    """Registra uma alteração importante sem armazenar senhas ou outros segredos."""
    usuario_id = current_user.id if current_user.is_authenticated else None
    db.session.add(
        Auditoria(
            usuario_id=usuario_id,
            acao=acao,
            entidade=entidade,
            registro_id=registro_id,
            detalhes=detalhes,
        )
    )
