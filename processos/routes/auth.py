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
        import time

        perf_start = time.perf_counter()
        perf_usuario_start = time.perf_counter()
        usuario = Usuario.query.filter_by(
            username=request.form.get("username", "").strip()
        ).first()
        perf_usuario = time.perf_counter() - perf_usuario_start

        if usuario:
            perf_senha_start = time.perf_counter()
            senha_valida = usuario.check_password(request.form.get("password", ""))
            perf_senha = time.perf_counter() - perf_senha_start
        else:
            senha_valida = False
            perf_senha = 0.0

        if usuario and senha_valida:
            perf_login_user_start = time.perf_counter()
            login_user(usuario)
            perf_login_user = time.perf_counter() - perf_login_user_start

            perf_movimentacoes_start = time.perf_counter()
            resultado = verificar_movimentacoes()
            perf_movimentacoes = time.perf_counter() - perf_movimentacoes_start
            print(
                f"[PERF-LOGIN] usuario={perf_usuario:.4f}s | "
                f"senha={perf_senha:.4f}s | "
                f"login_user={perf_login_user:.4f}s | "
                f"movimentacoes={perf_movimentacoes:.4f}s | "
                f"total={time.perf_counter() - perf_start:.4f}s"
            )
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
