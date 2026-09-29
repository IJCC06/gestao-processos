from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from processos.extensions import db
from processos.models import Usuario
from processos.services.auditoria import registrar_auditoria

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
                registrar_auditoria("LOGIN", "Usuario", usuario.id, "Login realizado.")
                db.session.commit()
                next_url = _safe_next_url(request.args.get("next"))
                return redirect(next_url or url_for("dashboard.index"))

        if not usuario or not senha_valida:
            flash("Usuário ou senha inválidos.", "error")

    return render_template("registration/login.html")


@auth_bp.route("/cadastro/", methods=["GET", "POST"])
def cadastro():
    flash("A criação de usuários é feita exclusivamente por um administrador.", "error")
    return redirect(url_for("auth.login"))


@auth_bp.post("/logout/")
@login_required
def logout():
    registrar_auditoria("LOGOUT", "Usuario", current_user.id, "Logout realizado.")
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))
