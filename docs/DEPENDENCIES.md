# Dependências do EDA AI Minds Backend

## Resumo da Stack Tecnológica

Este documento explica cada dependência usada no projeto e sua função específica.

## 📦 Dependências Core (Essenciais)

### Configuração e Ambiente
- **python-dotenv** `1.1.1` - Carrega variáveis de ambiente de arquivos `.env`
- **pydantic** `2.11.7` - Validação de dados com type hints modernos
- **pydantic-settings** `2.10.1` - Gerenciamento de configurações via environment

### Manipulação de Dados  
- **pandas** `2.2.3` - Análise e manipulação de dados CSV/Excel/SQL
- **numpy** `2.3.2` - Computação numérica fundamental para arrays

### Visualização
- **matplotlib** `3.10.6` - Biblioteca base para gráficos e plots
- **seaborn** `0.13.2` - Visualizações estatísticas elegantes sobre matplotlib

### HTTP e APIs
- **requests** `2.32.5` - Cliente HTTP simples e elegante
- **requests-toolbelt** `1.0.0` - Utilitários adicionais para requests

## 🗄️ Stack de Banco de Dados

### PostgreSQL
- **psycopg** `3.2.9` - Driver PostgreSQL moderno e assíncrono
- **psycopg-binary** `3.2.9` - Versão pré-compilada do psycopg
- **psycopg2-binary** `2.9.10` - Driver PostgreSQL clássico (fallback)
- **psycopg-pool** `3.2.6` - Pool de conexões para psycopg

### Supabase & Vector DB
- **supabase** `2.20.0` - Cliente oficial Supabase Python
- **pgvector** `0.3.6` - Extensão PostgreSQL para busca vetorial

## 🧠 Stack AI/ML

### Embeddings e NLP
- **sentence-transformers** `5.1.1` - Modelos pré-treinados para embeddings semânticos
- **torch** `2.8.0` - Framework PyTorch para deep learning
- **transformers** `4.56.2` - Modelos Hugging Face (BERT, GPT, etc.)
- **tokenizers** `0.22.1` - Tokenização rápida para modelos transformer

### Machine Learning  
- **scikit-learn** `1.7.2` - Algoritmos clássicos de ML (clustering, classificação)
- **scipy** `1.16.2` - Computação científica avançada
- **safetensors** `0.6.2` - Carregamento seguro de tensors ML

## 🔗 LangChain Ecosystem

### Core Framework
- **langchain** `0.3.27` - Framework principal para aplicações LLM
- **langchain-core** `0.3.76` - Abstrações fundamentais do LangChain  
- **langchain-community** `0.3.27` - Integrações comunitárias
- **langchain-text-splitters** `0.3.9` - Ferramentas de chunking de texto

### Integrações LLM
- **langchain-openai** `0.3.30` - Integração OpenAI (GPT-4, embeddings)
- **langchain-google-genai** `2.1.9` - Integração Google Gemini
- **langchain-experimental** `0.0.60` - Funcionalidades experimentais (pandas agent)

### Observabilidade
- **langsmith** `0.4.20` - Tracking e debugging de aplicações LangChain

## 🚀 Provedores de LLM

### OpenAI
- **openai** `1.102.0` - Cliente oficial OpenAI (GPT-4, DALL-E, embeddings)

### Google AI
- **google-ai-generativelanguage** `0.6.18` - API Google AI Gemini
- **google-api-core** `2.25.1` - Biblioteca core Google APIs
- **google-auth** `2.40.3` - Autenticação Google Cloud

## 🛠️ Utilitários

### Logging e Debug
- **coloredlogs** `15.0.1` - Logs coloridos e formatados no terminal
- **colorama** `0.4.6` - Cores ANSI para Windows

### Async e Concorrência
- **aiohttp** `3.12.15` - Cliente HTTP assíncrono
- **anyio** `4.10.0` - Abstração async/await universal

### Processamento JSON
- **orjson** `3.11.3` - Parser JSON ultrarrápido em Rust

### Utilidades Gerais
- **tabulate** `0.9.0` - Formatação elegante de tabelas
- **tqdm** `4.67.1` - Barras de progresso para loops

## 📊 Exemplo de Uso por Funcionalidade

### Para Análise CSV:
```python
import pandas as pd           # Carregar/manipular CSV
import numpy as np           # Operações numéricas
import matplotlib.pyplot as plt  # Gráficos
import seaborn as sns        # Visualizações estatísticas
```

### Para Sistema RAG:
```python
from sentence_transformers import SentenceTransformer  # Embeddings
from langchain import LLMChain                         # Orquestração LLM
from supabase import create_client                     # Vector store
import pgvector                                        # Busca vetorial
```

### Para Integrações LLM:
```python
import openai                          # GPT-4/embeddings
from langchain_openai import ChatOpenAI       # Interface LangChain
from langchain_google_genai import ChatGoogleGenerativeAI  # Gemini
```

## 🔧 Comandos de Instalação

```bash
# Instalação completa
pip install -r requirements.txt

# Instalação mínima (só CSV)
pip install -r requirements-minimal.txt  

# Instalação para desenvolvimento
pip install -r requirements-dev.txt

# Validar instalação
python validate_dependencies.py
```

## 📈 Estatísticas

- **Total de dependências**: ~21 principais + ~50 sub-dependências
- **Tamanho estimado**: ~2.5GB (incluindo modelos PyTorch)
- **Tempo de instalação**: ~5-15 minutos (dependendo da conexão)
- **Compatibilidade**: Python 3.10+ (recomendado 3.11+)

## 🎯 Dependências Opcionais por Funcionalidade

| Funcionalidade | Dependências Mínimas | Status |
|---|---|---|
| **CSV Analysis** | pandas, matplotlib, seaborn | ✅ Essencial |
| **Basic RAG** | sentence-transformers, numpy | ✅ Essencial | 
| **LLM Integration** | langchain, openai | 🟡 Opcional |
| **Vector Search** | supabase, pgvector | 🟡 Opcional |
| **Advanced ML** | scikit-learn, torch | 🟢 Nice-to-have |

## 💡 Otimizações de Performance

- **torch**: CPU-only por padrão (GPU opcional com CUDA)
- **sentence-transformers**: Modelo all-MiniLM-L6-v2 (384D, ~90MB)
- **psycopg**: Driver PostgreSQL moderno mais rápido que psycopg2
- **orjson**: JSON parsing ~2x mais rápido que json nativo