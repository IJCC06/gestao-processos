from .auth import auth_bp
from .clientes import clientes_bp
from .processos import processos_bp
from .prazos import prazos_bp
from .notificacoes import notificacoes_bp

__all__ = [
    "auth_bp",
    "clientes_bp",
    "processos_bp",
    "prazos_bp",
    "notificacoes_bp",
]
