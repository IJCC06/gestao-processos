from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from processos.extensions import db
from processos.models import Usuario\nfrom processos.services.auditoria import registrar_auditoria

auth_bp = Blueprint("auth", __name__)


def _safe_next_url(next_url):
    if not next_url:
        return None

    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc or next_url.startswith("//"):
        return None

    if not next_url.startswith("/"):
        return None

    return next_url


@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        usuario = Usuario.query.filter_by(
            username=request.form.get("username", "").strip()
        ).first()

        senha_valida = (
            usuario.check_password(request.form.get("password", ""))
            if usuario
            else False
        )

        if usuario and senha_valida:
            if not usuario.is_active:
                flash("Esta conta está desativada. Procure um administrador.", "error")
            else:
                login_user(usuario)
                next_url = _safe_next_url(request.args.get("next"))
                return redirect(next_url or url_for("dashboard.index"))

        if not usuario or not senha_valida:
            flash("Usuário ou senha inválidos.", "error")

    return render_template("registration/login.html")


@auth_bp.route("/cadastro/", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirmation = request.form.get("password_confirmation", "")

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
            usuario = Usuario(username=username, is_active=True, is_admin=False)
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            flash("Cadastro realizado com sucesso. Agora entre com sua conta.", "success")
            return redirect(url_for("auth.login"))

    return render_template(
        "registration/cadastro.html",
        username=username,
    )


@auth_bp.post("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
