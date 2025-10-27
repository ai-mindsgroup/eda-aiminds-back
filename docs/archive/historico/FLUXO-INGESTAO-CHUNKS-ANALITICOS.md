# 🔄 Fluxo de Ingestão de Chunks Analíticos

## 📋 Como Funciona o Sistema (Automático)

### **1️⃣ CARGA INICIAL (Base Zerada)**

```python
# Exemplo: Novo arquivo CSV
from src.agent.rag_agent import RAGAgent

agent = RAGAgent('rag_agent')

# Carregar CSV
with open('data/creditcard.csv', 'r') as f:
    csv_text = f.read()

# ⚡ INGESTÃO AUTOMÁTICA (faz TUDO)
result = agent.ingest_csv_data(
    csv_text=csv_text,
    source_id='creditcard_full'
)
```

**O que acontece automaticamente:**

```
┌──────────────────────────────────────────────────────────┐
│  1. ANÁLISE AUTOMÁTICA DO CSV                            │
│     - Pandas lê o CSV completo                           │
│     - Identifica colunas numéricas/categóricas/temporais │
│     - Calcula estatísticas (mean, std, min, max, etc.)   │
│     - Detecta correlações, outliers, distribuições       │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  2. CHUNKING EM 2 ETAPAS                                 │
│                                                           │
│  A) CHUNKS DE DADOS (17.801 chunks)                      │
│     - Cada chunk = 20 linhas do CSV                      │
│     - Estratégia: CSV_ROW                                │
│     - Overlap de 4 linhas                                │
│                                                           │
│  B) CHUNKS ANALÍTICOS (6 chunks) ← AUTOMÁTICO!           │
│     1. metadata_types           (tipos de dados)         │
│     2. metadata_distribution    (distribuições, min/max) │
│     3. metadata_central_variability (média, mediana, std)│
│     4. metadata_frequency_outliers  (valores freq/raros) │
│     5. metadata_correlations    (matriz correlação)      │
│     6. metadata_patterns_clusters (padrões temporais)    │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  3. GERAÇÃO DE EMBEDDINGS                                │
│     - Groq/OpenAI transforma cada chunk em vetor (384D)  │
│     - Vetores capuram significado semântico              │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  4. ARMAZENAMENTO NO SUPABASE                            │
│     Tabela: embeddings                                   │
│     - chunk_text: conteúdo                               │
│     - embedding: vetor [0.12, 0.45, ...]                 │
│     - metadata: { chunk_type, topic, ... }               │
└──────────────────────────────────────────────────────────┘
```

---

## 🔄 **2️⃣ NOVO DATASET (Vale Refeição)**

**Exemplo: CSV de Vale Refeição**

```csv
funcionario_id,nome,departamento,valor_refeicao,data_compra,quantidade_tickets
1001,João Silva,TI,15.50,2025-01-15,20
1002,Maria Santos,RH,15.50,2025-01-15,22
1003,Pedro Costa,Vendas,18.00,2025-01-16,25
...
```

### **Código de Ingestão (IDÊNTICO!):**

```python
from src.agent.rag_agent import RAGAgent

agent = RAGAgent('rag_agent')

# Carregar CSV de vale refeição
with open('data/vale_refeicao.csv', 'r') as f:
    csv_text = f.read()

# ⚡ MESMA FUNÇÃO - Sistema se adapta automaticamente!
result = agent.ingest_csv_data(
    csv_text=csv_text,
    source_id='vale_refeicao_jan2025'  # ← Só muda o ID
)
```

### **O Sistema Detecta AUTOMATICAMENTE:**

