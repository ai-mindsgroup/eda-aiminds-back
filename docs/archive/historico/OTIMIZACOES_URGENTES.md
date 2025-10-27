# Otimizações Urgentes - HybridQueryProcessorV2

**Data:** 2025-10-21  
**Status:** 🔧 CRÍTICO - Requer ação imediata

---

## 🚨 Problemas Identificados

### 1. **Rate Limit GROQ (CRÍTICO)**

**Erro:**
```
Error code: 413 - Request too large for model `llama-3.1-8b-instant`
Limit 6000 TPM, Requested 6582 tokens
```

**Impacto:**
- Sistema falha em 100% das queries com dataset creditcard (284K linhas)
- Primeira query já estourou o limite

**Causa Raiz:**
O sistema está enviando:
1. Query original
2. Todo o DataFrame (284K linhas) como contexto
3. Análise + metadados

Total: **6582 tokens > 6000 TPM**

**Solução Implementada (TEMPORÁRIA):**
```python
# Desabilitado análise LLM adicional para reduzir consumo
# linha 118-126 de hybrid_query_processor_v2.py
```

**Solução Definitiva (RECOMENDADA):**

#### Opção A: Fragmentação Inteligente de Contexto
```python
def _prepare_context_for_llm(self, df, query, max_tokens=4500):
    """
    Limita contexto para caber no budget GROQ.
    """
    # 1. Estatísticas resumidas (500 tokens)
    stats = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'memory_mb': df.memory_usage(deep=True).sum() / 1024**2
    }
    
    # 2. Amostra estratégica (2000 tokens)
    if len(df) > 1000:
        # Head + tail + amostra aleatória
        sample = pd.concat([
            df.head(50),
            df.sample(min(100, len(df))),
            df.tail(50)
        ])
    else:
        sample = df
    
    # 3. Converter para JSON compacto
    context = {
        'stats': stats,
        'sample': sample.to_dict(orient='records')[:100],  # Máximo 100 registros
        'query': query
    }
    
    # 4. Validar tamanho
    context_tokens = len(str(context)) // 4  # Estimativa: 4 chars/token
    if context_tokens > max_tokens:
        # Reduzir amostra
        context['sample'] = context['sample'][:50]
    
    return context
```

#### Opção B: Usar Fast Query Fragmenter SEMPRE
```python
# No _process_with_csv_fallback, linha 547:
if csv_shape[0] > 10000 or csv_shape[1] > 20:
    # Forçar fragmentação para datasets grandes
    return await self._process_with_csv_fragmented(
        query=query,
        source_id=source_id,
        existing_chunks=existing_chunks,
        covered_aspects=covered_aspects
    )
```

#### Opção C: Upgrade GROQ Plan
```
Dev Tier:
- 30,000 TPM (5x o limite atual)
- $0.05 per 1M tokens
- Sem rate limits agressivos
```

---

### 2. **Teste RAG ONLY Falha**

**Erro:**
```
❌ Teste 1 falhou: CSV não deve ser acessado em RAG ONLY
```

**Causa:**
- Cobertura 0% (nenhum chunk encontrado)
- Sistema decide por `csv_fallback` corretamente
- **Teste está errado**, não o código

**Solução:**
O teste precisa POPULAR chunks antes de rodar:

```python
async def test_rag_only_strategy():
    """RAG ONLY - quando chunks cobrem ≥80%"""
    
    # 1. Criar chunks ANTES de testar
    chunks = [
        {
            'content': 'Distribuição Amount: média 88.35, std 250.12...',
            'metadata': {'aspect': 'distribution', 'source': 'creditcard_test123'}
        },
        {
            'content': 'Estatísticas Amount: min 0, max 25691.16...',
            'metadata': {'aspect': 'statistics', 'source': 'creditcard_test123'}
        },
        {
            'content': 'Análise temporal: 48 horas de transações...',
            'metadata': {'aspect': 'time_analysis', 'source': 'creditcard_test123'}
        }
    ]
    
    # 2. Armazenar chunks
    for chunk in chunks:
        await processor.vector_store.store_embeddings([chunk])
    
    # 3. AGORA testar - deve usar RAG ONLY
    result = await processor.process_query(
        query="Qual a distribuição de valores do dataset?",
        source_id="creditcard_test123"
    )
    
    assert result['strategy'] == 'rag_only', "Deve usar RAG quando há cobertura"
    assert not result['csv_accessed'], "CSV não deve ser acessado"
```

