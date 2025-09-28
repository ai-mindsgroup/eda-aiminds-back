# Exemplo Interativo CSV com Orquestrador

## 📖 Descrição
Este exemplo permite carregar um arquivo CSV real e interagir com o sistema multiagente através de consultas em linguagem natural.

## 🚀 Como Usar

### 1. Executar o Exemplo
```bash
# Modo interativo (escolher arquivo)
python examples/exemplo_csv_interativo.py

# Especificando um arquivo
python examples/exemplo_csv_interativo.py --arquivo caminho/para/seu/arquivo.csv

# Usando arquivo de exemplo
python examples/exemplo_csv_interativo.py --arquivo examples/dados_exemplo.csv
```

### 2. Opções de Arquivo
- **Arquivo próprio**: Digite o caminho completo para seu CSV
- **Arquivo de exemplo**: Use `dados_exemplo.csv` para testar
- **Validação automática**: O sistema verifica se o arquivo é válido

### 3. Consultas Suportadas

#### 📊 Análise de Dados
```
• "carregue os dados"
• "faça um resumo completo"
• "mostre as estatísticas básicas"
• "quais são as correlações importantes?"
• "analise padrões suspeitos"
```

#### 🔍 Análises Específicas
```
• "detecte fraudes nos dados"
• "mostre a distribuição das categorias"
• "identifique outliers"
• "compare grupos de dados"
```

#### 🤖 Sistema
```
• "status do sistema"
• "quais agentes estão disponíveis?"
• "ajuda" - mostra mais opções
```

## 🎯 Funcionalidades

### ✅ Validação Automática
- Verifica se o arquivo existe
- Confirma formato CSV válido
- Mostra informações básicas do arquivo

### 🤖 Orquestrador Inteligente
- Roteamento automático para agentes especializados
- Contexto mantido durante toda a sessão
- Respostas em linguagem natural

### 🎨 Interface Colorida
- Cabeçalhos destacados
- Mensagens coloridas por tipo
- Feedback visual claro

## 📝 Exemplo de Sessão

```
==========================================================
            🚀 EDA AI MINDS - ANÁLISE INTERATIVA DE CSV
==========================================================

ℹ️  Sistema multiagente para análise inteligente de dados CSV

📁 SELEÇÃO DE ARQUIVO CSV
Escolha uma opção (1-3): 2

✅ Arquivo CSV válido: 7 colunas detectadas

ℹ️  📊 INFORMAÇÕES DO ARQUIVO
   📁 Nome: dados_exemplo.csv
   📏 Tamanho: 41,234 bytes
   📋 Linhas (amostra): 1,000
   📊 Colunas: 7
   🏷️  Nomes das colunas: id_transacao, valor, categoria, horario, dia_semana...

🤖 SESSÃO INTERATIVA DE ANÁLISE
💬 Sua consulta: faça um resumo dos dados

🔄 Processando...

🤖 Resposta:
📊 **Resumo do Dataset**
- Arquivo: dados_exemplo.csv
- Dimensões: 1,000 linhas × 7 colunas
- Colunas numéricas: 5
- Análise de fraude: 5.2% das transações marcadas como suspeitas
...
```

## 🔧 Requisitos
- Python 3.10+
- Dependências instaladas (`pip install -r requirements.txt`)
- Ambiente virtual ativado
- Configurações do Supabase (opcional para RAG)

## 🐛 Resolução de Problemas

### Erro: "Módulo src não encontrado"
O script já inclui configuração automática do PYTHONPATH.

### Erro: "Arquivo CSV inválido"
- Verifique se o arquivo existe
- Confirme a extensão .csv
- Teste com o arquivo de exemplo primeiro

### Erro: "RAGAgent não disponível"
Configure as variáveis do Supabase em `configs/.env` (opcional).

## 💡 Dicas

### Para Melhores Resultados:
1. Use arquivos CSV com cabeçalhos claros
2. Consulte em linguagem natural e específica
3. Experimente diferentes tipos de análise
4. Use o comando 'ajuda' para ver opções

### Consultas Eficazes:
- Seja específico: "analise fraudes por categoria" vs "analise dados"
- Use contexto: "compare gastos entre fins de semana e dias úteis"
- Peça visualizações: "mostre gráfico de correlações"

## 📊 Dados de Exemplo
O arquivo `dados_exemplo.csv` contém:
- **1000 transações** simuladas
- **7 colunas**: id_transacao, valor, categoria, horario, dia_semana, fraude, valor_suspeito
- **Casos de fraude**: ~5% das transações
- **Categorias**: Alimentação, Transporte, Lazer, Saúde
- **Perfeito para testar** detecção de padrões