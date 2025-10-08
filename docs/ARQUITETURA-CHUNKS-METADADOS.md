# Arquitetura de Chunks de Metadados - Sistema Genérico para CSV

**Data:** 06/10/2025  
**Versão:** 2.0 - Sistema Genérico Universal

---

## 📋 Visão Geral

O sistema EDA AI Minds implementa um mecanismo inteligente de **chunks de metadados analíticos** que são gerados automaticamente durante a ingestão de **qualquer arquivo CSV**, permitindo que o sistema RAG responda perguntas sobre:

- Estrutura e tipos de dados
- Distribuições estatísticas
- Correlações entre variáveis
- Outliers e anomalias
- Padrões temporais
- Agrupamentos naturais

## 🎯 Objetivo

Criar chunks adicionais que contenham **análises estatísticas completas** do dataset, complementando os chunks de dados transacionais. Isso permite que o sistema responda perguntas sobre **metadados e características gerais** do dataset, não apenas sobre registros individuais.

---

## 📊 Arquitetura dos 6 Chunks Analíticos

### Chunk 1: Tipologia e Estrutura
**Título:** `ANÁLISE DE TIPOLOGIA E ESTRUTURA - DATASET: {source_id}`

**Conteúdo:**
- Total de registros
- Total de colunas
- Colunas numéricas (lista completa com dtypes)
- Colunas categóricas (lista completa com contagem de valores únicos)
- Colunas temporais (se existirem)

**Responde às perguntas:**
- Quais são os tipos de dados (numéricos, categóricos)?
- Qual a estrutura do dataset?

**Metadata:**
```json
{
  "chunk_type": "metadata_types",
  "topic": "data_types_structure"
}
```

---

### Chunk 2: Distribuições e Intervalos
**Título:** `ANÁLISE DE DISTRIBUIÇÕES E INTERVALOS - DATASET: {source_id}`

**Conteúdo:**
- Estatísticas descritivas completas (describe() do pandas)
- Intervalos [min, max] de cada coluna numérica
- Quartis (Q1, Q2/Mediana, Q3)
- Percentis (P90, P95, P99)

**Responde às perguntas:**
- Qual a distribuição de cada variável?
- Qual o intervalo de cada variável (mínimo, máximo)?

**Metadata:**
```json
{
  "chunk_type": "metadata_distribution",
  "topic": "distributions_intervals"
}
```

---

### Chunk 3: Tendência Central e Variabilidade
**Título:** `ANÁLISE ESTATÍSTICA: TENDÊNCIA CENTRAL E VARIABILIDADE - DATASET: {source_id}`

**Conteúdo:**
- **Tendência Central:** Média, Mediana, Moda (para cada coluna numérica)
- **Variabilidade:** Desvio Padrão, Variância, IQR (Intervalo Interquartil)
- Tabelas formatadas para fácil leitura

**Responde às perguntas:**
- Quais são as medidas de tendência central (média, mediana)?
- Qual a variabilidade dos dados (desvio padrão, variância)?

**Metadata:**
```json
{
  "chunk_type": "metadata_central_variability",
  "topic": "central_tendency_variability"
}
```

---

### Chunk 4: Frequência e Outliers
**Título:** `ANÁLISE DE FREQUÊNCIA E DETECÇÃO DE OUTLIERS - DATASET: {source_id}`

**Conteúdo:**
- **Valores Frequentes:** Top 5 valores mais comuns em colunas categóricas
- **Outliers:** Detecção usando método IQR (1.5×IQR)
- Percentual de outliers por coluna
- Intervalo normal calculado

**Responde às perguntas:**
- Quais os valores mais frequentes ou menos frequentes?
- Existem valores atípicos (outliers)?
- Como esses outliers afetam a análise?

**Metadata:**
```json
{
  "chunk_type": "metadata_frequency_outliers",
  "topic": "frequent_values_outliers"
}
```

---

### Chunk 5: Correlações e Relacionamentos
**Título:** `ANÁLISE DE CORRELAÇÕES E RELACIONAMENTOS - DATASET: {source_id}`

**Conteúdo:**
- **Matriz de Correlação:** Primeiras 15 colunas numéricas
- **Correlações Fortes:** Pares de variáveis com |r| > 0.7
- Interpretação de relacionamentos entre variáveis

**Responde às perguntas:**
- Como as variáveis estão relacionadas umas com as outras?
- Existe correlação entre as variáveis?
- Quais variáveis parecem ter maior ou menor influência sobre outras?

**Metadata:**
```json
{
  "chunk_type": "metadata_correlations",
  "topic": "correlations_relationships"
}
```

---

### Chunk 6: Padrões Temporais e Agrupamentos
**Título:** `ANÁLISE DE PADRÕES TEMPORAIS E AGRUPAMENTOS - DATASET: {source_id}`

