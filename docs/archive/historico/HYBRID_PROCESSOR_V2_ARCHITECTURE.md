# Arquitetura Refatorada - HybridQueryProcessorV2

## 📋 Visão Geral

O **HybridQueryProcessorV2** é uma refatoração completa do processador de queries híbrido, integrando:

1. ✅ **Sistema de fragmentação de queries** (FastQueryFragmenter) para GROQ 6000 TPM
2. ✅ **Busca de histórico/cache** no Supabase antes de processar
3. ✅ **Fallback guiado** pelos 6 chunks analíticos originais (evita redundância)
4. ✅ **Controle dinâmico** entre embeddings RAG e CSV com fragmentação
5. ✅ **Logging detalhado** para auditoria completa
6. ✅ **Camada de abstração LLM** consistente (LangChain)

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                   HybridQueryProcessorV2                        │
│                                                                 │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  QueryAnalyzer│  │ LLMManager   │  │MemoryManager     │   │
│  │  (semantic)   │  │ (abstraction)│  │ (Supabase)       │   │
│  └───────────────┘  └──────────────┘  └──────────────────┘   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │         FLUXO DE PROCESSAMENTO                        │    │
│  │                                                        │    │
│  │  1. Buscar Cache/Histórico (Supabase)                │    │
│  │        ↓                                               │    │
│  │  2. Analisar Query (LLM + QueryAnalyzer)             │    │
│  │        ↓                                               │    │
│  │  3. Buscar Chunks Existentes (RAG)                   │    │
│  │        ↓                                               │    │
│  │  4. Decidir Estratégia (rag_only/csv_fallback/       │    │
│  │                         csv_fragmented)               │    │
│  │        ↓                                               │    │
│  │  5. Processar baseado na estratégia                  │    │
│  │        ↓                                               │    │
│  │  6. Gerar Resposta (LLM com contexto)                │    │
│  │        ↓                                               │    │
│  │  7. Armazenar em Cache (24h TTL)                     │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Estratégias de Processamento

### 1. RAG ONLY
**Quando usar:**
- Chunks existentes cobrem ≥80% dos aspectos necessários
- ≥3 chunks relevantes encontrados
- Query simples

**Vantagens:**
- ⚡ Mais rápido (sem acesso a disco)
- 💰 Menor custo (apenas busca vetorial)
- 🎯 Contexto pré-otimizado

**Fluxo:**
```
Query → Embedding → Busca Vetorial → Chunks (6) → Contexto → LLM → Resposta
```

**Exemplo:**
```python
query = "Qual a distribuição de valores do dataset?"
# Usa chunks: metadata_distribution, metadata_central_variability
# Resposta em ~2s
```

---

### 2. CSV FALLBACK
**Quando usar:**
- Chunks cobrem <80% dos aspectos
- Query menciona análises específicas não cobertas
- Dataset cabe em memória sem fragmentar

**Vantagens:**
- 🎯 Preenche gaps específicos
- 🔄 Gera chunks complementares (não duplicados)
- 💾 Armazena novos chunks no Supabase

**Fluxo:**
```
Query → Chunks Existentes → Identificar Gaps → Carregar CSV (focado) 
    → Análise Complementar → Novos Chunks → Contexto Híbrido → LLM → Resposta
```

**Exemplo:**
```python
query = "Quais outliers na coluna Amount?"
# Chunks existentes: metadata_types, metadata_distribution
# Gap identificado: outliers detalhados
# Carrega CSV → Análise IQR → Gera chunk complementary_outliers
# Resposta em ~5s
```

---

### 3. CSV FRAGMENTED
**Quando usar:**
- Dataset grande (>3000 linhas ou >20 colunas)
- Query complexa (>50 palavras)
- Limite GROQ 6000 tokens seria ultrapassado

**Vantagens:**
- ✅ Respeita limite GROQ 6000 TPM
- 🚀 Usa FastQueryFragmenter (heurístico, 600x mais rápido)
- 📦 Processa fragmentos sequencialmente
- 🔗 Agrega resultados parciais

**Fluxo:**
```
Query → Análise → Carregar CSV → Fragmentação (Fast) 
    → Processar Fragmentos (paralelo) → Agregação → Chunks Fragmentados 
    → Contexto Completo → LLM → Resposta
```

**Exemplo:**
```python
query = "Correlação entre Amount, Time e V1-V28, identificando fraudes"
df.shape = (5000, 28)  # Grande!
# FastQueryFragmenter divide em:
# - Fragmento 1: Amount, Time, Class (linhas 0-1250)
# - Fragmento 2: V1-V14 (linhas 0-1250)
# - Fragmento 3: V15-V28 (linhas 0-1250)
# - ... (total 12 fragmentos)
# Cada fragmento ~5000 tokens < 6000 limite
# Resposta em ~15s
```

