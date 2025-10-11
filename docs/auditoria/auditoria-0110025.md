
# Auditoria Técnica - EDA AI Minds Backend

**Data:** 01/10/2025

**Este relatório refere-se a um trabalho em grupo, sem menção a autores individuais. Todas as análises, decisões e recomendações são resultado do esforço coletivo dos membros do projeto.**

---

## 1. Bibliotecas e Frameworks Utilizados


### 1.1. LangChain
- **Status:** Utilizado apenas como camada de abstração/fallback para múltiplos provedores LLM (OpenAI, Gemini, Groq).
- **Presença:** Listado em `requirements.txt` e importado em módulos de LLM, mas não há uso de chains ou workflows LangChain.
- **Motivo:** Arquitetura final prioriza implementação customizada para chunking, embeddings, RAG e memória. LangChain é usado apenas para abstração de LLMs, não para chains.

### 1.2. Outras Dependências
- **Manipulação de dados:** `pandas`, `numpy`
- **Visualização:** `matplotlib`, `seaborn`, `plotly`
- **Banco de dados:** `supabase`, `psycopg`, `pgvector`
- **LLM Providers:** `groq`, `openai`, `google-ai-generativelanguage`
- **Embeddings:** `sentence-transformers`, `torch`, `transformers`
- **Utilitários:** `python-dotenv`, `coloredlogs`, `colorama`

---


## 2. Arquitetura dos Agentes

- **OrchestratorAgent:** Coordenador central, roteia consultas, integra respostas, mantém contexto e histórico.
- **CSVAnalysisAgent:** Análise de dados CSV via Pandas, sem acesso direto ao arquivo após ingestão.
- **RAGAgent:** Agente de ingestão autorizado, realiza chunking, geração de embeddings e armazenamento vetorial no Supabase.
- **EmbeddingsAnalysisAgent:** Analisa dados exclusivamente via tabela embeddings do Supabase.
- **DataProcessor:** Interface unificada para carregamento, validação, limpeza e análise de dados.
- **GraphGenerator:** Geração de gráficos e visualizações (matplotlib, seaborn, plotly).
- **SupabaseMemoryManager:** Gerencia memória persistente, contexto e histórico de sessões.
- **LLM Manager:** Abstração para múltiplos provedores (Groq, Google, OpenAI), com fallback automático via LangChain.

---

## 3. Flows, Chains e Métodos


- **Não há chains/workflows do LangChain.**
- **Fluxo multiagente:** Orchestrator recebe consulta, delega para agentes conforme tipo (análise, RAG, ingestão, visualização).
- **Memória:** Persistência de sessões, contexto e histórico via SupabaseMemoryManager.
- **Chunking:** Implementado em `src/embeddings/chunker.py` (customizado).
- **Retrieval:** Busca vetorial via pgvector/Supabase.
- **LLM Calls:** Direto via SDKs ou abstração LangChain (fallback multi-provider).

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
- **LangChain não utilizado para chains/workflows:** Usado apenas para abstração de LLMs.
- **Dependências desnecessárias:** LangChain pode ser removido se não houver necessidade de fallback multi-provider.
- **Documentação desatualizada:** Menciona flows/chains que não existem.
- **Chunking, retrieval e memória são customizados, não padronizados.

### Lacunas

- Remover dependências LangChain do projeto se não houver necessidade de fallback multi-provider.
- Atualizar documentação para refletir arquitetura real e módulos implementados.
- Avaliar integração futura com LangChain para chains/workflows se desejado.
- Manter modularidade, clareza e documentação detalhada para facilitar onboarding e evolução futura.

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


## 9. Documentação Técnica Consolidada

Relatórios completos de conformidade, segurança, agentes e fluxos estão disponíveis em `docs/`:
	- `docs/ANALISE-CONFORMIDADE-REQUISITOS.md`
	- `docs/ANALISE-COPYRIGHT-SEGURANCA.md`
	- `docs/RELATORIO-AGENTES-PROMPTS-GUARDRAILS.md`
	- `docs/GUIA-CORRECAO-SEGURANCA.md`

**Auditoria concluída.**

Sistema funcional, aderente à arquitetura multiagente, com documentação técnica consolidada. Recomenda-se manter modularidade, clareza e atualização contínua dos documentos para evitar confusões futuras.