"""
Módulo de utilitários para o sistema de memória dos agentes.

Este módulo fornece funções utilitárias, helpers e ferramentas de apoio
para o sistema de memória persistente dos agentes multiagente.
"""

import hashlib
import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from .memory_types import (
    AgentContext,
    ContextType,
    ConversationMessage,
    EmbeddingType,
    MemoryConfig,
    MessageType,
    SessionInfo,
    SessionStatus,
    SessionType
)


# ============================================================================
# GERADORES DE ID E HASH
# ============================================================================

def generate_session_id(prefix: str = "session", include_timestamp: bool = True) -> str:
    """
    Gera um ID único para sessão.
    
    Args:
        prefix: Prefixo para o ID
        include_timestamp: Se deve incluir timestamp no ID
        
    Returns:
        String com ID único da sessão
    """
    unique_part = str(uuid4())[:8]
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}_{unique_part}"
    else:
        return f"{prefix}_{unique_part}"


def generate_context_hash(agent_name: str, context_type: str, context_data: Dict[str, Any]) -> str:
    """
    Gera hash único para contexto baseado no conteúdo.
    
    Args:
        agent_name: Nome do agente
        context_type: Tipo do contexto
        context_data: Dados do contexto
        
    Returns:
        Hash MD5 do contexto
    """
    content_str = f"{agent_name}_{context_type}_{json.dumps(context_data, sort_keys=True)}"
    return hashlib.md5(content_str.encode()).hexdigest()


def generate_content_fingerprint(content: str) -> str:
    """
    Gera fingerprint de conteúdo para detecção de duplicatas.
    
    Args:
        content: Conteúdo para gerar fingerprint
        
    Returns:
        Hash SHA256 truncado do conteúdo
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# UTILITÁRIOS DE DATA E TEMPO
# ============================================================================

def calculate_session_expiry(session_type: SessionType, custom_hours: Optional[int] = None) -> datetime:
    """
    Calcula data de expiração baseada no tipo de sessão.
    
    Args:
        session_type: Tipo da sessão
        custom_hours: Duração customizada em horas
        
    Returns:
        Data/hora de expiração
    """
    if custom_hours:
        hours = min(custom_hours, MemoryConfig.MAX_SESSION_DURATION_HOURS)
    else:
        # Durações padrão por tipo
        duration_map = {
            SessionType.INTERACTIVE: 24,
            SessionType.BATCH: 2,
            SessionType.API: 12,
            SessionType.SYSTEM: 24 * 7  # 1 semana
        }
        hours = duration_map.get(session_type, MemoryConfig.DEFAULT_SESSION_DURATION_HOURS)
    
    return datetime.now() + timedelta(hours=hours)


def is_within_retention_period(created_at: datetime, retention_days: int) -> bool:
    """
    Verifica se está dentro do período de retenção.
    
    Args:
        created_at: Data de criação
        retention_days: Dias de retenção
        
    Returns:
        True se ainda está no período de retenção
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    return created_at > cutoff_date


def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """
    Formata duração entre dois timestamps.
    
    Args:
        start_time: Tempo inicial
        end_time: Tempo final (padrão: agora)
        
    Returns:
        String formatada da duração
    """
    if end_time is None:
        end_time = datetime.now()
    
    delta = end_time - start_time
    
    if delta.days > 0:
        return f"{delta.days}d {delta.seconds // 3600}h"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
    elif delta.seconds >= 60:
        return f"{(delta.seconds % 3600) // 60}m {delta.seconds % 60}s"
    else:
        return f"{delta.seconds}s"


# ============================================================================
# UTILITÁRIOS DE TAMANHO E COMPRESSÃO
# ============================================================================

def calculate_data_size(data: Any) -> int:
    """
    Calcula tamanho aproximado de dados em bytes.
    
    Args:
        data: Dados para calcular tamanho
        
    Returns:
        Tamanho em bytes
    """
    if isinstance(data, str):
        return len(data.encode('utf-8'))
    elif isinstance(data, dict) or isinstance(data, list):
        return len(json.dumps(data).encode('utf-8'))
    else:
        return sys.getsizeof(data)


def truncate_content(content: str, max_length: int = MemoryConfig.MAX_MESSAGE_LENGTH) -> str:
    """
    Trunca conteúdo se exceder tamanho máximo.
    
    Args:
        content: Conteúdo para truncar
        max_length: Tamanho máximo permitido
        
    Returns:
        Conteúdo truncado se necessário
    """
    if len(content) <= max_length:
        return content
    
    truncated = content[:max_length - 50]  # Reserva espaço para indicador
    return f"{truncated}... [TRUNCADO - {len(content)} caracteres originais]"


