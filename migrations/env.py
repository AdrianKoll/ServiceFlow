import os
import sys
from logging.config import fileConfig

from alembic import context

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from models import db  # importa todos os models via models/__init__.py

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

flask_app = create_app()
target_metadata = db.metadata

# Garante que o Alembic use a mesma conexão configurada no Flask.
config.set_main_option('sqlalchemy.url', flask_app.config['SQLALCHEMY_DATABASE_URI'])


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with flask_app.app_context():
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                render_as_batch=connection.dialect.name == 'sqlite',
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
