# Guia de Uso Rápido - Arquitetura V3.0

**Data:** 16 de outubro de 2025  
**Versão:** 3.0.0  

---

## 🚀 INÍCIO RÁPIDO

### Instalação

```powershell
# Clonar repositório
git clone <repo-url>
cd eda-aiminds-i2a2-rb

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### Configuração

```powershell
# Copiar arquivo de configuração
cp configs/.env.example configs/.env

# Editar configs/.env com suas credenciais
```

**Variáveis obrigatórias:**
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=... # opcional
```

---

## 📝 EXEMPLOS DE USO

### 1. Classificação de Intenção Simples

```python
from langchain_openai import ChatOpenAI
from src.analysis.intent_classifier import IntentClassifier

# Inicializar LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# Criar classificador
classifier = IntentClassifier(llm)

# Classificar query
result = classifier.classify("Qual a dispersão dos dados?")

print(f"Intenção: {result.primary_intent}")  # STATISTICAL
print(f"Confiança: {result.confidence}")     # 0.90
print(f"Explicação: {result.reasoning}")
```

**Output esperado:**
```
Intenção: AnalysisIntent.STATISTICAL
Confiança: 0.90
Explicação: 'Dispersão' é sinônimo de 'variabilidade', que se refere a métricas como desvio padrão, variância e coeficiente de variação.
```

---

### 2. Análise Estatística Básica

```python
import pandas as pd
from src.analysis.statistical_analyzer import StatisticalAnalyzer

# Carregar dados
df = pd.read_csv('data/creditcard.csv')

# Criar analyzer
analyzer = StatisticalAnalyzer()

# Executar análise
result = analyzer.analyze(df, columns=['Amount', 'Time'])

# Exibir relatório
print(result.to_markdown())
```

**Output esperado:**
```markdown
# Análise Estatística Descritiva

## Resumo Geral
| Métrica | Amount | Time |
|---------|--------|------|
| Média   | 88.35  | 94813.86 |
| Mediana | 22.00  | 84692.00 |
| Moda    | 1.00   | 82800.00 |

## Variabilidade
| Métrica | Amount | Time |
|---------|--------|------|
| Desvio Padrão | 250.12 | 47488.15 |
| Variância     | 62,560 | 2,255,123,456 |
| CV (%)        | 283.0  | 50.1 |
...
```

---

### 3. Análise de Frequência

```python
from src.analysis.frequency_analyzer import FrequencyAnalyzer

# Criar analyzer
analyzer = FrequencyAnalyzer()

# Executar análise
result = analyzer.analyze(df, columns=['Class'], top_n=5)

# Exibir valores mais frequentes
print("Valores mais frequentes:")
for col, freqs in result.frequency_distributions.items():
    print(f"\n{col}:")
    for value, count in freqs.items():
        print(f"  {value}: {count} ocorrências")

# Exibir estatísticas de moda
print("\nEstatísticas de Moda:")
print(result.mode_stats)
```

**Output esperado:**
```
Valores mais frequentes:

Class:
  0: 284315 ocorrências
  1: 492 ocorrências

Estatísticas de Moda:
{'Class': {'mode_value': 0, 'mode_frequency': 284315, 'mode_percentage': 99.83}}
```

---

### 4. Clustering com KMeans

```python
from src.analysis.clustering_analyzer import ClusteringAnalyzer

# Criar analyzer
analyzer = ClusteringAnalyzer()

# Executar clustering
result = analyzer.analyze(
    df, 
    n_clusters=3, 
    method='kmeans',
    features=['V1', 'V2', 'V3', 'V4', 'V5']
)

# Exibir métricas de qualidade
print(f"Silhouette Score: {result.quality_metrics['silhouette_score']:.3f}")
print(f"Davies-Bouldin Index: {result.quality_metrics['davies_bouldin_index']:.3f}")

# Exibir distribuição de clusters
print("\nDistribuição de pontos:")
for cluster_id, count in result.cluster_distribution.items():
    print(f"Cluster {cluster_id}: {count} pontos")
```

**Output esperado:**
```
Silhouette Score: 0.723
Davies-Bouldin Index: 0.845

Distribuição de pontos:
Cluster 0: 95000 pontos
Cluster 1: 120000 pontos
Cluster 2: 69807 pontos
```

---

### 5. Orquestração Completa (Recomendado)

```python
from langchain_openai import ChatOpenAI
from src.analysis.orchestrator import AnalysisOrchestrator
import pandas as pd

# Inicializar LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# Criar orquestrador
orchestrator = AnalysisOrchestrator(llm)

# Carregar dados
df = pd.read_csv('data/creditcard.csv')

# Executar análise orquestrada
result = orchestrator.orchestrate(
    query="Mostre intervalo E variabilidade dos dados",
    df=df
)

# Exibir relatório completo
print(result.to_markdown())
```

