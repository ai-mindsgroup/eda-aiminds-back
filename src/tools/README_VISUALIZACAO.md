# Sistema de Visualização Gráfica - EDA AI Minds

Sistema completo de geração automática de visualizações gráficas para análise exploratória de dados.

## 🎨 Características

### 5 Tipos de Gráficos Suportados

1. **Histogramas** com KDE e estatísticas
2. **Scatter Plots** com linha de tendência e correlação
3. **Boxplots** com detecção automática de outliers
4. **Gráficos de Barras** (verticais e horizontais)
5. **Heatmaps de Correlação** com análise de pares

### Funcionalidades Avançadas

- ✅ **Detecção Automática**: Identifica necessidade de visualização através de keywords
- ✅ **Retorno Flexível**: Base64 para APIs/web ou salvamento em arquivo
- ✅ **Estatísticas Integradas**: Cada gráfico retorna métricas relevantes
- ✅ **Integração Total**: Disponível em todos os agentes via `generate_visualization()`
- ✅ **Backend Não-Interativo**: Pronto para uso em servidores

## 📦 Dependências

```text
matplotlib==3.10.6
seaborn==0.13.2
plotly==6.0.1
pandas>=2.2.3
numpy>=2.3.2
```

## 🚀 Uso Básico

### Importar o Gerador

```python
from src.tools.graph_generator import GraphGenerator, detect_visualization_need

# Criar instância
generator = GraphGenerator(output_dir="temp/visualizations")
```

### Exemplo 1: Histograma

```python
import pandas as pd

df = pd.read_csv("data/creditcard.csv")

# Gerar histograma
img, stats = generator.histogram(
    data=df,
    column="Amount",
    bins=50,
    title="Distribuição de Valores",
    kde=True
)

print(f"Média: {stats['mean']:.2f}")
print(f"Mediana: {stats['median']:.2f}")
print(f"Desvio: {stats['std']:.2f}")
```

### Exemplo 2: Scatter Plot

```python
# Gerar scatter plot
img, stats = generator.scatter_plot(
    data=df,
    x_column="V1",
    y_column="V2",
    hue_column="Class",
    title="Relação V1 vs V2"
)

print(f"Correlação: {stats['correlation']:.4f}")
```

### Exemplo 3: Boxplot

```python
# Detectar outliers
img, stats = generator.boxplot(
    data=df,
    column="Time",
    title="Boxplot de Time"
)

print(f"Outliers: {stats['outliers_count']} ({stats['outliers_percentage']:.2f}%)")
```

### Exemplo 4: Gráfico de Barras

```python
# Contagem por categoria
class_counts = df['Class'].value_counts().to_dict()

img, stats = generator.bar_chart(
    data=class_counts,
    title="Transações por Classe"
)

print(f"Total: {stats['total']}")
print(f"Max categoria: {stats['max_category']}")
```

### Exemplo 5: Heatmap de Correlação

```python
# Matriz de correlação
img, stats = generator.correlation_heatmap(
    data=df,
    columns=['Time', 'Amount', 'V1', 'V2', 'V3'],
    title="Matriz de Correlação"
)

print(f"Correlação média: {stats['mean_correlation']:.4f}")
print(f"Mais forte: {stats['strongest_positive']}")
```

## 🤖 Integração com Agentes

Todos os agentes herdam o método `generate_visualization()`:

```python
from src.agent.csv_analysis_agent import EmbeddingsAnalysisAgent

agent = EmbeddingsAnalysisAgent("csv_agent")

# Gerar visualização via agente
result = agent.generate_visualization(
    data=df,
    viz_type='histogram',
    column='Amount',
    bins=30
)

if result:
    print(f"Gráfico gerado: {result['type']}")
    print(f"Estatísticas: {result['statistics']}")
    print(f"Imagem: {result['image'][:100]}...")
```

## 🎯 Detecção Automática

O sistema detecta automaticamente quando criar visualizações:

```python
queries = [
    "Mostre um histograma da distribuição de valores",
    "Gere um gráfico de dispersão entre V1 e V2",
    "Faça um boxplot para detectar outliers",
    "Crie um gráfico de barras comparando classes",
    "Exiba um heatmap de correlação"
]

for query in queries:
    viz_type = detect_visualization_need(query)
    if viz_type:
        print(f"Query: {query}")
        print(f"→ Tipo detectado: {viz_type}\n")
```

