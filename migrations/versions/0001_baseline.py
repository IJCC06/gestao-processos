"""baseline do schema atual

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-29

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("usuario", sa.Column("id", sa.Integer(), nullable=False), sa.Column("username", sa.String(length=150), nullable=False), sa.Column("password_hash", sa.String(length=255), nullable=False), sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("username"))
    op.create_table("cliente", sa.Column("id", sa.Integer(), nullable=False), sa.Column("nome", sa.String(length=200), nullable=False), sa.Column("cpf_cnpj", sa.String(length=20), nullable=False), sa.Column("contato", sa.String(length=100), nullable=True), sa.Column("endereco", sa.String(length=300), nullable=True), sa.Column("observacoes", sa.Text(), nullable=True), sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("cpf_cnpj"))
    op.create_table("processo", sa.Column("id", sa.Integer(), nullable=False), sa.Column("cliente_id", sa.Integer(), nullable=False), sa.Column("numero_cnj", sa.String(length=25), nullable=False), sa.Column("area", sa.String(length=20), nullable=False), sa.Column("tribunal", sa.String(length=150), nullable=True), sa.Column("tribunal_alias", sa.String(length=20), nullable=True), sa.Column("fase", sa.String(length=100), nullable=True), sa.Column("status", sa.String(length=20), nullable=False), sa.Column("valor_causa", sa.Numeric(12, 2), nullable=True), sa.Column("honorarios", sa.Numeric(12, 2), nullable=True), sa.Column("alerta_pendente", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("numero_cnj"))
    op.create_table("movimentacao", sa.Column("id", sa.Integer(), nullable=False), sa.Column("processo_id", sa.Integer(), nullable=False), sa.Column("data", sa.DateTime(), nullable=False), sa.Column("descricao", sa.Text(), nullable=False), sa.Column("origem", sa.String(length=50), nullable=False), sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False), sa.Column("lida", sa.Boolean(), nullable=False, server_default=sa.false()), sa.ForeignKeyConstraint(["processo_id"], ["processo.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("prazo", sa.Column("id", sa.Integer(), nullable=False), sa.Column("processo_id", sa.Integer(), nullable=False), sa.Column("titulo", sa.String(length=200), nullable=False), sa.Column("data_inicio", sa.Date(), nullable=True), sa.Column("data_vencimento", sa.Date(), nullable=False), sa.Column("status", sa.String(length=20), nullable=False), sa.Column("observacoes", sa.Text(), nullable=True), sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False), sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["processo_id"], ["processo.id"]), sa.PrimaryKeyConstraint("id"))

def downgrade():
    op.drop_table("prazo")
    op.drop_table("movimentacao")
    op.drop_table("processo")
    op.drop_table("cliente")
    op.drop_table("usuario")
