<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# A partir do checklist abaixo gere um arquivo md exportavel

- [ ] Avaliar os prompts existentes que respondem perguntas gerais de descrição e padrões
- [ ] Refatorar prompts para análise completa e contextualizada, removendo hardcodes
- [ ] Ajustar parâmetros da LLM para chunk_size ≥ 1024, thresholds ~0.6-0.65, temperatura dinâmica entre 0.1-0.35, max_tokens 2048
- [ ] Garantir fallback inteligente entre dados vetoriais e análise do CSV completo
- [ ] Incorporar geração dinâmica de gráficos para perguntas sobre distribuição
- [ ] Desenvolver testes automatizados para validação das respostas e geração gráfica
- [ ] Validar respostas humanizadas completas, cobrindo todas colunas e linhas conforme o escopo
- [ ] Implementar logging detalhado para auditoria e rastreabilidade
- [ ] Revisar o fluxo de ingestão e limpeza de memória para evitar contaminação
- [ ] Preparar documentação clara para futuras manutenções e onboarding
- [ ] Realizar revisões rápidas (sprints curtos) para garantir entregas dentro do prazo

---

```md
# Checklist para Refatoração Ágil do Sistema EDA AI Minds

- [ ] Avaliar os prompts existentes que respondem perguntas gerais de descrição e padrões  
  _Revisar os prompts atuais para entender a cobertura e limitações na geração das respostas relacionadas à descrição dos dados e identificação de padrões._

- [ ] Refatorar prompts para análise completa e contextualizada, removendo hardcodes  
  _Modificar os prompts para que a análise seja dinâmica, abranja todo o dataset e não dependa de estruturas rígidas ou keywords hardcoded._

- [ ] Ajustar parâmetros da LLM para chunk_size ≥ 1024, thresholds ~0.6-0.65, temperatura dinâmica entre 0.1-0.35, max_tokens 2048  
  _Configurar parâmetros da LLM para garantir maior recall, qualidade e controle do custo computacional, adaptando a temperatura ao tipo da análise._

- [ ] Garantir fallback inteligente entre dados vetoriais e análise do CSV completo  
  _Implementar e validar o fluxo preferencial que busca respostas nos embeddings/vetores e, se insuficiente, realiza análise direta no CSV._

- [ ] Incorporar geração dinâmica de gráficos para perguntas sobre distribuição  
  _Adicionar geração automática e contextualizada de gráficos (ex: histogramas) para as perguntas que solicitam visualização de distribuições._

- [ ] Desenvolver testes automatizados para validação das respostas e geração gráfica  
  _Criar e integrar testes que validem tanto a qualidade das respostas quanto a correta geração e exibição dos gráficos._

- [ ] Validar respostas humanizadas completas, cobrindo todas colunas e linhas conforme o escopo  
  _Garantir que as respostas geradas sejam claras, completas e precisas, contemplando o dataset na totalidade, salvo exceções justificadas._

- [ ] Implementar logging detalhado para auditoria e rastreabilidade  
  _Adicionar logging estruturado das decisões do agente e do fluxo de análise para facilitar auditoria técnica e aprendizado futuro._

- [ ] Revisar o fluxo de ingestão e limpeza de memória para evitar contaminação  
  _Assegurar que, antes de cada nova análise, memórias, histórico e contexto sejam limpos adequadamente para evitar dados residuals._

- [ ] Preparar documentação clara para futuras manutenções e onboarding  
  _Escrever documentação detalhada das mudanças e do funcionamento para facilitar entendimento e manutenção por outros desenvolvedores._

- [ ] Realizar revisões rápidas (sprints curtos) para garantir entregas dentro do prazo  
  _Organizar o trabalho em ciclos pequenos com revisões rápidas para ajustes incrementais e entrega ágil do mínimo viável._
```

Esse arquivo está pronto para exportação e uso imediato no controle da refatoração do sistema. Quer ajuda para detalhar ações para algum item específico?

