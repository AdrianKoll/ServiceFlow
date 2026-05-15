"""subscription plan fields

Revision ID: 20260424_0002
Revises: 20260424_0001
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa

revision = '20260424_0002'
down_revision = '20260424_0001'
branch_labels = None
depends_on = None

def _add_column_if_missing(table_name, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c['name'] for c in inspector.get_columns(table_name)}
    if column.name not in columns:
        op.add_column(table_name, column)

def upgrade():
    _add_column_if_missing('tenants', sa.Column('plan', sa.Text(), nullable=False, server_default='basic'))
    _add_column_if_missing('tenants', sa.Column('billing_status', sa.Text(), nullable=False, server_default='trial'))
    _add_column_if_missing('tenants', sa.Column('trial_ends_at', sa.DateTime(), nullable=True))
    _add_column_if_missing('tenants', sa.Column('subscription_started_at', sa.DateTime(), nullable=True))
    _add_column_if_missing('tenants', sa.Column('subscription_ends_at', sa.DateTime(), nullable=True))
    _add_column_if_missing('tenants', sa.Column('payment_method', sa.Text(), nullable=True))

def downgrade():
    pass
