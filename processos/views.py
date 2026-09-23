from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm
from .models import Cliente, Movimentacao, Processo


@login_required
def dashboard(request):
    context = {
        "total_clientes": Cliente.objects.count(),
        "total_processos": Processo.objects.count(),
        "processos_ativos": Processo.objects.filter(
            status=Processo.Status.ATIVO
        ).count(),
        "alertas_pendentes": Processo.objects.filter(alerta_pendente=True).count(),
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
        clientes = clientes.filter(
            Q(nome__icontains=busca)
            | Q(cpf_cnpj__icontains=busca)
            | Q(contato__icontains=busca)
        )

    return render(
        request,
        "processos/clientes/list.html",
        {"clientes": clientes, "busca": busca},
    )


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

    return render(
        request,
        "processos/clientes/form.html",
        {"form": form, "titulo": "Novo cliente"},
    )


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(
        Cliente.objects.prefetch_related("processos"),
        pk=pk,
    )
    return render(
        request,
        "processos/clientes/detail.html",
        {"cliente": cliente},
    )


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

    return render(
        request,
        "processos/clientes/form.html",
        {"form": form, "titulo": "Editar cliente", "cliente": cliente},
    )


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == "POST":
        try:
            cliente.delete()
        except Exception:
            messages.error(
                request,
                "Não foi possível excluir este cliente. "
                "Verifique se ele possui processos vinculados.",
            )
            return redirect("cliente_detail", pk=cliente.pk)

        messages.success(request, "Cliente excluído com sucesso.")
        return redirect("cliente_list")

    return render(
        request,
        "processos/clientes/delete.html",
        {"cliente": cliente},
    )