---

### 3. **Cache Timezone Issue (CORRIGIDO ✅)**

**Erro:**
```
can't compare offset-naive and offset-aware datetimes
```

**Correção Aplicada:**
```python
# Linha 226-232
if expires_at and expires_at.tzinfo:
    now = now.replace(tzinfo=expires_at.tzinfo)
```

**Status:** ✅ RESOLVIDO

---

## 📊 Métricas Atuais

### Performance dos Testes
```
✅ CSV FALLBACK: 5.00s (OK)
✅ CSV FRAGMENTED: 3.57s (OK)
✅ CACHE: 4.54s primeira exec (OK)
❌ RAG ONLY: 10.36s + falha (teste incorreto)
```

### Token Usage
```
Query simples:     ~500 tokens ✅
Query + stats:     ~2000 tokens ✅
Query + CSV full:  6582 tokens ❌ ESTOURA LIMITE
```

### Taxa de Sucesso
```
75% (3/4) - Limitado pelo problema de rate limit
```

---

## ✅ Ações Prioritárias

### 1. URGENTE (Hoje)
- [ ] Implementar `_prepare_context_for_llm()` com limite 4500 tokens
- [ ] Forçar fragmentação para df com >10K linhas
- [ ] Corrigir `test_rag_only_strategy` para popular chunks

### 2. ALTA (Esta Semana)
- [ ] Implementar estratégia adaptativa de sampling baseada em query
- [ ] Adicionar métricas de token usage em logs
- [ ] Configurar alertas quando uso > 80% do limite

### 3. MÉDIA (Próximo Sprint)
- [ ] Avaliar upgrade para GROQ Dev Tier
- [ ] Implementar cache de estatísticas do dataset
- [ ] Otimizar serialização JSON para reduzir tokens

---

## 🔧 Código de Correção Rápida

### Patch Temporário (Aplicar AGORA)

```python
# Em hybrid_query_processor_v2.py, linha 547:
async def _process_with_csv_fallback(self, ...):
    # ... código existente ...
    
    # ⚠️ PROTEÇÃO CONTRA RATE LIMIT
    csv_shape = await self._get_csv_shape(source_id)
    estimated_tokens = (csv_shape[0] * csv_shape[1]) // 100
    
    if estimated_tokens > 4000:  # Limite seguro: 4000 < 6000
        self.logger.warning(f"⚠️ CSV muito grande ({estimated_tokens} tokens estimados)")
        self.logger.warning("🔄 Redirecionando para estratégia fragmentada")
        
        return await self._process_with_csv_fragmented(
            query=query,
            source_id=source_id,
            existing_chunks=existing_chunks,
            covered_aspects=covered_aspects
        )
    
    # Prosseguir com fallback normal apenas se cabe no budget
    csv_loader = self._load_csv(source_id)
    # ... resto do código ...
```

---

## 📈 Resultados Esperados Pós-Correção

### Token Usage
```
Query simples:     ~500 tokens ✅
Query + stats:     ~1500 tokens ✅ (reduzido de 2000)
Query + sample:    ~3500 tokens ✅ (reduzido de 6582)
```

### Performance
```
RAG ONLY:          ~2s (com chunks populados)
CSV FALLBACK:      ~5s (dataset <10K linhas)
CSV FRAGMENTED:    ~15s (dataset >10K linhas)
CACHE HIT:         ~0.5s
```

### Taxa de Sucesso Esperada
```
100% (4/4) com correções aplicadas
```

---

## 📚 Referências

- [GROQ Rate Limits](https://console.groq.com/docs/rate-limits)
- [Token Estimation Best Practices](https://platform.openai.com/tokenizer)
- [FastQueryFragmenter Implementation](src/agent/fast_query_fragmenter.py)
- [HybridQueryProcessorV2 Architecture](docs/HYBRID_PROCESSOR_V2_ARCHITECTURE.md)

---

**Última atualização:** 2025-10-21 01:30 BRT  
**Responsável:** GitHub Copilot (GPT-4.1)  
**Status:** 🔴 CRÍTICO - Aguardando implementação das correções
