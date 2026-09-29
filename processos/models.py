class Auditoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    acao = db.Column(db.String(30), nullable=False)
    entidade = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=True)
    detalhes = db.Column(db.Text, default="")
    criado_em = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    usuario = db.relationship("Usuario", backref="auditorias")


from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=True, nullable=False)
    contato = db.Column(db.String(100), default="")
    endereco = db.Column(db.String(300), default="")
    observacoes = db.Column(db.Text, default="")
    criado_em = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    processos = db.relationship("Processo", back_populates="cliente")


class Processo(db.Model):
    class Area:
        TRABALHISTA = "trabalhista"
        CIVEL = "civel"
        PREVIDENCIARIO = "previdenciario"

        @classmethod
        def choices(cls):
            return [(cls.TRABALHISTA, "Trabalhista"), (cls.CIVEL, "Cível"), (cls.PREVIDENCIARIO, "Previdenciário")]

        @classmethod
        def values(cls):
            return {item[0] for item in cls.choices()}

    class Status:
        ATIVO = "ativo"
        SUSPENSO = "suspenso"
        ARQUIVADO = "arquivado"

        @classmethod
        def choices(cls):
            return [(cls.ATIVO, "Ativo"), (cls.SUSPENSO, "Suspenso"), (cls.ARQUIVADO, "Arquivado")]

        @classmethod
        def values(cls):
            return {item[0] for item in cls.choices()}

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    numero_cnj = db.Column(db.String(25), unique=True, nullable=False)
    area = db.Column(db.String(20), nullable=False)
    tribunal = db.Column(db.String(150), default="")
    tribunal_alias = db.Column(db.String(20), default="")
    fase = db.Column(db.String(100), default="")
    status = db.Column(db.String(20), default=Status.ATIVO, nullable=False)
    valor_causa = db.Column(db.Numeric(12, 2), nullable=True)
    honorarios = db.Column(db.Numeric(12, 2), nullable=True)
    alerta_pendente = db.Column(db.Boolean, default=False, nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    cliente = db.relationship("Cliente", back_populates="processos")
    movimentacoes = db.relationship("Movimentacao", back_populates="processo", cascade="all, delete-orphan", order_by="desc(Movimentacao.data)")
    prazos = db.relationship("Prazo", back_populates="processo", cascade="all, delete-orphan", order_by="Prazo.data_vencimento")

    def area_display(self):
        return dict(self.Area.choices()).get(self.area, self.area)

    def status_display(self):
        return dict(self.Status.choices()).get(self.status, self.status)


class Movimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey("processo.id"), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    origem = db.Column(db.String(50), default="datajud", nullable=False)
    criado_em = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    lida = db.Column(db.Boolean, default=False, nullable=False)
    processo = db.relationship("Processo", back_populates="movimentacoes")


class Prazo(db.Model):
    class Status:
        PENDENTE = "pendente"
        CONCLUIDO = "concluido"
        CANCELADO = "cancelado"

        @classmethod
        def choices(cls):
            return [(cls.PENDENTE, "Pendente"), (cls.CONCLUIDO, "Concluído"), (cls.CANCELADO, "Cancelado")]

        @classmethod
        def values(cls):
            return {item[0] for item in cls.choices()}

    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey("processo.id"), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    data_inicio = db.Column(db.Date, nullable=True)
    data_vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=Status.PENDENTE, nullable=False)
    observacoes = db.Column(db.Text, default="")
    criado_em = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    atualizado_em = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    processo = db.relationship("Processo", back_populates="prazos")

    @property
    def dias_restantes(self):
        from config.settings import Config
        return (self.data_vencimento - Config.local_date()).days

    def status_display(self):
        return dict(self.Status.choices()).get(self.status, self.status)
