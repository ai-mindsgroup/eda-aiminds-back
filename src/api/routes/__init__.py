"""
Configuração de rotas da API
"""

from src.api.routes.analysis import router as analysis_router
from src.api.routes.auth import router as auth_router
from src.api.routes.csv import router as csv_router
from src.api.routes.health import router as health_router
from src.api.routes.rag import router as rag_router

__all__ = [
    "analysis_router",
    "auth_router", 
    "csv_router",
    "health_router",
    "rag_router",
]