import os
import unittest
from unittest.mock import Mock, patch

from processos.services.datajud import (
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
    DataJudError,
    consultar_movimentacoes,
)


class DataJudServiceTests(unittest.TestCase):
    def setUp(self):
        self.api_key_anterior = os.environ.get("DATAJUD_API_KEY")
        os.environ["DATAJUD_API_KEY"] = "chave-de-teste"

    def tearDown(self):
        if self.api_key_anterior is None:
            os.environ.pop("DATAJUD_API_KEY", None)
        else:
            os.environ["DATAJUD_API_KEY"] = self.api_key_anterior

    @patch("processos.services.datajud.requests.post")
    def test_timeout_retorna_erro_amigavel(self, post):
        import requests

        post.side_effect = requests.Timeout()

        with self.assertRaisesRegex(DataJudError, "demorou demais"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

        post.assert_called_once()
        self.assertEqual(
            post.call_args.kwargs["timeout"],
            (CONNECT_TIMEOUT, READ_TIMEOUT),
        )

    @patch("processos.services.datajud.requests.post")
    def test_erro_de_conexao_retorna_erro_amigavel(self, post):
        import requests

        post.side_effect = requests.ConnectionError()

        with self.assertRaisesRegex(DataJudError, "Não foi possível conectar"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

    @patch("processos.services.datajud.requests.post")
    def test_http_401_identifica_problema_de_autenticacao(self, post):
        resposta = Mock(status_code=401)
        post.return_value = resposta

        with self.assertRaisesRegex(DataJudError, "recusou a autenticação"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

    @patch("processos.services.datajud.requests.post")
    def test_http_429_informa_limite_temporario(self, post):
        resposta = Mock(status_code=429)
        post.return_value = resposta

        with self.assertRaisesRegex(DataJudError, "limitou temporariamente"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

    @patch("processos.services.datajud.requests.post")
    def test_http_500_informa_indisponibilidade(self, post):
        resposta = Mock(status_code=503)
        post.return_value = resposta

        with self.assertRaisesRegex(DataJudError, "indisponível no momento"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

    @patch("processos.services.datajud.requests.post")
    def test_json_invalido_retorna_erro_controlado(self, post):
        resposta = Mock(status_code=200)
        resposta.json.side_effect = ValueError()
        post.return_value = resposta

        with self.assertRaisesRegex(DataJudError, "JSON inválida"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

    @patch("processos.services.datajud.requests.post")
    def test_resposta_sem_estrutura_esperada_retorna_erro(self, post):
        resposta = Mock(status_code=200)
        resposta.json.return_value = {"resultado": []}
        post.return_value = resposta

        with self.assertRaisesRegex(DataJudError, "estrutura esperada"):
            consultar_movimentacoes(
                "0000000-49.2026.8.00.0000",
                "tst",
            )

    @patch("processos.services.datajud.requests.post")
    def test_resposta_valida_sem_movimentacoes_retorna_lista_vazia(self, post):
        resposta = Mock(status_code=200)
        resposta.json.return_value = {"hits": {"hits": []}}
        post.return_value = resposta

        resultado = consultar_movimentacoes(
            "0000000-49.2026.8.00.0000",
            "tst",
        )

        self.assertEqual(resultado, [])

    def test_numero_cnj_invalido_nao_faz_requisicao(self):
        with patch("processos.services.datajud.requests.post") as post:
            with self.assertRaisesRegex(DataJudError, "número CNJ inválido"):
                consultar_movimentacoes("123", "tst")

            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
