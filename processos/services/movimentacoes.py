from datetime import datetime

from processos.extensions import db
from processos.models import Movimentacao, Processo
from processos.services.datajud import DataJudError, consultar_movimentacoes


def verificar_movimentacoes():
    processos = Processo.query.filter(Processo.status != Processo.Status.ARQUIVADO).all()
    total_novas = 0
    erros = 0
    for processo in processos:
        if not processo.tribunal_alias:
            erros += 1
            continue
        try:
            movimentos = consultar_movimentacoes(processo.numero_cnj, processo.tribunal_alias)
        except DataJudError:
            erros += 1
            continue
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
            existente = Movimentacao.query.filter_by(processo_id=processo.id, data=data_hora, descricao=descricao, origem="datajud").first()
            if existente:
                continue
            db.session.add(Movimentacao(processo=processo, data=data_hora, descricao=descricao, origem="datajud"))
            novas += 1
        if novas:
            processo.alerta_pendente = True
            total_novas += novas
    db.session.commit()
    return {"total_processos": len(processos), "total_novas": total_novas, "erros": erros}
