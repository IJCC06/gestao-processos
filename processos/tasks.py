from celery import shared_task

from processos.services.movimentacoes import verificar_movimentacoes


@shared_task
def verificar_movimentacoes_datajud():
    """Executa a verificação periódica de movimentações no DataJud."""
    return verificar_movimentacoes()
