from celery import Celery


def create_celery():
    from app import create_app
    flask_app=create_app()
    celery=Celery("gestao_processos", broker=flask_app.config["CELERY_BROKER_URL"])
    celery.conf.update(timezone=flask_app.config["CELERY_TIMEZONE"])
    celery.conf.beat_schedule={"verificar-movimentacoes-datajud-a-cada-30-minutos":{"task":"processos.tasks.verificar_movimentacoes_datajud","schedule":1800}}
    return celery, flask_app

celery, flask_app=create_celery()
