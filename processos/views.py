from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Cliente, Movimentacao, Processo


@login_required
def dashboard(request):
    context = {
        "total_clientes": Cliente.objects.count(),
        "total_processos": Processo.objects.count(),
        "processos_ativos": Processo.objects.filter(
            status=Processo.Status.ATIVO
        ).count(),
        "alertas_pendentes": Processo.objects.filter(
            alerta_pendente=True
        ).count(),
        "ultimas_movimentacoes": Movimentacao.objects.select_related(
            "processo", "processo__cliente"
        )[:10],
    }
    return render(request, "processos/dashboard.html", context)
