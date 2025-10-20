# ROTEIRO COMPLETO DE CORREÇÃO - SISTEMA EDA AI MINDS

**Data:** 19/10/2025  
**Objetivo:** Corrigir sistema para responder corretamente as 17 perguntas do curso, com foco especial na Pergunta 01 (tipos de dados)  
**Prazo:** 1.5 dias (máximo)  
**Status Atual:** Etapa 01 (80% concluída) - Etapas 02-05 (pendentes)

---

## 📋 CONTEXTO CONSOLIDADO

### **PROBLEMA CENTRAL**

Sistema não responde corretamente "Quais são os tipos de dados (numéricos, categóricos)?" porque:

1. **Embeddings não contêm metadados estruturados** do dataset (tipos de colunas, shape, semântica)
2. **Chunks contêm apenas análises descritivas** (média, mediana, desvio) - não tipos (int64, float64)
3. **Fluxo de análise decide tipo de análise ANTES de interpretar a pergunta** → detecta "Time" como temporal → executa TemporalAnalyzer
4. **LLM não processa dados reais do DataFrame** durante fallback → respostas genéricas/inventadas

### **O QUE JÁ FOI FEITO (ETAPA 01 - 80%)**

✅ Camada de abstração LLM auditada e documentada  
✅ GROQ funcionando via `LangChainLLMManager`  
✅ `RAGDataAgent._init_langchain_llm()` refatorado (40→26 linhas, -35%)  
✅ Testes unitários criados e passando  
✅ Documentação técnica completa (1,110 linhas)  
⚠️ **FALTA:** Validação em interface interativa e API (teste manual)

### **ESTRUTURA DE DADOS SUPABASE (AUDITADA)**

**Tabela `embeddings`:**
```sql
- id UUID
- chunk_text TEXT           -- Análises descritivas em Markdown
- embedding VECTOR(384)
- metadata JSONB            -- {"source", "chunk_index", "ingestion_id"}
- created_at TIMESTAMP
```

**GAP Crítico:** Metadados JSONB NÃO contêm informações estruturadas do dataset (tipos, shape, semântica das colunas).

---

## 🎯 ARQUITETURA DA SOLUÇÃO

### **PRINCÍPIOS FUNDAMENTAIS**

1. ✅ **LLM-First:** LLM deve SEMPRE processar dados reais, nunca respostas hardcoded
2. ✅ **Dinâmico:** Sem hardcoding de nomes/números de colunas - usar `df.dtypes`, `df.shape`
3. ✅ **Intent-Driven:** Classificar intenção da pergunta ANTES de decidir tipo de análise
4. ✅ **Metadata-Rich:** Persistir metadados estruturados durante ingestão para consultas rápidas
5. ✅ **Abstração LLM:** Respeitar camada existente (`LangChainLLMManager`)

### **FLUXO IDEAL DE QUERY**

```
User Query: "Quais são os tipos de dados?"
    ↓
IntentClassifier (LLM-based) → intent = "data_types"
    ↓
IF intent IN ["data_types", "structure", "summary"]:
    ↓
    Buscar chunk especial "dataset_metadata" (JSONB estruturado)
    ↓
    IF encontrado:
        → Parsear JSON com tipos/shape/semântica
        → LLM gera resposta humanizada a partir dos metadados
    ↓
    ELSE:
        → Fallback: Carregar CSV completo
        → Extrair df.dtypes, df.shape, detectar semântica
        → LLM processa dados reais → resposta humanizada
ELSE IF intent == "temporal":
    → Verificar se existem colunas temporais
    → Executar TemporalAnalyzer
ELSE:
    → RAG normal (busca chunks relevantes)
```

---

## 📅 ROTEIRO DE EXECUÇÃO - 5 ETAPAS

---

### **ETAPA 01: VALIDAÇÃO DA INFRAESTRUTURA LLM** ⚠️ 80% CONCLUÍDA

**Status:** LLM funcional, mas falta validação nos pontos de entrada reais

#### **Checklist:**

