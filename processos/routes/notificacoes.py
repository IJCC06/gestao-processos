from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from config.settings import Config
from processos.extensions import db
from processos.models import Movimentacao, Prazo, Processo
from processos.services.movimentacoes import verificar_movimentacoes
from processos.services.auditoria import registrar_auditoria

notificacoes_bp = Blueprint("notificacoes", __name__, url_prefix="/notificacoes")


@notificacoes_bp.get("/")
@login_required
def list():
    hoje = Config.local_date()
    prazos = Prazo.query.filter_by(status=Prazo.Status.PENDENTE).all()

    vencidos = [
        prazo for prazo in prazos if prazo.data_vencimento < hoje
    ]
    proximos = [
        prazo
        for prazo in prazos
        if hoje <= prazo.data_vencimento <= hoje + timedelta(days=7)
    ]

    movimentos = (
        Movimentacao.query.join(Processo)
        .filter(Movimentacao.lida.is_(False))
        .order_by(Movimentacao.data.desc())
        .all()
    )

    return render_template(
        "processos/notificacoes.html",
        vencidos=vencidos,
        prazos_proximos=proximos,
        movimentos=movimentos,
    )


@notificacoes_bp.post("/atualizar/")
@login_required
def atualizar_movimentacoes():
    resultado = verificar_movimentacoes()

    if resultado["erros"]:
        flash(
            f"Consulta concluída com {resultado['erros']} "
            "ocorrência(s) de erro ou configuração ausente.",
            "warning",
        )
    else:
        registrar_auditoria("DATAJUD", "Movimentacao", None, f"Consulta geral DataJud: {resultado['total_novas']} nova(s) movimentação(ões).")
        db.session.commit()
        flash(
            f"Consulta concluída: {resultado['total_novas']} "
            f"movimentação(ões) nova(s) encontrada(s) em "
            f"{resultado['total_processos']} processo(s).",
            "success",
        )

    return redirect(url_for("notificacoes.list"))


@notificacoes_bp.post("/processos/<int:pk>/limpar/")
@login_required
def limpar_alerta_processo(pk):
    processo = db.get_or_404(Processo, pk)
    Movimentacao.query.filter_by(
        processo_id=processo.id,
        lida=False,
    ).update({"lida": True}, synchronize_session=False)
    processo.alerta_pendente = False
    db.session.commit()
    registrar_auditoria("VISUALIZAR", "Movimentacao", processo.id, "Movimentações do processo marcadas como vistas.")
    db.session.commit()
    flash(
        "Movimentações do processo marcadas como vistas.",
        "success",
    )
    return redirect(url_for("notificacoes.list"))
