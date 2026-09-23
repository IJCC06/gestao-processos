from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Cliente, Movimentacao, Prazo, Processo
from .services.movimentacoes import verificar_movimentacoes


class FluxosPrincipaisTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="teste",
            password="senha-segura-123",
        )
        self.cliente = Cliente.objects.create(
            nome="Cliente Teste",
            cpf_cnpj="12345678901",
        )
        self.processo = Processo.objects.create(
            cliente=self.cliente,
            numero_cnj="0000000-00.2026.8.00.0000",
            area=Processo.Area.CIVEL,
            tribunal="Tribunal de Teste",
        )

    def login(self):
        self.client.login(username="teste", password="senha-segura-123")

    def test_dashboard_exige_login(self):
        resposta = self.client.get(reverse("dashboard"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("login"), resposta.url)

    def test_dashboard_separa_prazos_vencidos_e_proximos(self):
        hoje = timezone.localdate()

        vencido = Prazo.objects.create(
            processo=self.processo,
            titulo="Prazo vencido",
            data_vencimento=hoje - timedelta(days=2),
        )
        proximo = Prazo.objects.create(
            processo=self.processo,
            titulo="Prazo próximo",
            data_vencimento=hoje + timedelta(days=2),
        )
        distante = Prazo.objects.create(
            processo=self.processo,
            titulo="Prazo distante",
            data_vencimento=hoje + timedelta(days=8),
        )

        self.login()
        resposta = self.client.get(reverse("dashboard"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, vencido.titulo)
        self.assertContains(resposta, proximo.titulo)
        self.assertNotContains(resposta, distante.titulo)

        self.assertIn(vencido, resposta.context["prazos_vencidos"])
        self.assertIn(proximo, resposta.context["prazos_proximos"])
        self.assertNotIn(vencido, resposta.context["prazos_proximos"])

    def test_criacao_de_cliente(self):
        self.login()

        resposta = self.client.post(
            reverse("cliente_create"),
            {
                "nome": "Novo Cliente",
                "cpf_cnpj": "98765432100",
                "contato": "contato@example.com",
                "endereco": "Rua Teste, 100",
                "observacoes": "Observação",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Cliente.objects.filter(cpf_cnpj="98765432100").exists())

    def test_criacao_de_processo(self):
        self.login()

        resposta = self.client.post(
            reverse("processo_create"),
            {
                "cliente": self.cliente.pk,
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
        self.assertTrue(
            Processo.objects.filter(
                numero_cnj="1111111-11.2026.8.00.0000"
            ).exists()
        )

    def test_criacao_de_prazo_via_processo(self):
        self.login()

        resposta = self.client.post(
            f"{reverse('prazo_create')}?processo={self.processo.pk}",
            {
                "titulo": "Prazo de manifestação",
                "data_inicio": "2026-09-20",
                "data_vencimento": "2026-09-30",
                "status": Prazo.Status.PENDENTE,
                "observacoes": "",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            Prazo.objects.filter(
                processo=self.processo,
                titulo="Prazo de manifestação",
            ).exists()
        )

    def test_notificacoes_separam_prazos(self):
        hoje = timezone.localdate()

        Prazo.objects.create(
            processo=self.processo,
            titulo="Vencido",
            data_vencimento=hoje - timedelta(days=1),
        )
        Prazo.objects.create(
            processo=self.processo,
            titulo="Próximo",
            data_vencimento=hoje + timedelta(days=3),
        )

        self.login()
        resposta = self.client.get(reverse("notificacoes"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.context["vencidos"]), 1)
        self.assertEqual(len(resposta.context["prazos_proximos"]), 1)

    def test_marcar_alerta_de_processo_como_visto(self):
        self.processo.alerta_pendente = True
        self.processo.save(update_fields=["alerta_pendente"])

        self.login()
        resposta = self.client.post(
            reverse("limpar_alerta_processo", args=[self.processo.pk])
        )

        self.assertEqual(resposta.status_code, 302)
        self.processo.refresh_from_db()
        self.assertFalse(self.processo.alerta_pendente)

    @patch("processos.services.movimentacoes.consultar_movimentacoes")
    def test_verificacao_datajud_cria_movimentacao_nova(self, consultar):
        consultar.return_value = [
            {
                "dataHora": "2026-09-23T12:00:00Z",
                "nome": "Movimentação de teste",
            }
        ]

        resultado = verificar_movimentacoes()

        self.assertEqual(resultado["total_processos"], 1)
        self.assertEqual(resultado["total_novas"], 1)
        self.assertEqual(resultado["erros"], 0)
        self.assertEqual(
            Movimentacao.objects.filter(
                processo=self.processo,
                origem="datajud",
            ).count(),
            1,
        )

        resultado = verificar_movimentacoes()

        self.assertEqual(resultado["total_novas"], 0)
        self.assertEqual(
            Movimentacao.objects.filter(
                processo=self.processo,
                origem="datajud",
            ).count(),
            1,
        )
