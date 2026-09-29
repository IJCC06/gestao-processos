from datetime import timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from config.settings import Config
from processos.models import Cliente, Movimentacao, Prazo, Processo

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@login_required
def index():
    hoje = Config.local_date()
    prazos = Prazo.query.filter_by(
        status=Prazo.Status.PENDENTE
    ).all()

    prazos_vencidos = sorted(
        [p for p in prazos if p.data_vencimento < hoje],
        key=lambda p: (p.data_vencimento, p.titulo),
    )
    prazos_proximos = sorted(
        [
            p
            for p in prazos
            if hoje <= p.data_vencimento <= hoje + timedelta(days=7)
        ],
        key=lambda p: (p.data_vencimento, p.titulo),
    )

    return render_template(
        "processos/dashboard.html",
        total_clientes=Cliente.query.count(),
        total_processos=Processo.query.count(),
        processos_ativos=Processo.query.filter_by(
            status=Processo.Status.ATIVO
        ).count(),
        alertas_pendentes=Processo.query.filter_by(
            alerta_pendente=True
        ).count(),
        prazos_vencidos=prazos_vencidos,
        prazos_proximos=prazos_proximos,
        ultimas_movimentacoes=Movimentacao.query.order_by(
            Movimentacao.data.desc()
        ).limit(10).all(),
    )
