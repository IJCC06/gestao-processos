"""
Integração com a API Pública do DataJud (CNJ).

Documentação oficial: https://datajud-wiki.cnj.jus.br/
Endpoint por tribunal: https://api-publica.datajud.cnj.jus.br/api_publica_{alias}/_search
Autenticação: header "Authorization: APIKey <chave>" — a chave abaixo é a
chave pública oficial divulgada pelo CNJ (a mesma para todos os usuários).
Ela pode ser trocada pelo CNJ a qualquer momento; se parar de funcionar,
busque a chave atualizada em https://datajud-wiki.cnj.jus.br/.
"""
import os

import requests

BASE_URL = "https://api-publica.datajud.cnj.jus.br"
DEFAULT_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="


class DataJudError(Exception):
    """Erro ao consultar a API do DataJud."""


def _api_key() -> str:
    return os.environ.get("DATAJUD_API_KEY", DEFAULT_API_KEY)


def consultar_movimentacoes(numero_cnj: str, tribunal_alias: str) -> list[dict]:
    """
    Consulta o DataJud pelo número CNJ de um processo em um tribunal específico.

    Retorna uma lista de movimentações, cada uma com "codigo", "nome" e "dataHora",
    ordenada da mais antiga para a mais recente. Levanta DataJudError em caso de
    falha de rede ou resposta inesperada.
    """
    if not tribunal_alias:
        raise DataJudError("tribunal_alias não informado para este processo")

    numero_limpo = "".join(filter(str.isdigit, numero_cnj))
    url = f"{BASE_URL}/api_publica_{tribunal_alias.lower()}/_search"
    headers = {
        "Authorization": f"APIKey {_api_key()}",
        "Content-Type": "application/json",
    }
    body = {"query": {"match": {"numeroProcesso": numero_limpo}}}

    try:
        resposta = requests.post(url, json=body, headers=headers, timeout=20)
        resposta.raise_for_status()
    except requests.RequestException as exc:
        raise DataJudError(f"Falha ao consultar o DataJud: {exc}") from exc

    dados = resposta.json()
    hits = dados.get("hits", {}).get("hits", [])
    if not hits:
        return []

    movimentos = hits[0].get("_source", {}).get("movimentos", [])
    movimentos_ordenados = sorted(movimentos, key=lambda m: m.get("dataHora", ""))
    return movimentos_ordenados
