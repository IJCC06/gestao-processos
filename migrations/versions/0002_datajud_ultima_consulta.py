"""adiciona status e data da última consulta DataJud

Revision ID: 0002_datajud_ultima_consulta
Revises: 0001_baseline
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_datajud_ultima_consulta"
down_revision = "0002_auditoria"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "processo",
        sa.Column("datajud_ultima_consulta_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "processo",
        sa.Column("datajud_ultimo_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "processo",
        sa.Column("datajud_ultimo_erro", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("processo", "datajud_ultimo_erro")
    op.drop_column("processo", "datajud_ultimo_status")
    op.drop_column("processo", "datajud_ultima_consulta_em")
