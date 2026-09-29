from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from processos.extensions import db
from processos.models import Cliente, Movimentacao, Prazo, Processo, Usuario
from processos.services.auditoria import registrar_auditoria

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@admin_bp.get("/")
@admin_required
def index():
    usuarios = Usuario.query.order_by(Usuario.id.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        total_usuarios=Usuario.query.count(),
        usuarios_ativos=Usuario.query.filter_by(is_active=True).count(),
        usuarios_admin=Usuario.query.filter_by(is_admin=True).count(),
        total_clientes=Cliente.query.count(),
        total_processos=Processo.query.count(),
        processos_ativos=Processo.query.filter_by(status=Processo.Status.ATIVO).count(),
        prazos_pendentes=Prazo.query.filter_by(status=Prazo.Status.PENDENTE).count(),
        alertas_pendentes=Processo.query.filter_by(alerta_pendente=True).count(),
        datajud_configurado=bool(__import__("os").environ.get("DATAJUD_API_KEY", "").strip()),
        usuarios_recentes=usuarios,
    )


@admin_bp.get("/usuarios/")
@admin_required
def usuarios():
    busca = request.args.get("q", "").strip()
    consulta = Usuario.query
    if busca:
        consulta = consulta.filter(Usuario.username.ilike(f"%{busca}%"))
    lista = consulta.order_by(Usuario.username.asc()).all()
    return render_template("admin/usuarios.html", usuarios=lista, busca=busca)


@admin_bp.route("/usuarios/novo/", methods=["GET", "POST"])
@admin_required
def criar_usuario():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirmation = request.form.get("password_confirmation", "")
    is_admin = request.form.get("is_admin") == "1"

    if request.method == "POST":
        if not username:
            flash("Informe um nome de usuário.", "error")
        elif len(username) < 3:
            flash("O nome de usuário deve ter pelo menos 3 caracteres.", "error")
        elif len(username) > 150:
            flash("O nome de usuário deve ter no máximo 150 caracteres.", "error")
        elif Usuario.query.filter_by(username=username).first():
            flash("Este nome de usuário já está em uso.", "error")
        elif len(password) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.", "error")
        elif password != password_confirmation:
            flash("As senhas não coincidem.", "error")
        else:
            usuario = Usuario(
                username=username,
                is_admin=is_admin,
                is_active=True,
            )
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            registrar_auditoria("CRIAR", "Usuario", usuario.id, f"Usuário criado: {usuario.username}. Administrador: {usuario.is_admin}.")
            db.session.commit()
            flash("Usuário criado com sucesso.", "success")
            return redirect(url_for("admin.usuarios"))

    return render_template(
        "admin/usuario_form.html",
        usuario=None,
        username=username,
        is_admin=is_admin,
    )


@admin_bp.post("/usuarios/<int:pk>/alternar-status/")
@admin_required
def alternar_status(pk):
    usuario = db.session.get(Usuario, pk)
    if usuario is None:
        abort(404)

    if usuario.id == current_user.id and usuario.is_active:
        flash("Você não pode desativar a própria conta.", "error")
        return redirect(url_for("admin.usuarios"))

    usuario.is_active = not usuario.is_active
    db.session.commit()
    estado = "ativado" if usuario.is_active else "desativado"
    registrar_auditoria("STATUS", "Usuario", usuario.id, f"Conta {estado}.")
    db.session.commit()
    flash(f"Usuário {estado} com sucesso.", "success")
    return redirect(url_for("admin.usuarios"))


@admin_bp.route("/usuarios/<int:pk>/senha/", methods=["GET", "POST"])
@admin_required
def redefinir_senha(pk):
    usuario = db.session.get(Usuario, pk)
    if usuario is None:
        abort(404)

    password = request.form.get("password", "")
    password_confirmation = request.form.get("password_confirmation", "")

    if request.method == "POST":
        if len(password) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.", "error")
        elif password != password_confirmation:
            flash("As senhas não coincidem.", "error")
        else:
            usuario.set_password(password)
            db.session.commit()
            registrar_auditoria("ALTERAR", "Usuario", usuario.id, "Senha redefinida por administrador.")
            db.session.commit()
            flash("Senha redefinida com sucesso.", "success")
            return redirect(url_for("admin.usuarios"))

    return render_template("admin/senha_form.html", usuario=usuario)


@admin_bp.post("/usuarios/<int:pk>/alternar-admin/")
@admin_required
def alternar_admin(pk):
    usuario = db.session.get(Usuario, pk)
    if usuario is None:
        abort(404)

    if usuario.id == current_user.id and usuario.is_admin:
        flash("Você não pode remover a própria permissão de administrador.", "error")
        return redirect(url_for("admin.usuarios"))

    if usuario.is_admin:
        usuario.is_admin = False
        mensagem = "Permissão de administrador removida."
    else:
        usuario.is_admin = True
        mensagem = "Permissão de administrador concedida."

    db.session.commit()
    registrar_auditoria("PERMISSAO", "Usuario", usuario.id, mensagem)
    db.session.commit()
    flash(mensagem, "success")
    return redirect(url_for("admin.usuarios"))
