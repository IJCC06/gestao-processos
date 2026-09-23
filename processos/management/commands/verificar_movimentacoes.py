from django.core.management.base import BaseCommand

from processos.services.movimentacoes import verificar_movimentacoes


class Command(BaseCommand):
    help = "Consulta o DataJud e registra movimentações novas."

    def handle(self, *args, **options):
        resultado = verificar_movimentacoes()

        self.stdout.write(
            f"Verificação concluída: {resultado['total_processos']} processo(s) "
            f"checado(s), {resultado['total_novas']} movimentação(ões) nova(s), "
            f"{resultado['erros']} ocorrência(s) com erro ou configuração ausente."
        )
