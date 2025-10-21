# Especificação da Suite de Testes - Etapa 2

**Arquivo:** `test_hybrid_processor_v2_etapa2_completo.py`  
**Data:** 2025-10-21  
**Autor:** GitHub Copilot (GPT-4.1)  
**Status:** ✅ PRONTO PARA EXECUÇÃO

---

## 📋 Visão Geral

Suite de testes abrangente para validar o **HybridQueryProcessorV2** refatorado, cobrindo:

- ✅ Fragmentação de queries e agregação de resultados
- ✅ Cache e histórico em tabelas Supabase
- ✅ Fallback acionado apenas quando necessário
- ✅ Simulação de limite de tokens GROQ (6000 TPM)
- ✅ Validação de logs estruturados
- ✅ Variações linguísticas no QueryAnalyzer

---

## 🧪 Testes Implementados

### TESTE 1: Fragmentação e Agregação de Resultados

**Objetivo:** Validar que queries grandes (>6000 tokens) são fragmentadas corretamente.

**Cenário:**
```python
# Dataset: 50,000 linhas x 30 colunas
# Query: ~7500 tokens (estoura limite GROQ)
# Esperado: Fragmentação em 2+ partes
```

**Validações:**
- ✅ Query > 6000 tokens é fragmentada
- ✅ Cada fragmento ≤ 6000 tokens
- ✅ Resultados agregados sem perda de informação
- ✅ Resposta final contém análise completa

**Assertions:**
```python
assert fragments_count > 1, "Query grande deve fragmentar"
assert max_fragment_tokens <= 6000, "Respeitar limite GROQ"
assert len(answer) > 100, "Resposta substantiva"
```

**Tempo Esperado:** 15-30s (dataset grande + fragmentação)

---

### TESTE 2: Cache e Histórico no Supabase

**Objetivo:** Validar persistência de cache e histórico na tabela `contexts`.

**Fluxo:**
1. **Primeira execução:** Processa query, gera cache
2. **Segunda execução:** Deve usar cache (speedup 2x+)
3. **Validação Supabase:** Verifica registros na tabela

**Validações:**
- ✅ Primeira execução NÃO usa cache
- ✅ Segunda execução USA cache (from_cache=True)
- ✅ Speedup mínimo de 2x
- ✅ Histórico salvo no Supabase (context_type=CACHE, USER_QUERY)
- ✅ TTL respeitado (24h padrão)

**Assertions:**
```python
assert not result1['from_cache'], "Primeira sem cache"
assert result2['from_cache'], "Segunda com cache"
assert elapsed2 < elapsed1 * 0.5, "Cache 2x+ mais rápido"
assert len(history) > 0, "Histórico no Supabase"
```

**Tempo Esperado:**
- Primeira: 4-6s
- Segunda (cache): <2s

---

### TESTE 3: Decisão Inteligente de Fallback

**Objetivo:** Validar que fallback é acionado apenas quando necessário.

**Cenários:**

#### A) Alta cobertura (≥80%) → RAG ONLY
```python
# Chunks mock: statistics, distribution, correlation, outliers
# Query: "Qual a distribuição estatística dos valores e outliers?"
# Esperado: RAG ONLY (chunks cobrem a query)
```

#### B) Baixa cobertura (<80%) → CSV FALLBACK
```python
# Query: "Analise padrões temporais em Time e V27 e V28"
# Esperado: CSV FALLBACK (aspectos não cobertos)
```

#### C) Query repetida → Sem redundância
```python
# Query já respondida
# Esperado: Usar chunks existentes, não gerar novos
```

**Validações:**
- ✅ Cobertura ≥80% usa RAG ONLY
- ✅ Cobertura <80% usa CSV FALLBACK
- ✅ Chunks existentes usados como guia
- ✅ Gaps preenchidos apenas quando necessário
- ✅ Sem regeneração redundante de chunks

**Assertions:**
```python
if coverage >= 80:
    assert strategy == 'rag_only'
    assert not csv_accessed
if coverage < 80:
    assert strategy in ['csv_fallback', 'csv_fragmented']
    assert csv_accessed
```

**Tempo Esperado:** 3-8s por cenário

---

### TESTE 4: Simulação de Limite GROQ (6000 TPM)

**Objetivo:** Testar comportamento em diferentes tamanhos de query.

**Casos de Teste:**

| Caso | Tokens | Esperado | Validação |
|------|--------|----------|-----------|
| **Query Pequena** | <2000 | Sem fragmentação | fragments_count ≤ 1 |
| **Query Média** | 2000-5000 | Sem fragmentação | fragments_count ≤ 1 |
| **Query Grande** | >6000 | Fragmentação obrigatória | fragments_count ≥ 2 |

**Método:**
```python
def create_large_query(target_tokens: int) -> str:
    """Cria query com tamanho específico em tokens"""
    base = "Analise dataset com features: Time, Amount, V1-V28..."
    padding = "insights adicionais..." * (target / 100)
    return base + padding
```

