"""subscription lifecycle fields

Revision ID: 20260424_0003
Revises: 20260424_0002
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = '20260424_0003'
down_revision = '20260424_0002'
branch_labels = None
depends_on = None

def _add_column_if_missing(table_name, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c['name'] for c in inspector.get_columns(table_name)}
    if column.name not in columns:
        op.add_column(table_name, column)

def upgrade():
    _add_column_if_missing('tenants', sa.Column('billing_cycle', sa.Text(), nullable=False, server_default='monthly'))
    _add_column_if_missing('tenants', sa.Column('next_invoice_at', sa.DateTime(), nullable=True))
    _add_column_if_missing('tenants', sa.Column('last_payment_at', sa.DateTime(), nullable=True))
    _add_column_if_missing('tenants', sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    _add_column_if_missing('tenants', sa.Column('billing_email', sa.Text(), nullable=True))

def downgrade():
    pass
