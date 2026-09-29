from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from processos.extensions import db
from processos.models import Cliente, Processo

processos_bp = Blueprint("processos", __name__, url_prefix="/processos")


@processos_bp.get("/")
@login_required
def list():
    busca = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    area = request.args.get("area", "").strip()

    consulta = Processo.query.order_by(Processo.criado_em.desc())

    if busca:
        termo = f"%{busca}%"
        consulta = consulta.filter(
            or_(
                Processo.numero_cnj.ilike(termo),
                Processo.tribunal.ilike(termo),
                Processo.cliente.has(Cliente.nome.ilike(termo)),
            )
        )

    if status in Processo.Status.values():
        consulta = consulta.filter(Processo.status == status)

    if area in Processo.Area.values():
        consulta = consulta.filter(Processo.area == area)

    processos = consulta.all()

    return render_template(
        "processos/processos/list.html",
        processos=processos,
        busca=busca,
        status=status,
        area=area,
        status_choices=Processo.Status.choices(),
        area_choices=Processo.Area.choices(),
    )


@processos_bp.route("/novo/", methods=["GET", "POST"])
@login_required
def create():
    return form()


@processos_bp.route("/<int:pk>/editar/", methods=["GET", "POST"])
@login_required
def update(pk):
    return form(db.get_or_404(Processo, pk))


def form(processo=None):
    clientes = Cliente.query.order_by(Cliente.nome).all()

    if request.method == "POST":
        cliente = db.session.get(
            Cliente, request.form.get("cliente", type=int)
        )
        numero = request.form.get("numero_cnj", "").strip()

        if not cliente or not numero:
            flash("Informe o cliente e o número do processo.", "error")
        elif Processo.query.filter(
            Processo.numero_cnj == numero,
            Processo.id != (processo.id if processo else 0),
        ).first():
            flash(
                "Já existe um processo com este número CNJ.",
                "error",
            )
        else:
            if processo is None:
                processo = Processo()

            processo.cliente = cliente
            processo.numero_cnj = numero
            processo.area = request.form.get("area", "")
            processo.tribunal = request.form.get("tribunal", "").strip()
            processo.tribunal_alias = request.form.get(
                "tribunal_alias", ""
            ).strip()
            processo.fase = request.form.get("fase", "").strip()
            processo.status = request.form.get(
                "status", Processo.Status.ATIVO
            )
            processo.valor_causa = request.form.get("valor_causa") or None
            processo.honorarios = request.form.get("honorarios") or None

            db.session.add(processo)
            db.session.commit()
            flash("Processo salvo com sucesso.", "success")
            return redirect(
                url_for("processos.detail", pk=processo.id)
            )

    return render_template(
        "processos/processos/form.html",
        titulo="Editar processo" if processo else "Novo processo",
        processo=processo,
        clientes=clientes,
    )


@processos_bp.get("/<int:pk>/")
@login_required
def detail(pk):
    return render_template(
        "processos/processos/detail.html",
        processo=db.get_or_404(Processo, pk),
    )