**Output esperado:**
```markdown
# Análise Inteligente de Dados

## Classificação de Intenção
- **Intenção Principal:** STATISTICAL
- **Confiança:** 0.92
- **Justificativa:** Query solicita 'intervalo' (range/amplitude) e 'variabilidade' (dispersão/desvio padrão), ambos relacionados a análise estatística descritiva.

## Análises Executadas
1. ✅ Análise Estatística

---

## Análise Estatística Descritiva

### Métricas de Variabilidade
| Variável | Desvio Padrão | Variância | CV (%) | IQR |
|----------|---------------|-----------|--------|-----|
| Amount   | 250.12        | 62,560.14 | 283.0  | 42.00 |
| V1       | 1.958         | 3.832     | 415.2  | 3.12 |
...

### Métricas de Posição (Intervalo)
| Variável | Mín    | Q1     | Mediana | Q3     | Máx     | Range |
|----------|--------|--------|---------|--------|---------|-------|
| Amount   | 0.00   | 5.60   | 22.00   | 77.17  | 25,691  | 25,691|
...

## Interpretação Integrada

As variáveis apresentam alta variabilidade, especialmente Amount (CV = 283%), indicando grande dispersão dos valores em relação à média. O intervalo de Amount é muito amplo (0 a 25,691), com 50% dos dados concentrados entre 5.60 e 77.17 (IQR = 42.00).

Recomendações:
1. Considerar transformações (log) para Amount devido à alta assimetria
2. Investigar outliers em valores extremos
3. Segmentar análises por faixas de valores
```

---

## 🎯 CASOS DE USO COMUNS

### Caso 1: "Qual a média das transações?"

```python
result = orchestrator.orchestrate("Qual a média das transações?", df)
```

**Resposta automática:**
- Classifica como `STATISTICAL`
- Executa `StatisticalAnalyzer`
- Retorna média de todas variáveis numéricas
- Destaca métrica `mean` no relatório

---

### Caso 2: "Mostre os valores mais comuns"

```python
result = orchestrator.orchestrate("Mostre os valores mais comuns", df)
```

**Resposta automática:**
- Classifica como `FREQUENCY`
- Executa `FrequencyAnalyzer`
- Retorna top 10 valores mais frequentes
- Calcula estatísticas de moda

---

### Caso 3: "Agrupe os dados em clusters"

```python
result = orchestrator.orchestrate("Agrupe os dados em clusters", df)
```

**Resposta automática:**
- Classifica como `CLUSTERING`
- Executa `ClusteringAnalyzer` com KMeans (default)
- Retorna distribuição de clusters
- Calcula métricas de qualidade

---

### Caso 4: Query Mista - "Qual a dispersão E valores raros?"

```python
result = orchestrator.orchestrate(
    "Qual a dispersão E valores raros?", 
    df
)
```

**Resposta automática:**
- Classifica como `STATISTICAL + FREQUENCY`
- Executa **ambos** analyzers em paralelo
- Combina resultados via LLM
- Retorna relatório integrado com:
  - Métricas de variabilidade (dispersão)
  - Análise de valores raros (< 1% frequência)

---

## 🔧 CONFIGURAÇÕES AVANÇADAS

### Personalizar Classificador de Intenção

```python
from src.analysis.intent_classifier import IntentClassifier

classifier = IntentClassifier(
    llm=llm,
    logger=custom_logger  # Opcional
)

# Classificar com contexto adicional
result = classifier.classify(
    query="Mostre tendências",
    context={
        'available_columns': ['Time', 'Amount', 'Class'],
        'has_temporal_data': True
    }
)
```

---

### Personalizar Analyzer Estatístico

```python
from src.analysis.statistical_analyzer import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(logger=custom_logger)

# Analisar apenas colunas específicas
result = analyzer.analyze(
    df=df,
    columns=['Amount', 'Time']  # Só estas colunas
)

# Exportar para dict
data = result.to_dict()

# Exportar para markdown
markdown = result.to_markdown()
```

---

### Personalizar Clustering

```python
from src.analysis.clustering_analyzer import ClusteringAnalyzer

analyzer = ClusteringAnalyzer()

# KMeans com 5 clusters
result = analyzer.analyze(
    df=df,
    n_clusters=5,
    method='kmeans',
    features=['V1', 'V2', 'V3']
)

# DBSCAN com parâmetros customizados
result = analyzer.analyze(
    df=df,
    method='dbscan',
    eps=0.5,
    min_samples=10,
    features=['Amount', 'Time']
)

# Clustering hierárquico
result = analyzer.analyze(
    df=df,
    n_clusters=4,
    method='hierarchical',
    features=df.select_dtypes(include=['number']).columns.tolist()
)
```

---

### Orquestrador com Contexto

