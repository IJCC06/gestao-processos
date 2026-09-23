from datetime import datetime

from django.utils.timezone import is_naive, make_aware

from processos.models import Movimentacao, Processo
from processos.services.datajud import DataJudError, consultar_movimentacoes


def verificar_movimentacoes() -> dict:
    """Consulta o DataJud e registra apenas movimentações novas."""
    processos = Processo.objects.exclude(status=Processo.Status.ARQUIVADO)
    total_processos = processos.count()
    total_novas = 0
    erros = 0

    for processo in processos:
        if not processo.tribunal_alias:
            erros += 1
            continue

        try:
            movimentos = consultar_movimentacoes(
                processo.numero_cnj, processo.tribunal_alias
            )
        except DataJudError:
            erros += 1
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
    }
