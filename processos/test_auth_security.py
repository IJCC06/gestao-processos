import os
import unittest

from processos.extensions import db
from processos.models import Usuario


class AuthSecurityTests(unittest.TestCase):
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
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

            usuario = Usuario(username="teste")
            usuario.set_password("senha-segura-123")
            db.session.add(usuario)
            db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def test_login_redireciona_para_proxima_url_interna(self):
        resposta = self.client.post(
            "/login/?next=/processos/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.location, "/processos/")

    def test_login_ignora_proxima_url_externa(self):
        resposta = self.client.post(
            "/login/?next=https://exemplo.com/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.location, "/")

    def test_login_ignora_redirecionamento_com_duas_barras(self):
        resposta = self.client.post(
            "/login/?next=//exemplo.com/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.location, "/")

    def test_post_sem_csrf_e_rejeitado(self):
        self.app.config["WTF_CSRF_ENABLED"] = True

        resposta = self.client.post(
            "/login/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )

        self.assertEqual(resposta.status_code, 400)
        self.app.config["WTF_CSRF_ENABLED"] = False

    def test_post_de_exclusao_sem_csrf_e_rejeitado(self):
        from processos.models import Cliente

        self.app.config["WTF_CSRF_ENABLED"] = False
        with self.app.app_context():
            cliente = Cliente(
                nome="Cliente CSRF",
                cpf_cnpj="52998224725",
            )
            db.session.add(cliente)
            db.session.commit()
            cliente_id = cliente.id

        resposta = self.client.post(
            "/login/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        self.app.config["WTF_CSRF_ENABLED"] = True
        resposta = self.client.post(f"/clientes/{cliente_id}/excluir/")

        self.assertEqual(resposta.status_code, 400)
        self.app.config["WTF_CSRF_ENABLED"] = False

        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Cliente, cliente_id))

    def test_cookie_de_sessao_tem_protecoes_basicas(self):
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")

    def test_debug_fica_desabilitado_por_padrao(self):
        self.assertFalse(self.app.config["DEBUG"])

    def test_rotas_protegidas_exigem_login(self):
        rotas = [
            "/",
            "/clientes/",
            "/clientes/novo/",
            "/processos/",
            "/processos/novo/",
            "/prazos/",
            "/prazos/novo/",
            "/notificacoes/",
        ]

        for rota in rotas:
            with self.subTest(rota=rota):
                resposta = self.client.get(rota)
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("/login/", resposta.location)

    def test_logout_exige_login(self):
        resposta = self.client.post("/logout/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.location)

    def test_logout_remove_a_sessao_autenticada(self):
        self.app.config["WTF_CSRF_ENABLED"] = False
        resposta = self.client.post(
            "/login/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        resposta = self.client.post("/logout/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.location)

        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.location)
