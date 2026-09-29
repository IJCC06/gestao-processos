from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

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
    return form(db.get_or_404(Cliente, pk))


def form(cliente=None):
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cpf = request.form.get("cpf_cnpj", "").strip()
        contato = request.form.get("contato", "").strip()
        endereco = request.form.get("endereco", "").strip()
        observacoes = request.form.get("observacoes", "").strip()

        if not nome or not cpf:
            flash("Informe o nome e o CPF/CNPJ.", "error")
        elif len(nome) > 200:
            flash("O nome do cliente deve ter no máximo 200 caracteres.", "error")
        elif len(cpf) > 20:
            flash("O CPF/CNPJ deve ter no máximo 20 caracteres.", "error")
        elif len(contato) > 100:
            flash("O contato deve ter no máximo 100 caracteres.", "error")
        elif len(endereco) > 300:
            flash("O endereço deve ter no máximo 300 caracteres.", "error")
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
            cliente.contato = contato
            cliente.endereco = endereco
            cliente.observacoes = observacoes

            db.session.add(cliente)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Já existe um cliente com este CPF/CNPJ.", "error")
            else:
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
        cliente=db.get_or_404(Cliente, pk),
    )


@clientes_bp.route("/<int:pk>/excluir/", methods=["GET", "POST"])
@login_required
def delete(pk):
    cliente = db.get_or_404(Cliente, pk)

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
