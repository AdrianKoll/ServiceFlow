# ServiceFlow

O ServiceFlow é uma aplicação web de gestão de serviços desenvolvida em Flask. O sistema centraliza clientes, serviços, tarefas, agenda, financeiro, mensagens, relatórios e configurações em uma interface responsiva.

## Funcionalidades

- Dashboard com indicadores operacionais;
- cadastro e acompanhamento de clientes e serviços;
- tarefas, responsáveis, prazos e agenda;
- controle financeiro de entradas e saídas;
- mensagens e notificações internas;
- relatórios de desempenho;
- autenticação, perfis e permissões por função;
- configurações de perfil e aparência;
- backup, restauração e reset operacional com acesso administrativo;
- suporte a SQLite para desenvolvimento e PostgreSQL para produção.

## Stack

- Python 3.11+
- Flask 3
- Flask-SQLAlchemy e SQLAlchemy
- Alembic
- Jinja2, HTML, CSS e JavaScript
- SQLite para desenvolvimento local
- PostgreSQL recomendado para produção
- Gunicorn para execução em produção

## Estrutura do projeto

```text
ServiceFlow/
├── app.py                    # Fábrica e bootstrap da aplicação
├── core/                     # Configuração, autenticação e recursos transversais
├── models/                   # Entidades SQLAlchemy
├── modules/                  # Blueprints separados por domínio
├── services/                 # Regras reutilizáveis e serviços auxiliares
├── migrations/               # Migrações Alembic
├── templates/                # Templates Jinja2
├── static/                   # CSS, JavaScript e imagens
├── tests/                    # Testes automatizados
├── .env.example              # Modelo público de configuração
├── requirements.txt          # Dependências de produção
└── .github/workflows/ci.yml  # Pipeline de testes
```

A aplicação usa uma divisão por responsabilidade: `app.py` registra extensões e blueprints; `core/` concentra configurações e segurança; `modules/` organiza rotas por domínio; `services/` mantém regras reutilizáveis; e `models/` representa os dados persistidos.

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

Para desenvolvimento local, o projeto usa SQLite quando `DATABASE_URL` não é definida. A chave `SESSION_SECRET` deve ser trocada por um valor aleatório exclusivo:

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

## Executar

```bash
python app.py
```

Acesse <http://127.0.0.1:5000>. O servidor inicia com debug desativado. Para produção, use Gunicorn:

```bash
gunicorn app:app
```

Em produção, defina `SERVICEFLOW_ENV=production`, `SESSION_SECRET`, `DATABASE_URL` apontando para PostgreSQL e `SESSION_COOKIE_SECURE=true` quando a aplicação estiver atrás de HTTPS. O sistema recusa iniciar em produção sem uma chave de sessão configurada.

## Testes e qualidade

Instale o executor de testes e execute:

```bash
python -m pip install pytest
pytest -q
python -m compileall -q app.py core models modules services tests
```

O workflow em `.github/workflows/ci.yml` executa esses checks em pushes e pull requests direcionados à branch `main`. O pipeline possui somente permissão de leitura do conteúdo do repositório.

## Segurança operacional

As rotas administrativas de backup, restauração e reset exigem autenticação e perfil `admin`. Backups de restauração aceitam somente arquivos ZIP, limitam o tamanho do upload e validam a assinatura do banco SQLite extraído. O reset cria uma cópia preventiva antes de remover dados operacionais.

Senhas devem ter pelo menos 12 caracteres e são armazenadas com hash. Segredos, arquivos `.env`, bancos locais, uploads e backups são excluídos pelo `.gitignore`.

Todos os métodos mutáveis exigem token CSRF, inclusive os formulários públicos e o logout. O login aceita no máximo 5 tentativas por combinação de IP e e-mail a cada 15 minutos e responde com `429` quando o limite é atingido. Em produção com múltiplos processos/instâncias, configure `RATELIMIT_STORAGE_URI` para um backend compartilhado, como Redis, em vez do padrão `memory://`.

Antes de disponibilizar o sistema publicamente, ainda é necessária uma revisão específica da infraestrutura, habilitação de HTTPS, revisão de autorização por recurso e adoção de migrações versionadas em vez de depender apenas de `db.create_all()`.

## Status

Projeto de portfólio em evolução. A base atual prioriza organização modular, configuração segura, documentação reproduzível, testes de fumaça e integração contínua.
