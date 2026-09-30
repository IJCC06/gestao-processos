from .auth import auth_bp
from .clientes import clientes_bp
from .processos import processos_bp
from .prazos import prazos_bp
from .notificacoes import notificacoes_bp
from .dashboard import dashboard_bp
from .admin import admin_bp
from .auditoria import auditoria_bp
from .sistema import sistema_bp
from .setup import setup_bp

__all__ = [
    "auth_bp",
    "clientes_bp",
    "processos_bp",
    "prazos_bp",
    "notificacoes_bp",
    "dashboard_bp",
    "admin_bp",
    "auditoria_bp",
    "sistema_bp",
    "setup_bp",
]