### Keywords Reconhecidas

- **Histograma**: histograma, distribuição, frequência, histogram
- **Scatter**: dispersão, scatter, correlação, relação entre
- **Boxplot**: boxplot, outliers, quartis, box plot
- **Barras**: barras, bar chart, gráfico de barras, comparação
- **Heatmap**: heatmap, mapa de calor, correlações, matriz de correlação

## 📊 Exemplos Completos

Execute o script de demonstração:

```powershell
python examples/exemplo_visualizacao_graficos.py
```

Saída esperada:
```
================================================================================
🎨 EXEMPLOS DE USO: SISTEMA DE VISUALIZAÇÃO GRÁFICA
================================================================================

📊 EXEMPLO 1: HISTOGRAMA
✅ Histograma gerado com sucesso!
📈 Estatísticas:
  • Contagem: 500
  • Média: €69.72
  • Mediana: €18.16
  • Desvio Padrão: €217.90
  ...

📊 EXEMPLO 2: SCATTER PLOT
✅ Scatter plot gerado com sucesso!
📈 Estatísticas:
  • Correlação: 0.0250
  • Número de pontos: 500
  ...
```

## 🔧 Configuração Avançada

### Retorno em Base64 (padrão)

```python
img, stats = generator.histogram(
    data=df,
    column="Amount",
    return_base64=True  # Padrão
)

# img será: "data:image/png;base64,iVBORw0KG..."
```

### Salvar em Arquivo

```python
generator = GraphGenerator(output_dir="output/graphs")

img, stats = generator.histogram(
    data=df,
    column="Amount",
    return_base64=False
)

# img será: "output/graphs/graph_20251001_063245.png"
```

### Personalização Visual

```python
# Histograma customizado
img, stats = generator.histogram(
    data=df,
    column="Amount",
    bins=100,
    color="steelblue",
    kde=True,
    title="Distribuição Customizada",
    xlabel="Valor (€)",
    ylabel="Frequência Absoluta"
)

# Scatter com transparência
img, stats = generator.scatter_plot(
    data=df,
    x_column="V1",
    y_column="V2",
    size=20,
    alpha=0.5  # 50% transparência
)
```

## 📁 Estrutura de Arquivos

```
src/tools/
  └── graph_generator.py      # Módulo principal
      ├── GraphGenerator       # Classe principal
      ├── GraphGeneratorError  # Exceção customizada
      └── detect_visualization_need()  # Função de detecção

examples/
  └── exemplo_visualizacao_graficos.py  # Demonstração completa

temp/visualizations/         # Imagens geradas (git-ignored)
```

## 🐛 Tratamento de Erros

```python
from src.tools.graph_generator import GraphGeneratorError

try:
    img, stats = generator.histogram(
        data=df,
        column="NonExistentColumn"
    )
except GraphGeneratorError as e:
    print(f"Erro ao gerar gráfico: {e}")
```

## 🧪 Testes

```python
# Testar com dados sintéticos
import numpy as np

data = np.random.normal(100, 15, 1000)

img, stats = generator.histogram(
    data=data,
    bins=50,
    title="Distribuição Normal Sintética"
)

assert stats['count'] == 1000
assert 95 < stats['mean'] < 105  # Média próxima de 100
```

## 📖 Referências

- **Matplotlib**: [https://matplotlib.org/](https://matplotlib.org/)
- **Seaborn**: [https://seaborn.pydata.org/](https://seaborn.pydata.org/)
- **Plotly**: [https://plotly.com/python/](https://plotly.com/python/)

## 📝 Notas

- Backend não-interativo (`matplotlib.use('Agg')`) para uso em servidores
- Estilo consistente com Seaborn whitegrid
- Suporte a Pandas DataFrame, Series e NumPy arrays
- Validação automática de dados de entrada
- Logging estruturado para debug

---

**Desenvolvido por:** EDA AI Minds Team  
**Data:** Outubro de 2025  
**Versão:** 1.0.0
