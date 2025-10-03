#!/usr/bin/env python3
"""
Sistema de Cache para Modelos ML
================================

Cache inteligente para modelos de Machine Learning, otimizando carregamento
e reduzindo uso de memória desnecessário.
"""

import weakref
from typing import Dict, Any, Optional, Callable
from threading import Lock
import gc
import psutil
import time
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ModelCache:
    """Cache inteligente para modelos ML com gerenciamento de memória."""
    
    def __init__(self, max_memory_mb: int = 1000, max_models: int = 3):
        """
        Inicializa o cache de modelos.
        
        Args:
            max_memory_mb: Limite máximo de memória em MB para o cache
            max_models: Número máximo de modelos em cache simultaneamente
        """
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = Lock()
        self.max_memory_mb = max_memory_mb
        self.max_models = max_models
        
        logger.info(f"Cache ML inicializado - Max: {max_models} modelos, {max_memory_mb}MB")
    
    def get(self, key: str, loader: Optional[Callable] = None) -> Optional[Any]:
        """
        Recupera modelo do cache ou carrega se necessário.
        
        Args:
            key: Chave única do modelo
            loader: Função para carregar o modelo se não estiver em cache
            
        Returns:
            Modelo carregado ou None se não encontrado
        """
        with self._lock:
            # Verificar se está em cache
            if key in self._cache:
                self._access_times[key] = time.time()
                logger.debug(f"🔄 Modelo '{key}' recuperado do cache")
                return self._cache[key]
            
            # Carregar modelo se loader fornecido
            if loader:
                return self._load_and_cache(key, loader)
            
            return None
    
    def _load_and_cache(self, key: str, loader: Callable) -> Any:
        """Carrega modelo e adiciona ao cache."""
        try:
            # Verificar espaço disponível
            self._ensure_space()
            
            start_time = time.time()
            logger.info(f"🔄 Carregando modelo '{key}'...")
            
            # Carregar modelo
            model = loader()
            
            # Adicionar ao cache
            self._cache[key] = model
            self._access_times[key] = time.time()
            
            load_time = time.time() - start_time
            memory_mb = self._get_memory_usage_mb()
            
            logger.info(f"✅ Modelo '{key}' carregado em {load_time:.2f}s - Memória: {memory_mb}MB")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo '{key}': {str(e)}")
            raise
    
    def _ensure_space(self):
        """Garante espaço no cache removendo modelos antigos se necessário."""
        # Verificar limite de número de modelos
        while len(self._cache) >= self.max_models:
            self._remove_oldest()
        
        # Verificar limite de memória
        while self._get_memory_usage_mb() > self.max_memory_mb and self._cache:
            self._remove_oldest()
    
    def _remove_oldest(self):
        """Remove o modelo menos recentemente usado."""
        if not self._access_times:
            return
        
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self.remove(oldest_key)
    
    def remove(self, key: str):
        """Remove modelo específico do cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                gc.collect()  # Forçar garbage collection
                logger.info(f"🗑️ Modelo '{key}' removido do cache")
    
    def clear(self):
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            gc.collect()
            logger.info("🧹 Cache ML limpo completamente")
    
    def _get_memory_usage_mb(self) -> float:
        """Retorna uso atual de memória em MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            return {
                "models_count": len(self._cache),
                "max_models": self.max_models,
                "memory_mb": self._get_memory_usage_mb(),
                "max_memory_mb": self.max_memory_mb,
                "cached_models": list(self._cache.keys())
            }


# Instância global do cache
_global_cache = ModelCache()

def get_model_cache() -> ModelCache:
    """Retorna instância global do cache de modelos."""
    return _global_cache