```python
# _generate_metadata_chunks() faz análise inteligente:

# 1. Identifica tipos de dados
numeric_cols = ['funcionario_id', 'valor_refeicao', 'quantidade_tickets']
categorical_cols = ['nome', 'departamento']
datetime_cols = ['data_compra']

# 2. Gera CHUNK 1 (Tipos e Estrutura) - GENÉRICO!
"""
ANÁLISE DE TIPOLOGIA E ESTRUTURA - DATASET: VALE_REFEICAO_JAN2025

ESTRUTURA GERAL:
- Total de registros: 1.250
- Total de colunas: 6
- Colunas numéricas: 3
- Colunas categóricas: 2
- Colunas temporais: 1

COLUNAS NUMÉRICAS (3):
  • funcionario_id (int64)
  • valor_refeicao (float64)
  • quantidade_tickets (int64)

COLUNAS CATEGÓRICAS (2):
  • nome (15 valores únicos)
  • departamento (5 valores únicos)
...
"""

# 3. Gera CHUNK 2 (Distribuições) - GENÉRICO!
"""
ANÁLISE DE DISTRIBUIÇÕES E INTERVALOS - DATASET: VALE_REFEICAO_JAN2025

ESTATÍSTICAS DESCRITIVAS:
funcionario_id    valor_refeicao    quantidade_tickets
count     1250           1250                1250
mean      5625           16.25               22.5
std       3612            2.15                3.8
min       1001           15.50               18
25%       3313           15.50               20
50%       5625           15.50               22
75%       7937           18.00               25
max      10250           20.00               30

INTERVALOS (MIN-MAX):
  • valor_refeicao: [15.50, 20.00]
  • quantidade_tickets: [18, 30]
...
"""

# 4-6. Demais chunks analíticos gerados automaticamente!
```

---

## 🎯 **COMO O SISTEMA É GENÉRICO**

### **Código-Fonte (src/agent/rag_agent.py, linha 302):**

```python
def _generate_metadata_chunks(self, csv_text: str, source_id: str) -> List[TextChunk]:
    """Sistema GENÉRICO para QUALQUER CSV."""
    
    # Lê CSV com Pandas (funciona para QUALQUER estrutura)
    df = pd.read_csv(io.StringIO(csv_text))
    
    # ✅ DETECÇÃO AUTOMÁTICA (não precisa saber o domínio!)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    # ✅ GERA CHUNKS BASEADO NO QUE ENCONTROU (não hardcoded!)
    
    # Chunk 1: Tipos (funciona para fraude, vale refeição, vendas, etc.)
    types_content = f"""
    COLUNAS NUMÉRICAS: {len(numeric_cols)}
    {chr(10).join([f"  • {col} ({df[col].dtype})" for col in numeric_cols])}
    
    COLUNAS CATEGÓRICAS: {len(categorical_cols)}
    {chr(10).join([f"  • {col} ({df[col].nunique()} valores únicos)" for col in categorical_cols])}
    """
    
    # Chunk 2: Distribuições (calcula automaticamente para QUALQUER coluna numérica)
    desc = df[numeric_cols].describe()  # ← Pandas faz para QUALQUER dataset!
    
    # Chunk 3-6: Correlações, outliers, padrões (tudo genérico!)
    ...
```

---

## 📊 **COMPARAÇÃO: 3 Datasets Diferentes**

| Aspecto | Fraude (Cartão) | Vale Refeição | E-commerce (Vendas) |
|---------|----------------|---------------|---------------------|
| **Colunas** | 31 (Time, V1-V28, Amount, Class) | 6 (funcionario_id, nome, valor, data, etc.) | 12 (produto_id, categoria, preco, qtd, etc.) |
| **Linhas** | 284.808 | 1.250 | 45.600 |
| **Chunks de Dados** | 17.801 | 79 | 2.850 |
| **Chunks Analíticos** | **6** (gerados automaticamente) | **6** (gerados automaticamente) | **6** (gerados automaticamente) |
| **Código Python** | `agent.ingest_csv_data(csv, 'fraud')` | `agent.ingest_csv_data(csv, 'vale')` | `agent.ingest_csv_data(csv, 'vendas')` |

**⚠️ O CÓDIGO É IDÊNTICO! Sistema se adapta ao conteúdo.**

---

## 🛠️ **FLUXO TÉCNICO DETALHADO**

### **Arquivo: src/agent/rag_agent.py**

