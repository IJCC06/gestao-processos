import os
import time
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from config.settings import Config
from processos.extensions import db
from processos.models import Auditoria, Cliente, Movimentacao, Prazo, Processo, Usuario
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
            cliente = Cliente(nome="Cliente Teste", cpf_cnpj="52998224725")
            db.session.add_all([usuario, cliente])
            db.session.commit()

            processo = Processo(
                cliente=cliente,
                numero_cnj="0000000-49.2026.8.00.0000",
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

    def test_cadastro_publico_esta_bloqueado(self):
        resposta = self.client.get("/cadastro/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login/", resposta.location)

    def test_cadastro_publico_nao_cria_usuario(self):
        resposta = self.client.post(
            "/cadastro/",
            data={
                "username": "novo-usuario",
                "password": "senha-segura-123",
                "password_confirmation": "senha-segura-123",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(Usuario.query.filter_by(username="novo-usuario").first())

    def _get_cliente(self):
        return db.session.get(Cliente, self.cliente_id)

    def _get_processo(self):
        return db.session.get(Processo, self.processo_id)

    def test_paginacao_das_listagens_preserva_filtros(self):
        with self.app.app_context():
            clientes = [
                Cliente(nome=f"Cliente {i:02d}", cpf_cnpj=f"{10000000000 + i}")
                for i in range(40)
            ]
            db.session.add_all(clientes)

            processos = [
                Processo(
                    cliente=self._get_cliente(),
                    numero_cnj=f"{i + 1000000:07d}-49.2026.8.00.{i:04d}",
                    area=Processo.Area.CIVEL,
                    tribunal="Tribunal de Teste",
                    tribunal_alias="tst",
                )
                for i in range(20)
            ]
            db.session.add_all(processos)

            prazos = [
                Prazo(
                    processo=self._get_processo(),
                    titulo=f"Prazo {i:02d}",
                    data_vencimento=date(2026, 10, 1) + timedelta(days=i),
                    status=Prazo.Status.PENDENTE,
                )
                for i in range(40)
            ]
            db.session.add_all(prazos)
            db.session.commit()

        self.login()

        resposta = self.client.get("/clientes/?page=2")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Cliente 20", resposta.data)
        self.assertIn(b"Cliente 39", resposta.data)
        self.assertNotIn(b"Cliente 19", resposta.data)

        resposta = self.client.get(
            "/processos/",
            query_string={"q": "Tribunal de Teste", "page": 2},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"processo(s) encontrado(s)", resposta.data)
        self.assertIn(b"Tribunal de Teste", resposta.data)

        resposta = self.client.get(
            "/prazos/",
            query_string={"status": Prazo.Status.PENDENTE, "page": 2},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Prazo 20", resposta.data)
        self.assertIn(b"Prazo 39", resposta.data)
        self.assertNotIn(b"Prazo 19", resposta.data)

    def test_criacao_de_cliente(self):
        self.login()
        resposta = self.client.post(
            "/clientes/novo/",
            data={
                "nome": "Novo Cliente",
                "cpf_cnpj": "111.444.777-35",
                "contato": "contato@example.com",
                "endereco": "Rua Teste",
                "observacoes": "Obs",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            cliente = Cliente.query.filter_by(cpf_cnpj="11144477735").first()
            self.assertIsNotNone(cliente)
            self.assertEqual(cliente.nome, "Novo Cliente")

    def test_criacao_de_cliente_rejeita_documento_invalido(self):
        self.login()
        resposta = self.client.post(
            "/clientes/novo/",
            data={"nome": "Cliente Inválido", "cpf_cnpj": "123.456.789-00"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Informe um CPF ou CNPJ válido.".encode("utf-8"), resposta.data)

        with self.app.app_context():
            self.assertEqual(Cliente.query.count(), 1)

    def test_edicao_de_cliente_preserva_dados_digitados_em_erro(self):
        self.login()
        resposta = self.client.post(
            f"/clientes/{self.cliente_id}/editar/",
            data={
                "nome": "Nome Digitado",
                "cpf_cnpj": "123.456.789-00",
                "contato": "Contato Digitado",
                "endereco": "Endereco Digitado",
                "observacoes": "Observacao Digitada",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Nome Digitado", resposta.data)
        self.assertIn(b"123.456.789-00", resposta.data)
        self.assertIn(b"Contato Digitado", resposta.data)
        self.assertIn(b"Endereco Digitado", resposta.data)
        self.assertIn(b"Observacao Digitada", resposta.data)

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
            data={"nome": "Outro Cliente", "cpf_cnpj": "52998224725"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe um cliente com este CPF/CNPJ.".encode("utf-8"), resposta.data)

        with self.app.app_context():
            self.assertEqual(Cliente.query.count(), 1)

    def test_edicao_de_cliente(self):
        self.login()
        resposta = self.client.post(
            f"/clientes/{self.cliente_id}/editar/",
            data={
                "nome": "Cliente Atualizado",
                "cpf_cnpj": "52998224725",
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
            outro = Cliente(nome="Outro Cliente", cpf_cnpj="11144477735")
            db.session.add(outro)
            db.session.commit()

        self.login()
        resposta = self.client.post(
            f"/clientes/{self.cliente_id}/editar/",
            data={
                "nome": "Cliente Atualizado",
                "cpf_cnpj": "11144477735",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe um cliente com este CPF/CNPJ.".encode("utf-8"), resposta.data)

        with self.app.app_context():
            cliente = db.session.get(Cliente, self.cliente_id)
            self.assertEqual(cliente.nome, "Cliente Teste")
            self.assertEqual(cliente.cpf_cnpj, "52998224725")

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

    def test_lista_de_processos_exibe_dados_e_filtros(self):
        self.login()

        resposta = self.client.get("/processos/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"0000000-49.2026.8.00.0000", resposta.data)
        self.assertIn(b"Cliente Teste", resposta.data)
        self.assertIn(b"Novo processo", resposta.data)

        resposta = self.client.get(
            "/processos/",
            query_string={"q": "CNJ que nao existe"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Nenhum processo encontrado.", resposta.data)

        resposta = self.client.get(
            "/processos/",
            query_string={"status": Processo.Status.ATIVO},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"0000000-49.2026.8.00.0000", resposta.data)

    def test_criacao_de_processo(self):
        self.login()
        resposta = self.client.post(
            "/processos/novo/",
            data={
                "cliente": self.cliente_id,
                "numero_cnj": "1111111-62.2026.8.00.0000",
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
                    numero_cnj="1111111-62.2026.8.00.0000"
                ).first()
            )

    def test_busca_e_filtros_de_processos(self):
        with self.app.app_context():
            cliente = Cliente(nome="Maria de Souza", cpf_cnpj="98765432100")
            processo_suspenso = Processo(
                cliente=cliente,
                numero_cnj="1111111-69.2026.8.01.0001",
                area=Processo.Area.TRABALHISTA,
                tribunal="TRT da 2ª Região",
                tribunal_alias="trt2",
                status=Processo.Status.SUSPENSO,
            )
            processo_arquivado = Processo(
                cliente=cliente,
                numero_cnj="2222222-89.2026.8.02.0002",
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
        self.assertIn(b"1111111-69.2026.8.01.0001", resposta.data)
        self.assertIn(b"2222222-89.2026.8.02.0002", resposta.data)
        self.assertNotIn(b"0000000-49.2026.8.00.0000", resposta.data)

        resposta = self.client.get("/processos/", query_string={"q": "TRT da 2"})
        self.assertIn(b"1111111-69.2026.8.01.0001", resposta.data)
        self.assertNotIn(b"2222222-89.2026.8.02.0002", resposta.data)

        resposta = self.client.get("/processos/", query_string={"status": Processo.Status.SUSPENSO})
        self.assertIn(b"1111111-69.2026.8.01.0001", resposta.data)
        self.assertNotIn(b"0000000-49.2026.8.00.0000", resposta.data)

        resposta = self.client.get("/processos/", query_string={"area": Processo.Area.PREVIDENCIARIO})
        self.assertIn(b"2222222-89.2026.8.02.0002", resposta.data)
        self.assertNotIn(b"1111111-69.2026.8.01.0001", resposta.data)

        resposta = self.client.get(
            "/processos/",
            query_string={
                "q": "Maria",
                "status": Processo.Status.SUSPENSO,
                "area": Processo.Area.TRABALHISTA,
            },
        )
        self.assertIn(b"1111111-69.2026.8.01.0001", resposta.data)
        self.assertNotIn(b"2222222-89.2026.8.02.0002", resposta.data)

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
        self.assertIn(b"Processo 0000000-49.2026.8.00.0000", resposta.data)
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

    def test_crud_completo_de_prazo(self):
        self.login()

        resposta = self.client.get("/prazos/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Prazos", resposta.data)

        resposta = self.client.post(
            "/prazos/novo/",
            data={
                "processo": self.processo_id,
                "titulo": "Prazo inicial",
                "data_inicio": "2026-09-20",
                "data_vencimento": "2026-09-30",
                "status": Prazo.Status.PENDENTE,
                "observacoes": "Observacao inicial",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        prazo_id = int(resposta.location.rstrip("/").split("/")[-1])

        resposta = self.client.get(f"/prazos/{prazo_id}/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Prazo inicial", resposta.data)
        self.assertIn(b"Observacao inicial", resposta.data)

        resposta = self.client.post(
            f"/prazos/{prazo_id}/editar/",
            data={
                "processo": self.processo_id,
                "titulo": "Prazo atualizado",
                "data_inicio": "2026-09-21",
                "data_vencimento": "2026-10-05",
                "status": Prazo.Status.CONCLUIDO,
                "observacoes": "Observacao atualizada",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            prazo = db.session.get(Prazo, prazo_id)
            self.assertEqual(prazo.titulo, "Prazo atualizado")
            self.assertEqual(prazo.data_vencimento.isoformat(), "2026-10-05")
            self.assertEqual(prazo.status, Prazo.Status.CONCLUIDO)
            self.assertEqual(prazo.observacoes, "Observacao atualizada")

        resposta = self.client.get(f"/prazos/{prazo_id}/editar/")
        self.assertEqual(resposta.status_code, 200)

        resposta = self.client.get(f"/prazos/{prazo_id}/excluir/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Confirmar exclusão".encode("utf-8"), resposta.data)

        resposta = self.client.post(f"/prazos/{prazo_id}/excluir/", follow_redirects=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Prazo exclu", resposta.data)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Prazo, prazo_id))

    def test_criacao_de_prazo_rejeita_datas_e_status_invalidos(self):
        self.login()

        resposta = self.client.post(
            "/prazos/novo/",
            data={
                "processo": self.processo_id,
                "titulo": "Prazo invalido",
                "data_inicio": "2026-10-01",
                "data_vencimento": "2026-09-30",
                "status": Prazo.Status.PENDENTE,
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("não pode ser anterior".encode("utf-8"), resposta.data)

        resposta = self.client.post(
            "/prazos/novo/",
            data={
                "processo": self.processo_id,
                "titulo": "Prazo com status invalido",
                "data_vencimento": "2026-09-30",
                "status": "inexistente",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Selecione um status válido.".encode("utf-8"), resposta.data)

        with self.app.app_context():
            self.assertEqual(Prazo.query.count(), 0)

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


    def test_criacao_de_processo_rejeita_numero_cnj_invalido(self):
        self.login()
        resposta = self.client.post(
            "/processos/novo/",
            data={
                "cliente": self.cliente_id,
                "numero_cnj": "0000000-00.2026.8.00.0000",
                "area": Processo.Area.CIVEL,
                "tribunal": "Tribunal de Teste",
                "status": Processo.Status.ATIVO,
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Informe um n", resposta.data)

        with self.app.app_context():
            self.assertEqual(Processo.query.count(), 1)

    def test_criacao_de_processo_rejeita_area_status_e_valor_invalidos(self):
        self.login()
        base = {
            "cliente": self.cliente_id,
            "numero_cnj": "3333333-88.2026.8.00.0000",
            "area": "inexistente",
            "tribunal": "Tribunal de Teste",
            "status": "inexistente",
        }

        resposta = self.client.post("/processos/novo/", data=base)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Selecione uma", resposta.data)

        base["area"] = Processo.Area.CIVEL
        base["status"] = Processo.Status.ATIVO
        base["valor_causa"] = "-10.00"
        resposta = self.client.post("/processos/novo/", data=base)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"valores financeiros", resposta.data)

        with self.app.app_context():
            self.assertEqual(Processo.query.count(), 1)

    def test_edicao_de_processo_preserva_dados_digitados_em_erro(self):
        self.login()
        resposta = self.client.post(
            f"/processos/{self.processo_id}/editar/",
            data={
                "cliente": self.cliente_id,
                "numero_cnj": "9999999-99.2026.8.00.0000",
                "area": "invalida",
                "tribunal": "Tribunal Digitado",
                "tribunal_alias": "alias-digitado",
                "fase": "Fase Digitada",
                "status": Processo.Status.ATIVO,
                "valor_causa": "1234.56",
                "honorarios": "123.45",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"9999999-99.2026.8.00.0000", resposta.data)
        self.assertIn(b"Tribunal Digitado", resposta.data)
        self.assertIn(b"alias-digitado", resposta.data)
        self.assertIn(b"Fase Digitada", resposta.data)
        self.assertIn(b"1234.56", resposta.data)

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            self.assertEqual(processo.numero_cnj, "0000000-49.2026.8.00.0000")

    def test_edicao_de_processo_atualiza_dados(self):
        self.login()
        resposta = self.client.post(
            f"/processos/{self.processo_id}/editar/",
            data={
                "cliente": self.cliente_id,
                "numero_cnj": "3333333-88.2026.8.00.0000",
                "area": Processo.Area.TRABALHISTA,
                "tribunal": "TRT de Teste",
                "tribunal_alias": "trt1",
                "fase": "Recursal",
                "status": Processo.Status.SUSPENSO,
                "valor_causa": "2500.50",
                "honorarios": "250.00",
            },
        )

        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            self.assertEqual(processo.numero_cnj, "3333333-88.2026.8.00.0000")
            self.assertEqual(processo.area, Processo.Area.TRABALHISTA)
            self.assertEqual(processo.status, Processo.Status.SUSPENSO)
            self.assertEqual(str(processo.valor_causa), "2500.50")
            self.assertEqual(str(processo.honorarios), "250.00")

    def test_criacao_de_processo_rejeita_cnj_duplicado(self):
        self.login()
        resposta = self.client.post(
            "/processos/novo/",
            data={
                "cliente": self.cliente_id,
                "numero_cnj": "0000000-49.2026.8.00.0000",
                "area": Processo.Area.CIVEL,
                "tribunal": "Outro Tribunal",
                "status": Processo.Status.ATIVO,
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe um processo com este número CNJ.".encode("utf-8"), resposta.data)

        with self.app.app_context():
            self.assertEqual(Processo.query.count(), 1)

    def test_exclusao_de_processo_exibe_confirmacao(self):
        self.login()
        resposta = self.client.get(f"/processos/{self.processo_id}/excluir/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Confirmar exclusão".encode("utf-8"), resposta.data)
        self.assertIsNotNone(resposta)

    def test_exclusao_de_processo_remove_vinculos(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            db.session.add_all([
                Movimentacao(
                    processo=processo,
                    data=datetime.now(timezone.utc),
                    descricao="Movimentacao para exclusao",
                    origem="manual",
                ),
                Prazo(
                    processo=processo,
                    titulo="Prazo para exclusao",
                    data_vencimento=Config.local_date() + timedelta(days=2),
                ),
            ])
            db.session.commit()

        self.login()
        resposta = self.client.post(
            f"/processos/{self.processo_id}/excluir/",
            follow_redirects=True,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Processo exclu", resposta.data)

        with self.app.app_context():
            self.assertIsNone(db.session.get(Processo, self.processo_id))
            self.assertEqual(Movimentacao.query.count(), 0)
            self.assertEqual(Prazo.query.count(), 0)


    def test_lista_de_prazos_exibe_dados_e_filtro_de_status(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            db.session.add_all([
                Prazo(
                    processo=processo,
                    titulo="Prazo pendente",
                    data_vencimento=Config.local_date() + timedelta(days=3),
                    status=Prazo.Status.PENDENTE,
                ),
                Prazo(
                    processo=processo,
                    titulo="Prazo concluido",
                    data_vencimento=Config.local_date() - timedelta(days=2),
                    status=Prazo.Status.CONCLUIDO,
                ),
            ])
            db.session.commit()

        self.login()
        resposta = self.client.get("/prazos/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Prazo pendente", resposta.data)
        self.assertIn(b"Prazo concluido", resposta.data)
        self.assertIn(b"Novo prazo", resposta.data)

        resposta = self.client.get(
            "/prazos/",
            query_string={"status": Prazo.Status.PENDENTE},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Prazo pendente", resposta.data)
        self.assertNotIn(b"Prazo concluido", resposta.data)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_nova_movimentacao_datajud_fica_nao_lida(self, consultar):
        consultar.return_value = [
            {
                "dataHora": "2026-09-23T12:00:00Z",
                "nome": "Nova movimentacao",
            }
        ]

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            resultado = verificar_movimentacao_processo(processo)
            db.session.commit()

            movimento = Movimentacao.query.one()
            self.assertEqual(resultado["total_novas"], 1)
            self.assertFalse(movimento.lida)

    def test_notificacoes_exibem_apenas_movimentacoes_nao_lidas(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            db.session.add_all([
                Movimentacao(
                    processo=processo,
                    data=datetime.now(timezone.utc),
                    descricao="Movimentacao nao lida",
                    origem="datajud",
                    lida=False,
                ),
                Movimentacao(
                    processo=processo,
                    data=datetime.now(timezone.utc),
                    descricao="Movimentacao ja lida",
                    origem="datajud",
                    lida=True,
                ),
            ])
            db.session.commit()

        self.login()
        resposta = self.client.get("/notificacoes/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Movimentacao nao lida", resposta.data)
        self.assertNotIn(b"Movimentacao ja lida", resposta.data)

    def test_marcar_processo_como_visto_marca_movimentacoes_como_lidas(self):
        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            processo.alerta_pendente = True
            db.session.add_all([
                Movimentacao(
                    processo=processo,
                    data=datetime.now(timezone.utc),
                    descricao="Movimentacao 1",
                    origem="datajud",
                    lida=False,
                ),
                Movimentacao(
                    processo=processo,
                    data=datetime.now(timezone.utc),
                    descricao="Movimentacao 2",
                    origem="datajud",
                    lida=False,
                ),
            ])
            db.session.commit()

        self.login()
        resposta = self.client.post(
            f"/notificacoes/processos/{self.processo_id}/limpar/",
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            processo = db.session.get(Processo, self.processo_id)
            movimentos = Movimentacao.query.filter_by(processo_id=self.processo_id).all()
            self.assertFalse(processo.alerta_pendente)
            self.assertEqual(len(movimentos), 2)
            self.assertTrue(all(m.lida for m in movimentos))

        resposta = self.client.get("/notificacoes/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Nenhuma movimentação nova pendente.".encode("utf-8"), resposta.data)



    def admin_login(self):
        with self.app.app_context():
            usuario = db.session.get(Usuario, self.usuario_id)
            usuario.is_admin = True
            db.session.commit()
        return self.login()

    def test_painel_admin_exige_permissao_de_administrador(self):
        self.login()
        resposta = self.client.get("/admin/")
        self.assertEqual(resposta.status_code, 403)

    def test_painel_admin_exibe_resumo(self):
        self.admin_login()
        resposta = self.client.get("/admin/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Painel administrativo", resposta.data)
        self.assertIn("Usuários".encode("utf-8"), resposta.data)

    def test_admin_pode_criar_usuario(self):
        self.admin_login()
        resposta = self.client.post(
            "/admin/usuarios/novo/",
            data={
                "username": "advogado",
                "password": "senha-segura-123",
                "password_confirmation": "senha-segura-123",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            usuario = Usuario.query.filter_by(username="advogado").first()
            self.assertIsNotNone(usuario)
            self.assertFalse(usuario.is_admin)
            self.assertTrue(usuario.is_active)
            self.assertTrue(usuario.check_password("senha-segura-123"))

    def test_admin_pode_desativar_e_reativar_usuario(self):
        self.admin_login()
        with self.app.app_context():
            usuario = Usuario(username="temporario")
            usuario.set_password("senha-segura-123")
            db.session.add(usuario)
            db.session.commit()
            usuario_id = usuario.id

        resposta = self.client.post(f"/admin/usuarios/{usuario_id}/alternar-status/")
        self.assertEqual(resposta.status_code, 302)
        with self.app.app_context():
            self.assertFalse(db.session.get(Usuario, usuario_id).is_active)

        resposta = self.client.post(f"/admin/usuarios/{usuario_id}/alternar-status/")
        self.assertEqual(resposta.status_code, 302)
        with self.app.app_context():
            self.assertTrue(db.session.get(Usuario, usuario_id).is_active)

    def test_admin_nao_pode_desativar_a_propria_conta(self):
        self.admin_login()
        resposta = self.client.post(
            f"/admin/usuarios/{self.usuario_id}/alternar-status/"
        )
        self.assertEqual(resposta.status_code, 302)
        with self.app.app_context():
            self.assertTrue(db.session.get(Usuario, self.usuario_id).is_active)

    def test_admin_pode_redefinir_senha(self):
        self.admin_login()
        resposta = self.client.post(
            f"/admin/usuarios/{self.usuario_id}/senha/",
            data={
                "password": "nova-senha-123",
                "password_confirmation": "nova-senha-123",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        with self.app.app_context():
            usuario = db.session.get(Usuario, self.usuario_id)
            self.assertTrue(usuario.check_password("nova-senha-123"))

    def test_login_rejeita_usuario_desativado(self):
        with self.app.app_context():
            usuario = db.session.get(Usuario, self.usuario_id)
            usuario.is_active = False
            db.session.commit()

        resposta = self.client.post(
            "/login/",
            data={
                "username": "teste",
                "password": "senha-segura-123",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("desativada".encode("utf-8"), resposta.data)



if __name__ == "__main__":
    unittest.main()


class AuditoriaTests(unittest.TestCase):
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
            usuario = Usuario(
                username="auditor",
                password_hash=FluxosPrincipaisTests.TEST_PASSWORD_HASH,
            )
            db.session.add(usuario)
            db.session.commit()
            self.usuario_id = usuario.id

        self.client = self.app.test_client()

    def test_login_cria_registro_de_auditoria(self):
        resposta = self.client.post(
            "/login/",
            data={"username": "auditor", "password": "senha-segura-123"},
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            registro = Auditoria.query.filter_by(
                acao="LOGIN",
                entidade="Usuario",
                registro_id=self.usuario_id,
            ).first()
            self.assertIsNotNone(registro)
            self.assertEqual(registro.usuario_id, self.usuario_id)

    def test_criacao_de_cliente_cria_registro_de_auditoria(self):
        self.client.post(
            "/login/",
            data={"username": "auditor", "password": "senha-segura-123"},
        )
        with self.app.app_context():
            cliente = Cliente(nome="Cliente Auditado", cpf_cnpj="52998224725")
            db.session.add(cliente)
            db.session.commit()

        resposta = self.client.post(
            "/clientes/novo/",
            data={
                "nome": "Novo Cliente Auditado",
                "cpf_cnpj": "11144477735",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        with self.app.app_context():
            registro = Auditoria.query.filter_by(
                acao="CRIAR",
                entidade="Cliente",
            ).order_by(Auditoria.id.desc()).first()
            self.assertIsNotNone(registro)
            self.assertEqual(registro.usuario_id, self.usuario_id)
            self.assertIn("Novo Cliente Auditado", registro.detalhes)

    def test_admin_pode_consultar_auditoria(self):
        with self.app.app_context():
            usuario = db.session.get(Usuario, self.usuario_id)
            usuario.is_admin = True
            db.session.commit()

        self.client.post(
            "/login/",
            data={"username": "auditor", "password": "senha-segura-123"},
        )
        resposta = self.client.get("/admin/auditoria/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Log de auditoria", resposta.data)

    def test_usuario_comum_nao_pode_consultar_auditoria(self):
        self.client.post(
            "/login/",
            data={"username": "auditor", "password": "senha-segura-123"},
        )
        resposta = self.client.get("/admin/auditoria/")
        self.assertEqual(resposta.status_code, 403)
