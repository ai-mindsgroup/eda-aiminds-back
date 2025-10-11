"""
Módulo de tipos e schemas para o sistema de memória dos agentes.

Este módulo define as estruturas de dados, tipos e schemas utilizados
pelo sistema de memória persistente dos agentes multiagente.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4


# ============================================================================
# ENUMS E CONSTANTES
# ============================================================================

class SessionType(str, Enum):
    """Tipos de sessão disponíveis."""
    INTERACTIVE = "interactive"
    BATCH = "batch" 
    API = "api"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """Status possíveis de uma sessão."""
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    TERMINATED = "terminated"


class MessageType(str, Enum):
    """Tipos de mensagem em conversações."""
    QUERY = "query"
    RESPONSE = "response"
    SYSTEM = "system"
    ERROR = "error"
    DEBUG = "debug"


class ContentFormat(str, Enum):
    """Formatos de conteúdo suportados."""
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CODE = "code"


class ContextType(str, Enum):
    """Tipos de contexto dos agentes."""
    DATA = "data"
    PREFERENCES = "preferences"
    STATE = "state"
    CACHE = "cache"
    LEARNING = "learning"
    EMBEDDINGS = "embeddings"
    ANALYSIS = "analysis"


class EmbeddingType(str, Enum):
    """Tipos de embedding para memória."""
    QUERY = "query"
    RESPONSE = "response"
    CONTEXT = "context"
    SUMMARY = "summary"
    LEARNING = "learning"


# ============================================================================
# DATACLASSES PARA ESTRUTURAS DE DADOS
# ============================================================================

@dataclass
class SessionInfo:
    """Informações de uma sessão de agente."""
    id: UUID = field(default_factory=uuid4)
    session_id: str = ""
    user_id: Optional[str] = None
    agent_name: Optional[str] = None
    session_type: SessionType = SessionType.INTERACTIVE
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Verifica se a sessão está expirada."""
        return datetime.now() > self.expires_at
    
    def extend_expiry(self, hours: int = 24) -> None:
        """Estende o tempo de expiração da sessão."""
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.updated_at = datetime.now()


@dataclass
class ConversationMessage:
    """Estrutura de uma mensagem de conversação."""
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    agent_name: str = ""
    conversation_turn: int = 1
    message_type: MessageType = MessageType.QUERY
    content: str = ""
    content_format: ContentFormat = ContentFormat.TEXT
    processing_time_ms: Optional[int] = None
    token_count: Optional[int] = None
    model_used: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'agent_name': self.agent_name,
            'conversation_turn': self.conversation_turn,
            'message_type': self.message_type.value,
            'content': self.content,
            'content_format': self.content_format.value,
            'processing_time_ms': self.processing_time_ms,
            'token_count': self.token_count,
            'model_used': self.model_used,
            'confidence_score': self.confidence_score,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AgentContext:
    """Estrutura de contexto de um agente."""
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    agent_name: str = ""
    context_type: ContextType = ContextType.DATA
    context_key: str = ""
    context_data: Dict[str, Any] = field(default_factory=dict)
    data_size_bytes: Optional[int] = None
    access_count: int = 0
    priority: int = 5  # 1=highest, 10=lowest
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Verifica se o contexto está expirado."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> None:
        """Registra um acesso ao contexto."""
        self.access_count += 1
        self.last_accessed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'agent_name': self.agent_name,
            'context_type': self.context_type.value,
            'context_key': self.context_key,
            'context_data': self.context_data,
            'data_size_bytes': self.data_size_bytes,
            'access_count': self.access_count,
            'priority': self.priority,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_accessed_at': self.last_accessed_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class MemoryEmbedding:
    """Estrutura de embedding para memória semântica."""
    id: UUID = field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    agent_name: str = ""
    conversation_id: Optional[UUID] = None
    context_id: Optional[UUID] = None
    embedding_type: EmbeddingType = EmbeddingType.QUERY
    source_text: str = ""
    embedding: List[float] = field(default_factory=list)
    similarity_threshold: float = 0.800
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id) if self.session_id else None,
            'agent_name': self.agent_name,
            'conversation_id': str(self.conversation_id) if self.conversation_id else None,
            'context_id': str(self.context_id) if self.context_id else None,
            'embedding_type': self.embedding_type.value,
            'source_text': self.source_text,
            'embedding': self.embedding,
            'similarity_threshold': self.similarity_threshold,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass 
