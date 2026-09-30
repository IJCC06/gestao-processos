from __future__ import annotations

import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from processos.extensions import db
from processos.models import Usuario
from processos.services.auditoria import registrar_auditoria


setup_bp = Blueprint("setup", __name__, url_prefix="/configuracao-inicial")


def _setup_needed() -> bool:
    return db.session.scalar(db.select(Usuario.id).limit(1)) is None


@setup_bp.route("/", methods=["GET", "POST"])
def inicial():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if not _setup_needed():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("password", "")
        confirmacao = request.form.get("password_confirmation", "")
        datajud_key = request.form.get("datajud_api_key", "").strip()

        if len(username) < 3:
            flash("O nome de usuário deve ter pelo menos 3 caracteres.", "error")
        elif len(senha) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.", "error")
        elif senha != confirmacao:
            flash("As senhas não coincidem.", "error")
        elif not datajud_key:
            flash("Informe a chave da API DataJud para concluir a configuração.", "error")
        else:
            usuario = Usuario(
                username=username,
                is_admin=True,
                is_active=True,
            )
            usuario.set_password(senha)
            db.session.add(usuario)
            db.session.commit()
            registrar_auditoria(
                "CRIAR",
                "Usuario",
                usuario.id,
                "Primeiro administrador criado na configuração inicial.",
            )
            db.session.commit()

            if datajud_key:
                os.environ["DATAJUD_API_KEY"] = datajud_key
                from config.settings import DATA_DIR

                DATA_DIR.mkdir(parents=True, exist_ok=True)
                env_file = DATA_DIR / ".env"
                env_file.write_text(
                    f"FLASK_SECRET_KEY={os.environ.get('FLASK_SECRET_KEY', '')}\n"
                    "FLASK_DEBUG=False\n"
                    f"DATAJUD_API_KEY={datajud_key}\n"
                    "DATABASE_URL=sqlite:///flask.db\n",
                    encoding="utf-8",
                )

            flash("Configuração inicial concluída. Entre com sua conta.", "success")
            return redirect(url_for("auth.login"))

    return render_template("setup/inicial.html")
