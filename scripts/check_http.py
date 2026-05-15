"""Verifica as páginas principais com o app já rodando.

1) Em um terminal: python run_sqlite.py
2) Em outro terminal: python scripts/check_http.py
"""
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlencode
from http.cookiejar import CookieJar

BASE = 'http://127.0.0.1:5000'
jar = CookieJar()
opener = build_opener(HTTPCookieProcessor(jar))

def open_path(path, data=None):
    if data is not None:
        data = urlencode(data).encode()
    req = Request(BASE + path, data=data)
    return opener.open(req, timeout=10)

open_path('/login', {'email': 'admin@serviceflow.local', 'password': 'admin123'})
paths = ['/dashboard', '/servicos', '/clientes', '/equipe', '/tarefas', '/agenda', '/financeiro', '/mensagens', '/relatorios', '/configuracoes']
for path in paths:
    resp = open_path(path)
    print(f'{path}: {resp.status}')
print('Check HTTP concluído.')
