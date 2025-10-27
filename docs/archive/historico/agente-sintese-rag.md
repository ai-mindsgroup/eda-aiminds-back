# Agente de Síntese RAG - Documentação

## Visão Geral
O `RAGSynthesisAgent` é um módulo especializado em consolidar respostas fragmentadas do sistema RAG, garantindo que as respostas sejam claras, estruturadas e alinhadas com o padrão esperado pelo usuário.

## Arquitetura
- **Localização:** `src/agent/rag_synthesis_agent.py`
- **Integração:** Chamado automaticamente pelo `RAGAgent` após recuperação de chunks do Supabase.
- **Dependências:** LangChain (para síntese via LLM), camada de abstração LLM (`src.llm.manager`).

## Funcionalidades
1. **Síntese via LLM:** Usa a camada de abstração LLM (atualmente Groq) para gerar respostas consolidadas baseadas nos chunks recuperados.
2. **Fallback Manual:** Se o LLM estiver indisponível, realiza pós-processamento manual para extrair e estruturar informações dos chunks.
3. **Formatação Estruturada:** Respostas seguem o padrão do modelo ideal, com seções para variáveis numéricas, categóricas, estatísticas e insights.

## Pipeline de Funcionamento
1. `RAGAgent` recupera chunks relevantes do Supabase.
2. Chunks são passados para `synthesize_response(chunks, question, use_llm=True)`.
3. Se `use_llm=True`, o prompt é enviado via `LLMManager.chat()`.
4. Resposta consolidada é retornada ao usuário.

## Configuração e Ajustes
- **Prompt de Síntese:** Definido em `SYNTHESIS_PROMPT`. Pode ser ajustado para diferentes tipos de perguntas.
- **Fallback Manual:** Regex para extrair tabelas Markdown e estatísticas. Ajustar expressões regulares se o formato dos chunks mudar.
- **Integração:** Para desabilitar síntese, passar `use_llm=False` no `RAGAgent`.

## Exemplo de Uso
```python
from src.agent.rag_synthesis_agent import synthesize_response

chunks = ["Chunk 1 com dados...", "Chunk 2 com estatísticas..."]
question = "Quais são os tipos de dados?"
response = synthesize_response(chunks, question)
print(response)
```

## Benefícios
- Respostas consistentes e claras, independentemente da fragmentação dos chunks.
- Flexibilidade para operar com diferentes LLMs via camada de abstração.
- Robustez com fallback manual para cenários sem LLM.

## Próximos Passos
- Testar com diferentes tipos de perguntas analíticas.
- Ajustar prompt para otimizar qualidade das respostas.
- Integrar métricas de avaliação de síntese.