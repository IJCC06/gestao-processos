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
