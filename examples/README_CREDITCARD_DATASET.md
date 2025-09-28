# Dataset Credit Card Fraud

## Visão Geral

Este diretório deveria conter o arquivo `creditcard.csv` para análise de fraudes, mas devido ao tamanho do arquivo (143.84 MB), ele não pode ser incluído no repositório Git.

## Como Obter o Dataset

### Opção 1: Kaggle (Recomendado)
1. Acesse: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
2. Faça download do arquivo `creditcard.csv`
3. Coloque o arquivo neste diretório (`examples/creditcard.csv`)

### Opção 2: Dados Sintéticos
Use o gerador de dados sintéticos do sistema:

```python
from src.data.data_processor import create_demo_data

# Gerar dados de fraude sintéticos
processor = create_demo_data("fraud_detection", num_rows=10000, fraud_rate=0.05)

# Exportar para CSV
processor.export_to_csv("examples/creditcard_synthetic.csv")
```

### Opção 3: URL Direta (se disponível)
```python
from src.data.data_processor import load_csv_url

# Se houver uma URL pública disponível
processor = load_csv_url("https://exemplo.com/creditcard.csv")
```

## Estrutura Esperada do Dataset

O arquivo `creditcard.csv` deve ter as seguintes colunas:

| Coluna | Descrição | Tipo |
|--------|-----------|------|
| Time | Segundos desde primeira transação | Float |
| V1-V28 | Features principais (PCA) | Float |
| Amount | Valor da transação | Float |
| Class | Indicador de fraude (0=normal, 1=fraude) | Int |

## Uso nos Exemplos

Após obter o dataset, você pode usar os seguintes scripts:

- `creditcard_fraud_analysis.py` - Análise completa de fraudes
- `fraud_detection_llm_simple.py` - Detecção com LLM + RAG
- `fraud_detection_llm_advanced.py` - Análise avançada

## Estatísticas Esperadas

- **Total de transações**: ~284.807
- **Transações fraudulentas**: ~492 (0.172%)
- **Tamanho do arquivo**: ~143 MB
- **Formato**: CSV com cabeçalho

## Comandos para Usar

```bash
# Análise básica
python examples/creditcard_fraud_analysis.py

# Análise com LLM
python examples/fraud_detection_llm_simple.py

# Teste interativo
python examples/exemplo_csv_interativo.py
```

## Notas Importantes

- O arquivo original contém dados reais anonimizados
- Respeite os termos de uso do Kaggle
- Para produção, considere usar amostras menores
- O sistema suporta arquivos CSV de até 500MB