---

## 🧩 Componentes Integrados

### 1. FastQueryFragmenter
**Arquivo:** `src/llm/fast_fragmenter.py`

**Função:** Divide queries grandes em fragmentos menores

**Estratégias:**
- `COLUMN_GROUPS`: Divide por colunas (<50% mencionadas na query)
- `ROW_SEGMENTS`: Divide por linhas (query menciona "todas as colunas")
- `HYBRID`: Divide colunas E linhas (dataset muito grande)

**Performance:** ~1ms vs ~400ms (LLM-based)

```python
from src.llm.fast_fragmenter import fragment_query_fast

needs_frag, fragments, reason = fragment_query_fast(
    query="Correlação entre todas features",
    df=df,
    token_budget=TokenBudget(max_tokens_per_request=6000)
)

# Resultado:
# needs_frag = True
# fragments = [QueryFragment(...), QueryFragment(...), ...]
# reason = "Dataset grande - dividir por segmentos de linhas"
```

---

### 2. SupabaseMemoryManager
**Arquivo:** `src/memory/supabase_memory.py`

**Função:** Gerencia cache e histórico de queries

**Tabelas:**
- `agent_sessions`: Sessões de usuário
- `agent_conversations`: Histórico de queries/respostas
- `agent_context`: Cache e contexto (ContextType.CACHE)

**TTL:** 24 horas (configurável)

```python
# Buscar cache
cached = await memory_manager.get_context(
    session_id=session_id,
    context_type=ContextType.CACHE,
    context_key=cache_key
)

# Armazenar resultado
await memory_manager.save_context(
    session_id=session_id,
    context_type=ContextType.CACHE,
    context_key=cache_key,
    context_data={'result': result},
    expires_at=datetime.now() + timedelta(hours=24)
)
```

---

### 3. LLMManager (Abstração)
**Arquivo:** `src/llm/manager.py`

**Função:** Camada de abstração para múltiplos LLMs

**Providers:**
- Google Gemini (padrão)
- OpenAI GPT-4
- Groq (Llama)
- Fallback automático

```python
from src.llm.manager import get_llm_manager

llm_manager = get_llm_manager()

# Obter LLM com configuração
llm = llm_manager.get_llm(provider='google', temperature=0.2)

# Usar (async)
response = await llm.ainvoke("Analise este dataset...")
answer = response.content
```

---

## 📊 Decisão de Estratégia

### Algoritmo de Decisão

```python
def _decide_strategy(query, analysis, existing_chunks, force_csv):
    # 1. Force CSV?
    if force_csv:
        return 'csv_fragmented'
    
    # 2. Calcular cobertura dos chunks
    covered_aspects = identify_covered_aspects(existing_chunks)
    required_aspects = get_required_aspects(analysis['category'])
    
    coverage = len(covered ∩ required) / len(required)
    
    # 3. Decisão baseada em cobertura
    if coverage >= 0.8 AND len(existing_chunks) >= 3:
        return 'rag_only'  # ✅ Chunks suficientes
    
    # 4. Query pequena?
    if len(query.split()) < 50:
        return 'csv_fallback'  # CSV sem fragmentar
    
    # 5. Query grande
    return 'csv_fragmented'  # Requer fragmentação
```

### Mapeamento de Aspectos

**Chunks → Aspectos Cobertos:**

| Chunk Type | Aspectos Cobertos |
|------------|------------------|
| `metadata_types` | structure, schema, data_types |
| `metadata_distribution` | distribution, statistics_basic |
| `metadata_central_variability` | statistics, central_tendency |
| `metadata_frequency_outliers` | outliers, anomalies |
| `metadata_correlations` | correlation, relationships |
| `metadata_patterns_clusters` | patterns, trends |

**Query → Aspectos Necessários:**

| Categoria Query | Aspectos Necessários |
|----------------|---------------------|
| `statistics` | statistics, distribution |
| `correlation` | correlation |
| `outliers` | outliers, anomalies |
| `patterns` | patterns, trends |
| `structure` | structure, schema |

---

## 🔍 Fallback Guiado (Evita Redundância)

### Problema Original
❌ Processador antigo gerava chunks duplicados:
- CSV carregado → análise completa → chunks gerados
- Chunks sobrepunham com os 6 originais
- Memória desperdiçada

### Solução V2
✅ Usa chunks existentes como **guia**:

