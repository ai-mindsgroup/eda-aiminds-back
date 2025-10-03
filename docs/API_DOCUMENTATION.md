# 🚀 API REST - EDA AI Minds Backend

## **Sistema Multiagente para Análise de Dados CSV**

API REST completa para análise inteligente de dados CSV usando LLMs, RAG e sistema multiagente.

---

## 📋 **Visão Geral**

Esta API oferece endpoints para:

- **📁 Upload e análise de CSV** - Carregamento automático com validação
- **🔍 Detecção de fraudes** - Análise especializada com LLMs
- **🤖 Sistema RAG** - Busca semântica e chat inteligente  
- **📊 Análises avançadas** - Correlação, clustering, séries temporais
- **🔐 Autenticação** - Sistema de API keys para segurança
- **📈 Monitoramento** - Health checks e métricas do sistema

---

## 🛠️ **Instalação e Configuração**

### 1. Dependências

```bash
# Instalar dependências da API
pip install fastapi uvicorn python-multipart slowapi python-jose psutil httpx

# Ou instalar todas as dependências
pip install -r requirements.txt
```

### 2. Configuração

Certifique-se de ter o arquivo `configs/.env` configurado:

```env
# Configurações obrigatórias
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_supabase
GOOGLE_API_KEY=sua_chave_google_ai
LOG_LEVEL=INFO

# Configurações opcionais
GROK_API_KEY=sua_chave_grok
GROQ_API_KEY=sua_chave_groq
```

### 3. Executar Servidor

```bash
# Desenvolvimento (com reload automático)
python -m src.api.main

# Ou usando uvicorn diretamente
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Produção
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📚 **Documentação Automática**

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🔗 **Endpoints Principais**

### **Health Check**
```
GET /health/        # Verificação completa
GET /health/live    # Liveness probe
GET /health/ready   # Readiness probe
GET /health/metrics # Métricas básicas
```

### **Upload e Análise CSV**
```
POST /csv/upload           # Upload de arquivo CSV
POST /csv/analyze          # Análise geral de dados
POST /csv/fraud-detection  # Detecção especializada de fraudes
GET  /csv/files           # Listar arquivos carregados
DELETE /csv/files/{id}    # Remover arquivo
```

### **Sistema RAG e Chat**
```
POST /rag/search              # Busca semântica
POST /rag/chat                # Chat inteligente
GET  /rag/chat/{id}/history   # Histórico do chat
DELETE /rag/chat/{id}         # Limpar sessão
GET  /rag/documents           # Listar documentos
GET  /rag/sessions            # Sessões ativas
```

### **Análises Avançadas**
```
POST /analysis/correlation       # Análise de correlação
POST /analysis/clustering        # Clustering de dados
POST /analysis/time-series       # Séries temporais
POST /analysis/anomaly-detection # Detecção de anomalias
GET  /analysis/stats            # Estatísticas do sistema
GET  /analysis/history          # Histórico de análises
```

### **Autenticação**
```
POST /auth/api-key        # Criar API key
GET  /auth/api-keys       # Listar chaves
DELETE /auth/api-key/{id} # Revogar chave
GET  /auth/validate       # Validar autenticação
```

---

## 💡 **Exemplos de Uso**

### 1. Upload de CSV

```python
import requests

# Upload de arquivo
with open("dados.csv", "rb") as f:
    files = {"file": ("dados.csv", f, "text/csv")}
    data = {
        "delimiter": ",",
        "encoding": "utf-8", 
        "has_header": True,
        "preview_rows": 5
    }
    
    response = requests.post(
        "http://localhost:8000/csv/upload",
        files=files,
        data=data
    )

file_id = response.json()["file_id"]
print(f"Arquivo carregado: {file_id}")
```

### 2. Análise de Dados

```python
# Análise estatística
payload = {
    "file_id": file_id,
    "analysis_type": "statistical",
    "include_visualizations": True
}

response = requests.post(
    "http://localhost:8000/csv/analyze",
    json=payload
)

result = response.json()
print(f"Insights: {result['result']['insights']}")
```

### 3. Detecção de Fraudes

```python
# Detecção de fraudes
payload = {
    "file_id": file_id,
    "amount_column": "amount",
    "user_column": "user_id",
    "threshold": 0.8
}

response = requests.post(
    "http://localhost:8000/csv/fraud-detection",
    json=payload
)

fraud_result = response.json()
print(f"Fraudes detectadas: {fraud_result['result']['fraud_count']}")
```

### 4. Chat Inteligente

```python
# Chat com contexto
payload = {
    "message": "Como interpretar os resultados da análise de fraudes?",
    "session_id": "minha_sessao",
    "include_memory": True,
    "temperature": 0.7
}

