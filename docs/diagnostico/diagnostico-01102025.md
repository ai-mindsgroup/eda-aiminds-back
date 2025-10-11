# Diagnóstico e Plano de Refatoração - EDA AI Minds Backend

**Data:** 01/10/2025

---

## Parte 1 - Diagnóstico Abrangente

### 1. Agentes Implementados e Abstração
- **BaseAgent:** Classe abstrata, interface comum, logging, integração com LLM Manager e memória.
- **OrchestratorAgent:** Orquestrador central, coordena agentes, integra respostas, mantém contexto.
- **EmbeddingsAnalysisAgent:** Analisa dados via tabela embeddings do Supabase, sem acesso direto a CSV.
- **RAGAgent:** Agente de ingestão autorizado, faz chunking, gera embeddings, busca vetorial e respostas via LLM.
- **GroqLLMAgent, GoogleLLMAgent, GrokLLMAgent:** Especialistas em LLMs específicos, todos herdam de BaseAgent.
- **LLM Manager:** Camada de abstração para múltiplos provedores LLM (Groq, Google, OpenAI), com fallback.

### 2. Memória via Supabase
- **Implementação:** Classe `SupabaseMemoryManager` em `src/memory/supabase_memory.py`.
- **Uso:** Persistência de sessões, contexto, histórico e resultados de análise. Integrado nos agentes via BaseAgent.
- **Validação:** Utilizado corretamente, com métodos para inicializar sessão, salvar interações e recuperar contexto.

### 3. Chunking, Retrieval e RAG
- **Chunking:** Implementado em `src/embeddings/chunker.py`, configurável (tamanho, overlap, estratégia).
- **Retrieval:** Busca vetorial via pgvector/Supabase, com queries otimizadas.
- **RAG:** RAGAgent realiza ingestão, chunking, geração de embeddings e busca contextualizada.
- **Performance:** Algoritmos eficientes, mas chunking/retrieval são customizados, não padronizados.

### 4. Uso Real de LangChain
- **Status:** NÃO utilizado nos agentes nem na camada de abstração.
- **Presença:** Listado em `requirements.txt`, mas sem importações ou uso real.
- **Dependências ligadas:** Diversas dependências LangChain presentes, mas não utilizadas.

### 5. Parâmetros Importantes
- **Temperatura, top_p, max_tokens:** Configuráveis via LLM Manager (`src/llm/manager.py`), passados nas chamadas aos modelos LLM.
- **top_k:** Não explicitamente configurado, mas pode ser adicionado na busca vetorial.

### 6. Consultas à Base Vetorial e Migrations
- **Consultas:** Realizadas via Supabase/pgvector, com métodos para busca por similaridade e ingestão de embeddings.
- **Migrations:** Scripts SQL versionados em `migrations/`, garantindo schema atualizado e índices otimizados.

### 7. Pontos Fortes
- Arquitetura modular, extensível e robusta.
- Memória persistente e contextual via Supabase.
- Visualização avançada integrada.
- Suporte a múltiplos provedores LLM com fallback.
- Conformidade: agentes de resposta não acessam CSV diretamente.

### 8. Lacunas e Sugestões Iniciais
- **LangChain não utilizado:** Divergência entre documentação e implementação.
- **Dependências desnecessárias:** LangChain ocupa espaço e pode causar conflitos.
- **Chunking/retrieval customizados:** Avaliar migração para soluções padronizadas.
- **Documentação desatualizada:** Atualizar para refletir arquitetura real.

---

## Parte 2 - Plano de Integração Gradual LangChain

1. **Fase 1: Gerenciamento de LLMs**
   - Integrar LangChain para gerenciamento de LLMs (ChatOpenAI, ChatGoogleGenerativeAI, etc.)
   - Refatorar LLM Manager para usar LangChain como backend, mantendo fallback customizado.
   - Testar respostas e performance em paralelo com implementação atual.

2. **Fase 2: Memória e Agentes**
   - Migrar sistema de memória para LangChain Memory, mantendo integração com Supabase.
   - Refatorar BaseAgent e OrchestratorAgent para usar agentes LangChain, preservando lógica customizada.
   - Validar persistência e recuperação de contexto.

3. **Fase 3: Chunking e Retrieval**
   - Migrar chunking e retrieval para LangChain TextSplitters e retrievers.
   - Integrar pgvector como vectorstore LangChain.
   - Testar precisão e performance comparando com solução atual.

4. **Fase 4: Workflows e Chains**
   - Implementar chains e workflows LangChain para orquestração multiagente.
   - Garantir que fluxos críticos sejam testados e validados.

5. **Testes Contínuos**
   - Para cada etapa, criar testes automatizados para validar desempenho, precisão e robustez.
   - Documentar resultados e ajustar parâmetros conforme necessário.

---

## Parte 3 - Limpeza e Atualização

1. **Remover dependências não utilizadas**
   - Excluir LangChain e pacotes relacionados do `requirements.txt` até que estejam realmente integrados.
   - Remover imports e referências obsoletas.

2. **Atualizar documentação**
   - Refletir arquitetura real, uso de memória, chunking e retrieval.
   - Documentar contratos claros para integração futura com frontend e API.

3. **Configuração de parâmetros**
   - Garantir que temperatura, top_p, top_k e max_tokens estejam documentados e configuráveis.
   - Centralizar configurações em arquivo dedicado (`src/settings.py`).

4. **Critérios de sucesso**
   - Sistema mantém ou eleva precisão e robustez das respostas.
   - Integração LangChain feita de forma incremental, segura e escalável.
   - Documentação alinhada com o código, facilitando onboarding e manutenção.
   - Configurações de parâmetros e arquitetura de memória/retrieval bem definidas e testadas.

---

**Relatório concluído.**

Se desejar, posso detalhar exemplos de código ou sugerir templates para cada etapa do plano de integração.