# Análise Exploratória - Questão 02

## Objetivo
Realizar análise exploratória do arquivo `creditcard_test_500.csv`, identificando tipos de variáveis, estatísticas descritivas, distribuição/histogramas e possíveis insights relevantes.

## Decisões Técnicas
- Utilizado Pandas para leitura e análise dos dados.
- Geração automática de estatísticas e gráficos com matplotlib/seaborn.
- Script executado localmente, sem uso de embeddings ou Supabase.
- Segue padrão de relatório técnico do projeto.

## Estrutura do Dataset
- Total de linhas: 500
- Total de colunas: 31
- Colunas: Time, V1-V28, Amount, Class

## Tipos de Variáveis
- **Numéricas:** Todas as variáveis, exceto `Class` (target binário)
- **Target:** `Class` (0 = normal, 1 = fraude)

## Estatísticas Descritivas
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/creditcard_test_500.csv')
desc = df.describe().T
print(desc)
```

## Distribuição das Variáveis
- Foram gerados histogramas para todas as variáveis numéricas.
- Os gráficos estão disponíveis em `outputs/histogramas/`.

## Insights Relevantes
- A maioria das variáveis apresenta distribuição normal ou assimétrica.
- A coluna `Amount` possui grande variação de valores.
- A coluna `Class` está fortemente desbalanceada (predominância de classe 0).

## Próximos Passos
1. Realizar análise de correlação entre variáveis.
2. Investigar padrões de fraude (classe 1) com amostra maior.
3. Integrar análise com embeddings/Supabase para RAG.

## Problemas e Soluções
- Nenhum problema crítico identificado nesta amostra.

## Métricas
- Linhas analisadas: 500
- Colunas analisadas: 31
- Histogramas gerados: 30

## Screenshots/Logs
- [Inclua gráficos e logs relevantes em outputs/histogramas/]

---
Relatório gerado automaticamente por agente multiagente EDA AI Minds.




################

Analise Supabase - Tabela embeddings 
