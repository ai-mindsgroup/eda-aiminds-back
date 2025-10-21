# 🔍 AUDITORIA CRÍTICA - Pipeline de Análise Multi-Coluna

**Data:** 2025-10-21  
**Status:** 🔴 **PROBLEMAS CRÍTICOS IDENTIFICADOS**  
**Severidade:** ALTA - Sistema limitado a primeira coluna temporal

---

## 📊 Resumo Executivo

A auditoria revelou **limitações críticas** no pipeline de análise que restringem o processamento a **apenas a primeira coluna temporal**, ignorando outras colunas relevantes do dataset.

---

## 🚨 Problemas Identificados

### 1. ❌ PROBLEMA CRÍTICO: Chunking Limitado a Primeira Coluna

**Arquivo:** `src/embeddings/chunker.py` (linhas 272-340)

**Evidência:**
```python
def _chunk_csv_data(self, csv_text: str, source_id: str) -> List[TextChunk]:
    """Chunking especializado para dados CSV baseado em linhas com overlap."""
    raw_lines = csv_text.splitlines()
    header = raw_lines[0].strip()  # ❌ PEGA APENAS O HEADER COMPLETO
    data_lines = [line.strip() for r in raw_lines[1:] if line.strip()]
    
    # Cria chunks por ROW (linhas), não por COLUMN
    while start_row < total_rows:
        end_row = min(start_row + chunk_size_rows, total_rows)
        chunk_lines = data_lines[start_row:end_row]
        chunk_content_lines = [header] + chunk_lines
        chunk_content = '\n'.join(chunk_content_lines)
        # ❌ Chunks contêm TODAS as colunas, mas sem separação por coluna
```

**Problema:**
- ✅ Gera múltiplos chunks
- ❌ **Mas chunks são por LINHA, não por COLUNA**
- ❌ **Não separa análise de Time, Amount, Class, V1-V28 independentemente**
- ❌ **Primeira coluna temporal (Time) domina a análise vetorial**

**Impacto:**
- Queries sobre "Amount" ou "V1-V28" dependem do contexto de "Time"
- Busca vetorial encontra chunks pela proximidade temporal, não por relevância da coluna
- Análises multi-coluna ficam limitadas

---

### 2. ❌ HybridQueryProcessorV2 Processa TODOS os Chunks (Mas Sem Foco por Coluna)

**Arquivo:** `src/agent/hybrid_query_processor_v2.py`

**Evidência:**
```python
async def _search_existing_chunks(self, query: str, source_id: str) -> List:
    """Busca chunks existentes no VectorStore."""
    query_embedding_result = self.embedding_generator.generate_embedding(query)
    query_embedding = query_embedding_result.embedding
    
    results = self.vector_store.search_similar(
        query_embedding=query_embedding,
        similarity_threshold=0.3,
        limit=20,  # ✅ Busca ATÉ 20 chunks
        filters={'source': source_id}
    )
    # ✅ RETORNA MÚLTIPLOS CHUNKS
    # ❌ MAS chunks são por LINHA, não têm foco em coluna específica
```

**Problema:**
- ✅ Busca múltiplos chunks (até 20)
- ✅ Agrega resultados de múltiplos chunks
- ❌ **Mas chunks não são organizados por COLUNA**
- ❌ **Query "Qual a média de Amount?" retorna chunks com TODAS as colunas**
- ❌ **Análise vetorial não distingue relevância por coluna**

**Impacto:**
- LLM recebe contexto "poluído" com colunas irrelevantes
- Primeira coluna temporal (Time) tem peso desproporcional
- Respostas podem ser menos precisas para colunas secundárias

---

### 3. ⚠️ Prompts NÃO Instruem LLM a Analisar TODAS as Colunas

**Arquivo:** `src/prompts/manager.py`

**Busca realizada:**
```bash
$ grep -r "todas as colunas" src/prompts/
$ grep -r "all columns" src/prompts/
# Resultado: Nenhuma correspondência
```