```python
# 1. Identificar o que JÁ EXISTE
covered = identify_covered_aspects(existing_chunks)
# covered = {'statistics', 'distribution', 'structure'}

# 2. Identificar o que FALTA (gaps)
required = get_required_aspects(query_category)
# required = {'statistics', 'outliers'}

gaps = required - covered
# gaps = {'outliers'}

# 3. Carregar CSV APENAS para gaps
if gaps:
    df = load_csv(source_id)
    csv_analysis = perform_focused_analysis(df, gaps)
    # Analisa SOMENTE outliers
    
    # 4. Gerar chunks COMPLEMENTARES
    new_chunks = generate_complementary_chunks(csv_analysis, covered)
    # Gera chunk 'complementary_outliers' (único, não duplicado)
```

### Benefícios
- 📉 **Reduz armazenamento:** Não duplica análises
- ⚡ **Mais rápido:** Análise focada (não completa)
- 🎯 **Preciso:** Preenche apenas gaps reais

---

## 🛡️ Garantias de Token Budget

### Limite GROQ: 6000 TPM

**TokenBudgetController:**
```python
class TokenBudget:
    max_tokens_per_request = 6000
    reserved_tokens = 500  # Para prompt/resposta
    safety_margin = 200     # Buffer de segurança
    
    available_tokens = 6000 - 500 - 200 = 5300
```

**Validação de Fragmentos:**
```python
def validate_fragment(fragment):
    estimated_tokens = estimate_tokens(fragment)
    
    if estimated_tokens > budget.available_tokens:
        raise ValueError("Fragmento excede limite!")
    
    return True
```

**Cálculo de Tokens:**
```python
# Regra aproximada: 4 caracteres = 1 token
def estimate_tokens(text):
    return len(text) // 4

# Para DataFrame:
def estimate_dataframe_tokens(df):
    # Colunas
    col_tokens = len(df.columns) * 10
    
    # Células
    cell_tokens = df.shape[0] * df.shape[1] * 5
    
    return col_tokens + cell_tokens
```

**Cálculo de Máximo de Linhas:**
```python
def calculate_max_rows(df, available_tokens):
    cols = len(df.columns)
    
    # Cada linha ≈ cols * 5 tokens
    tokens_per_row = cols * 5
    
    max_rows = available_tokens // tokens_per_row
    
    return max(1, max_rows)  # Mínimo 1 linha

# Exemplo:
# df com 25 colunas
# available_tokens = 5300
# tokens_per_row = 25 * 5 = 125
# max_rows = 5300 // 125 = 42 linhas por fragmento
```

---

## 📝 Logging Detalhado

### Níveis de Log

```python
# INFO: Eventos principais
logger.info("🔍 Processando query: {query[:100]}...")
logger.info("📊 Análise: COMPLEX | Categoria: correlation")
logger.info("✅ Estratégia: csv_fragmented")

# DEBUG: Detalhes internos
logger.debug("📦 CSV do cache: creditcard_abc123")
logger.debug("🔍 Buscando cache: a3f2b1c9...")

# WARNING: Situações anormais
logger.warning("⚠️ Nenhum chunk encontrado, fallback para CSV")
logger.warning("⚠️ Erro ao buscar cache: timeout")

# ERROR: Erros recuperáveis
logger.error("❌ Erro ao carregar CSV: FileNotFoundError")
logger.error("❌ Erro LLM: rate limit exceeded")
```

### Auditoria Completa

Cada processamento gera log estruturado:

```
📥 INÍCIO - Query: Correlação entre Amount e Time...
   Source: creditcard_abc123 | Session: sess_20250120_123456
   
🔍 Buscando cache: a3f2b1c9d4e5f6...
📊 Análise: COMPLEX | Categoria: correlation | Requer CSV: True
📦 Chunks encontrados: 4
   - metadata_types
   - metadata_distribution
   - metadata_central_variability
   - metadata_correlations

📊 Cobertura: 75.0% (3/4 aspectos)
🎯 Estratégia: csv_fallback | Razão: Chunks cobrem 75% dos aspectos
📊 Aspectos cobertos: {'statistics', 'distribution', 'structure'}
⚠️ Gaps identificados: {'correlation_detailed'}

📂 Carregando CSV para preencher gaps...
✅ CSV carregado: (5000, 28)
🎯 Análise focada nos gaps: ['correlation_detailed']
🆕 Gerando chunks complementares (evitando duplicação)
✅ 1 chunks complementares armazenados

🤖 LLM recomenda: csv_fallback
✅ SUCESSO - Tempo: 4.52s | Estratégia: csv_fallback
💾 Resultado armazenado em cache (TTL: 24h)
```

---

## 🧪 Testes de Integração

**Arquivo:** `test_hybrid_processor_v2_integration.py`

### Cenários Testados

1. **RAG ONLY:** Query simples com chunks suficientes
2. **CSV FALLBACK:** Query complexa, complementa com CSV
3. **CSV FRAGMENTED:** Dataset grande, requer fragmentação
4. **CACHE:** Segunda execução usa cache

### Executar Testes