def compress_old_conversations(messages: List[ConversationMessage], max_turns: int = 50) -> List[ConversationMessage]:
    """
    Comprime conversações antigas mantendo apenas mensagens mais relevantes.
    
    Args:
        messages: Lista de mensagens
        max_turns: Máximo de turnos a manter
        
    Returns:
        Lista comprimida de mensagens
    """
    if len(messages) <= max_turns:
        return messages
    
    # Manter sempre as primeiras e últimas mensagens
    first_msgs = messages[:5]
    last_msgs = messages[-(max_turns - 10):]
    
    # Criar mensagem de sumário
    compressed_count = len(messages) - len(first_msgs) - len(last_msgs)
    summary_msg = ConversationMessage(
        agent_name="system",
        message_type=MessageType.SYSTEM,
        content=f"[SUMÁRIO: {compressed_count} mensagens comprimidas]",
        metadata={"compressed": True, "original_count": compressed_count}
    )
    
    return first_msgs + [summary_msg] + last_msgs


# ============================================================================
# UTILITÁRIOS DE VALIDAÇÃO E SANITIZAÇÃO
# ============================================================================

def sanitize_agent_name(agent_name: str) -> str:
    """
    Sanitiza nome do agente para uso seguro.
    
    Args:
        agent_name: Nome original do agente
        
    Returns:
        Nome sanitizado
    """
    # Remove caracteres especiais e limita tamanho
    sanitized = ''.join(c for c in agent_name if c.isalnum() or c in ['_', '-'])
    return sanitized[:100].lower()


def sanitize_session_id(session_id: str) -> str:
    """
    Sanitiza session ID para uso seguro.
    
    Args:
        session_id: ID original da sessão
        
    Returns:
        Session ID sanitizado
    """
    # Remove caracteres especiais exceto alguns permitidos
    sanitized = ''.join(c for c in session_id if c.isalnum() or c in ['_', '-', '.'])
    return sanitized[:255]


