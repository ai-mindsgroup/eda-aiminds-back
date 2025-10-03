"""
API REST do Sistema Multiagente EDA AI Minds
============================================

Sistema multiagente para análise exploratória de dados CSV com:
- Upload e análise automática de CSV
- Detecção de fraudes com LLMs
- Sistema RAG com busca semântica
- Chat inteligente com contexto

Tecnologias:
- FastAPI + Pydantic para API REST
- LangChain + LLMs para inteligência
- Supabase + pgvector para dados vetoriais
- Pandas + Matplotlib para análise de dados
"""

from __future__ import annotations

import os
import time
import traceback
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configurações de limites
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100MB

# Lazy loading para routes que dependem de ML
_routes_loaded = False
_available_routes = set()

def _load_routes_lazy(app: FastAPI):
    """Carrega routes lazily para evitar imports ML no startup."""
    global _routes_loaded, _available_routes
    
    if _routes_loaded:
        return
    
    logger.info("🔄 Carregando routes...")
    
    # Routes básicas sempre disponíveis
    try:
        from src.api.routes.health import router as health_router
        app.include_router(health_router, prefix="/health", tags=["Health"])
        _available_routes.add("health")
        logger.info("✅ Health router carregado")
    except Exception as e:
        logger.warning(f"⚠️ Health router falhou: {str(e)[:100]}")
    
    # CSV router (básico)
    try:
        from src.api.routes.csv import router as csv_router
        app.include_router(csv_router, prefix="/csv", tags=["CSV"])
        _available_routes.add("csv")
        logger.info("✅ CSV router carregado")
    except Exception as e:
        logger.warning(f"⚠️ CSV router falhou: {str(e)[:100]}")
    
    # Auth router (básico)
    try:
        from src.api.routes.auth import router as auth_router
        app.include_router(auth_router, prefix="/auth", tags=["Auth"])
        _available_routes.add("auth")
        logger.info("✅ Auth router carregado")
    except Exception as e:
        logger.warning(f"⚠️ Auth router falhou: {str(e)[:100]}")
    
    # Analysis router (pode depender de ML)
    try:
        from src.api.routes.analysis import router as analysis_router
        app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
        _available_routes.add("analysis")
        logger.info("✅ Analysis router carregado")
    except Exception as e:
        logger.warning(f"⚠️ Analysis router falhou (dependências ML): {str(e)[:100]}")
    
    # RAG router (depende de ML pesado)
    try:
        from src.api.routes.rag import router as rag_router
        app.include_router(rag_router, prefix="/rag", tags=["RAG"])
        _available_routes.add("rag")
        logger.info("✅ RAG router carregado")
    except Exception as e:
        logger.warning(f"⚠️ RAG router falhou (dependências ML): {str(e)[:100]}")
    
    _routes_loaded = True
    logger.info(f"📊 Routes carregadas: {', '.join(_available_routes)}")

from src.settings import LOG_LEVEL
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    logger.info("🚀 Iniciando Sistema Multiagente EDA AI Minds API")
    
    # Verificar configurações críticas
    try:
        from src.settings import SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY
        
        checks = {
            "Supabase URL": SUPABASE_URL,
            "Supabase Key": bool(SUPABASE_KEY),
            "Google API Key": bool(GOOGLE_API_KEY),
        }
        
        for check_name, check_value in checks.items():
            if check_value:
                logger.info(f"✅ {check_name}: Configurado")
            else:
                logger.warning(f"⚠️ {check_name}: Não configurado")
                
    except Exception as e:
        logger.error(f"❌ Erro verificando configurações: {e}")
    
    # Verificar conexão com banco vetorial
    try:
        from src.vectorstore.supabase_client import supabase
        
        # Teste simples de conexão
        result = supabase.table('embeddings').select('id').limit(1).execute()
        logger.info("✅ Conexão com banco vetorial: OK")
        
    except Exception as e:
        logger.warning(f"⚠️ Conexão com banco vetorial: {e}")
    
    logger.info("🎯 API pronta para receber requisições")
    
    yield  # Aplicação rodando
    
    # Shutdown
    logger.info("🛑 Finalizando Sistema Multiagente EDA AI Minds API")