**Prompts atuais:**
```python
# src/agent/hybrid_query_processor_v2.py (linha 676)
prompt = f"""Baseado nos fragmentos processados e chunks existentes, responda:

CONTEXTO:
{context}

QUERY ORIGINAL: {query}

Responda integrando todas as informações de forma coerente."""
# ❌ Não menciona "analisar todas as colunas"
# ❌ Não instrui a considerar colunas além da primeira
```

**Problema:**
- ❌ Prompts genéricos sem instrução explícita multi-coluna
- ❌ LLM não é guiado a explorar todas as colunas
- ❌ Pode focar apenas no contexto dominante (primeira coluna)

**Impacto:**
- LLM pode ignorar colunas secundárias mesmo quando relevantes
- Respostas incompletas para análises multi-coluna

---

### 4. ✅ Agregação de Múltiplas Respostas FUNCIONA (Mas Limitada Pelo Chunking)

**Arquivo:** `src/llm/simple_aggregator.py`

**Evidência:**
```python
def aggregate_results(self, results: List[FragmentResult], strategy: FragmentStrategy):
    """Agrega resultados de múltiplos fragmentos."""
    successful_results = [r for r in results if r.success]
    
    # ✅ Filtra sucessos
    # ✅ Concatena DataFrames verticalmente/horizontalmente
    # ✅ Merge de dicts de estatísticas
    # ✅ Retorna resultado consolidado
```

**Avaliação:**
- ✅ Agregação funciona corretamente
- ✅ Consolida múltiplos fragmentos
- ❌ **MAS fragmentos ainda são por LINHA, não por COLUNA**

**Impacto:**
- Sistema agrega bem, mas agregação é sobre **linhas diferentes**, não **colunas diferentes**

---

### 5. ⚠️ Cache e Fallback NÃO Limitam a Chunk Único (Mas Podem Otimizar Demais)

**Arquivo:** `src/agent/hybrid_query_processor_v2.py`

**Evidência:**
```python
async def _search_cached_result(self, query: str, source_id: str, session_id: str):
    """Busca resultado em cache."""
    cache_key = self._generate_cache_key(query, source_id)
    cached = await self.memory_manager.recall_context(
        session_id, ContextType.QUERY_RESULT
    )
    # ✅ Se encontrar, retorna imediatamente
    # ⚠️ Pode retornar resultado parcial se cache foi gerado com chunking limitado
```

**Problema:**
- ✅ Cache funciona corretamente
- ⚠️ **Se cache foi gerado com análise limitada, perpetua limitação**
- ⚠️ **Fallback pode usar apenas chunks mais similares (não mais completos)**

**Impacto:**
- Cache pode acelerar, mas também pode "congelar" respostas incompletas
- Fallback pode não explorar todas as colunas se similaridade vetorial favorecer primeira coluna

---

## 📋 Arquitetura Atual vs. Esperada

### ❌ Arquitetura ATUAL (Limitada)

```
CSV com 10 colunas (Time, Amount, V1-V8)
         |
         ▼
   Chunking por LINHA
   (chunks contêm TODAS as colunas)
         |
         ▼
   Embeddings por LINHA
   (vetor representa linha inteira)
         |
         ▼
   Busca Vetorial
   (similaridade baseada em LINHA, não COLUNA)
         |
         ▼
   LLM recebe contexto com TODAS as colunas
   (mas primeira coluna domina)
         |
         ▼
   Resposta pode ser incompleta para colunas secundárias
```

### ✅ Arquitetura ESPERADA (Multi-Coluna)

