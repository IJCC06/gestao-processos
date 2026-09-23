from celery import shared_task


@shared_task(name="processos.tasks.verificar_movimentacoes_datajud")
def verificar_movimentacoes_datajud():
    from app import create_app
    from processos.services.movimentacoes import verificar_movimentacoes
    app = create_app()
    with app.app_context():
        return verificar_movimentacoes()
