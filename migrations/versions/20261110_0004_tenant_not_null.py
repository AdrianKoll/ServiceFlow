"""Torna tenant_id obrigatório nas entidades operacionais.

Revision ID: 20261110_0004
Revises: 20260424_0003
"""

from alembic import op
import sqlalchemy as sa


revision = "20261110_0004"
down_revision = "20260424_0003"
branch_labels = None
depends_on = None

TABLES = (
    "users",
    "clients",
    "services",
    "tasks",
    "events",
    "transactions",
    "message_threads",
    "notifications",
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in TABLES:
        missing = bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")
        ).scalar_one()
        if missing:
            raise RuntimeError(
                f"{table} possui {missing} registros sem tenant_id. "
                "Associe cada registro ao tenant correto antes de aplicar esta migração."
            )

    for table in TABLES:
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.alter_column(
                "tenant_id",
                existing_type=sa.Integer(),
                nullable=False,
            )


def downgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.alter_column(
                "tenant_id",
                existing_type=sa.Integer(),
                nullable=True,
            )
