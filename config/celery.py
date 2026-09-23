import os
from celery import Celery

celery = Celery("gestao_processos", broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"))
celery.conf.timezone = "America/Sao_Paulo"
celery.conf.imports = ("processos.tasks",)
celery.conf.beat_schedule = {
    "verificar-movimentacoes-datajud-a-cada-30-minutos": {
        "task": "processos.tasks.verificar_movimentacoes_datajud",
        "schedule": 1800,
    }
}