```
CSV com 10 colunas (Time, Amount, V1-V8)
         |
         ▼
   Chunking por COLUNA + LINHA
   - Chunk 1: Time (todas as linhas)
   - Chunk 2: Amount (todas as linhas)
   - Chunk 3: V1 (todas as linhas)
   - ...
   - Chunk 10: V8 (todas as linhas)
   + Chunks por LINHA (contexto adicional)
         |
         ▼
   Embeddings específicos por COLUNA
   (vetor representa estatísticas da coluna)
         |
         ▼
   Busca Vetorial
   (similaridade baseada em COLUNA relevante)
         |
         ▼
   LLM recebe contexto FOCADO
   (apenas colunas relevantes para query)
         |
         ▼
   Prompt explícito: "Analise TODAS as colunas"
         |
         ▼
   Resposta completa para análises multi-coluna
```

---

## 🔧 Correções Necessárias

### Correção 1: Implementar Chunking Multi-Coluna

**Arquivo:** `src/embeddings/chunker.py`

**Adicionar novo método:**
```python
def _chunk_csv_by_columns(self, csv_text: str, source_id: str) -> List[TextChunk]:
    """Chunking especializado por COLUNA para análise multi-dimensional."""
    import io
    import pandas as pd
    
    df = pd.read_csv(io.StringIO(csv_text))
    chunks = []
    
    # Chunk 1: Metadados gerais
    metadata_text = f"""Dataset: {source_id}
Colunas: {', '.join(df.columns)}
Linhas: {len(df)}
Tipos: {df.dtypes.to_dict()}
"""
    chunks.append(TextChunk(
        content=metadata_text,
        metadata=ChunkMetadata(
            source=source_id,
            chunk_index=0,
            strategy=ChunkStrategy.CSV_COLUMN,
            additional_info={'chunk_type': 'metadata'}
        )
    ))
    
    # Chunks 2-N: Uma por COLUNA
    for idx, col in enumerate(df.columns, start=1):
        # Estatísticas da coluna
        col_data = df[col]
        
        if pd.api.types.is_numeric_dtype(col_data):
            stats = f"""Coluna: {col}
Tipo: numérico
Mínimo: {col_data.min()}
Máximo: {col_data.max()}
Média: {col_data.mean():.4f}
Mediana: {col_data.median()}
Desvio Padrão: {col_data.std():.4f}
Valores Nulos: {col_data.isnull().sum()}
Amostra: {col_data.head(10).tolist()}
"""
        else:
            freq = col_data.value_counts().head(10)
            stats = f"""Coluna: {col}
Tipo: categórico
Valores Únicos: {col_data.nunique()}
Mais Frequentes: {freq.to_dict()}
Valores Nulos: {col_data.isnull().sum()}
Amostra: {col_data.head(10).tolist()}
"""
        
        chunks.append(TextChunk(
            content=stats,
            metadata=ChunkMetadata(
                source=source_id,
                chunk_index=idx,
                strategy=ChunkStrategy.CSV_COLUMN,
                additional_info={
                    'chunk_type': 'column_analysis',
                    'column_name': col
                }
            )
        ))
    
    logger.info(f"Criados {len(chunks)} chunks por COLUNA ({len(df.columns)} colunas)")
    return chunks
```

**Modificar método principal:**
```python
def chunk_text(self, text: str, source: str = "", strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE):
    # ...
    elif strategy == ChunkStrategy.CSV_ROW:
        return self._chunk_csv_data(text, source)
    elif strategy == ChunkStrategy.CSV_COLUMN:  # NOVO
        return self._chunk_csv_by_columns(text, source)
```

---

### Correção 2: Adicionar ChunkStrategy.CSV_COLUMN

**Arquivo:** `src/embeddings/chunker.py` (linha 18)

```python
class ChunkStrategy(Enum):
    """Estratégias de chunking disponíveis."""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    CSV_ROW = "csv_row"
    CSV_COLUMN = "csv_column"  # ✅ NOVO
```

---

### Correção 3: Atualizar RAGAgent.ingest_csv_data para Gerar Ambos os Tipos

**Arquivo:** `src/agent/rag_agent.py`

