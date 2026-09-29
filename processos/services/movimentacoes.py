from datetime import datetime
import time

from processos.extensions import db
from processos.models import Movimentacao, Processo
from processos.services.datajud import DataJudError, consultar_movimentacoes


def verificar_movimentacao_processo(processo):
    """Consulta um processo no DataJud e grava apenas movimentações novas."""
    if not processo.tribunal_alias:
        return {"total_novas": 0, "erro": "Tribunal/alias DataJud não configurado."}

    try:
        movimentos = consultar_movimentacoes(
            processo.numero_cnj, processo.tribunal_alias
        )
    except DataJudError as exc:
        return {"total_novas": 0, "erro": str(exc)}

    novas = 0
    for mov in movimentos:
        data_hora_str = mov.get("dataHora")
        if not data_hora_str:
            continue

        try:
            data_hora = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        descricao = mov.get("nome") or "Movimentação sem descrição"
        existente = Movimentacao.query.filter_by(
            processo_id=processo.id,
            data=data_hora,
            descricao=descricao,
            origem="datajud",
        ).first()
        if existente:
            continue

        db.session.add(
            Movimentacao(
                processo=processo,
                data=data_hora,
                descricao=descricao,
                origem="datajud",
                lida=False,
            )
        )
        novas += 1

    if novas:
        processo.alerta_pendente = True

    return {"total_novas": novas, "erro": None}


def verificar_movimentacoes():
    perf_start = time.perf_counter()
    processos = Processo.query.filter(
        Processo.status != Processo.Status.ARQUIVADO
    ).all()
    perf_busca_processos = time.perf_counter() - perf_start

    total_novas = 0
    erros = 0
    print(
        f"[PERF-MOV] processos={len(processos)} | "
        f"busca_processos={perf_busca_processos:.4f}s"
    )

    for processo in processos:
        perf_processo_start = time.perf_counter()
        resultado = verificar_movimentacao_processo(processo)

        if resultado["erro"]:
            erros += 1
            print(
                f"[PERF-MOV] processo_id={processo.id} | "
                f"consulta=erro | tempo={time.perf_counter() - perf_processo_start:.4f}s"
            )
            continue

        novas = resultado["total_novas"]
        total_novas += novas
        print(
            f"[PERF-MOV] processo_id={processo.id} | "
            f"consulta/processamento={time.perf_counter() - perf_processo_start:.4f}s | "
            f"novas={novas}"
        )

    perf_commit_start = time.perf_counter()
    db.session.commit()
    perf_commit = time.perf_counter() - perf_commit_start

    print(
        f"[PERF-MOV] commit={perf_commit:.4f}s | "
        f"total={time.perf_counter() - perf_start:.4f}s"
    )

    return {
        "total_processos": len(processos),
        "total_novas": total_novas,
        "erros": erros,
    }
