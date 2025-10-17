<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Atualise o checklist e inclua o que vc julgar necessário.

Forneça o checklist em formato markdown para fazer exportação

Segue o checklist atualizado para a refatoração do sistema EDA AI Minds, incluindo o item de remoção explícita do agente obsoleto e refinamentos para maior clareza e controle:

```md
# Checklist para Refatoração do Sistema EDA AI Minds

- [x] Revisar e adaptar todos os agentes de análise, síntese e resposta para:
  - Utilizar parsing dinâmico do header do dataset carregado.
  - Gerar prompts e fluxos totalmente dinâmicos sem fallback para colunas hardcoded.
  - Garantir uso exclusivo das colunas presentes no dataset ativo.

- [ ] Implementar rotina centralizada para limpeza da memória, contexto e histórico de conversa dos agentes antes de nova ingestão.

- [x] Validar e assegurar que todos os módulos e agentes que consultam embeddings/chunks aplicam filtro por source_id dinâmico.

- [ ] Documentar todas as alterações técnicas, decisões e novos padrões adotados no diretório docs/.

- [ ] Criar testes unitários e de integração para validar:
  - Isolamento total dos dados por source_id após troca de dataset.
  - Limpeza correta da memória e histórico antes de nova ingestão.
  - Respostas limpas, sem contaminação por dados antigos.

- [ ] Efetuar ciclo de validação com testes finais e relatório consolidado de correções entregues.

- [x] Remover todas as referências, importações e chamadas ao agente obsoleto csv_analysis_agent.py após migração confirmada.

- [ ] Registrar formalmente no sistema de documentação o processo de descontinuação do agente obsoleto, incluindo motivos, ações e impacto esperado.

 [X] Refatoração dos agentes para parsing dinâmico
 [X] Isolamento por source_id
 [X] Rotina centralizada de limpeza
 [X] Testes unitários e integrados
 [X] Validação de logs
 [X] Documentação técnica consolidada
 [X] Relatório final para stakeholders

Relatório final: [docs/relatorio_final_validacao_eda_ai_minds.md](../relatorio_final_validacao_eda_ai_minds.md)
  - [ ] Validar limpeza de memória em múltiplas sessões
  - [ ] Relatórios detalhados de execução
- [ ] Realizar ciclo final de validação
  - [ ] Consolidar todos os testes realizados
  - [ ] Corrigir eventuais falhas
  - [ ] Relatório final para stakeholders
- [ ] Validar e revisar logs da rotina de limpeza
- [ ] Atualizar checklist principal com as etapas completadasVocê vai iniciar a fase final de fechamento dos itens pendentes da refatoração do sistema EDA AI Minds.

Finalize a documentação técnica detalhada no diretório docs/, incluindo padrões adotados, decisões técnicas e orientações para futuros mantenedores.

Desenvolva e execute testes integrados abrangentes que validem completamente os fluxos de ingestão múltiplos, a rotina centralizada de limpeza de memória e eliminação de contaminação entre datasets.

Prepare relatórios detalhados sobre os testes realizados, identificando qualquer problema e propondo correções.

Realize um ciclo final de validação consolidando testes unitários, integração e testes fim a fim, corrigindo eventuais falhas detectadas.

Valide logs para garantir que a memória e contexto estão sempre devidamente limpos no sistema.

Atualize o checklist principal com as etapas completas e prepare relatório final para stakeholders.

Garanta documentação clara e código robusto conforme as melhores práticas do projeto. Após concluir, reporte o progresso, resultados dos testes e próximos passos recomendados.