- [x] Auditar camada de abstração LLM (`LangChainLLMManager`)
- [x] Confirmar suporte GROQ (1ª prioridade)
- [x] Refatorar `RAGDataAgent._init_langchain_llm()` para usar abstração
- [x] Criar testes unitários (validação isolada do LLM)
- [x] Gerar documentação técnica
- [ ] **PENDENTE:** Testar interface interativa (`setup_and_run_interface_interativa.py`)
- [ ] **PENDENTE:** Testar API (endpoint de query)
- [ ] **PENDENTE:** Documentar logs de execução real

#### **Ações Imediatas:**

```bash
# 1. Testar interface interativa
python scripts/setup_and_run_interface_interativa.py

# Perguntar: "Quais são os tipos de dados?"
# Verificar log: "✅ LLM inicializado via abstração: GROQ"

# 2. Se API disponível, testar endpoint
# POST /query {"query": "Quais são os tipos de dados?"}
```

**Critério de Sucesso:**
- ✅ Logs confirmam GROQ via abstração em interface e API
- ✅ Nenhum erro de inicialização LLM
- ✅ Sistema responde (mesmo que incorretamente - será corrigido nas próximas etapas)

**Tempo Estimado:** 30 minutos

---

### **ETAPA 02: ENRIQUECER PROCESSO DE INGESTÃO**

**Objetivo:** Adicionar chunk especial com metadados estruturados do dataset

#### **Checklist:**

- [ ] Localizar módulo de ingestão (`src/ingestion/` ou similar)
- [ ] Adicionar função `extract_dataset_metadata(df)`:
  ```python
  def extract_dataset_metadata(df):
      return {
          "dataset_name": "creditcard.csv",
          "shape": {"rows": len(df), "cols": len(df.columns)},
          "columns_metadata": {
              col: {
                  "dtype": str(df[col].dtype),
                  "semantic_type": detect_semantic_type(df[col]),
                  "null_count": int(df[col].isnull().sum()),
                  "unique_values": int(df[col].nunique()),
                  "is_categorical_binary": (df[col].nunique() == 2)
              } for col in df.columns
          }
      }
  ```
- [ ] Implementar `detect_semantic_type(series)`:
  ```python
  def detect_semantic_type(series):
      if pd.api.types.is_numeric_dtype(series):
          if series.nunique() == 2:
              return "categorical_binary"
          elif series.name.lower() in ["time", "timestamp", "date"]:
              return "temporal"
          else:
              return "numeric"
      elif pd.api.types.is_object_dtype(series):
          return "categorical"
      else:
          return "other"
  ```
- [ ] Modificar fluxo de chunking para inserir chunk especial (índice -1 ou 0):
  ```python
  metadata_chunk = {
      "chunk_text": json.dumps(dataset_metadata, ensure_ascii=False, indent=2),
      "metadata": {
          "chunk_type": "dataset_metadata",  # TAG ESPECIAL
          "source": csv_path,
          "created_at": datetime.now().isoformat()
      }
  }
  # Inserir PRIMEIRO (antes dos chunks de análise)
  ```
- [ ] Testar ingestão com novo CSV (ex: creditcard_500lines.csv)
- [ ] Validar no Supabase:
  ```sql
  SELECT chunk_text, metadata 
  FROM embeddings 
  WHERE metadata->>'chunk_type' = 'dataset_metadata';
  ```

**Critério de Sucesso:**
- ✅ Chunk especial criado e persistido
- ✅ Metadados JSONB contêm tipos de TODAS as colunas
- ✅ Tag `chunk_type = "dataset_metadata"` presente

**Tempo Estimado:** 2-3 horas

---

### **ETAPA 03: CORRIGIR FLUXO DE INTERPRETAÇÃO DE PERGUNTAS**

**Objetivo:** Classificar intent ANTES de decidir tipo de análise

#### **Checklist:**

- [ ] Auditar `IntentClassifier` atual:
  - Localização: `src/agent/intent_classifier.py` (ou similar)
  - Confirmar que usa LLM (não keywords hardcoded)
