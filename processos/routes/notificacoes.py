from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from config.settings import Config
from processos.extensions import db
from processos.models import Movimentacao, Prazo, Processo
from processos.services.movimentacoes import verificar_movimentacoes

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
        .filter(Processo.alerta_pendente.is_(True))
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
    processo.alerta_pendente = False
    db.session.commit()
    flash(
        "Alerta de movimentação marcado como visto.",
        "success",
    )
    return redirect(url_for("notificacoes.list"))
