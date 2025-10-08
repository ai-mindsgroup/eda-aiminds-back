# Integração de Memória Conversacional - EDA AI Minds

## Tabelas Integradas
- agent_context
- agent_conversations
- agent_memory_embeddings
- agent_sessions

## Modelos Pydantic
- `AgentContext`: contexto do agente por sessão
- `AgentConversation`: histórico de mensagens e respostas
- `AgentMemoryEmbedding`: embeddings de memória contextual
- `AgentSession`: dados da sessão do usuário

## Métodos de Integração
- save_agent_context / get_agent_context
- save_agent_conversation / get_agent_conversations
- save_agent_memory_embedding / get_agent_memory_embeddings
- save_agent_session / get_agent_session

## Logging Estruturado
Todas operações de leitura/escrita geram logs detalhados, ex:
```
[MEMORY] Contexto salvo: agent_id=csv_agent, session_id=abc123
[MEMORY] Conversa salva: agent_id=orchestrator, session_id=abc123
[MEMORY] Embedding salvo: agent_id=rag_agent, session_id=abc123
[MEMORY] Sessão salva: session_id=abc123
```

## Exemplos de Uso
```python
from src.memory.supabase_memory import save_agent_context, get_agent_context
from src.memory.models import AgentContext
ctx = AgentContext(agent_id="csv_agent", session_id="abc123", context={"last_query": "média"})
save_agent_context(ctx)
recuperado = get_agent_context("csv_agent", "abc123")
```

## Troubleshooting
- Verifique logs para erros de conexão ou validação
- Use scripts de debug em /debug para consultar registros
- Valide schemas no Supabase para garantir compatibilidade

## Expansão
- Novos agentes podem integrar memória facilmente usando os métodos e modelos criados
- Adaptação para novas tabelas basta criar novo modelo Pydantic e métodos de acesso