- [ ] Se IntentClassifier falha, corrigir:
  ```python
  # Prompt para LLM classificar intent
  prompt = f"""
  Classifique a intenção da pergunta do usuário em UMA das categorias:
  - data_types: Pergunta sobre tipos de dados, estrutura, colunas
  - statistical: Média, mediana, desvio padrão, distribuição
  - temporal: Padrões temporais, tendências, séries temporais
  - correlation: Correlações entre variáveis
  - outliers: Detecção de outliers, valores atípicos
  - general: Perguntas gerais sobre o dataset
  
  Pergunta: {user_query}
  
  Responda APENAS com a categoria (ex: "data_types").
  """
  intent = llm.invoke(prompt).strip().lower()
  ```
- [ ] Modificar `RAGDataAgent._analisar_completo_csv()`:
  ```python
  # ANTES (errado)
  temporal_cols = detect_temporal_columns(df)
  if temporal_cols:
      return run_temporal_analysis()  # ❌
  
  # DEPOIS (correto)
  intent = classify_intent(user_query)  # ✅ PRIMEIRO
  
  if intent == "data_types":
      return answer_data_types_question(df, user_query)
  elif intent == "temporal" and has_temporal_columns(df):
      return run_temporal_analysis(df, user_query)
  elif intent == "statistical":
      return run_statistical_analysis(df, user_query)
  # ...
  ```
- [ ] Implementar `answer_data_types_question(df, query)`:
  ```python
  def answer_data_types_question(df, query):
      # Buscar chunk de metadados primeiro
      metadata_chunk = get_metadata_chunk_from_embeddings()
      
      if metadata_chunk:
          dataset_info = json.loads(metadata_chunk["chunk_text"])
      else:
          # Fallback: extrair ao vivo
          dataset_info = extract_dataset_metadata(df)
      
      # LLM processa metadados estruturados
      prompt = f"""
      Informações estruturadas do dataset:
      {json.dumps(dataset_info, indent=2, ensure_ascii=False)}
      
      Pergunta do usuário: {query}
      
      Responda de forma completa, humanizada e precisa, citando TODAS as colunas relevantes.
      """
      return llm.invoke(prompt)
  ```
- [ ] Testar com Pergunta 01:
  ```bash
  python scripts/setup_and_run_interface_interativa.py
  # "Quais são os tipos de dados (numéricos, categóricos)?"
  ```

**Critério de Sucesso:**
- ✅ Intent classificado corretamente: "data_types"
- ✅ Sistema busca chunk de metadados (não executa TemporalAnalyzer)
- ✅ Resposta lista TODAS as 31 colunas com tipos corretos
- ✅ Coluna "Class" identificada como categórica binária

**Tempo Estimado:** 3-4 horas

---

### **ETAPA 04: VALIDAÇÃO COMPLETA**

**Objetivo:** Testar as 17 perguntas e corrigir gaps remanescentes

#### **Checklist:**

- [ ] Executar suite de testes:
  ```bash
  python tests/test_17_perguntas_v4.py
  ```
- [ ] Analisar resultados:
  - Quantas passaram? (meta: 15+/17)
  - Quais falharam e por quê?
- [ ] Para cada falha, identificar root cause:
  - Intent mal classificado?
  - Metadados insuficientes?
  - LLM gerando resposta incompleta?
  - Falta de geração de gráficos?
- [ ] Corrigir problemas específicos:
  - Ajustar prompts de classificação
  - Enriquecer metadados (se necessário)
  - Corrigir geração de visualizações (Pergunta 02)
- [ ] Re-executar testes até atingir 90%+ de sucesso

**Critério de Sucesso:**
- ✅ 15+/17 perguntas passam (88%+)
- ✅ Pergunta 01 passa com 100% de precisão
- ✅ Pergunta 02 gera gráficos corretamente
- ✅ Nenhuma resposta contém dados inventados

**Tempo Estimado:** 4-5 horas

---

### **ETAPA 05: INTEGRAÇÃO E DEPLOYMENT**

**Objetivo:** Garantir que correções funcionam em todos os pontos de entrada

#### **Checklist:**

- [ ] Validar interface interativa (teste manual completo)
- [ ] Validar API (se disponível):
  - Testar endpoint `/query`
  - Verificar CORS, autenticação, rate limiting
- [ ] Atualizar documentação:
  - README com instruções de uso
  - Documentação da API
  - Guia de troubleshooting
- [ ] Limpar código:
  - Remover módulos temporários (rag_data_agent_v4.py, test_*.py antigos)
  - Consolidar em código principal
