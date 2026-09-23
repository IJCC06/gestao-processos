from django.contrib import admin
from .models import Cliente, Processo, Movimentacao


class MovimentacaoInline(admin.TabularInline):
    model = Movimentacao
    extra = 0
    readonly_fields = ("criado_em",)
    ordering = ("-data",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf_cnpj", "contato")
    search_fields = ("nome", "cpf_cnpj")


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ("numero_cnj", "cliente", "area", "status", "alerta_pendente")
    list_filter = ("area", "status", "alerta_pendente")
    search_fields = ("numero_cnj", "cliente__nome")
    inlines = [MovimentacaoInline]


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("processo", "data", "origem")
    list_filter = ("origem",)
    ordering = ("-data",)
