import os
import time
import unittest
from datetime import timedelta
from unittest.mock import patch

from app import create_app
from config.settings import Config
from processos.extensions import db
from processos.models import Cliente, Movimentacao, Prazo, Processo, Usuario
from processos.services.movimentacoes import verificar_movimentacoes


class FluxosPrincipaisTests(unittest.TestCase):
    # O banco em memória evita I/O em disco e a criação de arquivos temporários.
    # O hash abaixo é exclusivo dos testes e usa poucas iterações para acelerar
    # login/check_password sem alterar o hash usado pela aplicação em produção.
    TEST_PASSWORD_HASH = (
        "pbkdf2:sha256:1000$testsalt12345678$"
        "2ff4dfb6373dbfd4406002dd1983527ca84061feab36784fbec16a794e96372a"
    )

    @classmethod
    def setUpClass(cls):
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
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
            self.assertIsNotNone(
                Cliente.query.filter_by(cpf_cnpj="98765432100").first()
            )

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

    def test_criacao_de_prazo(self):
        self.login()
        resposta = self.client.post(
            "/prazos/novo/",
            data={
                "processo": self.processo_id,
                "titulo": "Prazo de manifestação",
                "data_inicio": "2026-09-20",
                "data_vencimento": "2026-09-30",
                "status": Prazo.Status.PENDENTE,
                "observacoes": "",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            self.assertIsNotNone(
                Prazo.query.filter_by(titulo="Prazo de manifestação").first()
            )

    def test_notificacoes_separam_prazos(self):
        with self.app.app_context():
            hoje = Config.local_date()
            processo = db.session.get(Processo, self.processo_id)
            db.session.add_all(
                [
                    Prazo(
                        processo=processo,
                        titulo="Vencido",
                        data_vencimento=hoje - timedelta(days=1),
                    ),
                    Prazo(
                        processo=processo,
                        titulo="Proximo",
                        data_vencimento=hoje + timedelta(days=3),
                    ),
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
    def test_verificacao_datajud_cria_movimentacao_nova(self, consultar):
        consultar.return_value = [
            {
                "dataHora": "2026-09-23T12:00:00Z",
                "nome": "Movimentação de teste",
            }
        ]

        with self.app.app_context():
            resultado = verificar_movimentacoes()
            self.assertEqual(resultado["total_novas"], 1)
            self.assertEqual(Movimentacao.query.count(), 1)

            resultado = verificar_movimentacoes()
            self.assertEqual(resultado["total_novas"], 0)
            self.assertEqual(Movimentacao.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
