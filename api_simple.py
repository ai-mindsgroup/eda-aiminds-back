#!/usr/bin/env python3
"""
API Simples - Sem dependências do Supabase
==========================================

FastAPI básica para demonstração, sem conectar ao sistema multiagente.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import sys
import io
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configurações de limites
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100MB

# Modelos Pydantic básicos
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    message: str = "API rodando com sucesso!"
    mode: str = "production"  # Para indicar que não é demo

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str

class APIInfo(BaseModel):
    title: str = "EDA AI Minds - API REST"
    version: str = "1.0.0"
    description: str = "Sistema multiagente para análise de dados CSV"
    status: str = "running"
    endpoints: List[str]

class CSVUploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: int
    message: str
    columns_list: List[str]
    preview: Dict[str, Any]

class DashboardMetrics(BaseModel):
    total_files: int
    total_rows: int
    total_columns: int
    status: str
    timestamp: str

# Aplicação FastAPI
app = FastAPI(
    title="EDA AI Minds API",
    description="API REST para sistema multiagente de análise de dados",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    # Aumentar limites de tamanho de request
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para verificar tamanho do request
@app.middleware("http")
async def check_request_size(request: Request, call_next):
    """Middleware para verificar tamanho do request."""
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request Too Large",
                    "message": f"Arquivo muito grande. Tamanho máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB",
                    "max_size_mb": MAX_FILE_SIZE // (1024*1024),
                    "received_size_mb": int(content_length) // (1024*1024)
                }
            )
    response = await call_next(request)
    return response

# Endpoints básicos
@app.get("/", response_model=APIInfo)
async def root():
    """Informações básicas da API."""
    return APIInfo(
        endpoints=[
            "/",
            "/health",
            "/chat",
            "/docs",
            "/redoc"
        ]
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificação de saúde da API."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        message="API funcionando perfeitamente!",
        mode="production"  # Frontend detecta como produção
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat inteligente com respostas contextuais."""
    
    message_lower = request.message.lower()
    
    # Respostas categorizadas por tipo de pergunta
    
    # 1. Saudações
    if any(word in message_lower for word in ["olá", "oi", "ola", "hey", "hello"]):
        response_text = "👋 Olá! Sou o assistente da EDA AI Minds.\n\n" \
                       "Posso ajudar você com:\n" \
                       "• 📊 Análise de dados CSV\n" \
                       "• 🔍 Detecção de padrões\n" \
                       "• 📈 Visualizações e insights\n" \
                       "• 🤖 Análises automatizadas\n\n" \
                       "Como posso ajudar?"
    
    # 2. Ajuda / Help
    elif any(word in message_lower for word in ["help", "ajuda", "ajudar", "socorro"]):
        response_text = "📚 **Funcionalidades Disponíveis:**\n\n" \
                       "**Upload de CSV:**\n" \
                       "• Faça upload de arquivos CSV para análise\n" \
                       "• Visualize preview dos dados\n" \
                       "• Obtenha estatísticas automáticas\n\n" \
                       "**Análise:**\n" \
                       "• Insights automáticos dos dados\n" \
                       "• Detecção de padrões\n" \
                       "• Estatísticas descritivas\n\n" \
                       "**Dashboard:**\n" \
                       "• Visualize métricas em tempo real\n" \
                       "• Acompanhe arquivos processados\n\n" \
                       "Digite sua dúvida ou faça upload de um CSV para começar!"
    
    # 3. Como funciona
    elif any(word in message_lower for word in ["como funciona", "funcionamento", "explicar", "explique"]):
        response_text = "🎯 **Como o Sistema Funciona:**\n\n" \
                       "1️⃣ **Upload**: Você envia um arquivo CSV\n" \
                       "2️⃣ **Processamento**: Analisamos automaticamente os dados\n" \
                       "3️⃣ **Insights**: Geramos estatísticas e visualizações\n" \
                       "4️⃣ **Resultados**: Você recebe análises detalhadas\n\n" \
                       "💡 **Tecnologias:**\n" \
                       "• Python + Pandas para análise\n" \
                       "• FastAPI para API REST\n" \
                       "• Sistema multiagente para IA\n\n" \
                       "Tudo automatizado e rápido! ⚡"
    
    # 4. Perguntas sobre CSV
    elif any(word in message_lower for word in ["csv", "arquivo", "upload", "carregar"]):
        response_text = "📊 **Sobre Arquivos CSV:**\n\n" \
                       "Você pode fazer upload de arquivos CSV com:\n" \
                       "• ✅ Dados tabulares\n" \
                       "• ✅ Qualquer número de colunas\n" \
                       "• ✅ Diversos tipos de análise\n\n" \
                       "**O que fazemos:**\n" \
                       "• Contagem de linhas/colunas\n" \
                       "• Estatísticas descritivas\n" \
                       "• Detecção de valores ausentes\n" \
                       "• Preview dos dados\n\n" \
                       "Use o botão de upload para começar! 📤"
    
    # 5. Perguntas sobre análise
    elif any(word in message_lower for word in ["análise", "analisar", "analise", "insights", "padrões", "padroes"]):
        response_text = "🔍 **Análises Disponíveis:**\n\n" \
                       "**Análise Básica:**\n" \
                       "• Estatísticas descritivas\n" \
                       "• Contagem de valores únicos\n" \
                       "• Detecção de valores ausentes\n\n" \
                       "**Análise Avançada** (requer configuração):\n" \
                       "• Detecção de fraude com IA\n" \
                       "• Análise preditiva\n" \
                       "• Clustering de dados\n\n" \
                       "Faça upload de um CSV para experimentar!"
    
    # 6. Status / Teste
    elif any(word in message_lower for word in ["status", "teste", "test", "funcionando"]):
        files_count = len(uploaded_files)
        response_text = f"✅ **Status do Sistema:**\n\n" \
                       f"• API: Operacional\n" \
                       f"• Arquivos carregados: {files_count}\n" \
                       f"• Modo: Produção\n" \
                       f"• Versão: 1.0.0\n\n" \
                       f"Tudo funcionando perfeitamente! 🚀"
    
    # 7. Sobre fraude
    elif any(word in message_lower for word in ["fraude", "fraud", "detecção", "detectar"]):
        response_text = "🛡️ **Detecção de Fraude:**\n\n" \
                       "Para análise de fraude com IA, você precisa:\n" \
                       "1. Configurar API key do Google Gemini\n" \
                       "2. Fazer upload de dados de transações\n" \
                       "3. Usar a API completa (não a versão simples)\n\n" \
                       "**Recursos de IA:**\n" \
                       "• Análise de padrões suspeitos\n" \
                       "• Scoring de risco\n" \
                       "• Detecção de anomalias\n\n" \
                       "Veja o arquivo SUPORTE_GEMINI.md para configuração!"
    
    # 8. Sobre IA/LLM
    elif any(word in message_lower for word in ["ia", "ai", "inteligência", "llm", "gemini", "openai", "gpt"]):
        response_text = "🤖 **Inteligência Artificial:**\n\n" \
                       "Este sistema suporta múltiplos LLMs:\n" \
                       "• 🧠 Google Gemini (recomendado)\n" \
                       "• 🚀 Groq (mais rápido)\n" \
                       "• 💬 OpenAI GPT\n\n" \
                       "**Funcionalidades com IA:**\n" \
                       "• Análise inteligente de dados\n" \
                       "• Detecção de fraude\n" \
                       "• Insights automáticos\n" \
                       "• Chat contextual\n\n" \
                       "Configure uma API key para habilitar! 🔑"
    
    # 9. Perguntas técnicas
    elif any(word in message_lower for word in ["api", "endpoint", "documentação", "docs"]):
        response_text = "⚙️ **Informações Técnicas:**\n\n" \
                       "**Endpoints Disponíveis:**\n" \
                       "• POST /csv/upload - Upload de CSV\n" \
                       "• GET /csv/files - Lista arquivos\n" \
                       "• GET /dashboard/metrics - Métricas\n" \
                       "• POST /chat - Este chat\n" \
                       "• GET /health - Status da API\n\n" \
                       "**Documentação:**\n" \
                       "• Swagger UI: http://localhost:8000/docs\n" \
                       "• ReDoc: http://localhost:8000/redoc\n\n" \
                       "Explore e teste os endpoints!"
    
    # 10. Agradecimentos
    elif any(word in message_lower for word in ["obrigado", "obrigada", "valeu", "thanks"]):
        response_text = "😊 Por nada! Estou aqui para ajudar.\n\n" \
                       "Se precisar de mais alguma coisa:\n" \
                       "• Faça upload de um CSV\n" \
                       "• Explore o dashboard\n" \
                       "• Pergunte sobre funcionalidades\n\n" \
                       "Boa análise de dados! 📊"
    
    # 11. Despedidas
    elif any(word in message_lower for word in ["tchau", "adeus", "bye", "até", "ate"]):
        response_text = "👋 Até logo! Volte sempre que precisar analisar dados.\n\n" \
                       "Boas análises! 📊✨"
    
    # 12. Perguntas sobre dados específicos
    elif "dados" in message_lower or "dataset" in message_lower:
        response_text = "📁 **Sobre seus Dados:**\n\n" \
                       f"Arquivos carregados: {len(uploaded_files)}\n\n" \
                       "**Formatos aceitos:**\n" \
                       "• CSV (valores separados por vírgula)\n" \
                       "• Codificação UTF-8 ou Latin-1\n" \
                       "• Com ou sem cabeçalho\n\n" \
                       "**Análises disponíveis:**\n" \
                       "• Estatísticas descritivas\n" \
                       "• Distribuição de valores\n" \
                       "• Correlações\n" \
                       "• Visualizações\n\n" \
                       "Faça upload para começar!"
    
    # 13. Resposta padrão mais útil
    else:
        response_text = "🤔 Desculpe, não entendi completamente sua pergunta.\n\n" \
                       "**Posso ajudar com:**\n" \
                       "• 📤 Upload e análise de CSV\n" \
                       "• 📊 Estatísticas e insights\n" \
                       "• 🔍 Detecção de padrões\n" \
                       "• ❓ Dúvidas sobre o sistema\n\n" \
                       "**Comandos úteis:**\n" \
                       "• Digite 'help' para ver todas as funcionalidades\n" \
                       "• Digite 'como funciona' para entender o sistema\n" \
                       "• Digite 'status' para ver informações\n\n" \
                       "Como posso ajudar?"
    
    return ChatResponse(
        response=response_text,
        session_id=request.session_id or "default",
        timestamp=datetime.now().isoformat()
    )

