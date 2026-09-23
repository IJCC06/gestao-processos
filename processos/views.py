from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClienteForm, PrazoForm, ProcessoForm
from .models import Cliente, Movimentacao, Prazo, Processo


@login_required
def dashboard(request):
    hoje = timezone.localdate()

    prazos = Prazo.objects.filter(
        status=Prazo.Status.PENDENTE,
    ).select_related("processo", "processo__cliente")

    prazos_vencidos = prazos.filter(
        data_vencimento__lt=hoje,
    )
    prazos_proximos = prazos.filter(
        data_vencimento__gte=hoje,
        data_vencimento__lte=hoje + timedelta(days=7),
    )

    context = {
        "total_clientes": Cliente.objects.count(),
        "total_processos": Processo.objects.count(),
        "processos_ativos": Processo.objects.filter(status=Processo.Status.ATIVO).count(),
        "alertas_pendentes": Processo.objects.filter(alerta_pendente=True).count(),
        "prazos_vencidos": prazos_vencidos,
        "prazos_proximos": prazos_proximos,
        "ultimas_movimentacoes": Movimentacao.objects.select_related(
            "processo", "processo__cliente"
        )[:10],
    }
    return render(request, "processos/dashboard.html", context)


@login_required
def cliente_list(request):
    busca = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()
    if busca:
        clientes = clientes.filter(Q(nome__icontains=busca) | Q(cpf_cnpj__icontains=busca) | Q(contato__icontains=busca))
    return render(request, "processos/clientes/list.html", {"clientes": clientes, "busca": busca})


@login_required
def cliente_create(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, "Cliente cadastrado com sucesso.")
            return redirect("cliente_detail", pk=cliente.pk)
    else:
        form = ClienteForm()
    return render(request, "processos/clientes/form.html", {"form": form, "titulo": "Novo cliente"})


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente.objects.prefetch_related("processos"), pk=pk)
    return render(request, "processos/clientes/detail.html", {"cliente": cliente})


@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso.")
            return redirect("cliente_detail", pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "processos/clientes/form.html", {"form": form, "titulo": "Editar cliente", "cliente": cliente})


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        try:
            cliente.delete()
        except ProtectedError:
            messages.error(request, "Não foi possível excluir este cliente. Verifique se ele possui processos vinculados.")
            return redirect("cliente_detail", pk=cliente.pk)
        messages.success(request, "Cliente excluído com sucesso.")
        return redirect("cliente_list")
    return render(request, "processos/clientes/delete.html", {"cliente": cliente})


@login_required
def processo_list(request):
    busca = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    area = request.GET.get("area", "").strip()

    processos = Processo.objects.select_related("cliente")

    if busca:
        processos = processos.filter(
            Q(numero_cnj__icontains=busca)
            | Q(cliente__nome__icontains=busca)
            | Q(tribunal__icontains=busca)
        )
    if status in dict(Processo.Status.choices):
        processos = processos.filter(status=status)
    if area in dict(Processo.Area.choices):
        processos = processos.filter(area=area)

    return render(
        request,
        "processos/processos/list.html",
        {
            "processos": processos,
            "busca": busca,
            "status": status,
            "area": area,
            "status_choices": Processo.Status.choices,
            "area_choices": Processo.Area.choices,
        },
    )


@login_required
def processo_create(request):
    if request.method == "POST":
        form = ProcessoForm(request.POST)
        if form.is_valid():
            processo = form.save()
            messages.success(request, "Processo cadastrado com sucesso.")
            return redirect("processo_detail", pk=processo.pk)
    else:
        form = ProcessoForm()
    return render(request, "processos/processos/form.html", {"form": form, "titulo": "Novo processo"})


@login_required
def processo_detail(request, pk):
    processo = get_object_or_404(
        Processo.objects.select_related("cliente").prefetch_related("movimentacoes", "prazos"), pk=pk
    )
    return render(request, "processos/processos/detail.html", {"processo": processo})


@login_required
def processo_update(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == "POST":
        form = ProcessoForm(request.POST, instance=processo)
        if form.is_valid():
            form.save()
            messages.success(request, "Processo atualizado com sucesso.")
            return redirect("processo_detail", pk=processo.pk)
    else:
        form = ProcessoForm(instance=processo)
    return render(request, "processos/processos/form.html", {"form": form, "titulo": "Editar processo", "processo": processo})


@login_required
def prazo_list(request):
    status = request.GET.get("status", "").strip()
    prazos = Prazo.objects.select_related("processo", "processo__cliente")
    if status in dict(Prazo.Status.choices):
        prazos = prazos.filter(status=status)
    return render(request, "processos/prazos/list.html", {"prazos": prazos, "status": status, "status_choices": Prazo.Status.choices})


@login_required
def prazo_create(request):
    processo_id = request.GET.get("processo")
    processo = None

    if processo_id:
        processo = get_object_or_404(Processo, pk=processo_id)

    if request.method == "POST":
        form = PrazoForm(request.POST)
        if processo and not request.POST.get("processo"):
            form.data = form.data.copy()
            form.data["processo"] = processo.pk

        if form.is_valid():
            prazo = form.save()
            messages.success(request, "Prazo cadastrado com sucesso.")
            return redirect("prazo_detail", pk=prazo.pk)
    else:
        form = PrazoForm(initial={"processo": processo} if processo else None)

    return render(
        request,
        "processos/prazos/form.html",
        {"form": form, "titulo": "Novo prazo", "processo": processo},
    )


@login_required
def prazo_detail(request, pk):
    prazo = get_object_or_404(Prazo.objects.select_related("processo", "processo__cliente"), pk=pk)
    return render(request, "processos/prazos/detail.html", {"prazo": prazo})


@login_required
def prazo_update(request, pk):
    prazo = get_object_or_404(Prazo, pk=pk)
    if request.method == "POST":
        form = PrazoForm(request.POST, instance=prazo)
        if form.is_valid():
            form.save()
            messages.success(request, "Prazo atualizado com sucesso.")
            return redirect("prazo_detail", pk=prazo.pk)
    else:
        form = PrazoForm(instance=prazo)
    return render(request, "processos/prazos/form.html", {"form": form, "titulo": "Editar prazo", "prazo": prazo})


@login_required
def prazo_concluir(request, pk):
    prazo = get_object_or_404(Prazo, pk=pk)
    if request.method == "POST":
        prazo.status = Prazo.Status.CONCLUIDO
        prazo.save(update_fields=["status", "atualizado_em"])
        messages.success(request, "Prazo marcado como concluído.")
    return redirect("prazo_list")


@login_required
def notificacoes(request):
    hoje = timezone.localdate()
    prazos = Prazo.objects.filter(status=Prazo.Status.PENDENTE).select_related("processo", "processo__cliente")
    vencidos = prazos.filter(data_vencimento__lt=hoje)
    proximos = prazos.filter(data_vencimento__gte=hoje, data_vencimento__lte=hoje + timedelta(days=7))
    movimentos = Movimentacao.objects.filter(processo__alerta_pendente=True).select_related("processo", "processo__cliente")
    return render(request, "processos/notificacoes.html", {"vencidos": vencidos, "prazos_proximos": proximos, "movimentos": movimentos})


@login_required
def limpar_alerta_processo(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == "POST":
        processo.alerta_pendente = False
        processo.save(update_fields=["alerta_pendente"])
        messages.success(request, "Alerta de movimentação marcado como visto.")
    return redirect("notificacoes")
