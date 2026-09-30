"""Integração com a API Pública do DataJud (CNJ)."""

import logging
import os
import time

import requests

BASE_URL = "https://api-publica.datajud.cnj.jus.br"
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 20

logger = logging.getLogger(__name__)


class DataJudError(Exception):
    """Erro controlado ao consultar a API do DataJud."""


def _api_key() -> str:
    api_key = os.environ.get("DATAJUD_API_KEY", "").strip()
    if not api_key:
        logger.error("DataJud sem API key configurada.")
        raise DataJudError(
            "DATAJUD_API_KEY não configurada. Defina a chave no arquivo .env."
        )
    return api_key


def _mensagem_status_http(status_code: int) -> str:
    if status_code in (401, 403):
        return (
            "O DataJud recusou a autenticação. "
            "Verifique a DATAJUD_API_KEY configurada."
        )
    if status_code == 429:
        return (
            "O DataJud limitou temporariamente as consultas. "
            "Tente novamente mais tarde."
        )
    if 500 <= status_code <= 599:
        return (
            f"O DataJud está indisponível no momento (HTTP {status_code}). "
            "Tente novamente mais tarde."
        )
    return f"O DataJud retornou HTTP {status_code}."


def consultar_movimentacoes(numero_cnj: str, tribunal_alias: str) -> list[dict]:
    if not tribunal_alias:
        raise DataJudError("tribunal_alias não informado para este processo")

    numero_limpo = "".join(filter(str.isdigit, numero_cnj))
    if len(numero_limpo) != 20:
        raise DataJudError("número CNJ inválido ou vazio")

    url = f"{BASE_URL}/api_publica_{tribunal_alias.lower()}/_search"
    headers = {
        "Authorization": f"APIKey {_api_key()}",
        "Content-Type": "application/json",
    }
    body = {"query": {"match": {"numeroProcesso": numero_limpo}}}

    inicio = time.perf_counter()

    try:
        resposta = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
    except requests.Timeout as exc:
        duracao = time.perf_counter() - inicio
        logger.warning(
            "Timeout ao consultar DataJud: alias=%s cnj_final=%s duracao=%.2fs",
            tribunal_alias,
            numero_limpo[-4:],
            duracao,
        )
        raise DataJudError(
            "O DataJud demorou demais para responder. Tente novamente."
        ) from exc
    except requests.ConnectionError as exc:
        duracao = time.perf_counter() - inicio
        logger.warning(
            "Falha de conexão com DataJud: alias=%s cnj_final=%s duracao=%.2fs",
            tribunal_alias,
            numero_limpo[-4:],
            duracao,
        )
        raise DataJudError(
            "Não foi possível conectar ao DataJud. Verifique a conexão e tente novamente."
        ) from exc
    except requests.RequestException as exc:
        duracao = time.perf_counter() - inicio
        logger.exception(
            "Falha inesperada de comunicação com DataJud: alias=%s cnj_final=%s duracao=%.2fs",
            tribunal_alias,
            numero_limpo[-4:],
            duracao,
        )
        raise DataJudError("Falha de comunicação com o DataJud. Tente novamente.") from exc

    duracao = time.perf_counter() - inicio
    logger.info(
        "Resposta do DataJud: alias=%s status=%s duracao=%.2fs",
        tribunal_alias,
        resposta.status_code,
        duracao,
    )

    if resposta.status_code >= 400:
        logger.warning("DataJud retornou HTTP %s: alias=%s cnj_final=%s", resposta.status_code, tribunal_alias, numero_limpo[-4:])
        raise DataJudError(_mensagem_status_http(resposta.status_code))

    try:
        dados = resposta.json()
    except ValueError as exc:
        logger.error("DataJud retornou JSON inválido: alias=%s cnj_final=%s", tribunal_alias, numero_limpo[-4:])
        raise DataJudError("O DataJud retornou uma resposta JSON inválida.") from exc

    if not isinstance(dados, dict):
        raise DataJudError("O DataJud retornou uma resposta em formato inválido.")

    hits_container = dados.get("hits")
    if not isinstance(hits_container, dict):
        raise DataJudError("Resposta do DataJud sem a estrutura esperada de resultados.")

    hits = hits_container.get("hits", [])
    if not isinstance(hits, list):
        raise DataJudError("Resposta do DataJud contém resultados em formato inválido.")

    if not hits:
        return []

    primeiro_hit = hits[0]
    if not isinstance(primeiro_hit, dict):
        raise DataJudError("Resposta do DataJud contém um resultado em formato inválido.")

    source = primeiro_hit.get("_source", {})
    if not isinstance(source, dict):
        raise DataJudError("Resposta do DataJud contém dados do processo em formato inválido.")

    movimentos = source.get("movimentos", [])
    if not isinstance(movimentos, list):
        raise DataJudError(
            "Resposta do DataJud contém movimentações em formato inválido."
        )

    return sorted(
        (movimento for movimento in movimentos if isinstance(movimento, dict)),
        key=lambda movimento: movimento.get("dataHora", ""),
    )
