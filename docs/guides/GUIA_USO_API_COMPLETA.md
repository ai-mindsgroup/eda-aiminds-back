# 🚀 Guia Completo - Como Usar a API EDA AI Minds

**Base URL**: `http://localhost:8000`

A API está rodando e oferece 12 endpoints principais para análise inteligente de dados CSV. Este guia mostra como usar cada endpoint com exemplos práticos.

## 📋 Índice de Endpoints

1. [Health Check](#1-health-check) - Verificar status da API
2. [Chat com IA](#2-chat-com-ia) - Conversar com agentes IA
3. [Upload CSV](#3-upload-csv) - Enviar arquivos CSV
4. [Listar Arquivos](#4-listar-arquivos) - Ver arquivos enviados
5. [Analisar CSV](#5-analisar-csv) - Análise específica de arquivo
6. [Análise Estatística](#6-análise-estatística) - Estatísticas detalhadas
7. [Busca Vetorial](#7-busca-vetorial) - Pesquisa semântica
8. [Visualizações](#8-visualizações) - Gerar gráficos
9. [Métricas Dashboard](#9-métricas-dashboard) - Painel de controle
10. [Gestão de Sessões](#10-gestão-de-sessões) - Gerenciar conversas
11. [Gestão de Memória](#11-gestão-de-memória) - Cache e contexto
12. [Configurações Sistema](#12-configurações-sistema) - Ajustes avançados

---

## 1. Health Check

### **GET** `/health`
Verifica se a API está funcionando.

#### **cURL:**
```bash
curl http://localhost:8000/health
```

#### **Python:**
```python
import requests

response = requests.get("http://localhost:8000/health")
print(response.json())
```

#### **Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T15:30:45",
  "message": "API funcionando corretamente",
  "version": "1.0.0"
}
```

---

## 2. Chat com IA

### **POST** `/chat`
Conversa com os agentes IA para análise de dados.

#### **Payload:**
```json
{
  "message": "Analise os dados de fraude no cartão de crédito",
  "session_id": "opcional-session-123",
  "use_memory": true
}
```

#### **cURL:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais são os padrões de fraude nos dados?",
    "session_id": "session_001"
  }'
```

#### **Python:**
```python
import requests

payload = {
    "message": "Analise os dados e identifique outliers",
    "session_id": "minha_sessao_001",
    "use_memory": True
}

response = requests.post("http://localhost:8000/chat", json=payload)
result = response.json()
print(f"IA: {result['response']}")
```

#### **Resposta:**
```json
{
  "response": "Analisando os dados, identifiquei 3 padrões principais de fraude...",
  "session_id": "session_001",
  "timestamp": "2025-10-04T15:35:20",
  "agent_used": "orchestrator",
  "tokens_used": 245
}
```

---

## 3. Upload CSV

### **POST** `/csv/upload`
Envia arquivo CSV para análise.

#### **cURL:**
```bash
curl -X POST http://localhost:8000/csv/upload \
  -F "file=@data/creditcard_test_500.csv"
```

#### **Python:**
```python
import requests

# Upload de arquivo
with open("data/creditcard_test_500.csv", "rb") as file:
    files = {"file": file}
    response = requests.post("http://localhost:8000/csv/upload", files=files)
    
result = response.json()
print(f"Arquivo enviado: {result['filename']}")
print(f"Linhas: {result['rows']}, Colunas: {result['columns']}")
```

#### **JavaScript (Frontend):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/csv/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Upload sucesso:', data);
});
```

#### **Resposta:**
```json
{
  "file_id": "csv_1728054930_creditcard",
  "filename": "creditcard_test_500.csv",
  "rows": 500,
  "columns": 31,
  "message": "CSV carregado com sucesso",
  "columns_list": ["Time", "V1", "V2", "Amount", "Class"],
  "preview": {
    "head": [
      {"Time": 0, "V1": -1.359807, "Amount": 149.62, "Class": 0},
      {"Time": 0, "V1": 1.191857, "Amount": 2.69, "Class": 0}
    ]
  }
}
```

---

## 4. Listar Arquivos

### **GET** `/csv/files`
Lista todos os arquivos CSV enviados.

#### **cURL:**
```bash
curl http://localhost:8000/csv/files
```

#### **Python:**
```python
import requests

response = requests.get("http://localhost:8000/csv/files")
files = response.json()

print(f"Total de arquivos: {files['total']}")
for file in files['files']:
    print(f"- {file['filename']} ({file['rows']} linhas)")
```

#### **Resposta:**
```json
{
  "total": 3,
  "files": [
    {
      "file_id": "csv_1728054930_creditcard",
      "filename": "creditcard_test_500.csv",
      "rows": 500,
      "columns": 31,
      "upload_date": "2025-10-04T15:30:45"
    },
    {
      "file_id": "csv_1728055100_transactions",
      "filename": "transactions.csv",
      "rows": 1200,
      "columns": 8,
      "upload_date": "2025-10-04T15:35:12"
    }
  ]
}
```

---

## 5. Analisar CSV

### **POST** `/csv/analyze`
Análise específica de um arquivo CSV.

#### **Payload:**
```json
{
  "file_id": "csv_1728054930_creditcard",
  "analysis_type": "fraud_detection",
  "columns": ["Amount", "Class"],
  "options": {
    "include_correlations": true,
    "detect_outliers": true
  }
}
```

#### **Python:**
```python
import requests

payload = {
    "file_id": "csv_1728054930_creditcard",
    "analysis_type": "general",
    "columns": ["Amount", "V1", "V2", "Class"],
    "options": {
        "include_correlations": True,
        "detect_outliers": True,
        "generate_insights": True
    }
}

response = requests.post("http://localhost:8000/csv/analyze", json=payload)
analysis = response.json()

print("Insights da análise:")
for insight in analysis['insights']:
    print(f"- {insight}")
```

#### **Resposta:**
```json
{
  "file_id": "csv_1728054930_creditcard",
  "analysis_summary": {
    "total_rows": 500,
    "missing_values": 0,
    "duplicates": 2,
    "outliers_detected": 15
  },
  "correlations": {
    "Amount_Class": -0.256,
    "V1_Class": 0.102
  },
  "insights": [
    "Detectadas 15 transações suspeitas baseadas em outliers",
    "Correlação negativa entre Amount e Class sugere padrão de fraude",
    "98.4% das transações são legítimas"
  ],
  "processing_time": 2.3
}
```

---

## 6. Análise Estatística

### **POST** `/csv/stats`
Estatísticas detalhadas dos dados.

#### **Payload:**
```json
{
  "file_id": "csv_1728054930_creditcard",
  "include_distributions": true,
  "include_correlations": true
}
```

#### **Python:**
```python
import requests

payload = {
    "file_id": "csv_1728054930_creditcard",
    "include_distributions": True,
    "include_correlations": True,
    "columns": ["Amount", "V1", "V2"]  # Opcional: colunas específicas
}

response = requests.post("http://localhost:8000/csv/stats", json=payload)
stats = response.json()

print("Estatísticas descritivas:")
print(f"Média Amount: {stats['descriptive']['Amount']['mean']}")
print(f"Desvio padrão: {stats['descriptive']['Amount']['std']}")
```

#### **Resposta:**
```json
{
  "file_id": "csv_1728054930_creditcard",
  "descriptive": {
    "Amount": {
      "count": 500,
      "mean": 88.25,
      "std": 250.12,
      "min": 0.0,
      "25%": 5.60,
      "50%": 22.0,
      "75%": 77.165,
      "max": 25691.16
    }
  },
  "distributions": {
    "Amount": {
      "skewness": 15.389,
      "kurtosis": 600.211,
      "normality_test": "não-normal"
    }
  },
  "correlations": {
    "Amount_V1": 0.076,
    "Amount_V2": 0.175
  }
}
```

---

## 7. Busca Vetorial

### **POST** `/search/semantic`
Busca semântica nos dados usando embeddings.

#### **Payload:**
```json
{
  "query": "transações de alto valor suspeitas",
  "limit": 5,
  "similarity_threshold": 0.7
}
```

#### **Python:**
```python
import requests

payload = {
    "query": "padrões de fraude em cartão de crédito",
    "limit": 10,
    "similarity_threshold": 0.8,
    "filters": {
        "file_id": "csv_1728054930_creditcard"
    }
}

response = requests.post("http://localhost:8000/search/semantic", json=payload)
results = response.json()

print(f"Encontrados {len(results['matches'])} resultados:")
for match in results['matches']:
    print(f"- Similaridade: {match['similarity']:.3f}")
    print(f"  Conteúdo: {match['content'][:100]}...")
```

#### **Resposta:**
```json
{
  "query": "transações de alto valor suspeitas",
  "matches": [
    {
      "id": "chunk_123",
      "content": "Análise de transações acima de $1000 mostra padrão suspeito...",
      "similarity": 0.892,
      "metadata": {
        "file_id": "csv_1728054930_creditcard",
        "chunk_type": "analysis_result"
      }
    }
  ],
  "total_found": 5,
  "processing_time": 0.45
}
```

---

## 8. Visualizações

### **POST** `/csv/visualize`
Gera gráficos e visualizações dos dados.

#### **Payload:**
```json
{
  "file_id": "csv_1728054930_creditcard",
  "chart_type": "histogram",
  "columns": ["Amount"],
  "options": {
    "bins": 50,
    "title": "Distribuição de Valores"
  }
}
```

#### **Python:**
```python
import requests
import base64
from PIL import Image
import io

payload = {
    "file_id": "csv_1728054930_creditcard",
    "chart_type": "correlation_heatmap",
    "columns": ["Amount", "V1", "V2", "V3"],
    "options": {
        "figsize": [10, 8],
        "title": "Matriz de Correlação"
    }
}

response = requests.post("http://localhost:8000/csv/visualize", json=payload)
result = response.json()

# Salvar gráfico
if result['success']:
    # Decodificar imagem base64
    image_data = base64.b64decode(result['image_base64'])
    image = Image.open(io.BytesIO(image_data))
    image.save("grafico_correlacao.png")
    print("Gráfico salvo como grafico_correlacao.png")
```

#### **Resposta:**
```json
{
  "success": true,
  "chart_type": "histogram",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "description": "Histograma da coluna Amount com 50 bins",
  "file_id": "csv_1728054930_creditcard",
  "generation_time": 1.2
}
```

---

## 9. Métricas Dashboard

### **GET** `/dashboard/metrics`
Métricas gerais do sistema.

#### **cURL:**
```bash
curl http://localhost:8000/dashboard/metrics
```

#### **Python:**
```python
import requests

response = requests.get("http://localhost:8000/dashboard/metrics")
metrics = response.json()

print("📊 Dashboard - EDA AI Minds")
print(f"Total de arquivos: {metrics['total_files']}")
print(f"Total de linhas: {metrics['total_rows']:,}")
print(f"Total de colunas: {metrics['total_columns']}")
print(f"Status: {metrics['status']}")
```

#### **Resposta:**
```json
{
  "total_files": 3,
  "total_rows": 2200,
  "total_columns": 67,
  "total_embeddings": 1500,
  "storage_used_mb": 45.2,
  "status": "operational",
  "last_activity": "2025-10-04T15:40:12",
  "agents_status": {
    "orchestrator": "active",
    "csv_agent": "active",
    "rag_agent": "active",
    "embeddings_agent": "active"
  }
}
```

---

## 10. Gestão de Sessões

### **GET** `/sessions`
Lista todas as sessões de chat.

### **GET** `/sessions/{session_id}`
Detalhes de uma sessão específica.

### **DELETE** `/sessions/{session_id}`
Remove uma sessão.

#### **Python:**
```python
import requests

# Listar sessões
response = requests.get("http://localhost:8000/sessions")
sessions = response.json()

print("Sessões ativas:")
for session in sessions['sessions']:
    print(f"- {session['session_id']}: {session['message_count']} mensagens")

# Detalhes de uma sessão
session_id = "session_001"
response = requests.get(f"http://localhost:8000/sessions/{session_id}")
details = response.json()

print(f"\nHistórico da sessão {session_id}:")
for msg in details['messages']:
    print(f"{msg['timestamp']}: {msg['content'][:50]}...")
```

---

## 11. Gestão de Memória

### **GET** `/memory/stats`
Estatísticas da memória do sistema.

### **POST** `/memory/clear`
Limpa cache e memória.

#### **Python:**
```python
import requests

# Ver estatísticas de memória
response = requests.get("http://localhost:8000/memory/stats")
memory = response.json()

print(f"Cache hits: {memory['cache_hits']}")
print(f"Memória usada: {memory['memory_used_mb']} MB")

# Limpar cache se necessário
if memory['memory_used_mb'] > 100:
    response = requests.post("http://localhost:8000/memory/clear")
    result = response.json()
    print(f"Cache limpo: {result['message']}")
```

---

## 12. Configurações Sistema

### **GET** `/config`
Configurações atuais do sistema.

### **POST** `/config`
Atualizar configurações.

#### **Python:**
```python
import requests

# Ver configurações atuais
response = requests.get("http://localhost:8000/config")
config = response.json()

print("Configurações atuais:")
print(f"Modelo LLM: {config['llm_model']}")
print(f"Temperatura: {config['temperature']}")

# Atualizar configurações
new_config = {
    "temperature": 0.3,
    "max_tokens": 1000,
    "enable_memory": True
}

response = requests.post("http://localhost:8000/config", json=new_config)
result = response.json()
print(f"Configurações atualizadas: {result['message']}")
```

---

## 🔧 Exemplos Práticos de Uso

### **1. Fluxo Completo de Análise**
```python
import requests
import json

# 1. Verificar se API está online
health = requests.get("http://localhost:8000/health").json()
print(f"API Status: {health['status']}")

# 2. Upload de arquivo CSV
with open("data/creditcard_test_500.csv", "rb") as file:
    files = {"file": file}
    upload_result = requests.post("http://localhost:8000/csv/upload", files=files).json()
    file_id = upload_result['file_id']
    print(f"Arquivo enviado: {upload_result['filename']}")

# 3. Análise estatística
stats_payload = {"file_id": file_id, "include_distributions": True}
stats = requests.post("http://localhost:8000/csv/stats", json=stats_payload).json()
print(f"Média Amount: {stats['descriptive']['Amount']['mean']}")

# 4. Chat com IA sobre os dados
chat_payload = {
    "message": f"Analise o arquivo {upload_result['filename']} e identifique padrões de fraude",
    "session_id": "analise_001"
}
chat_response = requests.post("http://localhost:8000/chat", json=chat_payload).json()
print(f"IA: {chat_response['response']}")

# 5. Gerar visualização
viz_payload = {
    "file_id": file_id,
    "chart_type": "histogram",
    "columns": ["Amount"],
    "options": {"bins": 30, "title": "Distribuição de Valores"}
}
visualization = requests.post("http://localhost:8000/csv/visualize", json=viz_payload).json()
print(f"Gráfico gerado: {visualization['success']}")
```

### **2. Análise Interativa com Memória**
```python
import requests

session_id = "analise_interativa_001"

# Sequência de perguntas mantendo contexto
perguntas = [
    "Carregue e analise o arquivo de fraudes",
    "Quais são as principais características das transações fraudulentas?",
    "Gere um gráfico mostrando a distribuição de valores por classe",
    "Baseado na análise, quais recomendações você daria?"
]

for i, pergunta in enumerate(perguntas, 1):
    payload = {
        "message": pergunta,
        "session_id": session_id,
        "use_memory": True
    }
    
    response = requests.post("http://localhost:8000/chat", json=payload).json()
    print(f"\n{i}. Pergunta: {pergunta}")
    print(f"   Resposta: {response['response'][:200]}...")
```

### **3. Busca Semântica e RAG**
```python
import requests

# Upload e processamento para RAG
with open("data/creditcard_test_500.csv", "rb") as file:
    files = {"file": file}
    upload_result = requests.post("http://localhost:8000/csv/upload", files=files).json()

# Busca semântica
search_payload = {
    "query": "transações suspeitas acima de 1000 dólares",
    "limit": 5,
    "similarity_threshold": 0.7
}

search_results = requests.post("http://localhost:8000/search/semantic", json=search_payload).json()

print(f"Encontrados {len(search_results['matches'])} resultados relevantes:")
for match in search_results['matches']:
    print(f"- Similaridade: {match['similarity']:.3f}")
    print(f"  Conteúdo: {match['content'][:100]}...")
```

---

## 🚨 Tratamento de Erros

### **Códigos de Status HTTP**
- `200` - Sucesso
- `400` - Erro na requisição (dados inválidos)
- `404` - Recurso não encontrado
- `422` - Erro de validação
- `500` - Erro interno do servidor

### **Exemplo de Tratamento**
```python
import requests

try:
    response = requests.post("http://localhost:8000/chat", json={"message": "teste"})
    response.raise_for_status()  # Levanta exceção para códigos 4xx/5xx
    
    result = response.json()
    print(result['response'])
    
except requests.exceptions.HTTPError as e:
    print(f"Erro HTTP: {e}")
    print(f"Detalhes: {response.json()}")
    
except requests.exceptions.ConnectionError:
    print("Erro: Não foi possível conectar à API. Verifique se está rodando.")
    
except Exception as e:
    print(f"Erro inesperado: {e}")
```

---

## 🔗 Links Úteis

- **API Base**: http://localhost:8000
- **Documentação Interativa**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📝 Notas Importantes

1. **Arquivos CSV**: Máximo 100MB por arquivo
2. **Sessões**: Expiram após 24h de inatividade
3. **Rate Limiting**: 100 requisições por minuto
4. **Formatos Suportados**: CSV, JSON (para payloads)
5. **Encoding**: UTF-8 preferível para arquivos CSV

---

## 🎯 Próximos Passos

Agora que você conhece todos os endpoints, experimente:

1. **Teste cada endpoint** individualmente
2. **Combine múltiplos endpoints** para análises complexas
3. **Use o sistema de memória** para conversas contextuais
4. **Explore a busca semântica** para insights avançados
5. **Integre com seu frontend** usando os exemplos JavaScript

**Happy Coding! 🚀**