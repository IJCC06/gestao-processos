from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from processos.extensions import db
from processos.models import Cliente

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


def normalizar_cpf_cnpj(valor):
    return "".join(ch for ch in valor if ch.isdigit())


def documento_valido(valor):
    if len(valor) not in (11, 14) or len(set(valor)) == 1:
        return False

    if len(valor) == 11:
        soma = sum(int(valor[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        digito1 = 0 if digito1 == 10 else digito1

        soma = sum(int(valor[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        digito2 = 0 if digito2 == 10 else digito2

        return valor[-2:] == f"{digito1}{digito2}"

    soma = sum(int(valor[i]) * (5 - i if i < 4 else 13 - i) for i in range(12))
    digito1 = 0 if (soma % 11) < 2 else 11 - (soma % 11)

    soma = sum(int(valor[i]) * (6 - i if i < 5 else 14 - i) for i in range(13))
    digito2 = 0 if (soma % 11) < 2 else 11 - (soma % 11)

    return valor[-2:] == f"{digito1}{digito2}"


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
    valores = None

    if request.method == "POST":
        valores = {
            "nome": request.form.get("nome", "").strip(),
            "cpf_cnpj": request.form.get("cpf_cnpj", "").strip(),
            "contato": request.form.get("contato", "").strip(),
            "endereco": request.form.get("endereco", "").strip(),
            "observacoes": request.form.get("observacoes", "").strip(),
        }

        nome = valores["nome"]
        cpf = normalizar_cpf_cnpj(valores["cpf_cnpj"])
        contato = valores["contato"]
        endereco = valores["endereco"]
        observacoes = valores["observacoes"]

        if not nome or not valores["cpf_cnpj"]:
            flash("Informe o nome e o CPF/CNPJ.", "error")
        elif len(nome) > 200:
            flash("O nome do cliente deve ter no máximo 200 caracteres.", "error")
        elif len(cpf) not in (11, 14):
            flash("Informe um CPF ou CNPJ válido.", "error")
        elif not documento_valido(cpf):
            flash("Informe um CPF ou CNPJ válido.", "error")
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
        valores=valores,
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