# Criar aplicação FastAPI
app = FastAPI(
    title="EDA AI Minds - API Multiagente",
    description="""
Sistema multiagente para análise exploratória de dados CSV com:
- Upload e análise automática de CSV
- Detecção de fraudes com LLMs
- Sistema RAG com busca semântica
- Chat inteligente com contexto

Tecnologias:
- FastAPI + Pydantic para API REST
- LangChain + LLMs para inteligência
- Supabase + pgvector para dados vetoriais
- Pandas + Matplotlib para análise de dados
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "AI Minds Group",
        "url": "https://github.com/ai-mindsgroup/eda-aiminds-back",
        "email": "contato@aiminds.com.br",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS - Configuração para produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev
        "http://localhost:8080",  # Vue dev
        "http://localhost:4200",  # Angular dev
        "https://eda-aiminds.vercel.app",  # Frontend em produção (exemplo)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware para carregamento lazy de routes
@app.middleware("http")
async def lazy_load_routes(request: Request, call_next):
    """Carrega routes lazily na primeira requisição."""
    global _routes_loaded
    if not _routes_loaded:
        _load_routes_lazy(app)
    response = await call_next(request)
    return response


# Middleware para verificar tamanho do request
@app.middleware("http")
async def check_request_size(request: Request, call_next):
    """Middleware para verificar tamanho do request."""
    if request.method in ["POST", "PUT"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            logger.warning(
                f"🚫 Request muito grande: {int(content_length) // (1024*1024)}MB > {MAX_REQUEST_SIZE // (1024*1024)}MB",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "content_length": int(content_length),
                    "max_size": MAX_REQUEST_SIZE
                }
            )
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request Too Large",
                    "message": f"Arquivo muito grande. Tamanho máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB",
                    "max_size_mb": MAX_FILE_SIZE // (1024*1024),
                    "received_size_mb": int(content_length) // (1024*1024),
                    "detail": "Reduza o tamanho do arquivo ou divida em partes menores"
                }
            )
    response = await call_next(request)
    return response


# Middleware de logging e métricas
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log estruturado de todas as requisições."""
    start_time = time.time()
    
    # Log da requisição
    logger.info(
        f"📨 {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
    )
    
    # Processar requisição
    try:
        response = await call_next(request)
        
        # Calcular tempo de resposta
        process_time = time.time() - start_time
        
        # Log da resposta
        logger.info(
            f"✅ {response.status_code} {request.method} {request.url.path} - {process_time:.3f}s",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
                "method": request.method,
                "path": request.url.path,
            }
        )
        
        # Adicionar header de tempo de resposta
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        logger.error(
            f"❌ 500 {request.method} {request.url.path} - {process_time:.3f}s - {str(e)}",
            extra={
                "status_code": 500,
                "process_time": process_time,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        )
        
        # Retornar erro padronizado
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "Erro interno do servidor. Contate o suporte.",
                "request_id": f"{int(time.time())}-{request.client.host}" if request.client else "unknown",
                "timestamp": time.time(),
            }
        )


# ============================================================================
# HANDLERS DE ERRO
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para erros de validação Pydantic."""
    logger.warning(
        f"🔍 Erro de validação {request.method} {request.url.path}",
        extra={
            "validation_errors": exc.errors(),
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Dados da requisição inválidos",
            "details": exc.errors(),
            "timestamp": time.time(),
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPExceptions."""
    logger.warning(
        f"🚫 {exc.status_code} {request.method} {request.url.path} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para erros gerais não capturados."""
    logger.error(
        f"💥 Erro não tratado {request.method} {request.url.path} - {str(exc)}",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "method": request.method,
            "path": request.url.path,
            "traceback": traceback.format_exc(),
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Erro interno não tratado. Contate o suporte.",
            "error_type": type(exc).__name__,
            "timestamp": time.time(),
        }
    )


