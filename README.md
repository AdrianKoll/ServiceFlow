# ServiceFlow

ServiceFlow é um sistema web de gestão de serviços desenvolvido em Flask. O objetivo do projeto é centralizar operações de pequenos negócios e equipes prestadoras de serviço, oferecendo controle de clientes, ordens de serviço, tarefas, agenda, financeiro, mensagens, relatórios e configurações em uma interface responsiva.

Este repositório foi organizado para facilitar manutenção, evolução e deploy futuro. A estrutura separa rotas, modelos, serviços, helpers, templates e arquivos estáticos de forma compatível com projetos Flask profissionais.

## Objetivo do sistema

O ServiceFlow ajuda prestadores de serviço e pequenos negócios a acompanharem o fluxo operacional do atendimento: cadastro de clientes, execução de serviços, responsáveis, prazos, tarefas, eventos, lançamentos financeiros e visão gerencial por relatórios.

## Funcionalidades principais

- Dashboard com indicadores operacionais.
- Cadastro e gestão de clientes.
- Cadastro e acompanhamento de serviços.
- Gestão de tarefas em fluxo de trabalho.
- Agenda de eventos e compromissos.
- Controle financeiro de entradas e saídas.
- Mensagens e notificações internas.
- Relatórios de desempenho.
- Configurações de perfil, tema e aparência.
- Estrutura preparada para planos/assinatura e recursos bloqueados por plano.

## Tecnologias usadas

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Alembic
- Jinja2
- HTML5
- CSS3 modular
- JavaScript
- SQLite para desenvolvimento local
- PostgreSQL recomendado para produção
- Gunicorn para deploy
- python-dotenv para variáveis de ambiente

## Estrutura de pastas

```text
flask_app/
├── app.py                    # Application factory, registro de extensões e blueprints
├── requirements.txt          # Dependências do projeto
├── alembic.ini               # Configuração de migrações
├── .env.example              # Exemplo seguro de variáveis de ambiente
├── .gitignore                # Arquivos que não devem ir para o GitHub
├── core/                     # Configurações, segurança, helpers globais e formatadores
├── models/                   # Modelos SQLAlchemy separados por entidade
├── modules/                  # Blueprints/rotas separados por domínio funcional
│   ├── agenda/
│   ├── auth/
│   ├── clientes/
│   ├── financeiro/
│   ├── main/
│   ├── mensagens/
│   ├── relatorios/
│   ├── servicos/
│   └── tarefas/
├── services/                 # Lógica de negócio reutilizável e serviços auxiliares
├── migrations/               # Migrações Alembic
├── templates/                # Templates Jinja2
├── static/
│   ├── css/
│   │   ├── variables.css     # Cores, fontes, espaçamentos, bordas e sombras
│   │   ├── base.css          # Reset, tipografia e estilos globais
│   │   ├── layout.css        # Estrutura raiz e mensagens flash
│   │   ├── sidebar.css       # Sidebar e navegação lateral
│   │   ├── topbar.css        # Header, busca, notificações e perfil
│   │   ├── components.css    # Cards, botões, formulários e componentes reutilizáveis
│   │   ├── dashboard.css     # Estilos específicos do dashboard
│   │   ├── landing.css       # Páginas públicas/comerciais
│   │   ├── responsive.css    # Breakpoints finais de responsividade
│   │   └── modules/          # CSS específico de páginas/módulos
│   ├── js/                   # JavaScript da aplicação
│   ├── img/                  # Imagens versionáveis do projeto
│   ├── assets/               # Arquivos estáticos auxiliares
│   └── uploads/              # Uploads locais gerados em execução
└── instance/                 # Banco local e arquivos de runtime não versionáveis
```

## Arquitetura aplicada

A organização segue uma divisão por responsabilidade:

- `app.py`: cria a aplicação, inicializa extensões e registra blueprints.
- `core/`: concentra configurações, segurança, contexto global e helpers transversais.
- `models/`: representa as entidades do banco de dados.
- `modules/`: concentra as rotas por domínio funcional, evitando um arquivo único gigante.
- `services/`: guarda regras e cálculos reutilizáveis fora das rotas.
- `templates/`: cuida apenas da camada de apresentação Jinja2.
- `static/css/`: separa estilos por camada e por módulo para facilitar manutenção.