```python
def ingest_csv_data(self, csv_text: str, source_id: str) -> Dict[str, Any]:
    """MÉTODO PRINCIPAL - Processa QUALQUER CSV."""
    
    # Passo 1: Ingestar dados brutos (linhas do CSV)
    result = self.ingest_text(
        text=csv_text,
        source_id=source_id,
        source_type="csv",
        chunk_strategy=ChunkStrategy.CSV_ROW  # 20 linhas por chunk
    )
    
    # Passo 2: SE ingestão OK, gerar chunks analíticos (AUTOMÁTICO!)
    if not result.get("metadata", {}).get("error"):
        metadata_chunks = self._generate_metadata_chunks(csv_text, source_id)
        # ↑ Aqui acontece a MÁGICA - análise Pandas + geração de 6 chunks
        
        # Gerar embeddings dos chunks analíticos
        embeddings = self.embedding_generator.generate_embeddings_batch(metadata_chunks)
        
        # Armazenar no Supabase
        self.vector_store.store_embeddings(embeddings, "csv")
    
    return result
```

### **Método _generate_metadata_chunks() - LINHA 302:**

```python
def _generate_metadata_chunks(self, csv_text: str, source_id: str) -> List[TextChunk]:
    """Gera 6 chunks analíticos para QUALQUER CSV."""
    
    # 1. Análise com Pandas (biblioteca universal para CSV)
    df = pd.read_csv(io.StringIO(csv_text))
    
    # 2. Detecção automática de tipos
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # 3. Gerar 6 chunks com estatísticas (funciona para QUALQUER dataset!)
    chunks = [
        self._create_types_chunk(df, source_id),           # Tipos de dados
        self._create_distribution_chunk(df, source_id),    # Distribuições
        self._create_central_chunk(df, source_id),         # Média, mediana
        self._create_outliers_chunk(df, source_id),        # Valores raros
        self._create_correlation_chunk(df, source_id),     # Correlações
        self._create_patterns_chunk(df, source_id)         # Padrões temporais
    ]
    
    return chunks
```

---

## 🚀 **EXEMPLO PRÁTICO: 3 Comandos Diferentes, Mesmo Sistema**

### **1. Fraude (Cartão de Crédito):**
```python
agent.ingest_csv_data(csv_text, 'creditcard_full')
# Resultado: 17.801 chunks dados + 6 chunks analíticos
```

### **2. Vale Refeição:**
```python
agent.ingest_csv_data(csv_text, 'vale_refeicao_jan2025')
# Resultado: 79 chunks dados + 6 chunks analíticos
```

### **3. Vendas E-commerce:**
```python
agent.ingest_csv_data(csv_text, 'vendas_ecommerce_2024')
# Resultado: 2.850 chunks dados + 6 chunks analíticos
```

**✅ Sistema se adapta automaticamente ao conteúdo do CSV!**

---

## 💡 **PERGUNTAS FREQUENTES**

### ❓ "Como o sistema sabe quais estatísticas gerar?"
**R:** Usa Pandas! `df.describe()` funciona para QUALQUER dataset.

### ❓ "E se o CSV tiver colunas diferentes?"
**R:** Pandas detecta automaticamente: `select_dtypes(include=[np.number])`.

### ❓ "Preciso configurar algo específico por domínio?"
**R:** NÃO! Apenas troque o `source_id`. O resto é automático.

### ❓ "Como responder perguntas específicas do domínio?"
**R:** O LLM interpreta! Exemplo:
- Fraude: "Quais transações são suspeitas?" → LLM encontra chunk com Class=1
- Vale: "Qual departamento gasta mais?" → LLM encontra chunk com aggregação por departamento

### ❓ "Os 6 chunks são sempre os mesmos?"
**R:** SIM! Estrutura fixa, CONTEÚDO dinâmico baseado no CSV.

---

## 📝 **RESUMO EXECUTIVO**

| Item | Descrição |
|------|-----------|
| **Entrada** | Qualquer arquivo CSV (fraude, vale, vendas, etc.) |
| **Processamento** | Pandas analisa automaticamente tipos, estatísticas, correlações |
| **Saída** | N chunks de dados + 6 chunks analíticos (sempre 6!) |
| **Armazenamento** | Supabase (tabela `embeddings`) com metadados |
| **Busca** | RAG encontra chunks relevantes por similaridade semântica |
| **Resposta** | LLM interpreta chunks e responde em linguagem natural |

**🎯 Conclusão:** Sistema 100% genérico! Basta chamar `ingest_csv_data()` com qualquer CSV.
