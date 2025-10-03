# 🚀 Guia de Início Rápido - API REST

## Visão Geral

API REST desenvolvida com **FastAPI** para o sistema multiagente **EDA AI Minds**. Oferece endpoints para análise de dados CSV, busca semântica, detecção de fraudes e interação via chat com IA.

## 📋 Pré-requisitos

- **Python 3.10+**
- **Ambiente virtual** (recomendado)
- **Configuração do Supabase** (opcional para funcionalidades completas)

## ⚡ Instalação Rápida

### 1. Clonar e Configurar Ambiente

```powershell
# Navegar para o diretório do projeto
cd eda-aiminds-back-1

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements-api.txt  # Mínimo para API
# OU
pip install -r requirements.txt      # Sistema completo
```

### 2. Configuração (Opcional)

```powershell
# Copiar arquivo de configuração
copy configs\.env.example configs\.env

# Editar configs\.env com suas credenciais:
# SUPABASE_URL=your_project_url
# SUPABASE_KEY=your_anon_key
# OPENAI_API_KEY=your_openai_key
```

### 3. Verificar Instalação

```powershell
# Verificação rápida
python check_api_quick.py

# Verificação completa (requer configuração)
python check_api_dependencies.py
```

### 4. Iniciar API

```powershell
# Método 1: Script automático
python start_api.py

# Método 2: Uvicorn direto
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 Acessar Documentação

Após iniciar a API:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🧪 Testar API

```powershell
# Teste automatizado
python test_api.py

# Teste manual
curl http://localhost:8000/health
```

## 📊 Principais Endpoints

### Saúde e Informações
- `GET /health` - Status da API
- `GET /` - Informações da API

### Upload e Análise de CSV
- `POST /csv/upload` - Upload de arquivo CSV
- `GET /csv/analyze/{file_id}` - Análise de CSV específico
- `GET /csv/list` - Listar CSVs carregados

### Busca Semântica (RAG)
- `POST /rag/search` - Busca semântica nos dados
- `POST /rag/ask` - Pergunta com contexto

### Análise Inteligente
- `POST /analysis/detect-fraud` - Detecção de fraudes
- `POST /analysis/generate-insights` - Insights automáticos
- `POST /analysis/compare-datasets` - Comparação de dados

### Chat com IA
- `POST /chat` - Conversa com agente IA
- `GET /chat/history/{session_id}` - Histórico de conversa

### Autenticação (Futuro)
- `POST /auth/login` - Login de usuário
- `POST /auth/register` - Registro de usuário

## 🛠️ Configuração Avançada

### Produção com Gunicorn

```powershell
# Instalar gunicorn
pip install gunicorn

# Executar em produção
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Futuro)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Variáveis de Ambiente

```env
# Configuração da API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# Banco de dados
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Modelos de IA
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🐛 Solução de Problemas

### Erro: Dependências Ausentes
```powershell
pip install -r requirements.txt
python check_api_quick.py
```

### Erro: Configuração Supabase
```powershell
# Verificar arquivo .env
type configs\.env

# Testar conexão
python check_db.py
```

### Erro: Porta em Uso
```powershell
# Usar porta diferente
python start_api.py --port 8001

# Ou matar processo
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Performance Lenta
```powershell
# Usar reload apenas em desenvolvimento
uvicorn src.api.main:app --no-reload

# Aumentar workers em produção
gunicorn src.api.main:app -w 4
```

## 📈 Monitoramento

### Health Checks
- `GET /health/live` - Verificação básica
- `GET /health/ready` - Verificação com dependências
- `GET /health/metrics` - Métricas do sistema

### Logs
```powershell
# Ver logs em tempo real
tail -f logs/api.log

# Logs estruturados
python -c "from src.utils.logging_config import get_logger; get_logger('api').info('Test')"
```

## 🔧 Desenvolvimento

### Estrutura da API

```
src/api/
├── main.py              # Aplicação FastAPI principal
├── schemas.py           # Modelos Pydantic
├── dependencies.py      # Dependências injetáveis
└── routes/
    ├── __init__.py      # Configuração de rotas
    ├── health.py        # Endpoints de saúde
    ├── csv.py           # Upload e análise de CSV
    ├── rag.py           # Busca semântica
    ├── analysis.py      # Análise inteligente
    ├── auth.py          # Autenticação
    └── chat.py          # Chat com IA
```

### Adicionar Novo Endpoint

```python
# src/api/routes/my_route.py
from fastapi import APIRouter
from src.api.schemas import MyRequest, MyResponse

router = APIRouter(prefix="/my", tags=["my-feature"])

@router.post("/endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    # Sua lógica aqui
    return MyResponse(result="success")
```

### Testes Automatizados

```powershell
# Executar todos os testes
pytest tests/test_api.py -v

# Teste específico
pytest tests/test_api.py::test_health_endpoint -v

# Com coverage
pytest --cov=src.api tests/ --cov-report=html
```

## 📚 Recursos Adicionais

- **Documentação FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Uvicorn Docs**: https://www.uvicorn.org/
- **Repositório EDA AI Minds**: [Link do repositório]

---

**Desenvolvido com ❤️ pela equipe EDA AI Minds**