# 🚀 Como Iniciar a API COMPLETA com Orquestrador e LLMs

**Data**: 01 de Outubro de 2025  
**Objetivo**: Executar a API COMPLETA do sistema multiagente com todos os recursos

---

## 🎯 Diferença Entre as APIs

### ❌ `api_simple.py` (API Simplificada)
- **Propósito**: Desenvolvimento rápido do frontend
- **Recursos**: CSV upload, chat básico, métricas
- **Limitações**:
  - ❌ Sem orquestrador
  - ❌ Sem LLMs (Google Gemini, Groq, OpenAI)
  - ❌ Sem sistema RAG
  - ❌ Sem análise avançada
  - ❌ Sem busca semântica
  - ❌ Dados em memória (não persistente)

### ✅ `src/api/main.py` (API COMPLETA)
- **Propósito**: Sistema multiagente completo em produção
- **Recursos**: TODOS os recursos disponíveis
- **Componentes**:
  - ✅ **Orquestrador Central** (`OrchestratorAgent`)
  - ✅ **LLMs Múltiplos** (Google Gemini, Groq, OpenAI)
  - ✅ **Sistema RAG** com busca vetorial
  - ✅ **Análise CSV Avançada** com IA
  - ✅ **Supabase** para persistência
  - ✅ **Embeddings** e busca semântica
  - ✅ **Detecção de Fraudes**
  - ✅ **Chat Contextual** com memória

---

## 📋 Pré-requisitos

### 1. Ambiente Virtual Ativado

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Verificar Python
python --version  # Deve ser 3.10+
```

### 2. Dependências Instaladas

```powershell
# Instalar todas as dependências
pip install -r requirements.txt

# Verificar instalação
pip list | Select-String "fastapi|uvicorn|langchain|supabase|pandas"
```

### 3. Variáveis de Ambiente Configuradas

Edite `configs/.env` com suas credenciais:

```env
# Supabase (obrigatório)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_anon_key
DB_PASSWORD=sua_senha_db

# LLMs (pelo menos um obrigatório)
GOOGLE_API_KEY=sua_api_key_google        # Google Gemini (recomendado)
GROQ_API_KEY=sua_api_key_groq            # Groq (alternativa)
OPENAI_API_KEY=sua_api_key_openai        # OpenAI (alternativa)

# Configuração
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 4. Banco de Dados Migrado

```powershell
# Executar migrations
python scripts/run_migrations.py

# Verificar conexão
python check_db.py
```

---

## 🚀 Como Iniciar a API COMPLETA

### Opção 1: Usando Python Diretamente

```powershell
# Método 1: Executar como módulo
python -m src.api.main

# Método 2: Executar arquivo diretamente
python src/api/main.py

# Método 3: Usando uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Opção 2: Usando Script Automatizado

```powershell
# Usar script start_api.py (recomendado)
python start_api.py

# Ou executar diretamente
.\start_api_completa.ps1
```

---

## 📡 Endpoints Disponíveis (API Completa)

### Health & Info
```
GET  /              → Informações da API
GET  /health        → Status do sistema
GET  /health/ready  → Pronto para receber requests?
GET  /health/live   → Sistema está vivo?
```

### Autenticação
```
POST /auth/register → Registrar usuário
POST /auth/login    → Login
POST /auth/logout   → Logout
GET  /auth/me       → Dados do usuário logado
```

### CSV Upload & Análise
```
POST /csv/upload              → Upload CSV
GET  /csv/files               → Listar arquivos
GET  /csv/{file_id}           → Detalhes do arquivo
DELETE /csv/{file_id}         → Deletar arquivo
GET  /csv/{file_id}/preview   → Preview dos dados
GET  /csv/{file_id}/stats     → Estatísticas
```

### Análises Avançadas (com LLMs)
```
POST /analysis/fraud          → Detecção de fraudes
POST /analysis/insights       → Insights automáticos
POST /analysis/visualize      → Gráficos e visualizações
POST /analysis/chat           → Chat com contexto dos dados
POST /analysis/python-code    → Gerar código Python
```

### Sistema RAG (Busca Semântica)
```
POST /rag/query               → Consulta com RAG
POST /rag/embed               → Criar embeddings
GET  /rag/search              → Busca semântica
POST /rag/index               → Indexar documentos
```

### Documentação
```
GET /docs     → Swagger UI (interativo)
GET /redoc    → ReDoc (documentação)
GET /openapi.json → Schema OpenAPI
```

---

## 🧪 Testando a API Completa

### Teste 1: Verificar Sistema

```powershell
# Health check completo
Invoke-RestMethod http://localhost:8000/health

# Resposta esperada:
# {
#   "status": "healthy",
#   "mode": "production",
#   "components": {
#     "database": "connected",
#     "llm_manager": "ready",
#     "orchestrator": "ready",
#     "rag_system": "ready"
#   },
#   "timestamp": "2025-10-01T..."
# }
```

### Teste 2: Upload CSV com Análise IA

```powershell
# Upload arquivo
$filePath = "data\creditcard_test_500.csv"
$uri = "http://localhost:8000/csv/upload"

$form = @{
    file = Get-Item -Path $filePath
}

