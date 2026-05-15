"""Utilitários de migração do ServiceFlow.

Fluxo principal: Alembic.
Fallback: db.create_all() somente quando Alembic não estiver instalado no ambiente de teste.
"""
from __future__ import annotations

from pathlib import Path
from werkzeug.security import generate_password_hash

from models import db, User


def _ensure_admin_password() -> None:
    admin = User.query.filter_by(role='admin').first()
    if admin and not admin.password_hash:
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()


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
        except Exception as exc:
            # Fallback intencional para SQLite/teste. Não interrompe o app por falha de ferramenta.
            print(f'[ServiceFlow] Alembic indisponível/falhou; usando db.create_all() como fallback: {exc}')
            db.create_all()

        _ensure_admin_password()