**Modificar ingestão:**
```python
def ingest_csv_data(self, csv_text: str, source_id: str) -> Dict[str, Any]:
    """Ingesta CSV com DOIS tipos de chunking: ROW e COLUMN."""
    
    # CHUNK TIPO 1: Por LINHA (existente)
    row_chunks = self.chunker.chunk_text(
        text=csv_text,
        source=source_id,
        strategy=ChunkStrategy.CSV_ROW
    )
    
    # CHUNK TIPO 2: Por COLUNA (NOVO)
    column_chunks = self.chunker.chunk_text(
        text=csv_text,
        source=source_id,
        strategy=ChunkStrategy.CSV_COLUMN
    )
    
    # Combinar ambos
    all_chunks = row_chunks + column_chunks
    
    # Gerar embeddings para TODOS
    for chunk in all_chunks:
        embedding_result = self.embedding_generator.generate_embedding(chunk.content)
        chunk.embedding = embedding_result.embedding
    
    # Armazenar TODOS
    stored_count = self.vector_store.store_chunks(all_chunks)
    
    return {
        'status': 'success',
        'source_id': source_id,
        'chunks_total': len(all_chunks),
        'chunks_by_row': len(row_chunks),
        'chunks_by_column': len(column_chunks),
        'chunks_stored': stored_count
    }
```

---

### Correção 4: Ajustar Prompts para Instruir Análise Multi-Coluna

**Arquivo:** `src/agent/hybrid_query_processor_v2.py` (linha 676)

**Prompt corrigido:**
```python
prompt = f"""Você é um analista de dados especializado. Sua tarefa é responder à query do usuário analisando TODAS as colunas relevantes do dataset.

INSTRUÇÕES IMPORTANTES:
1. Analise TODAS as colunas mencionadas no contexto
2. Não se limite à primeira coluna temporal
3. Considere correlações entre múltiplas colunas
4. Se houver chunks por coluna, priorize-os para análises específicas
5. Integre informações de diferentes chunks de forma coerente

CONTEXTO DISPONÍVEL:
{context}

QUERY DO USUÁRIO: {query}

RESPOSTA:
Forneça uma resposta completa considerando TODAS as colunas relevantes."""
```

---

### Correção 5: Adicionar Filtro por Tipo de Chunk na Busca Vetorial

**Arquivo:** `src/agent/hybrid_query_processor_v2.py`

**Método melhorado:**
```python
async def _search_existing_chunks(self, query: str, source_id: str) -> List:
    """Busca chunks existentes priorizando chunks por COLUNA."""
    query_embedding_result = self.embedding_generator.generate_embedding(query)
    query_embedding = query_embedding_result.embedding
    
    # BUSCA 1: Chunks por COLUNA (mais específicos)
    column_chunks = self.vector_store.search_similar(
        query_embedding=query_embedding,
        similarity_threshold=0.3,
        limit=10,
        filters={
            'source': source_id,
            'chunk_type': 'column_analysis'  # ✅ NOVO FILTRO
        }
    )
    
    # BUSCA 2: Chunks por LINHA (contexto adicional)
    row_chunks = self.vector_store.search_similar(
        query_embedding=query_embedding,
        similarity_threshold=0.4,
        limit=5,
        filters={
            'source': source_id,
            'chunk_type': 'row_data'
        }
    )
    
    # Combinar: Prioridade para chunks por COLUNA
    all_chunks = column_chunks + row_chunks
    
    self.logger.info(
        f"📦 Chunks: {len(column_chunks)} por COLUNA + {len(row_chunks)} por LINHA"
    )
    
    return all_chunks
```

---

### Correção 6: Atualizar VectorStore para Suportar Filtro por Tipo

**Arquivo:** `src/embeddings/vector_store.py`

