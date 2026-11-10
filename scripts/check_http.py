"""Verifica páginas públicas e, opcionalmente, páginas autenticadas.

Uso:
1. Em um terminal: ``python app.py``.
2. Em outro terminal: ``python scripts/check_http.py``.

Para verificar rotas autenticadas, informe ``SERVICEFLOW_CHECK_EMAIL`` e
``SERVICEFLOW_CHECK_PASSWORD`` no ambiente. O script primeiro obtém o token
CSRF da página de login e depois faz a autenticação.
"""

import os
import re
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


BASE = os.environ.get("SERVICEFLOW_CHECK_BASE", "http://127.0.0.1:5000")
LOGIN_EMAIL = os.environ.get("SERVICEFLOW_CHECK_EMAIL")
LOGIN_PASSWORD = os.environ.get("SERVICEFLOW_CHECK_PASSWORD")
jar = CookieJar()
opener = build_opener(HTTPCookieProcessor(jar))


def open_path(path, data=None):
    encoded = urlencode(data).encode() if data is not None else None
    request = Request(BASE + path, data=encoded)
    return opener.open(request, timeout=10)


def csrf_token():
    response = open_path("/login")
    html = response.read().decode("utf-8")
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise RuntimeError("Token CSRF não encontrado na página de login.")
    return match.group(1)


public_paths = ["/", "/planos", "/login", "/cadastro"]
for path in public_paths:
    response = open_path(path)
    print(f"{path}: {response.status}")

if LOGIN_EMAIL and LOGIN_PASSWORD:
    open_path(
        "/login",
        {
            "email": LOGIN_EMAIL,
            "password": LOGIN_PASSWORD,
            "csrf_token": csrf_token(),
        },
    )
    protected_paths = [
        "/dashboard",
        "/servicos",
        "/clientes",
        "/equipe",
        "/tarefas",
        "/agenda",
        "/financeiro",
        "/mensagens",
        "/relatorios",
        "/configuracoes",
    ]
    for path in protected_paths:
        response = open_path(path)
        print(f"{path}: {response.status}")
else:
    print("Rotas autenticadas ignoradas: credenciais não informadas no ambiente.")

print("Check HTTP concluído.")
