from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware, is_naive

from processos.models import Processo, Movimentacao
from processos.services.datajud import consultar_movimentacoes, DataJudError


class Command(BaseCommand):
    help = "Consulta o DataJud para cada processo ativo e registra movimentações novas."

    def handle(self, *args, **options):
        processos = Processo.objects.exclude(status=Processo.Status.ARQUIVADO)
        total_processos = processos.count()
        total_novas = 0

        for processo in processos:
            if not processo.tribunal_alias:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{processo.numero_cnj}] sem tribunal_alias cadastrado — pulando"
                    )
                )
                continue

            try:
                movimentos = consultar_movimentacoes(processo.numero_cnj, processo.tribunal_alias)
            except DataJudError as exc:
                self.stdout.write(self.style.ERROR(f"[{processo.numero_cnj}] {exc}"))
                continue

            ultima_registrada = processo.movimentacoes.order_by("-data").first()
            ultima_data = ultima_registrada.data if ultima_registrada else None

            novas = 0
            for mov in movimentos:
                data_hora_str = mov.get("dataHora")
                if not data_hora_str:
                    continue
                data_hora = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))
                if is_naive(data_hora):
                    data_hora = make_aware(data_hora)

                if ultima_data and data_hora <= ultima_data:
                    continue

                Movimentacao.objects.create(
                    processo=processo,
                    data=data_hora,
                    descricao=mov.get("nome", "Movimentação sem descrição"),
                    origem="datajud",
                )
                novas += 1

            if novas:
                processo.alerta_pendente = True
                processo.save(update_fields=["alerta_pendente"])
                total_novas += novas
                self.stdout.write(
                    self.style.SUCCESS(f"[{processo.numero_cnj}] {novas} movimentação(ões) nova(s)")
                )

        self.stdout.write(
            f"Verificação concluída: {total_processos} processo(s) checado(s), "
            f"{total_novas} movimentação(ões) nova(s) no total."
        )