- [ ] Preparar para entrega:
  - Relatório executivo de melhorias
  - Comparativo antes/depois
  - Métricas de qualidade

**Critério de Sucesso:**
- ✅ Interface interativa funciona perfeitamente
- ✅ API (se disponível) responde corretamente
- ✅ Documentação atualizada e clara
- ✅ Sistema pronto para avaliação do professor

**Tempo Estimado:** 2-3 horas

---

## 📊 RESUMO EXECUTIVO - CHECKLIST GERAL

### **ETAPA 01: INFRAESTRUTURA LLM** ⚠️ 80%

- [x] Auditar e documentar camada de abstração
- [x] Refatorar RAGDataAgent para usar abstração
- [x] Criar testes unitários
- [ ] **Testar interface interativa**
- [ ] **Testar API**

### **ETAPA 02: ENRIQUECER INGESTÃO** 🔴 PENDENTE

- [ ] Implementar `extract_dataset_metadata()`
- [ ] Implementar `detect_semantic_type()`
- [ ] Adicionar chunk especial de metadados
- [ ] Testar nova ingestão

### **ETAPA 03: CORRIGIR FLUXO** 🔴 PENDENTE

- [ ] Auditar IntentClassifier
- [ ] Classificar intent ANTES de análise
- [ ] Implementar `answer_data_types_question()`
- [ ] Testar Pergunta 01

### **ETAPA 04: VALIDAÇÃO** 🔴 PENDENTE

- [ ] Executar teste das 17 perguntas
- [ ] Corrigir falhas identificadas
- [ ] Re-executar até 90%+ sucesso

### **ETAPA 05: INTEGRAÇÃO** 🔴 PENDENTE

- [ ] Validar interface e API
- [ ] Atualizar documentação
- [ ] Limpar código temporário
- [ ] Preparar entrega

---

## ⏱️ CRONOGRAMA ESTIMADO (1.5 DIAS)

| Etapa | Tempo | Prioridade | Status |
|-------|-------|------------|--------|
| Etapa 01 (validação final) | 0.5h | 🔴 CRÍTICA | 80% |
| Etapa 02 (ingestão) | 3h | 🔴 CRÍTICA | 0% |
| Etapa 03 (fluxo) | 4h | 🔴 CRÍTICA | 0% |
| Etapa 04 (validação) | 5h | 🟡 ALTA | 0% |
| Etapa 05 (integração) | 3h | 🟢 MÉDIA | 0% |
| **TOTAL** | **15.5h** | **~1.5 dias** | **16%** |

---

## 🚨 RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| IntentClassifier falha constantemente | Média | Alto | Usar classificação por keywords temporariamente |
| Embeddings antigos incompatíveis | Baixa | Alto | Reprocessar CSV completo |
| LLM gera respostas incompletas | Média | Médio | Ajustar prompts e temperature |
| Prazo insuficiente | Alta | Alto | Priorizar Etapas 02-03, adiar 05 se necessário |

---

## 🎯 CRITÉRIOS DE SUCESSO FINAL

1. ✅ **Pergunta 01 respondida corretamente:** Lista todas as 31 colunas, tipos corretos (int64, float64), identifica "Class" como categórica binária
2. ✅ **Pergunta 02 gera gráficos:** Histogramas criados e referenciados na resposta
3. ✅ **15+/17 perguntas passam** no teste automatizado
4. ✅ **Interface interativa funciona** perfeitamente
5. ✅ **Nenhuma resposta contém dados inventados** (10 colunas A1-A10, valores falsos)

---

## 📝 PRÓXIMA AÇÃO IMEDIATA

**COMPLETAR ETAPA 01 (30 minutos):**

```bash
# 1. Testar interface interativa
python scripts/setup_and_run_interface_interativa.py

# 2. Fazer pergunta e capturar logs
# Pergunta: "Quais são os tipos de dados?"

# 3. Verificar:
# - Log confirma: "✅ LLM inicializado via abstração: GROQ"
# - Sistema responde (mesmo que incorreto - será corrigido)

# 4. Documentar resultado e prosseguir para Etapa 02
```

**Após completar Etapa 01, informar aqui para avançar para Etapa 02.**
