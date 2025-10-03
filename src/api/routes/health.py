"""
Rotas para Health Check
======================

Endpoints para verificar saúde da API e componentes.
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.schemas import HealthCheck
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Variável para tracking do uptime
_start_time = time.time()


@router.get("/", response_model=HealthCheck, summary="Verificação geral de saúde")
async def health_check():
    """
    Verificação completa de saúde da API.
    
    Retorna:
    - Status geral da API
    - Conectividade com banco de dados
    - Status do banco vetorial
    - Disponibilidade dos serviços LLM
    - Métricas de performance
    """
    try:
        # Calcular uptime
        uptime_seconds = time.time() - _start_time
        
        # Verificar banco de dados
        database_status = await _check_database()
        
        # Verificar banco vetorial
        vectorstore_status = await _check_vectorstore()
        
        # Verificar serviços LLM
        llm_status = await _check_llm_services()
        
        # Obter métricas de sistema
        memory_usage = _get_memory_usage()
        
        # Determinar status geral
        all_healthy = (
            database_status["healthy"] and
            vectorstore_status["healthy"] and
            llm_status["google"]["healthy"]  # Pelo menos Google deve estar OK
        )
        
        status = "healthy" if all_healthy else "degraded"
        
        return HealthCheck(
            status=status,
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            database=database_status,
            vectorstore=vectorstore_status,
            llm_services=llm_status,
            memory_usage=memory_usage,
            total_requests=0,  # TODO: Implementar contador
            error_rate=0.0,    # TODO: Implementar métrica
            avg_response_time=0.0  # TODO: Implementar métrica
        )
        
    except Exception as e:
        logger.error(f"Erro na verificação de saúde: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro na verificação de saúde da API"
        )


@router.get("/live", summary="Liveness probe")
async def liveness_probe():
    """
    Verificação básica se a API está respondendo.
    Usado por orquestradores como Kubernetes.
    """
    return {"status": "alive", "timestamp": time.time()}


@router.get("/ready", summary="Readiness probe")
async def readiness_probe():
    """
    Verificação se a API está pronta para receber tráfego.
    Valida dependências críticas.
    """
    try:
        # Verificar dependências críticas
        database_ok = (await _check_database())["healthy"]
        
        if not database_ok:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "database_unavailable"}
            )
        
        return {"status": "ready", "timestamp": time.time()}
        
    except Exception as e:
        logger.error(f"Erro na verificação de readiness: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": str(e)}
        )


@router.get("/metrics", summary="Métricas básicas da API")
async def get_metrics():
    """
    Métricas básicas para monitoramento.
    """
    try:
        uptime_seconds = time.time() - _start_time
        memory_info = psutil.Process().memory_info()
        
        return {
            "uptime_seconds": uptime_seconds,
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "timestamp": time.time(),
        }
        
    except Exception as e:
        logger.error(f"Erro obtendo métricas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro obtendo métricas da API"
        )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

async def _check_database() -> Dict[str, Any]:
    """Verifica conexão com banco principal."""
    try:
        from src.vectorstore.supabase_client import supabase
        
        # Teste simples de conexão
        result = supabase.table('embeddings').select('id').limit(1).execute()
        
        return {
            "healthy": True,
            "status": "connected",
            "response_time_ms": 50,  # TODO: Medir tempo real
            "last_check": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Banco de dados indisponível: {e}")
        return {
            "healthy": False,
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat(),
        }


async def _check_vectorstore() -> Dict[str, Any]:
    """Verifica banco vetorial."""
    try:
        from src.vectorstore.supabase_client import supabase
        
        # Teste específico para tabela de embeddings
        result = supabase.table('embeddings').select('id').limit(1).execute()
        
        # Contar embeddings
        count_result = supabase.table('embeddings').select('id', count='exact').execute()
        embeddings_count = count_result.count or 0
        
        return {
            "healthy": True,
            "status": "connected",
            "embeddings_count": embeddings_count,
            "last_check": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Banco vetorial indisponível: {e}")
        return {
            "healthy": False,
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat(),
        }


async def _check_llm_services() -> Dict[str, Any]:
    """Verifica serviços LLM."""
    services = {}
    
    # Verificar Google AI
    try:
        from src.settings import GOOGLE_API_KEY
        
        if GOOGLE_API_KEY:
            # TODO: Fazer teste real da API
            services["google"] = {
                "healthy": True,
                "status": "configured",
                "api_key_configured": True,
            }
        else:
            services["google"] = {
                "healthy": False,
                "status": "not_configured",
                "api_key_configured": False,
            }
            
    except Exception as e:
        services["google"] = {
            "healthy": False,
            "status": "error",
            "error": str(e),
        }
    
    # Verificar Grok
    try:
        from src.settings import GROK_API_KEY
        
        services["grok"] = {
            "healthy": bool(GROK_API_KEY),
            "status": "configured" if GROK_API_KEY else "not_configured",
            "api_key_configured": bool(GROK_API_KEY),
        }
        
    except Exception as e:
        services["grok"] = {
            "healthy": False,
            "status": "error", 
            "error": str(e),
        }
    
    # Verificar Groq
    try:
        from src.settings import GROQ_API_KEY
        
        services["groq"] = {
            "healthy": bool(GROQ_API_KEY),
            "status": "configured" if GROQ_API_KEY else "not_configured",
            "api_key_configured": bool(GROQ_API_KEY),
        }
        
    except Exception as e:
        services["groq"] = {
            "healthy": False,
            "status": "error",
            "error": str(e),
        }
    
    return services


def _get_memory_usage() -> Dict[str, Any]:
    """Obtém informações de uso de memória."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024,
        }
        
    except Exception as e:
        logger.warning(f"Erro obtendo uso de memória: {e}")
        return {
            "error": str(e)
        }