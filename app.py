"""Application factory do ServiceFlow.

Este arquivo mantém o bootstrap da aplicação Flask enxuto. Regras de negócio,
rotas, modelos, serviços e helpers ficam separados em seus próprios módulos.
"""

import os
from importlib import import_module

from flask import Flask

from core.config import Config
from core.constants import EVENT_TYPE_PT, PRIORITY_PT, ROLE_ICON, ROLE_PT, STATUS_PT
from core.context import register_context_processors
from core.formatters import fmt_brl, fmt_date, fmt_datetime
from core.migrations import run_migrations
from core.security import register_security_headers
from models import db
from core.extensions import limiter


# Blueprints registrados em ordem previsível.
# Para adicionar um novo módulo, crie modules/<nome>/routes.py com a variável `bp`
# e inclua o caminho abaixo.
BLUEPRINT_MODULES = [
    "modules.public.routes",
    "modules.auth.routes",
    "modules.main.routes",
    "modules.portal.routes",
    "modules.servicos.routes",
    "modules.clientes.routes",
    "modules.equipe.routes",
    "modules.tarefas.routes",
    "modules.agenda.routes",
    "modules.financeiro.routes",
    "modules.mensagens.routes",
    "modules.relatorios.routes",
    "modules.desempenho.routes",
    "modules.assinatura.routes",
    "modules.configuracoes.routes",
    "modules.notifications.routes",
]


def register_template_helpers(app: Flask) -> None:
    """Registra helpers globais usados nos templates Jinja."""
    app.jinja_env.globals.update(
        status_pt=STATUS_PT,
        priority_pt=PRIORITY_PT,
        role_pt=ROLE_PT,
        role_icon=ROLE_ICON,
        event_type_pt=EVENT_TYPE_PT,
        fmt_brl=fmt_brl,
        fmt_date=fmt_date,
        fmt_datetime=fmt_datetime,
    )


def register_blueprints(app: Flask) -> None:
    """Carrega e registra os blueprints da aplicação."""
    for module_path in BLUEPRINT_MODULES:
        module = import_module(module_path)
        app.register_blueprint(module.bp)


def create_app() -> Flask:
    """Cria e configura a instância Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensões
    db.init_app(app)
    limiter.init_app(app)

    # Camadas transversais
    register_template_helpers(app)
    register_context_processors(app)
    register_security_headers(app)
    register_blueprints(app)

    # Desenvolvimento usa create_all para facilitar testes; produção usa Alembic.
    if app.config.get("ENV") != "production":
        with app.app_context():
            db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    run_migrations(app)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
