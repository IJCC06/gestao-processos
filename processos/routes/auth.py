from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from processos.models import Usuario
from processos.services.movimentacoes import verificar_movimentacoes

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        usuario = Usuario.query.filter_by(
            username=request.form.get("username", "").strip()
        ).first()

        if usuario and usuario.check_password(request.form.get("password", "")):
            login_user(usuario)

            resultado = verificar_movimentacoes()
            if resultado["erros"]:
                flash(
                    f"Consulta de movimentações concluída com "
                    f"{resultado['erros']} ocorrência(s) de erro ou configuração ausente.",
                    "warning",
                )
            elif resultado["total_processos"]:
                flash(
                    f"Consulta concluída: {resultado['total_novas']} "
                    f"movimentação(ões) nova(s) encontrada(s) em "
                    f"{resultado['total_processos']} processo(s).",
                    "success",
                )

            return redirect(
                request.args.get("next") or url_for("dashboard.index")
            )

        flash("Usuário ou senha inválidos.", "error")

    return render_template("registration/login.html")


@auth_bp.post("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
