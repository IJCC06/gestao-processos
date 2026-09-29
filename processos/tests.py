import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app import create_app
from config.settings import Config
from processos.extensions import db
from processos.models import Cliente, Movimentacao, Prazo, Processo, Usuario
from processos.services.movimentacoes import verificar_movimentacoes


class FluxosPrincipaisTests(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_file.close()
        os.environ["DATABASE_URL"] = "sqlite:///" + self.db_file.name.replace("\\", "/")
        self.app = create_app()
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.usuario = Usuario(username="teste")
            self.usuario.set_password("senha-segura-123")
            self.cliente = Cliente(nome="Cliente Teste", cpf_cnpj="12345678901")
            db.session.add_all([self.usuario, self.cliente])
            db.session.commit()
            self.processo = Processo(cliente=self.cliente, numero_cnj="0000000-00.2026.8.00.0000", area=Processo.Area.CIVEL, tribunal="Tribunal de Teste", tribunal_alias="tst")
            db.session.add(self.processo)
            db.session.commit()
            self.usuario_id = self.usuario.id
            self.cliente_id = self.cliente.id
            self.processo_id = self.processo_id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.remove()
        os.unlink(self.db_file.name)
        os.environ.pop("DATABASE_URL", None)

    def login(self):
        return self.client.post("/login/", data={"username":"teste", "password":"senha-segura-123"}, follow_redirects=False)

    def test_dashboard_exige_login(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.location)

    def test_dashboard_separa_prazos(self):
        with self.app.app_context():
            hoje=Config.local_date()
            db.session.add_all([Prazo(processo=self.processo,titulo="Vencido",data_vencimento=hoje-timedelta(days=2)),Prazo(processo=self.processo,titulo="Proximo",data_vencimento=hoje+timedelta(days=2))])
            db.session.commit()
        self.login()
        resposta=self.client.get("/")
        self.assertEqual(resposta.status_code,200)
        self.assertIn(b"Vencido",resposta.data)
        self.assertIn(b"Proximo",resposta.data)

    def test_criacao_de_cliente(self):
        self.login()
        resposta=self.client.post("/clientes/novo/",data={"nome":"Novo Cliente","cpf_cnpj":"98765432100","contato":"contato@example.com","endereco":"Rua Teste","observacoes":"Obs"})
        self.assertEqual(resposta.status_code,302)
        with self.app.app_context(): self.assertIsNotNone(Cliente.query.filter_by(cpf_cnpj="98765432100").first())

    def test_criacao_de_processo(self):
        self.login()
        resposta=self.client.post("/processos/novo/",data={"cliente":self.cliente_id,"numero_cnj":"1111111-11.2026.8.00.0000","area":Processo.Area.TRABALHISTA,"tribunal":"Tribunal de Teste","tribunal_alias":"tst","fase":"Inicial","status":Processo.Status.ATIVO,"valor_causa":"1000.00","honorarios":"100.00"})
        self.assertEqual(resposta.status_code,302)
        with self.app.app_context(): self.assertIsNotNone(Processo.query.filter_by(numero_cnj="1111111-11.2026.8.00.0000").first())

    def test_criacao_de_prazo(self):
        self.login()
        resposta=self.client.post("/prazos/novo/",data={"processo":self.processo.id,"titulo":"Prazo de manifestação","data_inicio":"2026-09-20","data_vencimento":"2026-09-30","status":Prazo.Status.PENDENTE,"observacoes":""})
        self.assertEqual(resposta.status_code,302)
        with self.app.app_context(): self.assertIsNotNone(Prazo.query.filter_by(titulo="Prazo de manifestação").first())

    def test_notificacoes_separam_prazos(self):
        with self.app.app_context():
            hoje=Config.local_date()
            db.session.add_all([Prazo(processo=self.processo,titulo="Vencido",data_vencimento=hoje-timedelta(days=1)),Prazo(processo=self.processo,titulo="Proximo",data_vencimento=hoje+timedelta(days=3))])
            db.session.commit()
        self.login()
        resposta=self.client.get("/notificacoes/")
        self.assertEqual(resposta.status_code,200)
        self.assertIn(b"Vencido",resposta.data)
        self.assertIn(b"Proximo",resposta.data)

    def test_marcar_alerta_como_visto(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            processo.alerta_pendente=True
            db.session.commit()
        self.login()
        resposta=self.client.post(f"/notificacoes/processos/{self.processo.id}/limpar/")
        self.assertEqual(resposta.status_code,302)
        with self.app.app_context(): self.assertFalse(db.session.get(Processo,self.processo.id).alerta_pendente)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_verificacao_datajud_cria_movimentacao_nova(self, consultar):
        consultar.return_value=[{"dataHora":"2026-09-23T12:00:00Z","nome":"Movimentação de teste"}]
        with self.app.app_context():
            resultado=verificar_movimentacoes()
            self.assertEqual(resultado["total_novas"],1)
            self.assertEqual(Movimentacao.query.count(),1)
            resultado=verificar_movimentacoes()
            self.assertEqual(resultado["total_novas"],0)
            self.assertEqual(Movimentacao.query.count(),1)


if __name__ == "__main__":
    unittest.main()
