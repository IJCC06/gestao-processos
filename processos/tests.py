import os
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from config.settings import Config
from processos.extensions import db
from processos.models import Cliente, Movimentacao, Prazo, Processo, Usuario
from processos.services.movimentacoes import verificar_movimentacao_processo, verificar_movimentacoes


class FluxosPrincipaisTests(unittest.TestCase):
    TEST_PASSWORD_HASH = (
        "pbkdf2:sha256:1000$testsalt12345678$"
        "2ff4dfb6373dbfd4406002dd1983527ca84061feab36784fbec16a794e96372a"
    )

    @classmethod
    def setUpClass(cls):
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        from app import create_app

        cls.app = create_app()
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.remove()
            db.engine.dispose()

        os.environ.pop("DATABASE_URL", None)

    def setUp(self):
        self._perf_setup_start = time.perf_counter()
        self._perf_login_total = 0.0

        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

            usuario = Usuario(
                username="teste",
                password_hash=self.TEST_PASSWORD_HASH,
            )
            cliente = Cliente(nome="Cliente Teste", cpf_cnpj="12345678901")
            db.session.add_all([usuario, cliente])
            db.session.commit()

            processo = Processo(
                cliente=cliente,
                numero_cnj="0000000-00.2026.8.00.0000",
                area=Processo.Area.CIVEL,
                tribunal="Tribunal de Teste",
                tribunal_alias="tst",
            )
            db.session.add(processo)
            db.session.commit()

            self.usuario_id = usuario.id
            self.cliente_id = cliente.id
            self.processo_id = processo.id

        self.client = self.app.test_client()
        self._perf_setup_elapsed = time.perf_counter() - self._perf_setup_start
        self._perf_test_start = time.perf_counter()

    def tearDown(self):
        test_elapsed = time.perf_counter() - self._perf_test_start
        teardown_start = time.perf_counter()

        with self.app.app_context():
            db.session.remove()

        teardown_elapsed = time.perf_counter() - teardown_start
        print(
            f"[PERF] {self.id()} | "
            f"setUp={self._perf_setup_elapsed:.4f}s | "
            f"login={self._perf_login_total:.4f}s | "
            f"teste={test_elapsed:.4f}s | "
            f"tearDown={teardown_elapsed:.4f}s | "
            f"total={self._perf_setup_elapsed + test_elapsed + teardown_elapsed:.4f}s"
        )

    def login(self):
        start = time.perf_counter()
        resposta = self.client.post(
            "/login/",
            data={"username": "teste", "password": "senha-segura-123"},
            follow_redirects=False,
        )
        self._perf_login_total += time.perf_counter() - start
        return resposta

    def test_dashboard_exige_login(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.location)

    def test_dashboard_separa_prazos(self):
        with self.app.app_context():
            hoje = Config.local_date()
            processo = db.session.get(Processo, self.processo_id)
            db.session.add_all(
                [
                    Prazo(
                        processo=processo,
                        titulo="Vencido",
                        data_vencimento=hoje - timedelta(days=2),
                    ),
                    Prazo(
                        processo=processo,
                        titulo="Proximo",
                        data_vencimento=hoje + timedelta(days=2),
                    ),
                ]
            )
            db.session.commit()

        self.login()
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Vencido", resposta.data)
        self.assertIn(b"Proximo", resposta.data)
        self.assertIn(b"Prazos vencidos", resposta.data)
        self.assertIn(b"Prximos 7 dias", resposta.data)
        self.assertIn(b"Movimenta", resposta.data)

    def test_criacao_de_cliente(self):
        self.login()
        resposta = self.client.post(
            "/clientes/novo/",
            data={
                "nome": "Novo Cliente",
                "cpf_cnpj": "98765432100",
                "contato": "contato@example.com",
                "endereco": "Rua Teste",
                "observacoes": "Obs",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            cliente = Cliente.query.filter_by(cpf_cnpj="98765432100").first()
            self.assertIsNotNone(cliente)
            self.assertEqual(cliente.nome, "Novo Cliente")

    def test_criacao_de_cliente_exige_nome_e_cpf_cnpj(self):
        self.login()
        resposta = self.client.post(
            "/clientes/novo/",
            data={"nome": "", "cpf_cnpj": ""},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Informe o nome e o CPF/CNPJ.", resposta.data)

        with self.app.app_context():
            self.assertEqual(Cliente.query.count(), 1)

    def test_criacao_de_cliente_rejeita_cpf_cnpj_duplicado(self):
        self.login()
        resposta = self.client.post(
            "/clientes/novo/",
            data={"nome": "Outro Cliente", "cpf_cnpj": "12345678901"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"J\\xc3\\xa1 existe um cliente com este CPF/CNPJ.", resposta.data)

        with self.app.app_context():
            self.assertEqual(Cliente.query.count(), 1)

    def test_edicao_de_cliente(self):
        self.login()
        resposta = self.client.post(
            f"/clientes/{self.cliente_id}/editar/",
            data={
                "nome": "Cliente Atualizado",
                "cpf_cnpj": "12345678901",
                "contato": "novo-contato",
                "endereco": "Novo endereco",
                "observacoes": "Nova observacao",
            },
        )

        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            cliente = db.session.get(Cliente, self.cliente_id)
            self.assertEqual(cliente.nome, "Cliente Atualizado")
            self.assertEqual(cliente.contato, "novo-contato")
            self.assertEqual(cliente.endereco, "Novo endereco")
            self.assertEqual(cliente.observacoes, "Nova observacao")

    def test_edicao_de_cliente_rejeita_cpf_cnpj_de_outro_cliente(self):
        with self.app.app_context():
            outro = Cliente(nome="Outro Cliente", cpf_cnpj="98765432100")
            db.session.add(outro)
            db.session.commit()

        self.login()
        resposta = self.client.post(
            f"/clientes/{self.cliente_id}/editar/",
            data={
                "nome": "Cliente Atualizado",
                "cpf_cnpj": "98765432100",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe um cliente com este CPF/CNPJ.".encode("utf-8"), resposta.data)

        with self.app.app_context():
            cliente = db.session.get(Cliente, self.cliente_id)
            self.assertEqual(cliente.nome, "Cliente Teste")
            self.assertEqual(cliente.cpf_cnpj, "12345678901")

    def test_exclusao_de_cliente_sem_processos(self):
        with self.app.app_context():
            cliente = Cliente(nome="Cliente Excluir", cpf_cnpj="98765432100")
            db.session.add(cliente)
            db.session.commit()
            cliente_id = cliente.id

        self.login()
        resposta = self.client.post(f"/clientes/{cliente_id}/excluir/")

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/clientes/", resposta.location)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Cliente, cliente_id))

    def test_exclusao_de_cliente_com_processo_e_bloqueada(self):
        self.login()
        resposta = self.client.post(
            f"/clientes/{self.cliente_id}/excluir/",
            follow_redirects=True,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Existem processos vinculados.", resposta.data)

        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Cliente, self.cliente_id))
            self.assertIsNotNone(db.session.get(Processo, self.processo_id))

    def test_criacao_de_processo(self):
        self.login()
        resposta = self.client.post(
            "/processos/novo/",
            data={
                "cliente": self.cliente_id,
                "numero_cnj": "1111111-11.2026.8.00.0000",
                "area": Processo.Area.TRABALHISTA,
                "tribunal": "Tribunal de Teste",
                "tribunal_alias": "tst",
                "fase": "Inicial",
                "status": Processo.Status.ATIVO,
                "valor_causa": "1000.00",
                "honorarios": "100.00",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            self.assertIsNotNone(
                Processo.query.filter_by(
                    numero_cnj="1111111-11.2026.8.00.0000"
                ).first()
            )

    def test_busca_e_filtros_de_processos(self):
        with self.app.app_context():
            cliente = Cliente(nome="Maria de Souza", cpf_cnpj="98765432100")
            processo_suspenso = Processo(
                cliente=cliente,
                numero_cnj="1111111-11.2026.8.01.0001",
                area=Processo.Area.TRABALHISTA,
                tribunal="TRT da 2ª Região",
                tribunal_alias="trt2",
                status=Processo.Status.SUSPENSO,
            )
            processo_arquivado = Processo(
                cliente=cliente,
                numero_cnj="2222222-22.2026.8.02.0002",
                area=Processo.Area.PREVIDENCIARIO,
                tribunal="TRF da 3ª Região",
                tribunal_alias="trf3",
                status=Processo.Status.ARQUIVADO,
            )
            db.session.add_all([cliente, processo_suspenso, processo_arquivado])
            db.session.commit()

        self.login()

        resposta = self.client.get("/processos/", query_string={"q": "Maria de Souza"})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"1111111-11.2026.8.01.0001", resposta.data)
        self.assertIn(b"2222222-22.2026.8.02.0002", resposta.data)
        self.assertNotIn(b"0000000-00.2026.8.00.0000", resposta.data)

        resposta = self.client.get("/processos/", query_string={"q": "TRT da 2"})
        self.assertIn(b"1111111-11.2026.8.01.0001", resposta.data)
        self.assertNotIn(b"2222222-22.2026.8.02.0002", resposta.data)

        resposta = self.client.get("/processos/", query_string={"status": Processo.Status.SUSPENSO})
        self.assertIn(b"1111111-11.2026.8.01.0001", resposta.data)
        self.assertNotIn(b"0000000-00.2026.8.00.0000", resposta.data)

        resposta = self.client.get("/processos/", query_string={"area": Processo.Area.PREVIDENCIARIO})
        self.assertIn(b"2222222-22.2026.8.02.0002", resposta.data)
        self.assertNotIn(b"1111111-11.2026.8.01.0001", resposta.data)

        resposta = self.client.get(
            "/processos/",
            query_string={
                "q": "Maria",
                "status": Processo.Status.SUSPENSO,
                "area": Processo.Area.TRABALHISTA,
            },
        )
        self.assertIn(b"1111111-11.2026.8.01.0001", resposta.data)
        self.assertNotIn(b"2222222-22.2026.8.02.0002", resposta.data)

    def test_detalhes_do_processo_exibem_resumo_prazos_movimentacoes_e_alerta(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            processo.alerta_pendente = True
            processo.valor_causa = "1500.00"
            processo.honorarios = "150.00"

            prazo = Prazo(
                processo=processo,
                titulo="Manifestacao",
                data_vencimento=Config.local_date() + timedelta(days=5),
                status=Prazo.Status.PENDENTE,
            )
            movimento = Movimentacao(
                processo=processo,
                data=datetime.now(timezone.utc),
                descricao="Intimacao publicada",
                origem="datajud",
            )
            db.session.add_all([prazo, movimento])
            db.session.commit()

        self.login()
        resposta = self.client.get(f"/processos/{self.processo_id}/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Processo 0000000-00.2026.8.00.0000", resposta.data)
        self.assertIn(b"Cliente Teste", resposta.data)
        self.assertIn(b"Intima", resposta.data)
        self.assertIn(b"Manifest", resposta.data)
        self.assertIn(b"novas moviment", resposta.data)
        self.assertIn(b"5 dia(s) restante(s).", resposta.data)

    def test_criacao_de_prazo(self):
        self.login()
        resposta = self.client.post(
            "/prazos/novo/",
            data={
                "processo": self.processo_id,
                "titulo": "Prazo de manifestacao",
                "data_inicio": "2026-09-20",
                "data_vencimento": "2026-09-30",
                "status": Prazo.Status.PENDENTE,
                "observacoes": "",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            self.assertIsNotNone(
                Prazo.query.filter_by(titulo="Prazo de manifestacao").first()
            )

    def test_notificacoes_separam_prazos(self):
        with self.app.app_context():
            hoje = Config.local_date()
            processo = db.session.get(Processo, self.processo_id)
            db.session.add_all(
                [
                    Prazo(processo=processo, titulo="Vencido", data_vencimento=hoje - timedelta(days=1)),
                    Prazo(processo=processo, titulo="Proximo", data_vencimento=hoje + timedelta(days=3)),
                ]
            )
            db.session.commit()

        self.login()
        resposta = self.client.get("/notificacoes/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Vencido", resposta.data)
        self.assertIn(b"Proximo", resposta.data)

    def test_marcar_alerta_como_visto(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            processo.alerta_pendente = True
            db.session.commit()

        self.login()
        resposta = self.client.post(
            f"/notificacoes/processos/{self.processo_id}/limpar/"
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            self.assertFalse(processo.alerta_pendente)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_atualizacao_individual_datajud_cria_movimentacao(self, consultar):
        consultar.return_value = [{"dataHora": "2026-09-23T12:00:00Z", "nome": "Movimentacao individual"}]

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            resultado = verificar_movimentacao_processo(processo)
            db.session.commit()

            self.assertEqual(resultado["total_novas"], 1)
            self.assertIsNone(resultado["erro"])
            self.assertTrue(processo.alerta_pendente)
            self.assertEqual(Movimentacao.query.count(), 1)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_atualizacao_individual_datajud_retorna_erro(self, consultar):
        from processos.services.datajud import DataJudError

        consultar.side_effect = DataJudError("DataJud indisponivel")

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            resultado = verificar_movimentacao_processo(processo)

            self.assertEqual(resultado["total_novas"], 0)
            self.assertEqual(resultado["erro"], "DataJud indisponivel")
            self.assertEqual(Movimentacao.query.count(), 0)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_atualizacao_individual_datajud_exibe_mensagem_na_tela(self, consultar):
        consultar.return_value = []

        self.login()
        resposta = self.client.post(
            f"/processos/{self.processo_id}/atualizar-movimentacoes/",
            follow_redirects=True,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"0 movimenta", resposta.data)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_verificacao_datajud_cria_movimentacao_nova(self, consultar):
        consultar.return_value = [{"dataHora": "2026-09-23T12:00:00Z", "nome": "Movimentacao de teste"}]

        with self.app.app_context():
            resultado = verificar_movimentacoes()
            self.assertEqual(resultado["total_novas"], 1)
            self.assertEqual(Movimentacao.query.count(), 1)

            resultado = verificar_movimentacoes()
            self.assertEqual(resultado["total_novas"], 0)
            self.assertEqual(Movimentacao.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