```bash
# Testes de integração
python test_hybrid_processor_v2_integration.py

# Testes rápidos de fragmentação
python test_fast_fragmentation.py
```

### Métricas Esperadas

| Teste | Tempo | Estratégia | Cache |
|-------|-------|-----------|-------|
| RAG ONLY | ~2s | rag_only | ❌ |
| CSV FALLBACK | ~5s | csv_fallback | ❌ |
| CSV FRAGMENTED | ~15s | csv_fragmented | ❌ |
| CACHE (2ª exec) | ~0.5s | N/A | ✅ |

---

## 📚 Exemplos de Uso

### Exemplo 1: Query Simples (RAG ONLY)

```python
from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator

# Setup
processor = HybridQueryProcessorV2(
    vector_store=VectorStore(),
    embedding_generator=EmbeddingGenerator(),
    agent_name="my_agent"
)

# Processar
result = await processor.process_query(
    query="Qual a média da coluna Amount?",
    source_id="creditcard_abc123"
)

# Resultado
print(result['strategy_decision']['strategy'])  # → 'rag_only'
print(result['answer'])  # → "A média da coluna Amount é 88.35..."
print(result['processing_time_seconds'])  # → 2.1
```

### Exemplo 2: Query Complexa (CSV FALLBACK)

```python
result = await processor.process_query(
    query="Identifique outliers na coluna Amount usando método IQR",
    source_id="creditcard_abc123"
)

# Resultado
print(result['strategy_decision']['strategy'])  # → 'csv_fallback'
print(result['covered_aspects'])  # → ['statistics', 'distribution']
print(result['gaps_filled'])  # → ['outliers']
print(result['new_chunks_generated'])  # → 1
print(result['csv_accessed'])  # → True
```

### Exemplo 3: Dataset Grande (CSV FRAGMENTED)

```python
result = await processor.process_query(
    query="""Analise correlação entre Amount, Time e todas features V1-V28,
             identificando padrões de fraude e outliers significativos""",
    source_id="creditcard_large_5000rows",
    force_csv=True  # Forçar para garantir fragmentação
)

# Resultado
print(result['strategy_decision']['strategy'])  # → 'csv_fragmented'
print(result['fragments_count'])  # → 12
print(result['fragments_success'])  # → 12
print(result['fragmentation_reason'])  # → "Query complexa, fragmentação necessária"
```

### Exemplo 4: Usar Cache

```python
# Primeira execução
result1 = await processor.process_query(
    query="Média de Amount",
    source_id="creditcard_abc123"
)

print(result1['from_cache'])  # → False
print(result1['processing_time_seconds'])  # → 3.2

# Segunda execução (mesma query)
result2 = await processor.process_query(
    query="Média de Amount",
    source_id="creditcard_abc123",
    session_id=result1['session_id']  # IMPORTANTE: mesma sessão
)

print(result2['from_cache'])  # → True
print(result2['processing_time_seconds'])  # → 0.5 (6x mais rápido!)
```

---

## 🚀 Próximos Passos

### Melhorias Planejadas

1. **Fragmentação Paralela:**
   - Processar fragmentos em paralelo (asyncio)
   - Reduzir tempo de ~15s para ~5s

2. **Cache Inteligente:**
   - Cache por similaridade semântica (não apenas hash exato)
   - "Média de Amount" vs "Amount médio" → mesmo cache

3. **Estratégia TIME_WINDOWS:**
   - Implementar fragmentação temporal
   - Para queries como "Análise mensal de fraudes"

4. **Fallback LLM Automático:**
   - Se heurística tem confidence <0.7, usar LLM
   - Melhor de dois mundos: velocidade + precisão

5. **Métricas de Performance:**
   - Dashboard com métricas de cache hit/miss
   - Tempo médio por estratégia
   - Uso de tokens por query

---

## 📖 Referências

- **FastQueryFragmenter:** `src/llm/fast_fragmenter.py`
- **SimpleQueryAggregator:** `src/llm/simple_aggregator.py`
- **SupabaseMemoryManager:** `src/memory/supabase_memory.py`
- **LLMManager:** `src/llm/manager.py`
- **QueryAnalyzer:** `src/agent/query_analyzer.py`
- **Testes Rápidos:** `test_fast_fragmentation.py`
- **Testes Integração:** `test_hybrid_processor_v2_integration.py`

---

## 👥 Contribuindo

Ao contribuir para este módulo:

1. ✅ Manter logging detalhado em TODAS as funções principais
2. ✅ Usar camada de abstração LLM (não chamar APIs diretamente)
3. ✅ Validar token budget em novos fragmentadores
4. ✅ Adicionar testes para novos cenários
5. ✅ Documentar decisões técnicas no código

---

**Versão:** 2.0  
**Data:** 2025-01-20  
**Autor:** AI Minds Group
