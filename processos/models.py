from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=20, unique=True)
    contato = models.CharField(max_length=100, blank=True)
    endereco = models.CharField("Endereço", max_length=300, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Processo(models.Model):
    class Area(models.TextChoices):
        TRABALHISTA = "trabalhista", "Trabalhista"
        CIVEL = "civel", "Cível"
        PREVIDENCIARIO = "previdenciario", "Previdenciário"

    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        SUSPENSO = "suspenso", "Suspenso"
        ARQUIVADO = "arquivado", "Arquivado"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="processos")
    numero_cnj = models.CharField("Número CNJ", max_length=25, unique=True)
    area = models.CharField(max_length=20, choices=Area.choices)
    tribunal = models.CharField("Tribunal/Vara", max_length=150, blank=True)
    fase = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ATIVO)
    valor_causa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    honorarios = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    alerta_pendente = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.numero_cnj} — {self.cliente.nome}"


class Movimentacao(models.Model):
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name="movimentacoes")
    data = models.DateTimeField()
    descricao = models.TextField()
    origem = models.CharField(max_length=50, default="datajud")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.processo.numero_cnj} — {self.data:%d/%m/%Y}"
