from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from processos.extensions import db
from processos.models import Cliente

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@clientes_bp.get("/")
@login_required
def list():
    busca = request.args.get("q", "").strip()
    clientes = Cliente.query.order_by(Cliente.nome).all()

    if busca:
        termo = busca.lower()
        clientes = [
            cliente
            for cliente in clientes
            if termo in cliente.nome.lower()
            or termo in cliente.cpf_cnpj.lower()
            or termo in (cliente.contato or "").lower()
        ]

    return render_template(
        "processos/clientes/list.html",
        clientes=clientes,
        busca=busca,
    )


@clientes_bp.route("/novo/", methods=["GET", "POST"])
@login_required
def create():
    return form()


@clientes_bp.route("/<int:pk>/editar/", methods=["GET", "POST"])
@login_required
def update(pk):
    return form(Cliente.query.get_or_404(pk))


def form(cliente=None):
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf_cnpj", "").strip()

        if not nome or not cpf:
            flash("Informe o nome e o CPF/CNPJ.", "error")
        elif Cliente.query.filter(
            Cliente.cpf_cnpj == cpf,
            Cliente.id != (cliente.id if cliente else 0),
        ).first():
            flash("Já existe um cliente com este CPF/CNPJ.", "error")
        else:
            if cliente is None:
                cliente = Cliente()

            cliente.nome = nome
            cliente.cpf_cnpj = cpf
            cliente.contato = request.form.get("contato", "").strip()
            cliente.endereco = request.form.get("endereco", "").strip()
            cliente.observacoes = request.form.get("observacoes", "").strip()

            db.session.add(cliente)
            db.session.commit()
            flash("Cliente salvo com sucesso.", "success")
            return redirect(url_for("clientes.detail", pk=cliente.id))

    return render_template(
        "processos/clientes/form.html",
        titulo="Editar cliente" if cliente else "Novo cliente",
        cliente=cliente,
    )


@clientes_bp.get("/<int:pk>/")
@login_required
def detail(pk):
    return render_template(
        "processos/clientes/detail.html",
        cliente=Cliente.query.get_or_404(pk),
    )


@clientes_bp.route("/<int:pk>/excluir/", methods=["GET", "POST"])
@login_required
def delete(pk):
    cliente = Cliente.query.get_or_404(pk)

    if request.method == "POST":
        if cliente.processos:
            flash(
                "Não foi possível excluir este cliente. "
                "Existem processos vinculados.",
                "error",
            )
            return redirect(url_for("clientes.detail", pk=pk))

        db.session.delete(cliente)
        db.session.commit()
        flash("Cliente excluído com sucesso.", "success")
        return redirect(url_for("clientes.list"))

    return render_template(
        "processos/clientes/delete.html",
        cliente=cliente,
    )