class SimilaritySearchResult:
    """Resultado de busca por similaridade."""
    id: UUID
    source_text: str
    similarity: float
    embedding_type: EmbeddingType
    conversation_id: Optional[UUID] = None
    context_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'id': str(self.id),
            'source_text': self.source_text,
            'similarity': self.similarity,
            'embedding_type': self.embedding_type.value,
            'conversation_id': str(self.conversation_id) if self.conversation_id else None,
            'context_id': str(self.context_id) if self.context_id else None,
            'metadata': self.metadata
        }


# ============================================================================
# CONFIGURAÇÕES PADRÃO
# ============================================================================

class MemoryConfig:
    """Configurações padrão para o sistema de memória."""
    
    # Configurações de sessão
    DEFAULT_SESSION_DURATION_HOURS = 24
    MAX_SESSION_DURATION_HOURS = 24 * 7  # 1 semana
    SESSION_CLEANUP_INTERVAL_HOURS = 6
    
    # Configurações de contexto
    MAX_CONTEXT_SIZE_BYTES = 1024 * 1024  # 1MB
    DEFAULT_CONTEXT_PRIORITY = 5
    MAX_CONTEXT_ACCESS_COUNT = 1000
    
    # Configurações de conversação
    MAX_CONVERSATION_TURNS = 1000
    MAX_MESSAGE_LENGTH = 50000  # caracteres
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    
    # Configurações de embeddings
    EMBEDDING_DIMENSION = 1536  # OpenAI default
    DEFAULT_SIMILARITY_THRESHOLD = 0.800
    MAX_SIMILARITY_RESULTS = 20
    
    # Configurações de cleanup
    EXPIRED_SESSION_RETENTION_DAYS = 30
    ARCHIVED_CONTEXT_RETENTION_DAYS = 7
    LOW_PRIORITY_CONTEXT_CLEANUP_DAYS = 3


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class MemoryError(Exception):
    """Exceção base para erros de memória."""
    pass


class SessionNotFoundError(MemoryError):
    """Exceção para sessão não encontrada."""
    pass


class SessionExpiredError(MemoryError):
    """Exceção para sessão expirada."""
    pass


class ContextNotFoundError(MemoryError):
    """Exceção para contexto não encontrado."""
    pass


class MemoryQuotaExceededError(MemoryError):
    """Exceção para quota de memória excedida."""
    pass


class InvalidEmbeddingError(MemoryError):
    """Exceção para embedding inválido."""
    pass


# ============================================================================
# VALIDADORES
# ============================================================================

def validate_embedding_dimension(embedding: List[float], expected_dim: int = MemoryConfig.EMBEDDING_DIMENSION) -> bool:
    """Valida a dimensão de um embedding."""
    return len(embedding) == expected_dim


def validate_session_id(session_id: str) -> bool:
    """Valida formato de session_id."""
    return bool(session_id and len(session_id) >= 3 and len(session_id) <= 255)


def validate_agent_name(agent_name: str) -> bool:
    """Valida nome do agente."""
    return bool(agent_name and len(agent_name) >= 2 and len(agent_name) <= 100)


def validate_context_key(context_key: str) -> bool:
    """Valida chave de contexto."""
    return bool(context_key and len(context_key) >= 1 and len(context_key) <= 255)


def validate_confidence_score(score: Optional[float]) -> bool:
    """Valida score de confiança."""
    if score is None:
        return True
    return 0.0 <= score <= 1.0


def validate_priority(priority: int) -> bool:
    """Valida prioridade."""
    return 1 <= priority <= 10