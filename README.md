# ServiceFlow

O ServiceFlow é uma aplicação web de gestão de serviços desenvolvida em Flask. O sistema centraliza clientes, serviços, tarefas, agenda, financeiro, mensagens, relatórios e configurações em uma interface responsiva.

> **Estado do projeto:** protótipo/portfólio em evolução. A aplicação tem boas proteções de base, mas não deve receber dados reais de múltiplos clientes antes da conclusão do isolamento por tenant descrito na seção de segurança.

## Funcionalidades

- Dashboard com indicadores operacionais;
- cadastro e acompanhamento de clientes e serviços;
- tarefas, responsáveis, prazos e agenda;
- controle financeiro de entradas e saídas;
- mensagens internas restritas a participantes da equipe;
- relatórios de desempenho e exportação CSV;
- autenticação, perfis e permissões por função;
- configurações de perfil e aparência;
- backup, restauração e reset operacional para SQLite;
- suporte a SQLite para desenvolvimento e PostgreSQL para produção, com limitações de backup documentadas abaixo.

As integrações exibidas na tela de configurações são um catálogo demonstrativo. Alternar uma integração grava apenas o estado na sessão; não há conexão real com WhatsApp, Google Calendar, Stripe/Pagar.me, Slack ou Zapier.

## Stack

- Python 3.11+
- Flask 3
- Flask-SQLAlchemy e SQLAlchemy
- Alembic
- Jinja2, HTML, CSS e JavaScript
- SQLite para desenvolvimento local
- PostgreSQL recomendado para produção
- Gunicorn para execução em produção
- Flask-Limiter para limitação de tentativas

## Estrutura do projeto

```text
ServiceFlow/
├── app.py                    # Fábrica, bootstrap e registro dos blueprints
├── core/                     # Configuração, autenticação e recursos transversais
├── models/                   # Entidades SQLAlchemy
├── modules/                  # Blueprints separados por domínio
├── services/                 # Regras reutilizáveis e serviços auxiliares
├── migrations/               # Migrações Alembic
├── templates/                # Templates Jinja2
├── static/                   # CSS, JavaScript e uploads de perfil
├── tests/                    # Testes automatizados
├── scripts/check_http.py     # Verificação HTTP pública/autenticada
├── .env.example              # Modelo público de configuração
├── requirements.txt          # Dependências de produção
└── .github/workflows/ci.yml  # Pipeline de testes
```

A aplicação usa uma divisão por responsabilidade: `app.py` registra extensões e blueprints; `core/` concentra configuração, autenticação e segurança; `modules/` organiza rotas por domínio; `services/` mantém regras reutilizáveis; e `models/` representa os dados persistidos.

## Instalação local

### Windows PowerShell

```powershell
git clone https://github.com/AdrianKoll/ServiceFlow.git
cd ServiceFlow
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux/macOS

```bash
git clone https://github.com/AdrianKoll/ServiceFlow.git
cd ServiceFlow
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Para desenvolvimento local, use SQLite e uma chave de sessão exclusiva:

```env
SERVICEFLOW_ENV=development
SESSION_SECRET=gere-uma-chave-aleatoria-e-exclusiva
DATABASE_URL=sqlite:///serviceflow_dev.sqlite3
SESSION_COOKIE_SECURE=false
RATELIMIT_STORAGE_URI=memory://
PORT=5000
```

Gere uma chave segura com:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

O arquivo `.env` é ignorado pelo Git e nunca deve ser enviado ao repositório.

O `.env.example` contém uma URL PostgreSQL como referência de produção. Para desenvolvimento SQLite, substitua `DATABASE_URL` conforme o exemplo acima.

## Banco de dados e migrações

O fluxo oficial de evolução do schema é Alembic. Antes de iniciar a aplicação em um ambiente novo ou após atualizar o código, execute:

```bash
alembic upgrade head
```

O bloco `if __name__ == "__main__"` de `app.py` também chama `run_migrations(app)` quando a aplicação é iniciada com `python app.py`. O comando `gunicorn app:app` importa a aplicação e não executa esse bloco; em produção, a migração deve ser uma etapa explícita do deploy.

`db.create_all()` permanece apenas como compatibilidade para demonstrações e testes. Ele não substitui migrações, não altera tabelas existentes e não deve ser usado como estratégia de deploy.

## Executar

```bash
python app.py
```

Acesse <http://127.0.0.1:5000>. O servidor inicia com debug desativado. Para produção, execute as migrações e use Gunicorn:

```bash
alembic upgrade head
gunicorn app:app
```

Em produção, defina `SERVICEFLOW_ENV=production`, `SESSION_SECRET`, `DATABASE_URL` apontando para PostgreSQL, `SESSION_COOKIE_SECURE=true` atrás de HTTPS e um `RATELIMIT_STORAGE_URI` compartilhado, como Redis. A aplicação recusa iniciar em produção sem `SESSION_SECRET` ou sem cookie seguro.