**Método search_similar atualizado:**
```python
def search_similar(self, query_embedding: List[float], similarity_threshold: float = 0.3,
                   limit: int = 10, filters: Optional[Dict] = None) -> List:
    """Busca vetorial com suporte a filtro por chunk_type."""
    
    # Construir query SQL com filtro adicional
    where_clauses = []
    
    if filters:
        if 'source' in filters:
            where_clauses.append(f"metadata->>'source' = '{filters['source']}'")
        
        if 'chunk_type' in filters:
            # ✅ NOVO: Filtro por tipo de chunk
            where_clauses.append(f"metadata->>'chunk_type' = '{filters['chunk_type']}'")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Executar busca...
```

---

## 🧪 Testes Necessários

### Teste 1: Validar Chunking Multi-Coluna

**Arquivo:** `tests/test_multicolumn_chunking.py` (CRIAR)

```python
def test_csv_chunking_generates_column_chunks():
    """Verificar que chunking gera chunks por COLUNA."""
    chunker = Chunker()
    
    csv_text = """Time,Amount,V1,V2
1,100.5,0.1,0.2
2,200.3,0.3,0.4
3,150.7,0.5,0.6"""
    
    chunks = chunker.chunk_text(
        csv_text, 
        source='test_csv',
        strategy=ChunkStrategy.CSV_COLUMN
    )
    
    # Deve gerar: 1 metadata + 4 colunas = 5 chunks
    assert len(chunks) == 5
    
    # Verificar tipos
    chunk_types = [c.metadata.additional_info.get('chunk_type') for c in chunks]
    assert 'metadata' in chunk_types
    assert sum(1 for t in chunk_types if t == 'column_analysis') == 4
    
    # Verificar nomes de colunas
    column_names = [c.metadata.additional_info.get('column_name') for c in chunks[1:]]
    assert set(column_names) == {'Time', 'Amount', 'V1', 'V2'}
```

---

### Teste 2: Validar Busca por Tipo de Chunk

**Arquivo:** `tests/test_multicolumn_search.py` (CRIAR)

```python
async def test_hybrid_processor_prioritizes_column_chunks():
    """Verificar que HQPv2 prioriza chunks por COLUNA."""
    processor = HybridQueryProcessorV2(vector_store, embedding_gen)
    
    # Simular query sobre coluna específica
    query = "Qual a média de Amount?"
    chunks = await processor._search_existing_chunks(query, 'test_csv')
    
    # Verificar que chunks por COLUNA aparecem primeiro
    first_5 = chunks[:5]
    column_chunks = [c for c in first_5 if c.metadata.get('chunk_type') == 'column_analysis']
    
    assert len(column_chunks) >= 3, "Deve priorizar chunks por COLUNA"
    
    # Verificar que chunk de "Amount" está presente
    amount_chunks = [
        c for c in chunks 
        if c.metadata.additional_info.get('column_name') == 'Amount'
    ]
    assert len(amount_chunks) > 0, "Deve encontrar chunk da coluna Amount"
```

---

### Teste 3: Validar Prompt Multi-Coluna

**Arquivo:** `tests/test_multicolumn_prompt.py` (CRIAR)

```python
def test_prompt_includes_multicolumn_instructions():
    """Verificar que prompt instrui análise de TODAS as colunas."""
    processor = HybridQueryProcessorV2(vector_store, embedding_gen)
    
    # Construir prompt
    prompt = processor._build_multicolumn_prompt("Analise o dataset", ["col1", "col2"])
    
    # Verificar instruções críticas
    assert "TODAS as colunas" in prompt
    assert "não se limite" in prompt.lower()
    assert "primeira coluna" in prompt.lower()
```

---

### Teste 4: Teste End-to-End via Interface V3

**Executar manualmente:**
```bash
python scripts/setup_and_run_interface_interativa_v3.py
```

**Queries de teste:**
```
1. "Qual a média de Amount?" 
   → Deve usar chunk da coluna Amount

2. "Mostre a correlação entre Time e Amount"
   → Deve usar chunks de ambas as colunas

3. "Analise a distribuição de V1, V2, V3"
   → Deve usar chunks das 3 colunas

4. "Quais colunas têm maior variabilidade?"
   → Deve analisar TODAS as colunas numéricas
```

