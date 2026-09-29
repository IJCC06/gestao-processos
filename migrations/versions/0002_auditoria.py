"""cria tabela de auditoria

Revision ID: 0002_auditoria
Revises: 0001_baseline
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_auditoria"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("acao", sa.String(length=30), nullable=False),
        sa.Column("entidade", sa.String(length=50), nullable=False),
        sa.Column("registro_id", sa.Integer(), nullable=True),
        sa.Column("detalhes", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("auditoria")
