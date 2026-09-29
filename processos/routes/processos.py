from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from processos.extensions import db
from processos.models import Cliente, Prazo, Processo
from processos.services.auditoria import registrar_auditoria
from processos.services.movimentacoes import verificar_movimentacao_processo

processos_bp = Blueprint("processos", __name__, url_prefix="/processos")


def normalizar_numero_cnj(valor):
    digitos = "".join(ch for ch in valor if ch.isdigit())
    if len(digitos) != 20:
        return None

    base = digitos[:7] + digitos[9:] + "0100"
    digito_verificador = 98 - (int(base) % 97)
    esperado = f"{digito_verificador:02d}"

    if digitos[7:9] != esperado:
        return None

    return (
        f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}."
        f"{digitos[13]}.{digitos[14:16]}.{digitos[16:]}"
    )


def decimal_positivo_ou_vazio(valor):
    if not valor:
        return None

    try:
        numero = Decimal(valor.replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValueError

    if numero < 0:
        raise ValueError

    return numero.quantize(Decimal("0.01"))


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
    processo = db.session.get(Processo, pk)
    if processo is None:
        abort(404)
    return form(processo)


def form(processo=None):
    clientes = Cliente.query.order_by(Cliente.nome).all()
    valores = None

    if request.method == "POST":
        valores = {
            "cliente": request.form.get("cliente", ""),
            "numero_cnj": request.form.get("numero_cnj", "").strip(),
            "area": request.form.get("area", "").strip(),
            "tribunal": request.form.get("tribunal", "").strip(),
            "tribunal_alias": request.form.get("tribunal_alias", "").strip(),
            "fase": request.form.get("fase", "").strip(),
            "status": request.form.get("status", "").strip(),
            "valor_causa": request.form.get("valor_causa", "").strip(),
            "honorarios": request.form.get("honorarios", "").strip(),
        }

        cliente = db.session.get(Cliente, request.form.get("cliente", type=int))
        numero_cnj = normalizar_numero_cnj(valores["numero_cnj"])

        try:
            valor_causa = decimal_positivo_ou_vazio(valores["valor_causa"])
            honorarios = decimal_positivo_ou_vazio(valores["honorarios"])
            valores_financeiros_validos = True
        except ValueError:
            valor_causa = honorarios = None
            valores_financeiros_validos = False

        numero_duplicado = (
            numero_cnj
            and Processo.query.filter(
                Processo.numero_cnj == numero_cnj,
                Processo.id != (processo.id if processo else 0),
            ).first()
        )

        if not cliente or not valores["numero_cnj"]:
            flash("Informe o cliente e o número do processo.", "error")
        elif not numero_cnj:
            flash("Informe um número CNJ válido.", "error")
        elif numero_duplicado:
            flash("Já existe um processo com este número CNJ.", "error")
        elif valores["area"] not in Processo.Area.values():
            flash("Selecione uma área válida.", "error")
        elif valores["status"] not in Processo.Status.values():
            flash("Selecione um status válido.", "error")
        elif not valores_financeiros_validos:
            flash("Informe valores financeiros válidos e não negativos.", "error")
        elif len(valores["tribunal"]) > 150:
            flash("O tribunal deve ter no máximo 150 caracteres.", "error")
        elif len(valores["tribunal_alias"]) > 20:
            flash("O alias DataJud deve ter no máximo 20 caracteres.", "error")
        elif len(valores["fase"]) > 100:
            flash("A fase deve ter no máximo 100 caracteres.", "error")
        elif valores_financeiros_validos and (
            valor_causa is not None and valor_causa > Decimal("9999999999.99")
            or honorarios is not None and honorarios > Decimal("9999999999.99")
        ):
            flash("Os valores financeiros excedem o limite permitido.", "error")
        else:
            if processo is None:
                processo = Processo()

            processo.cliente = cliente
            processo.numero_cnj = numero_cnj
            processo.area = valores["area"]
            processo.tribunal = valores["tribunal"]
            processo.tribunal_alias = valores["tribunal_alias"]
            processo.fase = valores["fase"]
            processo.status = valores["status"]
            processo.valor_causa = valor_causa
            processo.honorarios = honorarios

            db.session.add(processo)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Já existe um processo com este número CNJ.", "error")
            else:
                registrar_auditoria("ALTERAR" if processo.id else "CRIAR", "Processo", processo.id, f"Processo salvo: {processo.numero_cnj}.")
                db.session.commit()
                flash("Processo salvo com sucesso.", "success")
                return redirect(url_for("processos.detail", pk=processo.id))

    return render_template(
        "processos/processos/form.html",
        titulo="Editar processo" if processo else "Novo processo",
        processo=processo,
        clientes=clientes,
        valores=valores,
    )


@processos_bp.route("/<int:pk>/excluir/", methods=["GET", "POST"])
@login_required
def delete(pk):
    processo = db.session.get(Processo, pk)
    if processo is None:
        abort(404)

    if request.method == "POST":
        processo_id = processo.id
        numero_cnj = processo.numero_cnj
        db.session.delete(processo)
        db.session.commit()
        registrar_auditoria("EXCLUIR", "Processo", processo_id, f"Processo excluído: {numero_cnj}.")
        db.session.commit()
        flash("Processo excluído com sucesso.", "success")
        return redirect(url_for("processos.list"))

    return render_template(
        "processos/processos/delete.html",
        processo=processo,
    )


@processos_bp.post("/<int:pk>/atualizar-movimentacoes/")
@login_required
def atualizar_movimentacoes(pk):
    processo = db.session.get(Processo, pk)
    if processo is None:
        abort(404)
    resultado = verificar_movimentacao_processo(processo)

    if resultado["erro"]:
        db.session.rollback()
        flash(
            f"Não foi possível atualizar o processo: {resultado['erro']}",
            "error",
        )
    else:
        db.session.commit()
        registrar_auditoria("DATAJUD", "Processo", processo.id, f"Consulta DataJud: {resultado["total_novas"]} nova(s) movimentação(ões).")
        db.session.commit()
        flash(
            f"Consulta concluída: {resultado['total_novas']} "
            "movimentação(ões) nova(s) encontrada(s).",
            "success",
        )

    return redirect(url_for("processos.detail", pk=processo.id))


@processos_bp.get("/<int:pk>/")
@login_required
def detail(pk):
    processo = db.session.get(Processo, pk)
    if processo is None:
        abort(404)
    return render_template(
        "processos/processos/detail.html",
        processo=processo,
        prazos_pendentes=[
            prazo
            for prazo in processo.prazos
            if prazo.status == Prazo.Status.PENDENTE
        ],
    )
