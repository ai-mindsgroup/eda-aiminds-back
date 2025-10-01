"""
Módulo de memória para agentes multiagente.

Este módulo fornece um sistema completo de memória persistente para agentes,
incluindo armazenamento de conversações, contexto, preferências e busca semântica
usando Supabase como backend.
"""

from .base_memory import BaseMemoryManager, MemoryMixin
from .memory_types import (
    # Enums
    SessionType,
    SessionStatus,
    MessageType,
    ContentFormat,
    ContextType,
    EmbeddingType,
    
    # Dataclasses
    SessionInfo,
    ConversationMessage,
    AgentContext,
    MemoryEmbedding,
    SimilaritySearchResult,
    
    # Config e Exceções
    MemoryConfig,
    MemoryError,
    SessionNotFoundError,
    SessionExpiredError,
    ContextNotFoundError,
    MemoryQuotaExceededError,
    InvalidEmbeddingError,
    
    # Validadores
    validate_embedding_dimension,
    validate_session_id,
    validate_agent_name,
    validate_context_key,
    validate_confidence_score,
    validate_priority
)
from .memory_utils import (
    # Geradores
    generate_session_id,
    generate_context_hash,
    generate_content_fingerprint,
    
    # Data/Tempo
    calculate_session_expiry,
    is_within_retention_period,
    format_duration,
    
    # Tamanho/Compressão
    calculate_data_size,
    truncate_content,
    compress_old_conversations,
    
    # Validação/Sanitização
    sanitize_agent_name,
    sanitize_session_id,
    validate_context_data,
    clean_metadata,
    
    # Busca/Filtro
    filter_sessions_by_status,
    filter_expired_sessions,
    group_contexts_by_type,
    find_recent_conversations,
    
    # Embeddings
    normalize_embedding,
    calculate_cosine_similarity,
    
    # Performance/Monitoramento
    calculate_memory_usage_stats,
    identify_cleanup_candidates,
    format_memory_summary
)
from .supabase_memory import SupabaseMemoryManager

# Versão do módulo
__version__ = "1.0.0"

# Exportações principais
__all__ = [
    # Classes principais
    "BaseMemoryManager",
    "SupabaseMemoryManager", 
    "MemoryMixin",
    
    # Tipos de dados
    "SessionInfo",
    "ConversationMessage",
    "AgentContext",
    "MemoryEmbedding",
    "SimilaritySearchResult",
    
    # Enums
    "SessionType",
    "SessionStatus", 
    "MessageType",
    "ContentFormat",
    "ContextType",
    "EmbeddingType",
    
    # Configuração
    "MemoryConfig",
    
    # Exceções
    "MemoryError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "ContextNotFoundError",
    "MemoryQuotaExceededError",
    "InvalidEmbeddingError",
    
    # Utilitários principais
    "generate_session_id",
    "calculate_data_size",
    "validate_context_data",
    "calculate_memory_usage_stats",
    
    # Validadores
    "validate_embedding_dimension",
    "validate_session_id",
    "validate_agent_name",
    "validate_context_key",
    "validate_confidence_score",
    "validate_priority"
]


def create_memory_manager(agent_name: str, backend: str = "supabase") -> BaseMemoryManager:
    """
    Factory function para criar gerenciador de memória.
    
    Args:
        agent_name: Nome do agente
        backend: Backend de armazenamento ("supabase")
        
    Returns:
        Instância do gerenciador de memória
        
    Raises:
        ValueError: Se backend não suportado
    """
    if backend.lower() == "supabase":
        return SupabaseMemoryManager(agent_name)
    else:
        raise ValueError(f"Backend '{backend}' não suportado. Use: 'supabase'")


def get_memory_info() -> Dict[str, str]:
    """
    Retorna informações sobre o módulo de memória.
    
    Returns:
        Dicionário com informações do módulo
    """
    return {
        "module": "src.memory",
        "version": __version__,
        "description": "Sistema de memória persistente para agentes multiagente",
        "backends_supported": ["supabase"],
        "features": [
            "Sessões persistentes",
            "Histórico de conversação",
            "Contexto por agente",
            "Busca semântica com embeddings",
            "Limpeza automática",
            "Estatísticas de uso"
        ]
    }


# Configuração de logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Módulo de memória carregado - versão {__version__}")


# Exemplo de uso
if __name__ == "__main__":
    print("=== Sistema de Memória para Agentes Multiagente ===")
    print(f"Versão: {__version__}")
    print("\nCaracterísticas:")
    for feature in get_memory_info()["features"]:
        print(f"  ✓ {feature}")
    
    print("\nExemplo de uso:")
    print("""
    from src.memory import SupabaseMemoryManager, MemoryMixin
    
    # Criar gerenciador de memória
    memory = SupabaseMemoryManager("meu_agente")
    
    # Inicializar sessão
    session_id = await memory.initialize_session()
    
    # Salvar conversa
    await memory.add_user_query("Como analisar dados CSV?", session_id)
    await memory.add_agent_response("Posso ajudar com análise...", session_id)
    
    # Recuperar contexto
    context = await memory.get_recent_context(session_id)
    """)