def validate_context_data(context_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Valida dados de contexto.
    
    Args:
        context_data: Dados do contexto para validar
        
    Returns:
        Tuple (é_válido, mensagem_erro)
    """
    if not isinstance(context_data, dict):
        return False, "Context data deve ser um dicionário"
    
    # Verifica tamanho
    size = calculate_data_size(context_data)
    if size > MemoryConfig.MAX_CONTEXT_SIZE_BYTES:
        return False, f"Context data muito grande: {size} bytes (máximo: {MemoryConfig.MAX_CONTEXT_SIZE_BYTES})"
    
    # Verifica se é serializável
    try:
        json.dumps(context_data)
    except (TypeError, ValueError) as e:
        return False, f"Context data não é serializável: {str(e)}"
    
    return True, None


def clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpa e padroniza metadados.
    
    Args:
        metadata: Metadados originais
        
    Returns:
        Metadados limpos
    """
    if not isinstance(metadata, dict):
        return {}
    
    cleaned = {}
    for key, value in metadata.items():
        # Limita chaves e converte valores não serializáveis
        if isinstance(key, str) and len(key) <= 50:
            try:
                json.dumps(value)  # Testa se é serializável
                cleaned[key] = value
            except (TypeError, ValueError):
                cleaned[key] = str(value)  # Converte para string se não for serializável
    
    return cleaned


# ============================================================================
# UTILITÁRIOS DE BUSCA E FILTRO
# ============================================================================

def filter_sessions_by_status(sessions: List[SessionInfo], status: SessionStatus) -> List[SessionInfo]:
    """
    Filtra sessões por status.
    
    Args:
        sessions: Lista de sessões
        status: Status para filtrar
        
    Returns:
        Lista filtrada de sessões
    """
    return [session for session in sessions if session.status == status]


def filter_expired_sessions(sessions: List[SessionInfo]) -> List[SessionInfo]:
    """
    Filtra sessões expiradas.
    
    Args:
        sessions: Lista de sessões
        
    Returns:
        Lista de sessões expiradas
    """
    return [session for session in sessions if session.is_expired()]


def group_contexts_by_type(contexts: List[AgentContext]) -> Dict[ContextType, List[AgentContext]]:
    """
    Agrupa contextos por tipo.
    
    Args:
        contexts: Lista de contextos
        
    Returns:
        Dicionário agrupado por tipo
    """
    grouped = {}
    for context in contexts:
        context_type = context.context_type
        if context_type not in grouped:
            grouped[context_type] = []
        grouped[context_type].append(context)
    
    return grouped


def find_recent_conversations(messages: List[ConversationMessage], hours: int = 24) -> List[ConversationMessage]:
    """
    Encontra conversações recentes.
    
    Args:
        messages: Lista de mensagens
        hours: Número de horas para considerar "recente"
        
    Returns:
        Lista de mensagens recentes
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    return [msg for msg in messages if msg.timestamp > cutoff_time]


# ============================================================================
# UTILITÁRIOS DE EMBEDDINGS
# ============================================================================

def normalize_embedding(embedding: List[float]) -> List[float]:
    """
    Normaliza embedding para magnitude unitária.
    
    Args:
        embedding: Lista de valores do embedding
        
    Returns:
        Embedding normalizado
    """
    import math
    
    magnitude = math.sqrt(sum(x * x for x in embedding))
    if magnitude == 0:
        return embedding
    
    return [x / magnitude for x in embedding]


def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calcula similaridade cosseno entre dois embeddings.
    
    Args:
        embedding1: Primeiro embedding
        embedding2: Segundo embedding
        
    Returns:
        Valor de similaridade (0-1)
    """
    if len(embedding1) != len(embedding2):
        raise ValueError("Embeddings devem ter a mesma dimensão")
    
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    magnitude1 = sum(a * a for a in embedding1) ** 0.5
    magnitude2 = sum(b * b for b in embedding2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return max(0.0, min(1.0, dot_product / (magnitude1 * magnitude2)))


# ============================================================================
# UTILITÁRIOS DE PERFORMANCE E MONITORAMENTO
# ============================================================================

def calculate_memory_usage_stats(contexts: List[AgentContext]) -> Dict[str, Any]:
    """
    Calcula estatísticas de uso de memória.
    
    Args:
        contexts: Lista de contextos
        
    Returns:
        Dicionário com estatísticas
    """
    if not contexts:
        return {
            'total_contexts': 0,
            'total_size_bytes': 0,
            'avg_size_bytes': 0,
            'total_access_count': 0,
            'avg_access_count': 0
        }
    
    total_size = sum(ctx.data_size_bytes or 0 for ctx in contexts)
    total_access = sum(ctx.access_count for ctx in contexts)
    
    return {
        'total_contexts': len(contexts),
        'total_size_bytes': total_size,
        'avg_size_bytes': total_size / len(contexts),
        'total_access_count': total_access,
        'avg_access_count': total_access / len(contexts),
        'contexts_by_type': {
            ctx_type.value: len([ctx for ctx in contexts if ctx.context_type == ctx_type])
            for ctx_type in ContextType
        }
    }


def identify_cleanup_candidates(contexts: List[AgentContext], 
                               min_priority: int = 8,
                               max_unused_days: int = 7) -> List[AgentContext]:
    """
    Identifica contextos candidatos para limpeza.
    
    Args:
        contexts: Lista de contextos
        min_priority: Prioridade mínima para considerar limpeza
        max_unused_days: Máximo de dias sem uso
        
    Returns:
        Lista de contextos candidatos para limpeza
    """
    cutoff_date = datetime.now() - timedelta(days=max_unused_days)
    
    candidates = []
    for context in contexts:
        # Critérios para limpeza:
        # 1. Baixa prioridade E não acessado recentemente
        # 2. OU expirado
        # 3. OU contexto de cache antigo
        
        if context.is_expired():
            candidates.append(context)
        elif (context.priority >= min_priority and 
              context.last_accessed_at < cutoff_date):
            candidates.append(context)
        elif (context.context_type == ContextType.CACHE and 
              context.last_accessed_at < cutoff_date):
            candidates.append(context)
    
    return candidates


def format_memory_summary(stats: Dict[str, Any]) -> str:
    """
    Formata resumo de estatísticas de memória.
    
    Args:
        stats: Estatísticas de memória
        
    Returns:
        String formatada com resumo
    """
    total_mb = stats['total_size_bytes'] / (1024 * 1024)
    avg_kb = stats['avg_size_bytes'] / 1024
    
    summary = f"""
📊 Resumo da Memória dos Agentes:
├─ Total de contextos: {stats['total_contexts']}
├─ Tamanho total: {total_mb:.2f} MB
├─ Tamanho médio: {avg_kb:.2f} KB
├─ Total de acessos: {stats['total_access_count']}
└─ Média de acessos: {stats['avg_access_count']:.1f}

📈 Distribuição por tipo:
"""
    
    for ctx_type, count in stats['contexts_by_type'].items():
        if count > 0:
            summary += f"├─ {ctx_type}: {count}\n"
    
    return summary.strip()