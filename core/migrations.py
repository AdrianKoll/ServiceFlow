"""Utilitários de migração do ServiceFlow.

Fluxo principal: Alembic.
Fallback: db.create_all() somente quando Alembic não estiver instalado no ambiente de teste.
"""
from __future__ import annotations

from pathlib import Path
from models import db


def run_migrations(app) -> None:
    """Aplica migrations Alembic no banco configurado pelo Flask.

    Mantém compatibilidade com ambientes simples: se o pacote Alembic não existir,
    cria as tabelas com SQLAlchemy para permitir teste local rápido.
    """
    with app.app_context():
        try:
            from alembic import command
            from alembic.config import Config as AlembicConfig

            base_dir = Path(app.root_path)
            alembic_cfg = AlembicConfig(str(base_dir / 'alembic.ini'))
            alembic_cfg.set_main_option('script_location', str(base_dir / 'migrations'))
            alembic_cfg.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
            command.upgrade(alembic_cfg, 'head')
        except ImportError as exc:
            if app.config.get('ENV') == 'production':
                raise RuntimeError('Alembic é obrigatório em produção.') from exc
            print(f'[ServiceFlow] Alembic indisponível; usando db.create_all() apenas em desenvolvimento: {exc}')
            db.create_all()