$response = Invoke-RestMethod -Uri $uri -Method POST -Form $form

# Resposta esperada: Análise completa com IA
# - Estatísticas detalhadas
# - Insights automáticos
# - Detecção de fraudes
# - Recomendações
```

### Teste 3: Chat com Contexto

```powershell
# Chat inteligente
$body = @{
    message = "Quantas fraudes foram detectadas?"
    context = @{
        file_id = "abc123"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/analysis/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Resposta: Análise usando LLM + dados do CSV
```

### Teste 4: Busca Semântica (RAG)

```powershell
# Busca semântica nos dados
$body = @{
    query = "transações suspeitas com valores altos"
    top_k = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/rag/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Resposta: Resultados semelhantes semanticamente
```

---

## 🔍 Verificar Componentes Ativos

### No Console (ao iniciar a API):

```
🚀 Iniciando Sistema Multiagente EDA AI Minds API
✅ Supabase URL: Configurado
✅ Supabase Key: Configurado
✅ Google API Key: Configurado
✅ Conexão com banco vetorial: OK
✅ LLM Manager: Inicializado (Google Gemini)
✅ Orquestrador: Pronto
✅ RAG System: Pronto
🎯 API pronta para receber requisições
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Logs Durante Uso:

```
📨 POST /csv/upload
🤖 [Orchestrator] Analisando query...
🎯 [Orchestrator] Agentes selecionados: CSVAnalysisAgent, RAGAgent
🧠 [Google LLM] Gerando insights...
✅ 200 POST /csv/upload - 2.345s
```

---

## 🆚 Comparação Rápida

| Recurso | api_simple.py | src/api/main.py |
|---------|---------------|-----------------|
| CSV Upload | ✅ | ✅ |
| Estatísticas Básicas | ✅ | ✅ |
| **Orquestrador** | ❌ | ✅ |
| **LLMs (Gemini/Groq)** | ❌ | ✅ |
| **Sistema RAG** | ❌ | ✅ |
| **Busca Semântica** | ❌ | ✅ |
| **Detecção de Fraudes IA** | ❌ | ✅ |
| **Chat Contextual** | ⚠️ Básico | ✅ Avançado |
| **Geração de Código** | ❌ | ✅ |
| **Insights Automáticos** | ❌ | ✅ |
| Persistência | ❌ Memória | ✅ Supabase |
| Autenticação | ❌ | ✅ |
| Documentação | ⚠️ Básica | ✅ Completa |

---

## 🐛 Troubleshooting

### Erro: "Supabase not configured"

```powershell
# Verificar .env
cat configs\.env | Select-String "SUPABASE"

# Deve conter:
# SUPABASE_URL=https://...
# SUPABASE_KEY=...
```

### Erro: "LLM Manager not available"

```powershell
# Verificar chaves de API
cat configs\.env | Select-String "API_KEY"

# Pelo menos uma deve estar configurada:
# GOOGLE_API_KEY=...
# GROQ_API_KEY=...
# OPENAI_API_KEY=...
```

### Erro: "Module not found"

```powershell
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall

# Verificar ambiente virtual ativo
python -c "import sys; print(sys.prefix)"
# Deve apontar para .venv
```

### API não inicia

```powershell
# Ver erros detalhados
python src/api/main.py

# Verificar logs
LOG_LEVEL=DEBUG python src/api/main.py
```

---

## 📚 Documentação Adicional

- **Arquitetura**: `docs/relatorio-final.md`
- **Orquestrador**: `docs/agente-orquestrador-documentacao.md`
- **LLMs**: `LLMs_SUPORTADOS.md`
- **Sistema RAG**: `docs/sistema-carregamento-dados.md`
- **API Reference**: `http://localhost:8000/docs` (quando rodando)

---

## ✅ Checklist de Validação

Use este checklist ao iniciar a API completa:

- [ ] Ambiente virtual ativado
- [ ] Dependências instaladas (`pip list`)
- [ ] Arquivo `.env` configurado
- [ ] Pelo menos 1 LLM API key configurada
- [ ] Supabase configurado
- [ ] Migrations executadas
- [ ] API iniciada sem erros
- [ ] Console mostra "✅ Orquestrador: Pronto"
- [ ] Console mostra "✅ LLM Manager: Inicializado"
- [ ] Console mostra "✅ RAG System: Pronto"
- [ ] Endpoint `/health` responde com componentes OK
- [ ] Documentação acessível em `/docs`
- [ ] Upload CSV funciona com análise IA
- [ ] Chat responde com contexto

---

## 🎯 Resumo

**Para desenvolvimento frontend simples**:
```powershell
uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload
```

**Para sistema completo com IA**:
```powershell
python start_api.py
# OU
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Diferença chave**:
- `api_simple.py`: Apenas backend básico para testar frontend
- `src/api/main.py`: Sistema multiagente completo com LLMs, RAG, análise avançada

**Escolha conforme sua necessidade**:
- ✅ Testando frontend? → `api_simple.py`
- ✅ Demo completa do sistema? → `src/api/main.py`
- ✅ Produção? → `src/api/main.py`

---

**Última atualização**: 01/10/2025  
**Autor**: GitHub Copilot + Time Backend