**Validações:**
- ✅ Query <6000: processamento direto
- ✅ Query >6000: fragmentação automática
- ✅ Cada fragmento ≤ 6000 tokens
- ✅ Resposta final agrega todos os fragmentos

**Assertions:**
```python
if query_tokens > 6000:
    assert fragments_count >= 2
    assert max_fragment_tokens <= 6000
else:
    assert fragments_count <= 1
```

**Tempo Esperado:**
- Pequena: 2-4s
- Média: 5-8s
- Grande: 15-25s

---

### TESTE 5: Validação de Logs Estruturados

**Objetivo:** Garantir logging detalhado em todas as etapas.

**Logs Esperados:**

| Etapa | Pattern | Nível | Exemplo |
|-------|---------|-------|---------|
| Início | "INÍCIO" | INFO | `📥 INÍCIO - Query: Qual a média...` |
| Análise | "Análise" | INFO | `📊 Análise: SIMPLE \| statistics` |
| Estratégia | "Estratégia" | INFO | `🎯 Estratégia: rag_only` |
| Chunks | "chunks" | INFO | `📦 Chunks encontrados: 5` |
| CSV | "CSV" | INFO | `✅ CSV carregado: (1000, 20)` |
| Fragmentação | "fragmentos" | INFO | `🔪 Query fragmentada: 3 partes` |
| Sucesso | "SUCESSO" | INFO | `✅ SUCESSO - Tempo: 5.23s` |

**Método:**
```python
# Capturar logs via handler temporário
log_capture = StringIO()
handler = logging.StreamHandler(log_capture)
root_logger.addHandler(handler)

# ... executar query ...

log_output = log_capture.getvalue()
assert "INÍCIO" in log_output
assert "Estratégia" in log_output
# etc...
```

**Validações:**
- ✅ Logs estruturados (JSON quando possível)
- ✅ Timestamps em todas as mensagens
- ✅ Níveis corretos (INFO, WARNING, ERROR)
- ✅ Cobertura mínima de 70% dos logs esperados

**Assertions:**
```python
coverage = len(logs_found) / len(expected) * 100
assert coverage >= 70, "Cobertura mínima de logs"
```

**Tempo Esperado:** 5-7s

---

### TESTE 6: Variações Linguísticas no QueryAnalyzer

**Objetivo:** Validar robustez do classificador com português variado.

**Casos de Teste:**

#### 1. Estatísticas (SIMPLE)
```python
queries = [
    "Qual a média de Amount?",          # Formal
    "Me dá a média da coluna Amount",   # Informal
    "Calcule o valor médio de Amount",  # Técnico
    "Quanto é a média dos valores?",    # Coloquial
]
expected: QueryCategory.STATISTICS, QueryComplexity.SIMPLE
```

#### 2. Correlações (SIMPLE)
```python
queries = [
    "Correlação entre Amount e Time",
    "Amount e Time estão correlacionados?",
    "Existe relação entre Amount e Time?",
    "Calcule Pearson entre Amount e Time",
]
expected: QueryCategory.CORRELATION, QueryComplexity.SIMPLE
```

#### 3. Distribuições (SIMPLE)
```python
queries = [
    "Distribuição de Amount",
    "Como é a distribuição dos valores?",
    "Mostre distribuição estatística",
    "Histograma de Amount",
]
expected: QueryCategory.DISTRIBUTION, QueryComplexity.SIMPLE
```

#### 4. Outliers (SIMPLE)
```python
queries = [
    "Outliers em Amount",
    "Valores atípicos na coluna Amount",
    "Anomalias em Amount",
    "Pontos fora da curva em Amount",
]
expected: QueryCategory.OUTLIERS, QueryComplexity.SIMPLE
```

#### 5. Queries Complexas (COMPLEX)
```python
queries = [
    "Analise correlação entre Amount, Time e V1-V28...",
    "Análise completa: stats, distribuições, correlações",
    "Padrões de fraude através de análise multivariada",
]
expected: QueryComplexity.COMPLEX
```

**Validações:**
- ✅ Classificação correta de categoria
- ✅ Classificação correta de complexidade
- ✅ Robustez a variações (formal/informal)
- ✅ Taxa de acerto ≥70%

**Assertions:**
```python
accuracy = (passed / total) * 100
assert accuracy >= 70, "Taxa mínima de acerto"
```

**Tempo Esperado:** <1s (apenas análise, sem LLM)

---

## 🚀 Como Executar

### Execução Completa

```powershell
python test_hybrid_processor_v2_etapa2_completo.py
```

### Execução Individual (para debug)

```python
import asyncio
from test_hybrid_processor_v2_etapa2_completo import test_01_query_fragmentation_and_aggregation

# Rodar apenas teste 1
asyncio.run(test_01_query_fragmentation_and_aggregation())
```

### Com Pytest

```powershell
pytest test_hybrid_processor_v2_etapa2_completo.py -v -s
```

---

## 📊 Resultados Esperados

### Taxa de Sucesso

```
Target: 100% (6/6 testes)
Mínimo aceitável: 83% (5/6 testes)
```

### Tempo de Execução

