from celery import Celery

celery = Celery("gestao_processos")
celery.conf.beat_schedule = {
    "verificar-movimentacoes-datajud-a-cada-30-minutos": {
        "task": "processos.tasks.verificar_movimentacoes_datajud",
        "schedule": 1800,
    }
}