Essa estrutura permite crescer o sistema sem misturar regra de negócio, rotas, banco de dados e interface.

## Como alterar as cores do sistema

As cores principais ficam em:

```text
static/css/variables.css
```

Exemplo:

```css
:root {
  --primary: #6366f1;
  --primary-hover: #5558e3;
  --primary-alpha: rgba(99, 102, 241, 0.15);
}
```

Para trocar a identidade visual do sistema, altere esses tokens. O restante dos arquivos CSS usa `var(--primary)`, `var(--bg)`, `var(--text)`, `var(--border)` e demais variáveis globais.

A ordem de importação dos estilos fica em `templates/base.html`:

1. `variables.css`
2. `base.css`
3. `layout.css`
4. `sidebar.css`
5. `topbar.css`
6. `components.css`
7. CSS de páginas/módulos
8. `responsive.css`

`responsive.css` deve permanecer por último para sobrescrever regras nos breakpoints mobile/tablet.

## Instalação local

### 1. Clonar ou extrair o projeto

```bash
cd flask_app
```

### 2. Criar ambiente virtual

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
copy .env.example .env
```

Edite o `.env` com os dados reais do ambiente. Nunca envie `.env` para o GitHub.

Variáveis principais:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/serviceflow
SESSION_SECRET=troque-por-uma-chave-longa-e-aleatoria
PORT=5000
```

Para desenvolvimento local sem PostgreSQL, o sistema usa SQLite automaticamente caso `DATABASE_URL` não esteja definido.

### 5. Executar o projeto

```bash
python app.py
```

Acesse:

```text
http://localhost:5000
```

## Banco de dados e migrações

O projeto possui suporte a Alembic. Para ambientes locais simples, o bootstrap cria tabelas quando necessário. Para produção, prefira usar PostgreSQL e controlar alterações de schema por migrações.

Arquivos de banco local ficam em `instance/` e não devem ser versionados.

## Preparação para deploy

Checklist recomendado antes de publicar:

- Definir `SESSION_SECRET` forte no ambiente de produção.
- Usar PostgreSQL em vez de SQLite.
- Configurar `DATABASE_URL` no painel da hospedagem.
- Definir `SESSION_COOKIE_SECURE=true` quando usar HTTPS.
- Não subir `.env`, `.venv`, `instance/`, bancos locais ou caches.
- Usar Gunicorn em produção:

```bash
gunicorn app:app
```

## Segurança e manutenção

Este pacote foi limpo para evitar envio de arquivos sensíveis ou desnecessários:

- `.env` real não deve ser versionado.
- Bancos locais em `instance/` não devem ir para o GitHub.
- `.venv/` não deve ser enviado.
- `__pycache__/` não deve ser enviado.
- Uploads gerados em execução não devem ser enviados, exceto `.gitkeep` para manter a pasta.

Use `.env.example` apenas como modelo público.

## Boas práticas para evoluir o projeto

- Criar um novo blueprint dentro de `modules/<nome>/` para cada grande domínio funcional.
- Criar CSS específico em `static/css/modules/<nome>.css` quando a tela tiver estilos próprios.
- Manter componentes globais em `components.css` apenas quando forem reutilizáveis.
- Manter tokens visuais em `variables.css`.
- Evitar lógica de negócio pesada dentro das rotas; mover para `services/`.
- Evitar templates grandes demais; considerar includes/macros Jinja quando uma tela crescer muito.

## Melhorias futuras sugeridas

- Criar testes automatizados para rotas críticas.
- Adicionar camada de repositories caso a lógica de banco cresça.
- Criar macros Jinja para cards, tabelas, formulários e badges repetidos.
- Adicionar pipeline de lint/format para padronização de código.
- Criar documentação de deploy específica para Render, Railway, PythonAnywhere ou VPS.
- Preparar seed de dados demonstrativos para apresentação a clientes/recrutadores.
