from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from processos.extensions import db
from processos.models import Prazo, Processo

prazos_bp = Blueprint("prazos", __name__, url_prefix="/prazos")


@prazos_bp.route("/novo/", methods=["GET", "POST"])
@login_required
def create():
    return form()


@prazos_bp.route("/<int:pk>/editar/", methods=["GET", "POST"])
@login_required
def update(pk):
    return form(Prazo.query.get_or_404(pk))


def form(prazo=None):
    processo_id = (
        request.args.get("processo", type=int)
        if prazo is None
        else None
    )
    processos = Processo.query.order_by(Processo.numero_cnj).all()

    if request.method == "POST":
        processo = db.session.get(
            Processo, request.form.get("processo", type=int)
        )
        titulo = request.form.get("titulo", "").strip()
        inicio = request.form.get("data_inicio") or None
        vencimento = request.form.get("data_vencimento") or ""

        if not processo or not titulo or not vencimento:
            flash("Informe processo, título e vencimento.", "error")
        elif inicio and vencimento < inicio:
            flash(
                "A data de vencimento não pode ser anterior à data de início.",
                "error",
            )
        else:
            if prazo is None:
                prazo = Prazo()

            prazo.processo = processo
            prazo.titulo = titulo
            prazo.data_inicio = (
                date.fromisoformat(inicio) if inicio else None
            )
            prazo.data_vencimento = date.fromisoformat(vencimento)
            prazo.status = request.form.get(
                "status", Prazo.Status.PENDENTE
            )
            prazo.observacoes = request.form.get(
                "observacoes", ""
            ).strip()

            db.session.add(prazo)
            db.session.commit()
            flash("Prazo salvo com sucesso.", "success")
            return redirect(
                url_for("prazos.detail", pk=prazo.id)
            )

    return render_template(
        "processos/prazos/form.html",
        titulo="Editar prazo" if prazo else "Novo prazo",
        prazo=prazo,
        processos=processos,
        processo_id=processo_id,
    )


@prazos_bp.get("/")
@login_required
def list():
    status = request.args.get("status", "").strip()
    prazos = Prazo.query.order_by(
        Prazo.data_vencimento, Prazo.titulo
    ).all()

    if status in Prazo.Status.values():
        prazos = [prazo for prazo in prazos if prazo.status == status]

    return render_template(
        "processos/prazos/list.html",
        prazos=prazos,
        status=status,
        status_choices=Prazo.Status.choices(),
    )


@prazos_bp.get("/<int:pk>/")
@login_required
def detail(pk):
    return render_template(
        "processos/prazos/detail.html",
        prazo=Prazo.query.get_or_404(pk),
    )


@prazos_bp.post("/<int:pk>/concluir/")
@login_required
def concluir(pk):
    prazo = Prazo.query.get_or_404(pk)
    prazo.status = Prazo.Status.CONCLUIDO
    db.session.commit()
    flash("Prazo marcado como concluído.", "success")
    return redirect(url_for("prazos.list"))