response = requests.post(
    "http://localhost:8000/rag/chat",
    json=payload
)

chat_response = response.json()
print(f"Resposta: {chat_response['message']}")
```

### 5. Busca Semântica

```python
# Busca no banco vetorial
payload = {
    "query": "padrões de fraude em cartão de crédito",
    "query_type": "semantic_search",
    "max_results": 5,
    "similarity_threshold": 0.8
}

response = requests.post(
    "http://localhost:8000/rag/search",
    json=payload
)

search_result = response.json()
print(f"Resposta: {search_result['answer']}")
print(f"Fontes: {len(search_result['sources'])}")
```

---

## 🔐 **Autenticação**

### Criar API Key

```python
# Criar chave de API
payload = {
    "name": "Minha Aplicação",
    "permissions": ["read", "write"],
    "expires_at": "2024-12-31T23:59:59"  # Opcional
}

response = requests.post(
    "http://localhost:8000/auth/api-key",
    json=payload
)

api_key = response.json()["api_key"]
```

### Usar API Key

```python
# Usar chave em requisições
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(
    "http://localhost:8000/csv/files",
    headers=headers
)
```

---

## 📊 **Monitoramento e Métricas**

### Health Check Completo

```python
response = requests.get("http://localhost:8000/health/")
health = response.json()

print(f"Status: {health['status']}")
print(f"Uptime: {health['uptime_seconds']}s")
print(f"Banco: {health['database']['healthy']}")
print(f"LLMs: {health['llm_services']['google']['healthy']}")
```

### Estatísticas do Sistema

```python
response = requests.get("http://localhost:8000/analysis/stats")
stats = response.json()

print(f"Arquivos processados: {stats['total_files_processed']}")
print(f"Análises realizadas: {stats['total_analyses_performed']}")
print(f"Embeddings armazenados: {stats['vectorstore_embeddings']}")
```

---

## 🧪 **Testes**

### Teste Automático

```bash
# Executar testador completo
python test_api.py

# Testar URL específica
python test_api.py --url http://meu-servidor:8000
```

### Teste Manual com cURL

```bash
# Health check
curl http://localhost:8000/health/live

# Upload de CSV
curl -X POST \
  -F "file=@dados.csv" \
  -F "delimiter=," \
  -F "has_header=true" \
  http://localhost:8000/csv/upload

# Chat
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"Olá!","session_id":"test"}' \
  http://localhost:8000/rag/chat
```

---

## 🏗️ **Arquitetura da API**

```
FastAPI Application
├── Main App (src/api/main.py)
│   ├── Middleware (CORS, Logging, Error Handling)
│   ├── Exception Handlers
│   └── Lifespan Management
│
├── Routes (src/api/routes/)
│   ├── health.py     # Health checks
│   ├── csv.py        # Upload e análise CSV
│   ├── rag.py        # Sistema RAG e chat
│   ├── analysis.py   # Análises avançadas
│   └── auth.py       # Autenticação
│
├── Schemas (src/api/schemas.py)
│   ├── Request Models (Pydantic)
│   ├── Response Models
│   └── Validation Rules
│
└── Integration
    ├── OrchestratorAgent  # Coordenação multiagente
    ├── Supabase Client    # Banco vetorial
    └── LLM Services       # Google, Grok, Groq
```

---

## 🚀 **Deploy em Produção**

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./configs/.env:/app/configs/.env
```

### Nginx (Proxy Reverso)

```nginx
server {
    listen 80;
    server_name api.meudominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 🔍 **Troubleshooting**

### Problemas Comuns

1. **Erro 500 na inicialização**
   ```bash
   # Verificar configurações
   python check_db.py
   
   # Verificar logs
   LOG_LEVEL=DEBUG python -m src.api.main
   ```

2. **Upload falha**
   ```python
   # Verificar formato do arquivo
   # Arquivo deve ser CSV válido
   # Máximo 100MB
   ```

3. **LLM não responde**
   ```bash
   # Verificar API keys
   python examples/diagnostico_grok_key.py
   ```

### Logs Estruturados

```python
# Ver logs detalhados
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs são salvos com contexto estruturado
# Incluem: timestamp, nível, módulo, mensagem, metadados
```

---

## 📞 **Suporte**

- **Documentação**: `/docs` (Swagger UI)
- **Repositório**: https://github.com/ai-mindsgroup/eda-aiminds-back
- **Issues**: Use o GitHub Issues para reportar problemas
- **Logs**: Consulte os logs estruturados para debug

---

**🎯 API desenvolvida seguindo as melhores práticas de REST, OpenAPI, e arquitetura multiagente.**