## Verificação HTTP

Com a aplicação em execução, verifique as páginas públicas:

```bash
python scripts/check_http.py
```

Para testar páginas autenticadas, não existem credenciais fixas no repositório. Informe credenciais de uma conta de teste por variáveis de ambiente:

```bash
SERVICEFLOW_CHECK_EMAIL=admin@example.com \
SERVICEFLOW_CHECK_PASSWORD='senha-de-teste-com-12-caracteres' \
python scripts/check_http.py
```

O script obtém o token CSRF da página de login antes de enviar as credenciais.

## Testes e qualidade

```bash
python -m pip install pytest
pytest -q
python -m compileall -q app.py core models modules services tests
```

O workflow em `.github/workflows/ci.yml` executa esses checks em pushes e pull requests direcionados à branch `main`, com permissão somente de leitura do conteúdo do repositório.

## Segurança implementada

- Senhas são armazenadas com hash via Werkzeug e o cadastro exige pelo menos 12 caracteres;
- métodos mutáveis exigem token CSRF, inclusive formulários públicos, uploads, restauração, reset e logout;
- TRACE é rejeitado e redirects baseados em `next`/`Referer` aceitam somente caminhos locais;
- o login aceita no máximo 5 tentativas por combinação de IP e e-mail a cada 15 minutos e responde com `429` ao atingir o limite;
- em produção, `SESSION_COOKIE_SECURE=true` é obrigatório; o cookie também é `HttpOnly` e `SameSite=Lax`;
- notificações só podem ser marcadas como lidas pelo usuário dono;
- mensagens são restritas ao tenant, aos participantes da conversa e, para edição/exclusão, ao autor da mensagem;
- consultas operacionais usam `core.tenant_policy`, com escopo por tenant em clientes, serviços, tarefas, agenda, financeiro, portal, dashboard, relatórios e analytics;
- IDs relacionados, como `client_id`, `service_id`, `responsible_id`, `assignee_id` e `user_id`, são validados dentro do tenant atual antes de criar ou atualizar registros;
- edições, exclusões, reset operacional e exportações são limitados ao tenant atual;
- testes negativos cobrem dois tenants, listagem cross-tenant, edição cross-tenant e associação de serviço a cliente de outra empresa;
- criação/edição de membros valida cargo, status e senha mínima;
- uploads de restauração têm limite de tamanho, são validados como SQLite e o arquivo recebido é removido após o processamento;
- headers básicos incluem `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Permissions-Policy`;
- o CI mantém `contents: read` e não contém credenciais de teste fixas.

## Limitações e pendências de segurança

A política de autorização por tenant foi implementada nos módulos operacionais e validada com testes negativos usando dois tenants. A migração `20261110_0004_tenant_not_null` torna `tenant_id` obrigatório e falha de propósito se encontrar registros órfãos. Antes do deploy, execute `alembic upgrade head` em uma cópia do banco e associe manualmente qualquer registro antigo sem tenant ao tenant correto.

Outras pendências para produção são:

1. usar Redis ou outro backend compartilhado no rate limiting;
2. exigir reautenticação para restauração, reset, download de backup e troca de senha, além de invalidar sessões antigas após troca de senha;
3. criptografar backups em repouso, aplicar retenção e auditoria; os backups atuais são cópias integrais SQLite sem criptografia;
4. validar uploads de avatar por conteúdo/magic bytes, dimensões e re-encode, não apenas pela extensão;
5. adicionar CSP com nonce/hash, HSTS somente quando HTTPS estiver garantido e revisar scripts/CDNs externos;
6. adicionar SAST, auditoria de dependências e secret scanning ao CI; os testes básicos de autorização cross-tenant já estão no projeto.

### Escopo de backup

O backup atual é **SQLite-only**. Os arquivos ficam em `instance/backups/{automaticos,manuais,restauracoes}` e o limite de upload é 10 MiB. O backup automático é criado sob demanda quando `/configuracoes` é acessado; não há scheduler configurado. Portanto, esse mecanismo não é um backup de produção PostgreSQL nem uma política de disaster recovery.

## Comentários e documentação de código

Os comentários e docstrings que explicam arquitetura, fluxo de migração, segurança, backup, dependências de foreign key e decisões de compatibilidade foram preservados. Comentários puramente decorativos ou ambíguos foram simplificados para descrever diretamente o comportamento da aplicação.

Não foram encontradas integrações ou comentários sobre modelos generativos. Os termos “automático” e “automatizado” existentes referem-se a tarefas determinísticas, como backup sob demanda, CI e comportamento da interface.

## Status

Projeto de portfólio em evolução. O isolamento por tenant está implementado na camada de aplicação e coberto por testes. O uso público ainda exige migração controlada do banco, rate limiting compartilhado, backups criptografados, reautenticação para operações destrutivas e hardening do ambiente HTTP.