# ============================================================================
# ROTAS - Carregamento Lazy
# ============================================================================

# Routes são carregadas no primeiro acesso para evitar imports ML no startup


# ============================================================================
# ROTAS COMPATIBILIDADE COM FRONTEND
# ============================================================================

@app.post("/chat", tags=["Frontend Compatibility"])
async def chat_endpoint(request: dict):
    """
    Rota de compatibilidade para /chat (versão simplificada).
    
    Esta rota existe para manter compatibilidade com o frontend
    que está enviando requests para /chat ao invés de /rag/chat.
    
    Versão simplificada que não depende do sistema RAG completo.
    """
    try:
        # Validar entrada básica
        message = request.get("message", "")
        session_id = request.get("session_id", "default")
        
        if not message:
            raise HTTPException(status_code=400, detail="Mensagem é obrigatória")
        
        logger.info(f"💬 Chat simplificado: '{message[:50]}...' (sessão: {session_id})")
        
        # Resposta simples para teste
        response = {
            "message": f"Recebi sua mensagem: '{message}'. Esta é uma resposta de teste do sistema simplificado.",
            "session_id": session_id,
            "timestamp": time.time(),
            "type": "assistant",
            "metadata": {
                "model": "sistema-simplificado",
                "status": "ok",
                "processing_time": 0.1
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no chat endpoint simplificado: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Erro interno do servidor",
                "message": f"Erro no processamento: {str(e)}",
                "timestamp": time.time()
            }
        )


# ============================================================================
# ROTAS EXTRAS PARA DASHBOARD
# ============================================================================

@app.get("/dashboard/metrics", tags=["Dashboard"])
async def get_dashboard_metrics():
    """
    Métricas do sistema para dashboard.
    
    Retorna estatísticas em tempo real do sistema incluindo:
    - Número de uploads processados
    - Status da conexão com banco vetorial
    - Métricas de performance
    - Estatísticas de uso
    """
    try:
        from src.vectorstore.supabase_client import supabase
        
        # Teste de conexão simples
        embeddings_count = 0
        supabase_status = "disconnected"
        
        try:
            result = supabase.table('embeddings').select('*').limit(1).execute()
            embeddings_count = len(result.data) if result.data else 0
            supabase_status = "connected"
        except Exception as e:
            logger.warning(f"Erro ao conectar com Supabase: {e}")
        
        return {
            "status": "operational",
            "timestamp": time.time(),
            "database": {
                "status": supabase_status,
                "embeddings_count": embeddings_count,
            },
            "api": {
                "uptime_seconds": time.time() - getattr(app, '_start_time', time.time()),
                "version": "1.0.0",
            },
            "system": {
                "total_requests": getattr(app, '_request_count', 0),
                "active_sessions": 0,  # Implementar contagem de sessões ativas
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas do dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Erro interno do servidor",
                "message": "Não foi possível obter métricas do sistema",
                "timestamp": time.time()
            }
        )


# Rota raiz com informações da API
@app.get("/", tags=["Root"])
async def root():
    """Informações gerais da API."""
    return {
        "name": "EDA AI Minds - API Multiagente",
        "version": "1.0.0",
        "description": "Sistema multiagente para análise exploratória de dados CSV",
        "features": [
            "Upload e análise automática de CSV",
            "Detecção de fraudes com LLMs",
            "Sistema RAG com busca semântica",
            "Chat inteligente com contexto",
        ],
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "github": "https://github.com/ai-mindsgroup/eda-aiminds-back",
        "timestamp": time.time(),
    }


# ============================================================================
# EXECUTAR SERVIDOR
# ============================================================================

if __name__ == "__main__":
    # Configuração de desenvolvimento
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=LOG_LEVEL.lower(),
        access_log=True,
    )