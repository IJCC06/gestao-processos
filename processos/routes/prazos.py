from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
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
    prazo = db.session.get(Prazo, pk)
    if prazo is None:
        abort(404)
    return form(prazo)


def form(prazo=None):
    processo_id = request.args.get("processo", type=int) if prazo is None else None
    processos = Processo.query.order_by(Processo.numero_cnj).all()
    valores = None

    if request.method == "POST":
        valores = {
            "processo": request.form.get("processo", ""),
            "titulo": request.form.get("titulo", "").strip(),
            "data_inicio": request.form.get("data_inicio", "").strip(),
            "data_vencimento": request.form.get("data_vencimento", "").strip(),
            "status": request.form.get("status", "").strip(),
            "observacoes": request.form.get("observacoes", "").strip(),
        }

        processo = db.session.get(Processo, request.form.get("processo", type=int))
        inicio = None
        vencimento = None
        datas_validas = True

        try:
            if valores["data_inicio"]:
                inicio = date.fromisoformat(valores["data_inicio"])
            if valores["data_vencimento"]:
                vencimento = date.fromisoformat(valores["data_vencimento"])
        except ValueError:
            datas_validas = False

        if not processo or not valores["titulo"] or not valores["data_vencimento"]:
            flash("Informe processo, título e vencimento.", "error")
        elif not datas_validas:
            flash("Informe datas válidas.", "error")
        elif inicio and vencimento < inicio:
            flash(
                "A data de vencimento não pode ser anterior à data de início.",
                "error",
            )
        elif valores["status"] not in Prazo.Status.values():
            flash("Selecione um status válido.", "error")
        else:
            if prazo is None:
                prazo = Prazo()

            prazo.processo = processo
            prazo.titulo = valores["titulo"]
            prazo.data_inicio = inicio
            prazo.data_vencimento = vencimento
            prazo.status = valores["status"]
            prazo.observacoes = valores["observacoes"]

            db.session.add(prazo)
            db.session.commit()
            flash("Prazo salvo com sucesso.", "success")
            return redirect(url_for("prazos.detail", pk=prazo.id))

    return render_template(
        "processos/prazos/form.html",
        titulo="Editar prazo" if prazo else "Novo prazo",
        prazo=prazo,
        processos=processos,
        processo_id=processo_id,
        valores=valores,
        status_choices=Prazo.Status.choices(),
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
        prazo=db.session.get(Prazo, pk),
    )


@prazos_bp.route("/<int:pk>/excluir/", methods=["GET", "POST"])
@login_required
def delete(pk):
    prazo = db.session.get(Prazo, pk)
    if prazo is None:
        abort(404)

    if request.method == "POST":
        db.session.delete(prazo)
        db.session.commit()
        flash("Prazo excluído com sucesso.", "success")
        return redirect(url_for("prazos.list"))

    return render_template("processos/prazos/delete.html", prazo=prazo)


@prazos_bp.post("/<int:pk>/concluir/")
@login_required
def concluir(pk):
    prazo = Prazo.query.get_or_404(pk)
    prazo.status = Prazo.Status.CONCLUIDO
    db.session.commit()
    flash("Prazo marcado como concluído.", "success")
    return redirect(url_for("prazos.list"))
