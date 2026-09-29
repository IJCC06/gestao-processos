import logging
import os
from logging.handlers import RotatingFileHandler

import click
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from werkzeug.exceptions import HTTPException
from flask_wtf import CSRFProtect

from config.settings import Config
from processos.extensions import db, migrate
from processos.models import Usuario
from processos.services.auditoria import registrar_auditoria
from processos.services.movimentacoes import verificar_movimentacoes
from processos.routes import (
    auth_bp,
    clientes_bp,
    processos_bp,
    prazos_bp,
    notificacoes_bp,
    dashboard_bp,
    admin_bp,
    auditoria_bp,
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
    configure_logging(app)

    if os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    register_routes(app)
    register_error_handlers(app)
    register_blueprints(app)
    register_cli(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def configure_logging(app):
    log_file = app.config["LOG_FILE"]
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, app.config["LOG_LEVEL"], logging.INFO)
    app.logger.setLevel(level)

    if not any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == os.path.abspath(log_file)
        for handler in app.logger.handlers
    ):
        handler = RotatingFileHandler(
            log_file,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        app.logger.addHandler(handler)

    logging.getLogger("werkzeug").setLevel(level)



def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning("Acesso negado: caminho=%s", getattr(error, "description", "desconhecido"))
        return render_template(
            "errors/403.html",
            codigo=403,
            titulo="Acesso não autorizado",
            mensagem="Você não tem permissão para acessar esta página.",
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        app.logger.info("Página não encontrada: %s", getattr(error, "description", "desconhecido"))
        return render_template(
            "errors/404.html",
            codigo=404,
            titulo="Página não encontrada",
            mensagem="A página que você tentou acessar não existe ou foi removida.",
        ), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.exception("Erro interno não tratado na aplicação")
        db.session.rollback()
        return render_template(
            "errors/500.html",
            codigo=500,
            titulo="Erro interno",
            mensagem="Ocorreu um erro inesperado. Tente novamente. Se o problema persistir, verifique os logs do sistema.",
        ), 500


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
    app.register_blueprint(auditoria_bp)


def register_cli(app):
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
            registrar_auditoria("PERMISSAO", "Usuario", usuario.id, "Usuário promovido a administrador via CLI.")
            db.session.commit()
            click.echo(f"Usuário '{usuario.username}' agora é administrador.")

    @app.cli.command("backup-db")
    @click.option(
        "--retention-days",
        default=30,
        show_default=True,
        type=click.IntRange(min=1),
        help="Quantidade de dias de backups a manter.",
    )
    def backup_db_cli(retention_days):
        """Cria um backup consistente do banco SQLite."""
        from processos.services.backup import BackupError, backup_sqlite

        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if not database_uri.startswith("sqlite"):
            raise click.ClickException(
                "O backup local está configurado apenas para bancos SQLite."
            )

        database_path = db.engine.url.database
        backup_dir = os.environ.get(
            "BACKUP_DIR",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups"),
        )

        try:
            destino = backup_sqlite(
                database_path=database_path,
                backup_dir=backup_dir,
                retention_days=retention_days,
            )
        except BackupError as exc:
            raise click.ClickException(str(exc)) from exc

        click.echo(f"Backup criado com sucesso: {destino}")

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