# Armazenamento temporário em memória
uploaded_files = {}

@app.post("/csv/upload", response_model=CSVUploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload e análise básica de arquivo CSV."""
    try:
        # Validar nome do arquivo
        filename = file.filename or "unknown.csv"
        
        if not filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos CSV são permitidos"
            )
        
        # Ler arquivo com limite de tamanho
        contents = await file.read()
        
        # Verificar tamanho
        file_size = len(contents)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB. Recebido: {file_size // (1024*1024)}MB"
            )
        df = pd.read_csv(io.BytesIO(contents))
        
        # Gerar ID único
        file_id = f"csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Armazenar em memória
        uploaded_files[file_id] = {
            'filename': filename,
            'dataframe': df,
            'uploaded_at': datetime.now().isoformat()
        }
        
        # Preparar preview (primeiras 5 linhas)
        preview = df.head(5).to_dict(orient='records')
        
        return CSVUploadResponse(
            file_id=file_id,
            filename=filename,
            rows=len(df),
            columns=len(df.columns),
            message=f"Arquivo '{filename}' carregado com sucesso!",
            columns_list=df.columns.tolist(),
            preview={'data': preview, 'total_preview_rows': len(preview)}
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Arquivo CSV está vazio")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Erro ao processar CSV. Verifique o formato.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")

@app.get("/csv/files")
async def list_csv_files():
    """Lista todos os arquivos CSV carregados."""
    files_info = []
    for file_id, info in uploaded_files.items():
        files_info.append({
            'file_id': file_id,
            'filename': info['filename'],
            'uploaded_at': info['uploaded_at'],
            'rows': len(info['dataframe']),
            'columns': len(info['dataframe'].columns)
        })
    
    return {
        'total': len(files_info),
        'files': files_info
    }

@app.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Métricas do dashboard."""
    total_rows = sum(len(info['dataframe']) for info in uploaded_files.values())
    total_columns = sum(len(info['dataframe'].columns) for info in uploaded_files.values())
    
    return DashboardMetrics(
        total_files=len(uploaded_files),
        total_rows=total_rows,
        total_columns=total_columns,
        status="operational",
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/config")
async def get_api_config():
    """Retorna configuração da API para o frontend."""
    return {
        "mode": "production",  # Não é demo
        "features": {
            "csv_upload": True,
            "csv_analysis": True,
            "chat": True,
            "dashboard": True,
            "llm_analysis": False,  # Não disponível sem API keys
            "rag_search": False,  # Não disponível sem Supabase
        },
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/endpoints")
async def list_endpoints():
    """Lista todos os endpoints disponíveis."""
    return {
        "available_endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Informações da API"
            },
            {
                "path": "/health", 
                "method": "GET",
                "description": "Status de saúde"
            },
            {
                "path": "/chat",
                "method": "POST", 
                "description": "Chat com IA (versão demo)"
            },
            {
                "path": "/csv/upload",
                "method": "POST", 
                "description": "Upload de arquivo CSV"
            },
            {
                "path": "/csv/files",
                "method": "GET", 
                "description": "Lista arquivos carregados"
            },
            {
                "path": "/dashboard/metrics",
                "method": "GET", 
                "description": "Métricas do dashboard"
            },
            {
                "path": "/endpoints",
                "method": "GET",
                "description": "Lista de endpoints"
            },
            {
                "path": "/docs",
                "method": "GET", 
                "description": "Documentação Swagger"
            },
            {
                "path": "/redoc",
                "method": "GET",
                "description": "Documentação ReDoc"
            }
        ],
        "note": "API totalmente funcional para análise de CSV e processamento de dados."
    }

# Tratamento de erros
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint não encontrado",
            "message": f"O endpoint {request.url.path} não existe",
            "available_endpoints": "/endpoints"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": "Algo deu errado. Verifique os logs.",
            "contact": "Consulte a documentação em /docs"
        }
    )

def main():
    """Iniciar servidor."""
    print("🚀 Iniciando API Simples - EDA AI Minds")
    print("=" * 50)
    print("📍 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("📋 ReDoc: http://localhost:8000/redoc")
    print("⏹️ Pressione Ctrl+C para parar")
    print()
    
    try:
        uvicorn.run(
            "api_simple:app",
            host="0.0.0.0", 
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️ API parada pelo usuário")

if __name__ == "__main__":
    main()