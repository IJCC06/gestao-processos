"""Rotinas reutilizáveis de monitoramento de movimentações do DataJud."""

from datetime import datetime

from django.utils.timezone import is_naive, make_aware

from processos.models import Movimentacao, Processo
from processos.services.datajud import DataJudError, consultar_movimentacoes


def verificar_movimentacoes():
    """Consulta processos e registra somente movimentações novas.

    Retorna um resumo para uso pelo comando Django e pelo Celery.
    """
    processos = Processo.objects.exclude(status=Processo.Status.ARQUIVADO)
    total_processos = processos.count()
    total_novas = 0
    erros = 0
    avisos = []

    for processo in processos:
        if not processo.tribunal_alias:
            avisos.append(
                f"[{processo.numero_cnj}] sem tribunal_alias cadastrado — pulando"
            )
            continue

        try:
            movimentos = consultar_movimentacoes(
                processo.numero_cnj, processo.tribunal_alias
            )
        except DataJudError as exc:
            erros += 1
            avisos.append(f"[{processo.numero_cnj}] {exc}")
            continue

        novas = 0
        for mov in movimentos:
            data_hora_str = mov.get("dataHora")
            if not data_hora_str:
                continue

            try:
                data_hora = datetime.fromisoformat(
                    data_hora_str.replace("Z", "+00:00")
                )
            except ValueError:
                avisos.append(
                    f"[{processo.numero_cnj}] movimentação com data inválida — pulando"
                )
                continue

            if is_naive(data_hora):
                data_hora = make_aware(data_hora)

            descricao = mov.get("nome") or "Movimentação sem descrição"

            if Movimentacao.objects.filter(
                processo=processo,
                data=data_hora,
                descricao=descricao,
                origem="datajud",
            ).exists():
                continue

            Movimentacao.objects.create(
                processo=processo,
                data=data_hora,
                descricao=descricao,
                origem="datajud",
            )
            novas += 1

        if novas:
            processo.alerta_pendente = True
            processo.save(update_fields=["alerta_pendente"])
            total_novas += novas

    return {
        "total_processos": total_processos,
        "total_novas": total_novas,
        "erros": erros,
        "avisos": avisos,
    }
