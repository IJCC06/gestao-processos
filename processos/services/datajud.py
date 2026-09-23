"""Integração com a API Pública do DataJud (CNJ)."""

import os

import requests

BASE_URL = "https://api-publica.datajud.cnj.jus.br"


class DataJudError(Exception):
    """Erro ao consultar a API do DataJud."""


def _api_key() -> str:
    api_key = os.environ.get("DATAJUD_API_KEY", "").strip()
    if not api_key:
        raise DataJudError(
            "DATAJUD_API_KEY não configurada. Defina a chave no arquivo .env."
        )
    return api_key


def consultar_movimentacoes(numero_cnj: str, tribunal_alias: str) -> list[dict]:
    if not tribunal_alias:
        raise DataJudError("tribunal_alias não informado para este processo")

    numero_limpo = "".join(filter(str.isdigit, numero_cnj))
    if not numero_limpo:
        raise DataJudError("número CNJ inválido ou vazio")

    url = f"{BASE_URL}/api_publica_{tribunal_alias.lower()}/_search"
    headers = {
        "Authorization": f"APIKey {_api_key()}",
        "Content-Type": "application/json",
    }
    body = {"query": {"match": {"numeroProcesso": numero_limpo}}}

    try:
        resposta = requests.post(url, json=body, headers=headers, timeout=20)
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.RequestException as exc:
        raise DataJudError(f"Falha ao consultar o DataJud: {exc}") from exc
    except ValueError as exc:
        raise DataJudError("O DataJud retornou uma resposta JSON inválida") from exc

    hits = dados.get("hits", {}).get("hits", [])
    if not hits:
        return []

    movimentos = hits[0].get("_source", {}).get("movimentos", [])
    if not isinstance(movimentos, list):
        raise DataJudError("Resposta do DataJud contém movimentações em formato inválido")

    return sorted(movimentos, key=lambda m: m.get("dataHora", ""))
