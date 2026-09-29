import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager, current_user
from flask_wtf import CSRFProtect

from config.settings import Config
from processos.extensions import db, migrate
from processos.models import Usuario
from processos.services.movimentacoes import verificar_movimentacoes
from processos.routes import (
    auth_bp,
    clientes_bp,
    processos_bp,
    prazos_bp,
    notificacoes_bp,
    dashboard_bp,
    admin_bp,
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
    Config.validate_security()

    if os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

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


def register_blueprints(app):
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(processos_bp)
    app.register_blueprint(prazos_bp)
    app.register_blueprint(notificacoes_bp)
    app.register_blueprint(admin_bp)


def register_cli(app):
    @app.cli.command("migrar-usuarios")
    def migrar_usuarios_cli():
        """Adiciona as colunas de administração à tabela de usuários existente."""
        import click
        from sqlalchemy import inspect, text

        if not db.engine.url.drivername.startswith("sqlite"):
            click.echo("Migração automática disponível apenas para SQLite.")
            return

        with app.app_context():
            colunas = {col["name"] for col in inspect(db.engine).get_columns("usuario")}
            with db.engine.begin() as conexao:
                if "is_admin" not in colunas:
                    conexao.execute(
                        text("ALTER TABLE usuario ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
                    )
                    click.echo("Coluna is_admin adicionada.")
                if "is_active" not in colunas:
                    conexao.execute(
                        text("ALTER TABLE usuario ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
                    )
                    click.echo("Coluna is_active adicionada.")
            click.echo("Migração de usuários concluída.")

    @app.cli.command("tornar-admin")
    def tornar_admin_cli():
        """Concede permissão de administrador a um usuário existente."""
        import click

        username = click.prompt("Nome de usuário")
        with app.app_context():
            usuario = Usuario.query.filter_by(username=username.strip()).first()
            if usuario is None:
                click.echo("Usuário não encontrado.")
                return
            usuario.is_admin = True
            usuario.is_active = True
            db.session.commit()
            click.echo(f"Usuário '{usuario.username}' agora é administrador.")

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
