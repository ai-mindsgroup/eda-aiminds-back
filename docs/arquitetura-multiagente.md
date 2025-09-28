# Arquitetura Multiagente (Backend)

Este documento descreve o esqueleto inicial da arquitetura multiagente desenvolvido em 26/09/2025.

## Visão Geral
- **Objetivo:** Orquestrar agentes especializados (profiling → indexing → executor) em um pipeline sequencial.
- **Mensagem canônica:** `AgentMessage` (`src/agent/base_agent.py`) com `sender`, `content`, `metadata`.
- **Orquestração:** `AgentOrchestrator` (`src/rag/orchestrator.py`) conduz o fluxo e registra histórico.
**LLM:** Cliente Grok dedicado (`src/api/llm_client.py`) configurado via `src/settings.py`.
> OpenAI/LangChain permanecem fora de uso e serão reabilitados somente após revisão de custo/política.

## Módulos Principais
| Módulo | Responsabilidade |
|--------|------------------|
| `src/agent/base_agent.py` | Define `BaseAgent`, logging padrão e helper `build_message`. |
| `src/agent/profiling_agent.py` | Recebe `pandas.DataFrame`, calcula perfil básico (missing, colunas numéricas). |
| `src/agent/indexing_agent.py` | Gera insights estatísticos (describe, colunas com mais missing). |
| `src/agent/executor_agent.py` | Constrói plano de execução/prompt a partir dos insights. |
| `src/rag/orchestrator.py` | Encadeia agentes, mantém histórico (`OrchestrationResult`, `MessageExchange`). |
| `src/api/llm_client.py` | Cliente Grok (`LLMClient`) com camada de abstração para provedores futuros. |

## Fluxo Atual
1. **Ingestão:** `AgentOrchestrator.build_initial_message` recebe conteúdo `{ "data": DataFrame }`.
2. **Profiling:** `ProfilingAgent` emite perfil (`rows`, `columns`, `missing_values`).
3. **Indexing:** `IndexingAgent` resume estatísticas e colunas prioritárias.
4. **Execution:** `ExecutorAgent` produz plano (steps + contexto) para uso posterior pelo LLM.
5. **Histórico:** Cada `AgentMessage` é armazenado em `OrchestrationResult.history`.

```
┌────────────┐   ┌────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ DataFrame  │→→│ ProfilingAgent │→→│ IndexingAgent    │→→│ ExecutorAgent    │
└────────────┘   └────────────────┘   └─────────────────┘   └─────────────────┘
                                         │
                                         ▼
                               `AgentMessage` final
```

## Comunicação entre Agentes
- Interface baseada em `AgentMessage`.
- Metadados (`stage`) usados para rastrear progressão.
- `MessageExchange` (buffer) disponível para futuros cenários assíncronos ou branching.

## Extensibilidade Planejada
- Substituir/estender agentes adicionando novos módulos na pasta `src/agent/`.
- Integrar `LLMClient` (com Grok ativo) diretamente em `ExecutorAgent` ou no orquestrador para formatar prompts e consultar LLM.
- Adicionar **model router**, guardrails, e caching de respostas.
- Expandir `MessageExchange` para suportar eventos paralelos ou broadcast.

## Testes Automatizados
`tests/test_agents_pipeline.py` cobre:
- Fluxo sequencial completo entre agentes (usando DataFrame de exemplo).
- Helper `build_message` e validação de metadata.
- Validação de que o orquestrador exige ao menos um agente.

## Próximos Passos
- Implementar agentes adicionais (ex.: geração de embeddings, guardrails, executor LLM).
- Conectar `LLMClient` (Grok) ao pipeline real de respostas assim que o fluxo LLM estiver definido.
- Reavaliar a reativação do provedor OpenAI quando políticas e custos permitirem.
- Adicionar métricas, monitoramento e roteamento de modelos.
- Criar documentação de uso (CLI/serviço) e exemplos de prompts.