**Conteúdo:**
- **Análise Temporal:** Detecta colunas de data/tempo
  - Período coberto (min-max)
  - Intervalo em dias
  - Monotonicidade
- **Agrupamentos:** Distribuição de categorias
  - Top 5 grupos por coluna categórica
  - Percentual de cada grupo

**Responde às perguntas:**
- Existem padrões ou tendências temporais?
- Existem agrupamentos (clusters) nos dados?

**Metadata:**
```json
{
  "chunk_type": "metadata_patterns_clusters",
  "topic": "temporal_patterns_clustering"
}
```

---

## 🔄 Fluxo de Ingestão

```
1. CSV carregado → RAGAgent.ingest_csv_data()
2. Chunks transacionais criados (CSV_ROW strategy)
3. Embeddings gerados e armazenados
4. _generate_metadata_chunks() executado
5. 6 chunks analíticos criados
6. Embeddings de metadados gerados
7. Armazenados no Supabase com metadata específica
```

---

## 🎨 Design Principles

### 1. **Genericidade Total**
- Sistema funciona para **QUALQUER CSV**
- Não há hardcoding de colunas específicas
- Não há menções a domínios específicos (fraude, transporte, etc.)

### 2. **Descritivo, Não Prescritivo**
- Chunks descrevem **O QUE EXISTE** nos dados
- Não mencionam **PERGUNTAS ESPECÍFICAS**
- LLM interpreta o contexto e responde adequadamente

### 3. **Estatisticamente Robusto**
- Usa pandas, numpy para análises precisas
- Métricas padronizadas (IQR para outliers, Pearson para correlação)
- Cobre estatística descritiva completa

### 4. **RAG-Friendly**
- Chunks autoexplicativos
- Títulos claros e estruturados
- Metadata rica para filtragem

---

## 📈 Cobertura de Perguntas

| Pergunta | Chunk Responsável |
|----------|-------------------|
| Tipos de dados? | Chunk 1 |
| Distribuição? | Chunk 2 |
| Intervalos (min/max)? | Chunk 2 |
| Média, mediana? | Chunk 3 |
| Desvio padrão, variância? | Chunk 3 |
| Valores frequentes? | Chunk 4 |
| Outliers? | Chunk 4 |
| Como outliers afetam? | Chunk 4 |
| Variáveis relacionadas? | Chunk 5 |
| Correlações? | Chunk 5 |
| Influência entre variáveis? | Chunk 5 |
| Padrões temporais? | Chunk 6 |
| Agrupamentos/clusters? | Chunk 6 |

**Cobertura:** 14/14 perguntas = **100%** ✅

---

## 🧪 Exemplo de Uso

### CSV de Fraudes (creditcard.csv)
```python
agent.ingest_csv_data(csv_text, "creditcard_full")
# Gera 17.801 chunks transacionais + 6 chunks analíticos
```

### CSV de Vale Transporte (vt_transactions.csv)
```python
agent.ingest_csv_data(csv_text, "vale_transporte")
# Gera N chunks transacionais + 6 chunks analíticos
# Os mesmos 6 chunks, mas com dados de vale transporte
```

### CSV de Vendas (sales_data.csv)
```python
agent.ingest_csv_data(csv_text, "sales_2024")
# Gera N chunks transacionais + 6 chunks analíticos
# Os mesmos 6 chunks, mas com dados de vendas
```

---

## 🔍 Busca Vetorial

Quando usuário pergunta:
```
"Quais são os tipos de dados do dataset?"
```

O sistema:
1. Gera embedding da pergunta
2. Busca vetorial encontra **Chunk 1** (alta similaridade semântica)
3. LLM recebe contexto do Chunk 1
4. Gera resposta baseada nos dados reais

---

## 🛡️ Vantagens

1. **Escalabilidade:** Funciona para qualquer CSV futuro
2. **Precisão:** Respostas baseadas em análises reais, não inventadas
3. **Completude:** Cobre 100% das perguntas analíticas comuns
4. **Manutenibilidade:** Código genérico, fácil de expandir
5. **Performance:** Análise uma vez, consultas infinitas

---

## 🔮 Expansões Futuras

- [ ] Chunk 7: Análise de missing values (padrões de ausência)
- [ ] Chunk 8: Análise de normalidade (testes estatísticos)
- [ ] Chunk 9: Feature importance (se houver target)
- [ ] Chunk 10: Análise de séries temporais (se aplicável)

---

**Arquitetura:** Sistema Genérico Universal para Análise Exploratória de Dados  
**Status:** ✅ Implementado e Funcional  
**Compatibilidade:** Qualquer CSV estruturado
