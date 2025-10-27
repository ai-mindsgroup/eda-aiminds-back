# Rule — Gerenciamento de scripts utilitários no EDA AI Minds

- É proibida a geração de scripts utilitários ou ferramentas manuais fora do fluxo produtivo principal do sistema.
- Toda validação, teste ou função adicional deve ser feita via módulos já integrados aos entrypoints ([run_auto_ingest.py](...), [setup_and_run_fastapi_v3.py], etc) ou via testes integrados automatizados.
- A criação de novos scripts para debug ou diagnóstico só é permitida quando houver justificativa técnica explícita, aprovada e registrada na documentação do projeto.
- O Copilot ou qualquer engenheiro responsável deve documentar claramente a utilidade e o ciclo de vida desses scripts antes de sua inclusão. Scripts não justificados devem ser descartados.
- Objetivo: manter o sistema enxuto, auditável, escalável e fácil de manter, sem dívida técnica ou código morto.
1. Rule de Testes no Fluxo Produtivo
“Todos os testes automatizados e de validação precisam ser implementados diretamente sobre os entrypoints e módulos realmente usados na produção. Não é permitido criar scripts de teste paralelos desconexos. Cobertura de testes deve visar uso real, não cenários hipotéticos.”

2. Rule de Documentação e Rastreamento
“Qualquer decisão técnica importante (refatoração, feature, permissão de script) deve ser registrada no changelog do projeto ou na documentação de arquitetura. Implementações que não tenham respaldo em justificativa documentada podem ser removidas no ciclo de revisão.”

3. Rule de Compatibilidade
“Todo novo módulo, função ou patch deve, obrigatoriamente, ser validado em ambientes Linux e Windows usando o setup de produção. Quebra de compatibilidade entre sistemas não será aceita em PRs sem justificativa formal.”

4. Rule de Padrão Modular
“Contribuições devem garantir isolamento de dependências, exposição de API clara e nenhuma função/método em módulos core pode depender de helper scripts externos não versionados no fluxo principal.”

5. Rule de LLM e Agentes
“Não é permitido engessar lógica da LLM ou dos agentes em heurísticas fixas ou hardcodes não parametrizáveis. Qualquer fallback, heurística, threshold ou comportamento excepcional deve ser configurável via parametrização, mantendo a inteligência adaptativa como prioridade.”