# Auditoria Técnica - EDA AI Minds Backend

**Data:** 01/10/2025

---

## 1. Bibliotecas e Frameworks Utilizados

### 1.1. LangChain
- **Status:** NÃO utilizado no código-fonte.
- **Presença:** Listado em `requirements.txt` (várias dependências LangChain), mas não há nenhum import ou uso real nos arquivos Python.
- **Motivo:** Documentação previa uso, mas arquitetura final é 100% customizada.

### 1.2. Outras Dependências
- **Manipulação de dados:** `pandas`, `numpy`
- **Visualização:** `matplotlib`, `seaborn`, `plotly`
- **Banco de dados:** `supabase`, `psycopg`, `pgvector`
- **LLM Providers:** `groq`, `openai`, `google-ai-generativelanguage`
- **Embeddings:** `sentence-transformers`, `torch`, `transformers`
- **Utilitários:** `python-dotenv`, `coloredlogs`, `colorama`

---

## 2. Arquitetura dos Agentes

- **BaseAgent:** Classe abstrata, fornece logging, interface, integração com LLM Manager e sistema de memória.
- **OrchestratorAgent:** Orquestrador central, coordena agentes especializados, mantém contexto e histórico.
- **EmbeddingsAnalysisAgent:** Analisa dados exclusivamente via tabela embeddings do Supabase.
- **RAGAgent:** Agente de ingestão autorizado, faz chunking, gera embeddings, busca vetorial e respostas via LLM.
- **LLM Manager:** Abstração para múltiplos provedores (Groq, Google, OpenAI), com fallback automático.
- **Memória:** Sistema customizado usando SupabaseMemoryManager (`src/memory/supabase_memory.py`).

---

## 3. Flows, Chains e Métodos

- **Não há chains do LangChain.**
- **Fluxo multiagente:** Orchestrator recebe consulta, delega para agentes conforme tipo (análise, RAG, ingestão, visualização).
- **Memória:** Persistência de sessões, contexto e histórico via Supabase.
- **Chunking:** Implementado em `src/embeddings/chunker.py`.
- **Retrieval:** Busca vetorial via pgvector/Supabase.
- **LLM Calls:** Direto via SDKs, sem LangChain.

---

## 4. Visualização e Geração de Gráficos

- **Bibliotecas:** `matplotlib`, `seaborn`, `plotly`.
- **Fluxo:** Agentes chamam `GraphGenerator` (`src/tools/graph_generator.py`) para gerar PNG/base64 de histogramas, scatter, boxplot, barras, heatmap.
- **Entrega:** Imagem codificada + estatísticas retornadas ao usuário.

---

## 5. Funcionalidades Principais

- **Ingestão:** RAGAgent lê CSV, faz chunking, gera embeddings e armazena.
- **Análise:** EmbeddingsAnalysisAgent consulta embeddings e retorna insights.
- **Orquestração:** OrchestratorAgent decide qual agente acionar e integra respostas.
- **Memória:** SupabaseMemoryManager armazena histórico, contexto e resultados.
- **Visualização:** BaseAgent e GraphGenerator geram gráficos sob demanda.
- **RAG:** Busca vetorial e geração aumentada via embeddings.

---

## 6. Pontos Fortes, Limitações e Lacunas

### Pontos Fortes
- Arquitetura modular e extensível.
- Sistema de memória persistente e contextual.
- Visualização avançada integrada.
- Suporte a múltiplos provedores LLM com fallback.
- Conformidade: agentes de resposta não acessam CSV diretamente.

### Limitações
- **LangChain não utilizado:** Divergência entre documentação e implementação real.
- **Dependências desnecessárias:** LangChain ocupa espaço e pode causar conflitos.
- **Documentação desatualizada:** Menciona flows/chains que não existem.
- **Chunking e retrieval são customizados, não padronizados.**

### Lacunas
- Remover dependências LangChain do projeto para evitar confusão.
- Atualizar documentação para refletir arquitetura real.
- Avaliar integração futura com LangChain se desejado.

---

## 7. Recomendações

1. **Remover LangChain do requirements.txt** e dependências associadas.
2. **Atualizar toda documentação** para refletir arquitetura customizada.
3. **Padronizar chunking/retrieval** se desejar maior interoperabilidade.
4. **Revisar imports e referências** para evitar tentativas de acesso a arquivos obsoletos.
5. **Manter modularidade e clareza** na evolução do sistema.

---

## 8. Exemplos Relevantes

- `src/agent/base_agent.py`: Uso de SupabaseMemoryManager, integração com LLM Manager.
- `src/llm/manager.py`: Abstração multi-LLM, sem LangChain.
- `src/tools/graph_generator.py`: Geração de gráficos e estatísticas.
- `src/agent/rag_agent.py`: Chunking, embeddings, ingestão autorizada.
- `src/agent/csv_analysis_agent.py`: Análise via embeddings, sem acesso direto a CSV.

---

**Auditoria concluída.**

Sistema funcional, mas recomenda-se ajuste nas dependências e documentação para evitar confusões futuras.