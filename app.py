import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, flash, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from flask_wtf import CSRFProtect

from config.settings import Config
from processos.extensions import db
from processos.models import Movimentacao, Prazo, Processo, Cliente, Usuario
from processos.services.movimentacoes import verificar_movimentacoes
from processos.routes import (
    auth_bp,
    clientes_bp,
    processos_bp,
    prazos_bp,
    notificacoes_bp,
)

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Entre com sua conta para acessar o sistema."
csrf = CSRFProtect()


def create_app():
    app = Flask(
        __name__,
        template_folder="processos/templates",
        static_folder="processos/static",
    )
    app.config.from_object(Config)

    if os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    register_blueprints(app)
    register_cli(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def register_routes(app):
    @app.context_processor
    def inject_helpers():
        return {"current_user": current_user}

    @app.get("/")
    @login_required
    def dashboard():
        hoje = Config.local_date()
        prazos = Prazo.query.filter_by(
            status=Prazo.Status.PENDENTE
        ).all()

        prazos_vencidos = sorted(
            [p for p in prazos if p.data_vencimento < hoje],
            key=lambda p: (p.data_vencimento, p.titulo),
        )
        prazos_proximos = sorted(
            [
                p
                for p in prazos
                if hoje <= p.data_vencimento <= hoje + timedelta(days=7)
            ],
            key=lambda p: (p.data_vencimento, p.titulo),
        )

        return render_template(
            "processos/dashboard.html",
            total_clientes=Cliente.query.count(),
            total_processos=Processo.query.count(),
            processos_ativos=Processo.query.filter_by(
                status=Processo.Status.ATIVO
            ).count(),
            alertas_pendentes=Processo.query.filter_by(
                alerta_pendente=True
            ).count(),
            prazos_vencidos=prazos_vencidos,
            prazos_proximos=prazos_proximos,
            ultimas_movimentacoes=Movimentacao.query.order_by(
                Movimentacao.data.desc()
            ).limit(10).all(),
        )


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(processos_bp)
    app.register_blueprint(prazos_bp)
    app.register_blueprint(notificacoes_bp)


def register_cli(app):
    @app.cli.command("verificar-movimentacoes")
    def verificar_movimentacoes_cli():
        resultado = verificar_movimentacoes()
        print(
            f"Verificação concluída: {resultado['total_processos']} "
            f"processo(s) checado(s), {resultado['total_novas']} "
            f"movimentação(ões) nova(s), {resultado['erros']} "
            f"ocorrência(s) com erro ou configuração ausente."
        )


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
