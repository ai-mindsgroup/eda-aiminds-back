"""
Query Fragmentation System - Sistema Inteligente de Fragmentação de Queries
============================================================================

Sistema que usa LLMs para fragmentar queries grandes em múltiplas queries menores,
respeitando limites de tokens do GROQ e otimizando uso de cache/memória.

Componentes:
- QueryFragmenter: Fragmenta queries usando LLM para seleção inteligente
- QueryAggregator: Agrega resultados de múltiplos fragmentos
- TokenBudgetController: Controla rigorosamente limites de tokens
- FragmentCache: Cache inteligente usando memória Supabase

Autor: Sistema Multiagente EDA AI Minds
Data: 2025-01-20
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib

from src.utils.logging_config import get_logger
from src.llm.manager import get_llm_manager, LLMConfig, LLMResponse
from src.memory.supabase_memory import SupabaseMemoryManager
from src.memory.memory_types import ContextType

logger = get_logger(__name__)


class FragmentStrategy(str, Enum):
    """Estratégias de fragmentação disponíveis."""
    COLUMN_GROUPS = "column_groups"      # Divide por grupos de colunas relacionadas
    ROW_SEGMENTS = "row_segments"        # Divide por segmentos de linhas
    HYBRID = "hybrid"                    # Combina colunas + segmentos
    TIME_WINDOWS = "time_windows"        # Divide por janelas temporais (para séries temporais)


@dataclass
class TokenBudget:
    """Orçamento de tokens para controle rigoroso."""
    max_tokens_per_request: int = 6000  # Limite GROQ
    reserved_tokens: int = 500           # Tokens reservados para prompt base
    safety_margin: int = 200             # Margem de segurança
    
    @property
    def available_tokens(self) -> int:
        """Tokens disponíveis para dados."""
        return self.max_tokens_per_request - self.reserved_tokens - self.safety_margin
    
    def can_fit(self, estimated_tokens: int) -> bool:
        """Verifica se quantidade de tokens cabe no orçamento."""
        return estimated_tokens <= self.available_tokens


@dataclass
class QueryFragment:
    """Representa um fragmento de query."""
    fragment_id: str
    strategy: FragmentStrategy
    columns: Optional[List[str]] = None
    row_range: Optional[Tuple[int, int]] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    filters: Optional[Dict[str, Any]] = None
    estimated_tokens: int = 0
    priority: int = 5  # 1=highest, 10=lowest
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        return {
            'fragment_id': self.fragment_id,
            'strategy': self.strategy.value,
            'columns': self.columns,
            'row_range': list(self.row_range) if self.row_range else None,
            'time_range': [t.isoformat() if t else None for t in (self.time_range or (None, None))],
            'filters': self.filters,
            'estimated_tokens': self.estimated_tokens,
            'priority': self.priority,
            'metadata': self.metadata
        }


@dataclass
class FragmentResult:
    """Resultado da execução de um fragmento."""
    fragment_id: str
    success: bool
    result: Any
    tokens_used: int
    processing_time_ms: int
    from_cache: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        return {
            'fragment_id': self.fragment_id,
            'success': self.success,
            'result': self.result if isinstance(self.result, (dict, list, str, int, float, bool, type(None))) else str(self.result),
            'tokens_used': self.tokens_used,
            'processing_time_ms': self.processing_time_ms,
            'from_cache': self.from_cache,
            'error': self.error,
            'metadata': self.metadata
        }


class TokenBudgetController:
    """Controlador rigoroso de orçamento de tokens."""
    
    def __init__(self, budget: Optional[TokenBudget] = None):
        """
        Inicializa o controlador de tokens.
        
        Args:
            budget: Orçamento de tokens (usa padrão se None)
        """
        self.budget = budget or TokenBudget()
        self.logger = get_logger(f"{__name__}.TokenBudgetController")
        
    def estimate_tokens(self, text: str) -> int:
        """
        Estima quantidade de tokens em um texto.
        
        Usa regra simples: ~4 caracteres = 1 token
        Para estimativas mais precisas, pode-se usar tiktoken.
        
        Args:
            text: Texto para estimar tokens
            
        Returns:
            Estimativa de tokens
        """
        return len(text) // 4 + 1
    
    def estimate_dataframe_tokens(self, df_shape: Tuple[int, int], include_values: bool = True) -> int:
        """
        Estima tokens necessários para representar um DataFrame.
        
        Args:
            df_shape: (num_rows, num_cols)
            include_values: Se deve incluir valores ou apenas estrutura
            
        Returns:
            Estimativa de tokens
        """
        num_rows, num_cols = df_shape
        
        # Tokens para nomes de colunas (~10 tokens por coluna)
        column_tokens = num_cols * 10
        
        if include_values:
            # Tokens para valores (~5 tokens por célula em média)
            value_tokens = num_rows * num_cols * 5
        else:
            # Apenas estatísticas básicas
            value_tokens = num_cols * 20
        
        return column_tokens + value_tokens
    
    def calculate_max_rows(self, num_cols: int) -> int:
        """
        Calcula número máximo de linhas que cabem no orçamento.
        
        Args:
            num_cols: Número de colunas
            
        Returns:
            Número máximo de linhas
        """
        tokens_per_row = num_cols * 5  # ~5 tokens por célula
        return self.budget.available_tokens // tokens_per_row
    
    def validate_fragment(self, fragment: QueryFragment) -> Tuple[bool, str]:
        """
        Valida se fragmento respeita orçamento de tokens.
        
        Args:
            fragment: Fragmento a validar
            
        Returns:
            Tuple[bool, str]: (válido, mensagem)
        """
        if fragment.estimated_tokens == 0:
            return True, "Fragmento sem estimativa de tokens"
        
        if fragment.estimated_tokens > self.budget.available_tokens:
            return False, (
                f"Fragmento excede orçamento: {fragment.estimated_tokens} tokens "
                f"(limite: {self.budget.available_tokens})"
            )
        
        return True, "Fragmento válido"


class FragmentCache:
    """Cache inteligente de fragmentos usando memória Supabase."""
    
    def __init__(self, session_id: str, agent_name: str = "query_fragmenter"):
        """
        Inicializa o cache de fragmentos.
        
        Args:
            session_id: ID da sessão atual
            agent_name: Nome do agente para namespace
        """
        self.session_id = session_id
        self.agent_name = agent_name
        self.memory_manager = SupabaseMemoryManager(agent_name=agent_name)
        self.logger = get_logger(f"{__name__}.FragmentCache")
        
    def _generate_cache_key(self, fragment: QueryFragment) -> str:
        """
        Gera chave única para cache de fragmento.
        
        Args:
            fragment: Fragmento para gerar chave
            
        Returns:
            Chave única (hash MD5)
        """
        # Serializa fragmento de forma determinística
        fragment_dict = fragment.to_dict()
        # Remove campos que não afetam resultado
        fragment_dict.pop('fragment_id', None)
        fragment_dict.pop('estimated_tokens', None)
        fragment_dict.pop('priority', None)
        
        # Gera hash
        content = json.dumps(fragment_dict, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_result(self, fragment: QueryFragment) -> Optional[FragmentResult]:
        """
        Busca resultado em cache.
        
        Args:
            fragment: Fragmento para buscar
            
        Returns:
            Resultado em cache ou None se não encontrado
        """
        cache_key = self._generate_cache_key(fragment)
        
        try:
            # Busca no contexto de cache
            cached_data = await self.memory_manager.get_context(
                session_id=self.session_id,
                context_type=ContextType.CACHE,
                context_key=cache_key
            )
            
            if cached_data:
                self.logger.info(f"✅ Cache HIT para fragmento {fragment.fragment_id}")
                # Reconstrói FragmentResult
                return FragmentResult(
                    fragment_id=fragment.fragment_id,
                    success=cached_data.get('success', False),
                    result=cached_data.get('result'),
                    tokens_used=cached_data.get('tokens_used', 0),
                    processing_time_ms=cached_data.get('processing_time_ms', 0),
                    from_cache=True,
                    metadata=cached_data.get('metadata', {})
                )
            
            self.logger.info(f"❌ Cache MISS para fragmento {fragment.fragment_id}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Erro ao buscar cache: {str(e)}")
            return None
    
    async def save_result(
        self, 
        fragment: QueryFragment, 
        result: FragmentResult,
        ttl_hours: int = 24
    ) -> bool:
        """
        Salva resultado no cache.
        
        Args:
            fragment: Fragmento executado
            result: Resultado a salvar
            ttl_hours: Tempo de vida em horas
            
        Returns:
            True se salvou com sucesso
        """
        cache_key = self._generate_cache_key(fragment)
        
        try:
            # Salva no contexto de cache com expiração
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            await self.memory_manager.save_context(
                session_id=self.session_id,
                context_type=ContextType.CACHE,
                context_key=cache_key,
                context_data=result.to_dict(),
                expires_at=expires_at
            )
            
            self.logger.info(f"💾 Resultado salvo em cache: {fragment.fragment_id} (TTL: {ttl_hours}h)")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar em cache: {str(e)}")
            return False


# Singleton global do LLM Manager
_llm_manager = None

def get_fragmenter_llm() -> Any:
    """Obtém instância singleton do LLM Manager."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = get_llm_manager()
    return _llm_manager
