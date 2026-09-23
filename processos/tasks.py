from celery import shared_task

from processos.services.movimentacoes import verificar_movimentacoes


@shared_task(name="processos.tasks.verificar_movimentacoes_datajud")
def verificar_movimentacoes_datajud():
    return verificar_movimentacoes()
