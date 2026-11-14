# Plano de melhoria e publicação do ServiceFlow

## Objetivo

Entregar o ServiceFlow como site permanente, mantendo a aplicação Flask existente, com dashboard baseado em dados reais do tenant atual, gráficos coerentes com as entidades persistidas, modo claro e escuro realmente funcionais e responsividade consistente em desktop, tablet e mobile.

## Diagnóstico atual

- A rota `/dashboard` já consulta KPIs, serviços, clientes, usuários, tarefas e transações com escopo por `tenant_id`.
- O template Bento ainda contém valores demonstrativos: barras diárias calculadas artificialmente, distribuição com acréscimos fixos, workspaces hardcoded, tempo médio fixo, throughput artificial e meta sem origem persistida.
- Os dados de gráficos financeiros e de status são calculados no backend, mas não são usados pelo dashboard Bento.
- O gráfico principal tem controles de período que apenas alteram o estado visual e não alteram a série.
- O `web3-bento.css` fixa superfícies escuras, portanto o modo claro não cobre a dashboard.
- Há breakpoints gerais, mas faltam regras específicas para a grade Bento no modo claro e para a escala dos tiles em larguras pequenas.

## Implementação

1. **Dados reais e contrato da dashboard**
   - Adicionar séries diárias e métricas derivadas apenas de registros persistidos do tenant atual.
   - Remover números fictícios e rótulos que afirmam metas ou tempos não existentes no modelo.
   - Exibir estado vazio explícito quando o tenant ainda não possui dados.
   - Usar no template as séries de serviços, financeiro, status, atividade, clientes, equipe e tarefas fornecidas pela rota.
   - Fazer os controles de período alterarem as séries reais disponíveis.

2. **Temas**
   - Substituir cores fixas do Bento por tokens da paleta oficial.
   - Criar overrides completos para `.light` e `.dark`, incluindo tiles, SVGs, pills, cards empilhados, bordas e textos.
   - Garantir que a personalização de cor não quebre o contraste dos dois temas.

3. **Responsividade**
   - Definir grid Bento para desktop, tablet, mobile e telas estreitas.
   - Corrigir overflow horizontal, dimensões mínimas, tipografia, cards empilhados, gráficos e controles.
   - Validar renderização nos breakpoints relevantes.

4. **Qualidade e publicação**
   - Adicionar testes de contrato para os dados reais da dashboard e testes de regressão para tema.
   - Rodar testes, compilação, validação de templates e verificações de CSS.
   - Registrar cada etapa em commit separado e publicar em `origin/main`.
   - Preparar o projeto para publicação permanente com Dockerfile, health check, porta configurável e manifest de rotas, caso a configuração da plataforma esteja disponível.

## Design

A referência Web3 Bento enviada pelo usuário permanece como direção visual: superfícies densas, composição modular assimétrica, dados em monoespaçado, alto contraste controlado e cores semânticas da paleta oficial. A interação deve priorizar leitura rápida e revelar detalhes por hover/foco sem ocultar dados essenciais. O modo claro usará as variáveis claras da mesma paleta, sem inverter componentes arbitrariamente.

## Estrutura envolvida

- `modules/main/routes.py`: composição do contexto do dashboard.
- `services/analytics.py`: consultas e séries agregadas por tenant.
- `templates/dashboard.html`: tiles, gráficos e estados vazios.
- `static/css/web3-bento.css`: tokens e layout Bento.
- `static/css/responsive.css`: breakpoints globais e específicos da dashboard.
- `static/css/theme.css` e `static/css/variables.css`: temas e tokens.
- `tests/test_smoke.py`: regressões de dados e isolamento multi-tenant.