```python
from src.analysis.orchestrator import AnalysisOrchestrator

orchestrator = AnalysisOrchestrator(
    llm=llm,
    logger=custom_logger
)

# Orquestrar com contexto adicional
result = orchestrator.orchestrate(
    query="Analise as fraudes",
    df=df,
    context={
        'target_column': 'Class',
        'fraud_class': 1,
        'previous_queries': ['Qual a proporção de fraudes?']
    }
)
```

---

## 🧪 TESTANDO SUA IMPLEMENTAÇÃO

### Teste Rápido de Classificação

```python
from langchain_openai import ChatOpenAI
from src.analysis.intent_classifier import IntentClassifier

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
classifier = IntentClassifier(llm)

# Teste com sinônimos
queries = [
    "Qual a dispersão?",
    "Mostre a variabilidade",
    "Calcule o desvio padrão",
    "Qual o spread dos dados?"
]

for query in queries:
    result = classifier.classify(query)
    print(f"{query} → {result.primary_intent}")
```

**Resultado esperado:** Todos devem classificar como `STATISTICAL`

---

### Teste de Orquestração End-to-End

```python
import pandas as pd
from langchain_openai import ChatOpenAI
from src.analysis.orchestrator import AnalysisOrchestrator

# Setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
orchestrator = AnalysisOrchestrator(llm)
df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50]
})

# Executar
result = orchestrator.orchestrate("Qual a média?", df)

# Validar
assert result.intent_classification.primary_intent.value == 'statistical'
assert 'statistical' in result.execution_order
assert result.combined_results is not None

print("✅ Teste passou!")
```

---

## 📊 MONITORAMENTO E LOGGING

### Habilitar Logs Detalhados

```python
import logging
from src.utils.logging_config import get_logger

# Configurar nível de log
logging.basicConfig(level=logging.DEBUG)

# Usar logger em seus módulos
logger = get_logger(__name__)

# Logs serão exibidos automaticamente:
# INFO: Classificando intenção da query: 'Qual a média?'
# DEBUG: Intenção classificada: STATISTICAL (confidence: 0.92)
# INFO: Executando StatisticalAnalyzer...
# INFO: Análise estatística concluída
```

---

### Exportar Resultados para Arquivo

```python
# Exportar resultado para Markdown
with open('outputs/relatorio.md', 'w', encoding='utf-8') as f:
    f.write(result.to_markdown())

# Exportar resultado para JSON
import json

with open('outputs/resultado.json', 'w', encoding='utf-8') as f:
    json.dump(result.to_dict(), f, indent=2)
```

---

## ⚠️ TROUBLESHOOTING

### Problema: "LLM não classifica corretamente"

**Solução:**
- Verifique temperatura do LLM (deve ser baixa: 0.1-0.3)
- Confirme que está usando modelo poderoso (gpt-4o, gpt-4o-mini, gemini-1.5)
- Adicione contexto na classificação

```python
result = classifier.classify(
    query=query,
    context={'domain': 'fraud detection', 'available_analyses': ['statistical', 'clustering']}
)
```

---

### Problema: "Erro ao calcular métricas estatísticas"

**Solução:**
- Confirme que DataFrame tem colunas numéricas
- Verifique valores nulos/infinitos

```python
# Pré-processar dados
df_clean = df.select_dtypes(include=['number']).fillna(0)
result = analyzer.analyze(df_clean)
```

---

### Problema: "Clustering retorna apenas 1 cluster"

**Solução:**
- Ajuste parâmetros do algoritmo
- Normalize/padronize features antes

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
df_scaled = pd.DataFrame(
    scaler.fit_transform(df[features]),
    columns=features
)

result = analyzer.analyze(df_scaled, n_clusters=3, method='kmeans')
```

---

## 📚 PRÓXIMOS PASSOS

1. **Integrar com RAGDataAgent** - usar orquestrador no fluxo principal
2. **Adicionar mais analyzers** - correlação, outliers, comparação
3. **Visualização automática** - gráficos baseados em tipo de análise
4. **Cache de resultados** - evitar recomputação de análises repetidas
5. **Testes automatizados** - garantir qualidade contínua

---

## 🔗 REFERÊNCIAS

- **Documentação Completa:** `docs/ARCHITECTURE_V3.md`
- **Diagramas de Fluxo:** `docs/ARCHITECTURE_FLOW.md`
- **Exemplo V3.0:** `examples/rag_data_agent_v3_proposal.py`
- **Auditoria V2.0:** `docs/2025-10-16_relatorio-auditoria-tecnica-refatoracao.md`

---

**Guia criado por:** EDA AI Minds Team  
**Última atualização:** 16 de outubro de 2025  
**Versão mínima Python:** 3.10+  
**Dependências:** LangChain 0.2+, pandas 2.0+, scikit-learn 1.3+
