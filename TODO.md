# TODO — Dashboard real, temas e publicação permanente

## Dados reais na dashboard

- [ ] A rota do dashboard deve fornecer séries e agregações calculadas somente a partir dos registros do tenant atual.
- [ ] Todos os cards devem exibir dados persistidos ou uma derivação claramente identificada; nenhum valor demonstrativo fixo deve permanecer.
- [ ] Os gráficos de serviços, financeiro e distribuição devem consumir os dados enviados pelo backend.
- [ ] Os filtros de período devem alterar as séries exibidas ou indicar que o período ainda não está disponível.
- [ ] O estado vazio deve ser legível quando não houver serviços, clientes, tarefas ou transações.

## Temas

- [ ] O modo escuro deve manter a paleta oficial e contraste legível.
- [ ] O modo claro deve aplicar superfícies, textos, bordas, gráficos, tiles e controles claros em toda a dashboard.
- [ ] A alternância persistida de tema deve continuar funcionando após login e navegação.
- [ ] Componentes SVG e gráficos devem usar tokens, não cores escuras fixas incompatíveis com o modo claro.

## Responsividade

- [ ] Desktop deve preservar a composição Bento sem sobreposição.
- [ ] Tablet deve reduzir a grade sem cortar cards ou gráficos.
- [ ] Mobile deve usar uma coluna, permitir leitura dos dados e evitar overflow horizontal.
- [ ] Telas estreitas devem ajustar tipografia, controles, cards empilhados e gráficos.

## Qualidade e publicação

- [ ] Adicionar testes para o contrato de dados da dashboard e regressões de tema.
- [ ] Executar pytest, compilação Python, validação de templates e `git diff --check`.
- [ ] Criar commits separados por etapa e publicar cada commit validado em `origin/main`.
- [ ] Preparar e validar o runtime permanente com health check e porta configurável.