| Teste | Tempo Esperado |
|-------|----------------|
| 1. Fragmentação | 15-30s |
| 2. Cache | 6-8s |
| 3. Fallback | 10-20s |
| 4. Limite GROQ | 25-35s |
| 5. Logs | 5-7s |
| 6. Linguística | <1s |
| **TOTAL** | **60-100s** |

### Saída Esperada

```
================================================================================
🧪 SUITE DE TESTES COMPLETA - ETAPA 2
   HybridQueryProcessorV2 + FastQueryFragmenter + Supabase
================================================================================
⏱️ Início: 2025-10-21 01:45:00

################################################################################
# TESTE 1/6: Fragmentação e Agregação
################################################################################
...
✅ TESTE 1 PASSOU - Fragmentação e agregação funcionando

################################################################################
# TESTE 2/6: Cache e Histórico Supabase
################################################################################
...
✅ TESTE 2 PASSOU - Cache e histórico funcionando

... (continua para todos os testes)

================================================================================
📊 SUMÁRIO DOS TESTES - ETAPA 2
================================================================================
Fragmentação e Agregação........................... ✅ PASSOU
Cache e Histórico Supabase......................... ✅ PASSOU
Fallback Inteligente............................... ✅ PASSOU
Limite GROQ (6000 TPM)............................. ✅ PASSOU
Logs Estruturados.................................. ✅ PASSOU
Variações Linguísticas............................. ✅ PASSOU
================================================================================
⏱️ Tempo total: 78.34s
📈 Taxa de sucesso: 6/6 (100%)

🎉 TODOS OS TESTES PASSARAM!
```

---

## 🐛 Troubleshooting

### Problema: Rate Limit GROQ

**Sintoma:**
```
Error code: 413 - Request too large
Limit 6000, Requested 6582
```

**Solução:**
1. Verificar se FastQueryFragmenter está ativo
2. Confirmar `token_budget=6000` no processor
3. Validar que queries grandes estão sendo fragmentadas

### Problema: Cache não ativa

**Sintoma:**
```
⚠️ Cache não ativado (pode ser esperado em ambiente de teste)
```

**Causa:** Session ID diferente ou tabela `contexts` não criada

**Solução:**
1. Usar mesmo `session_id` na segunda execução
2. Rodar migrations: `python scripts/run_migrations.py`
3. Verificar conexão Supabase: `python check_db.py`

### Problema: Chunks não encontrados (Teste 3)

**Sintoma:**
```
Cobertura: 0.0%
Estratégia: csv_fallback (esperado: rag_only)
```

**Causa:** Chunks mock não inseridos no vector store

**Solução:**
```python
# Confirmar que populate_chunks_in_vectorstore foi executado
await populate_chunks_in_vectorstore(vector_store, mock_chunks)
await asyncio.sleep(1)  # Aguardar propagação
```

### Problema: Logs não capturados (Teste 5)

**Sintoma:**
```
Cobertura de logs: 20% (2/10)
```

**Causa:** Handler de log não configurado corretamente

**Solução:**
```python
# Garantir que handler está no root logger
root_logger = logging.getLogger()  # SEM nome
root_logger.addHandler(handler)
```

---

## 📚 Dependências

### Módulos Python
```python
asyncio, pandas, numpy, hashlib, json, datetime, pathlib, logging
```

### Módulos Internos
```python
src.agent.hybrid_query_processor_v2
src.agent.query_analyzer
src.agent.fast_query_fragmenter
src.embeddings.vector_store
src.embeddings.generator
src.memory.supabase_memory
src.llm.manager
src.utils.logging_config
```

### Configurações Necessárias
- ✅ Supabase configurado (`.env` com credenciais)
- ✅ Migrations executadas (`python scripts/run_migrations.py`)
- ✅ GROQ API key configurada
- ✅ Python 3.10+

---

## 🔄 Manutenção

### Adicionar Novo Teste

```python
async def test_07_meu_novo_teste():
    """Descrição do teste."""
    print(f"\n{'='*80}")
    print("🧪 TESTE 7: MEU NOVO TESTE")
    print(f"{'='*80}")
    
    # Setup
    # ... código ...
    
    # Validações
    assert resultado == esperado
    
    print("\n✅ TESTE 7 PASSOU")
    return resultado

# Adicionar em run_all_etapa2_tests():
tests = [
    # ... testes existentes ...
    ("Meu Novo Teste", test_07_meu_novo_teste),
]
```

### Atualizar Expectativas

Editar seção de cada teste para refletir mudanças na arquitetura.

---

## 📖 Referências

- [HybridQueryProcessorV2 Architecture](HYBRID_PROCESSOR_V2_ARCHITECTURE.md)
- [FastQueryFragmenter](../src/agent/fast_query_fragmenter.py)
- [QueryAnalyzer](../src/agent/query_analyzer.py)
- [Supabase Memory](../src/memory/supabase_memory.py)

---

**Última atualização:** 2025-10-21 02:00 BRT  
**Status:** ✅ PRONTO PARA EXECUÇÃO  
**Cobertura:** 6 testes / 100% das funcionalidades da Etapa 2
