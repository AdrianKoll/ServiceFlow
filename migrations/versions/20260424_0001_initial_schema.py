"""initial schema

Revision ID: 20260424_0001
Revises: 
Create Date: 2026-04-24
"""
from typing import Sequence, Union
from alembic import op

revision: str = '20260424_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migration inicial segura para SQLite de teste.
    # Usa o metadata atual do SQLAlchemy para criar somente o que ainda não existir.
    from models import db  # import tardio para usar o app context configurado pelo env.py
    bind = op.get_bind()
    db.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Para ambiente de teste. Em produção, preferir downgrade granular por tabela.
    from models import db
    bind = op.get_bind()
    db.metadata.drop_all(bind=bind)