**Validação:**
- [ ] Resposta menciona análise de TODAS as colunas solicitadas
- [ ] Não se limita à primeira coluna temporal
- [ ] Logs mostram chunks por COLUNA sendo usados
- [ ] Contexto inclui estatísticas de múltiplas colunas

---

## 📊 Checklist de Implementação

### FASE 1: Chunking Multi-Coluna (2-3h)
- [ ] Adicionar `ChunkStrategy.CSV_COLUMN` ao enum
- [ ] Implementar `_chunk_csv_by_columns()` em chunker.py
- [ ] Testar geração de chunks por coluna
- [ ] Validar metadados (chunk_type, column_name)

### FASE 2: Ingestão Dupla (1-2h)
- [ ] Modificar `RAGAgent.ingest_csv_data()` para gerar AMBOS os tipos
- [ ] Testar ingestão completa (ROW + COLUMN)
- [ ] Validar embeddings de chunks por coluna
- [ ] Verificar armazenamento no Supabase

### FASE 3: Busca Priorizada (2h)
- [ ] Atualizar `VectorStore.search_similar()` com filtro chunk_type
- [ ] Modificar `HQPv2._search_existing_chunks()` para buscar por tipo
- [ ] Testar priorização de chunks por COLUNA
- [ ] Validar fallback para chunks por LINHA

### FASE 4: Prompts Multi-Coluna (1h)
- [ ] Atualizar prompt em `HQPv2._process_with_csv_fragmented()`
- [ ] Adicionar instruções explícitas: "Analise TODAS as colunas"
- [ ] Testar com LLM real
- [ ] Validar respostas multi-coluna

### FASE 5: Testes Automatizados (2h)
- [ ] Criar `test_multicolumn_chunking.py`
- [ ] Criar `test_multicolumn_search.py`
- [ ] Criar `test_multicolumn_prompt.py`
- [ ] Executar todos os testes (100% aprovação)

### FASE 6: Teste E2E via Interface V3 (1h)
- [ ] Executar `setup_and_run_interface_interativa_v3.py`
- [ ] Testar 4 queries multi-coluna
- [ ] Validar logs e contexto
- [ ] Documentar resultados

---

## 🎯 Critérios de Sucesso

### Chunking:
- [X] Gera chunks por LINHA (existente)
- [ ] Gera chunks por COLUNA (novo) ✅
- [ ] Chunks por COLUNA contêm estatísticas isoladas
- [ ] Metadados incluem `chunk_type` e `column_name`

### Busca Vetorial:
- [ ] Prioriza chunks por COLUNA para queries específicas
- [ ] Usa chunks por LINHA como contexto adicional
- [ ] Filtro `chunk_type` funciona corretamente

### Prompts:
- [ ] Instrução explícita: "Analise TODAS as colunas"
- [ ] LLM considera múltiplas colunas na resposta
- [ ] Não se limita à primeira coluna temporal

### Agregação:
- [X] Agrega resultados de múltiplos chunks (existente)
- [ ] Agrega chunks de DIFERENTES COLUNAS (novo) ✅
- [ ] Resposta consolidada coerente

### Testes:
- [ ] 100% aprovação em testes unitários
- [ ] 100% aprovação em testes de integração
- [ ] Teste E2E via interface v3 validado

---

## 📝 Próximos Passos

1. **IMEDIATO**: Implementar chunking multi-coluna
2. **CURTO PRAZO**: Atualizar busca vetorial
3. **MÉDIO PRAZO**: Ajustar prompts e testar
4. **LONGO PRAZO**: Deploy e monitoramento

---

**Autor:** GitHub Copilot (Agente Sênior de IA)  
**Data:** 2025-10-21  
**Status:** Auditoria concluída, correções especificadas
