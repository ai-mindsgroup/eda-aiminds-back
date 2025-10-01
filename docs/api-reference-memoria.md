# API Reference - Sistema de Memória

## 📚 Visão Geral

Esta documentação fornece referência completa da API do sistema de memória persistente para agentes multiagente.

## 🔗 Imports Principais

```python
from src.memory import (
    # Classes principais
    BaseMemoryManager,
    SupabaseMemoryManager,
    MemoryMixin,
    
    # Tipos de dados
    SessionInfo,
    ConversationMessage,
    AgentContext,
    MemoryEmbedding,
    
    # Enums
    SessionType,
    SessionStatus,
    MessageType,
    ContextType,
    EmbeddingType,
    
    # Configurações
    MemoryConfig,
    
    # Utilitários
    generate_session_id,
    calculate_data_size,
    validate_context_data
)
```

---

## 🏗️ Classes Principais

### BaseMemoryManager (Abstract)

Interface abstrata para implementações de memória.

```python
class BaseMemoryManager(ABC):
    """Gerenciador base de memória para agentes."""
    
    def __init__(self, agent_name: str):
        """
        Inicializar gerenciador de memória.
        
        Args:
            agent_name: Nome único do agente
        """
```

#### Métodos Abstratos

```python
@abstractmethod
async def initialize_session(
    self, 
    user_id: Optional[str] = None,
    session_type: SessionType = SessionType.INTERACTIVE,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Inicializar nova sessão de memória."""

@abstractmethod
async def add_user_query(
    self, 
    query: str, 
    session_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> ConversationMessage:
    """Adicionar query do usuário ao histórico."""

@abstractmethod
async def add_agent_response(
    self, 
    response: str, 
    session_id: str,
    processing_time_ms: Optional[int] = None,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ConversationMessage:
    """Adicionar resposta do agente ao histórico."""

@abstractmethod
async def get_recent_context(
    self, 
    session_id: str,
    hours_back: int = 24
) -> Dict[str, Any]:
    """Recuperar contexto recente da sessão."""
```

### SupabaseMemoryManager

Implementação concreta usando Supabase/PostgreSQL.

```python
class SupabaseMemoryManager(BaseMemoryManager):
    """Gerenciador de memória usando Supabase como backend."""
    
    def __init__(self, agent_name: str):
        """
        Inicializar com Supabase.
        
        Args:
            agent_name: Nome único do agente
            
        Raises:
            ConnectionError: Se não conseguir conectar ao Supabase
        """
```

#### Métodos Públicos

```python
async def create_session(
    self,
    session_id: str,
    user_id: Optional[str] = None,
    session_type: SessionType = SessionType.INTERACTIVE,
    expires_in_hours: int = 24,
    metadata: Optional[Dict[str, Any]] = None
) -> SessionInfo:
    """
    Criar nova sessão.
    
    Args:
        session_id: ID único da sessão
        user_id: ID do usuário (opcional)
        session_type: Tipo da sessão
        expires_in_hours: TTL da sessão
        metadata: Metadados adicionais
        
    Returns:
        SessionInfo: Informações da sessão criada
        
    Raises:
        ValueError: Se session_id já existe
        DatabaseError: Se falhar ao criar no banco
    """

async def get_session(self, session_id: str) -> Optional[SessionInfo]:
    """
    Recuperar sessão por ID.
    
    Args:
        session_id: ID da sessão
        
    Returns:
        SessionInfo ou None se não encontrada
    """

async def save_conversation(
    self,
    session_id: str,
    message_type: MessageType,
    content: str,
    content_format: str = "text",
    processing_time_ms: Optional[int] = None,
    confidence_score: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ConversationMessage:
    """
    Salvar mensagem de conversação.
    
    Args:
        session_id: ID da sessão
        message_type: Tipo da mensagem (QUERY, RESPONSE, etc.)
        content: Conteúdo da mensagem
        content_format: Formato do conteúdo (text, json, html)
        processing_time_ms: Tempo de processamento em ms
        confidence_score: Score de confiança (0.0-1.0)
        metadata: Metadados adicionais
        
    Returns:
        ConversationMessage: Mensagem salva
    """

async def save_context(
    self,
    session_id: str,
    context_type: ContextType,
    context_key: str,
    context_data: Dict[str, Any],
    priority: int = 5,
    expires_in_hours: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AgentContext:
    """
    Salvar contexto do agente.
    
    Args:
        session_id: ID da sessão
        context_type: Tipo do contexto
        context_key: Chave única do contexto
        context_data: Dados do contexto
        priority: Prioridade (1-10, maior = mais importante)
        expires_in_hours: TTL do contexto
        metadata: Metadados adicionais
        
    Returns:
        AgentContext: Contexto salvo
    """

async def get_context(
    self,
    session_id: str,
    context_type: ContextType,
    context_key: str
) -> Optional[AgentContext]:
    """
    Recuperar contexto específico.
    
    Args:
        session_id: ID da sessão
        context_type: Tipo do contexto
        context_key: Chave do contexto
        
    Returns:
        AgentContext ou None se não encontrado
    """

async def save_embedding(
    self,
    session_id: str,
    embedding_type: EmbeddingType,
    source_text: str,
    embedding: List[float],
    similarity_threshold: float = 0.800,
    metadata: Optional[Dict[str, Any]] = None
) -> MemoryEmbedding:
    """
    Salvar embedding para busca semântica.
    
    Args:
        session_id: ID da sessão
        embedding_type: Tipo do embedding
        source_text: Texto fonte
        embedding: Vetor de embedding (1536 dimensões)
        similarity_threshold: Threshold de similaridade
        metadata: Metadados adicionais
        
    Returns:
        MemoryEmbedding: Embedding salvo
        
    Raises:
        ValueError: Se embedding não tem 1536 dimensões
    """

async def search_similar_embeddings(
    self,
    session_id: str,
    query_embedding: List[float],
    embedding_type: Optional[EmbeddingType] = None,
    similarity_threshold: float = 0.800,
    max_results: int = 10
) -> List[MemoryEmbedding]:
    """
    Buscar embeddings similares.
    
    Args:
        session_id: ID da sessão
        query_embedding: Embedding da query (1536 dimensões)
        embedding_type: Filtrar por tipo de embedding
        similarity_threshold: Threshold mínimo de similaridade
        max_results: Máximo de resultados
        
    Returns:
        Lista de embeddings similares ordenados por similaridade
    """

async def cleanup_expired_data(self, session_id: Optional[str] = None) -> Dict[str, int]:
    """
    Limpar dados expirados.
    
    Args:
        session_id: Limpar apenas esta sessão (None = todas)
        
    Returns:
        Dicionário com contadores do que foi removido
    """
```

### MemoryMixin

Mixin para integrar memória em agentes.

```python
class MemoryMixin:
    """Mixin para adicionar capacidades de memória a agentes."""
    
    def __init__(self, memory_manager: Optional[BaseMemoryManager] = None):
        """
        Inicializar mixin de memória.
        
        Args:
            memory_manager: Gerenciador de memória (cria novo se None)
        """
```

#### Propriedades

```python
@property
def has_memory(self) -> bool:
    """Verificar se memória está disponível."""

@property  
def current_session(self) -> Optional[str]:
    """Obter ID da sessão atual."""

@property
def memory_manager(self) -> Optional[BaseMemoryManager]:
    """Obter gerenciador de memória."""
```

#### Métodos Públicos

```python
async def init_memory(
    self,
    user_id: Optional[str] = None,
    session_type: SessionType = SessionType.INTERACTIVE,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Inicializar memória do agente.
    
    Args:
        user_id: ID do usuário
        session_type: Tipo da sessão
        metadata: Metadados da sessão
        
    Returns:
        ID da sessão criada
    """

async def remember_query(
    self,
    query: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Lembrar query do usuário.
    
    Args:
        query: Query do usuário
        metadata: Metadados adicionais
        
    Returns:
        True se salvou com sucesso
    """

async def remember_response(
    self,
    response: str,
    processing_time_ms: Optional[int] = None,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Lembrar resposta do agente.
    
    Args:
        response: Resposta do agente
        processing_time_ms: Tempo de processamento
        confidence: Score de confiança (0.0-1.0)
        metadata: Metadados adicionais
        
    Returns:
        True se salvou com sucesso
    """

async def recall_context(self, hours_back: int = 24) -> Dict[str, Any]:
    """
    Recuperar contexto da conversa.
    
    Args:
        hours_back: Quantas horas voltar no histórico
        
    Returns:
        Dicionário com contexto da conversa
    """

async def store_data_context(
    self,
    context_key: str,
    context_data: Dict[str, Any],
    context_type: ContextType = ContextType.DATA,
    expires_in_hours: Optional[int] = None
) -> bool:
    """
    Armazenar contexto de dados.
    
    Args:
        context_key: Chave única do contexto
        context_data: Dados a armazenar
        context_type: Tipo do contexto
        expires_in_hours: TTL do contexto
        
    Returns:
        True se salvou com sucesso
    """
```

---

## 📊 Tipos de Dados

### SessionInfo

```python
@dataclass
class SessionInfo:
    """Informações de uma sessão de memória."""
    
    session_id: str
    user_id: Optional[str] = None
    agent_name: Optional[str] = None
    session_type: SessionType = SessionType.INTERACTIVE
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Verificar se sessão expirou."""
        
    def time_until_expiry(self) -> Optional[timedelta]:
        """Tempo até expiração."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
```

### ConversationMessage

```python
@dataclass
class ConversationMessage:
    """Mensagem de conversação entre usuário e agente."""
    
    session_id: UUID
    agent_name: str
    conversation_turn: int
    message_type: MessageType
    content: str
    content_format: str = "text"
    processing_time_ms: Optional[int] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
        
    def is_user_message(self) -> bool:
        """Verificar se é mensagem do usuário."""
        
    def is_agent_message(self) -> bool:
        """Verificar se é mensagem do agente."""
```

### AgentContext

```python
@dataclass
class AgentContext:
    """Contexto armazenado pelo agente."""
    
    session_id: UUID
    agent_name: str
    context_type: ContextType
    context_key: str
    context_data: Dict[str, Any]
    data_size_bytes: Optional[int] = None
    access_count: int = 0
    priority: int = 5
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def access(self) -> None:
        """Registrar acesso ao contexto."""
        
    def is_expired(self) -> bool:
        """Verificar se contexto expirou."""
        
    def size_mb(self) -> float:
        """Tamanho em megabytes."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
```

### MemoryEmbedding

```python
@dataclass
class MemoryEmbedding:
    """Embedding armazenado para busca semântica."""
    
    session_id: UUID
    agent_name: str
    embedding_type: EmbeddingType
    source_text: str
    embedding: List[float]
    source_hash: Optional[str] = None
    similarity_threshold: float = 0.800
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validar dimensões do embedding."""
        
    def calculate_similarity(self, other_embedding: List[float]) -> float:
        """Calcular similaridade com outro embedding."""
        
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário."""
```

---

## 🏷️ Enums

### SessionType

```python
class SessionType(str, Enum):
    """Tipos de sessão de memória."""
    
    INTERACTIVE = "interactive"    # Sessão interativa normal
    BATCH = "batch"               # Processamento em lote
    BACKGROUND = "background"     # Processamento em background
```

### SessionStatus

```python
class SessionStatus(str, Enum):
    """Status de uma sessão."""
    
    ACTIVE = "active"           # Sessão ativa
    COMPLETED = "completed"     # Sessão completada normalmente
    EXPIRED = "expired"         # Sessão expirou por tempo
    TERMINATED = "terminated"   # Sessão terminada forçadamente
```

### MessageType

```python
class MessageType(str, Enum):
    """Tipos de mensagem na conversação."""
    
    QUERY = "query"         # Query/pergunta do usuário
    RESPONSE = "response"   # Resposta do agente
    SYSTEM = "system"       # Mensagem do sistema
    ERROR = "error"         # Mensagem de erro
```

### ContextType

```python
class ContextType(str, Enum):
    """Tipos de contexto armazenado."""
    
    DATA = "data"                           # Dados/datasets carregados
    USER_PREFERENCE = "user_preference"     # Preferências do usuário
    ANALYSIS_CACHE = "analysis_cache"       # Cache de análises
    SEARCH_CACHE = "search_cache"           # Cache de buscas
    LEARNING_PATTERN = "learning_pattern"   # Padrões aprendidos
```

### EmbeddingType

```python
class EmbeddingType(str, Enum):
    """Tipos de embedding."""
    
    QUERY = "query"         # Embedding de query
    RESPONSE = "response"   # Embedding de resposta
    CONTEXT = "context"     # Embedding de contexto
    DOCUMENT = "document"   # Embedding de documento
```

---

## ⚙️ Configurações

### MemoryConfig

```python
class MemoryConfig:
    """Configurações do sistema de memória."""
    
    # Limites de tamanho
    MAX_CONTEXT_SIZE_BYTES: int = 1024 * 1024  # 1MB
    MAX_CONVERSATION_TURNS: int = 1000
    MAX_EMBEDDINGS_PER_SESSION: int = 10000
    
    # TTL padrão
    DEFAULT_SESSION_DURATION_HOURS: int = 24
    DEFAULT_CONTEXT_TTL_HOURS: int = 48
    DEFAULT_EMBEDDING_TTL_HOURS: int = 72
    
    # Embedding
    EMBEDDING_DIMENSION: int = 1536
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.800
    MIN_SIMILARITY_THRESHOLD: float = 0.500
    MAX_SIMILARITY_THRESHOLD: float = 0.999
    
    # Performance
    MAX_RECENT_CONVERSATIONS: int = 50
    CACHE_SIZE_LIMIT: int = 100
    CLEANUP_BATCH_SIZE: int = 1000
    
    # Validação
    MAX_SESSION_ID_LENGTH: int = 255
    MAX_AGENT_NAME_LENGTH: int = 100
    MAX_CONTENT_LENGTH: int = 1000000  # 1M chars
```

---

## 🛠️ Utilitários

### Funções de Utilidade

```python
def generate_session_id(prefix: str = "session", include_timestamp: bool = True) -> str:
    """
    Gerar ID único de sessão.
    
    Args:
        prefix: Prefixo do ID
        include_timestamp: Se deve incluir timestamp
        
    Returns:
        ID único da sessão
    """

def calculate_data_size(data: Any) -> int:
    """
    Calcular tamanho dos dados em bytes.
    
    Args:
        data: Dados para calcular tamanho
        
    Returns:
        Tamanho em bytes
    """

def validate_context_data(data: Any) -> Tuple[bool, Optional[str]]:
    """
    Validar dados de contexto.
    
    Args:
        data: Dados para validar
        
    Returns:
        (é_válido, mensagem_erro)
    """

def sanitize_agent_name(name: str) -> str:
    """
    Sanitizar nome do agente.
    
    Args:
        name: Nome a sanitizar
        
    Returns:
        Nome sanitizado
    """

def sanitize_session_id(session_id: str) -> str:
    """
    Sanitizar ID da sessão.
    
    Args:
        session_id: ID a sanitizar
        
    Returns:
        ID sanitizado
    """

def truncate_content(content: str, max_length: int = 10000) -> str:
    """
    Truncar conteúdo se muito longo.
    
    Args:
        content: Conteúdo a truncar
        max_length: Tamanho máximo
        
    Returns:
        Conteúdo truncado
    """

async def compress_old_conversations(
    messages: List[ConversationMessage], 
    max_turns: int = 50
) -> List[ConversationMessage]:
    """
    Comprimir conversações antigas em sumários.
    
    Args:
        messages: Lista de mensagens
        max_turns: Máximo de turnos a manter
        
    Returns:
        Lista comprimida com sumários
    """

async def cleanup_expired_sessions(
    memory_manager: BaseMemoryManager,
    batch_size: int = 100
) -> int:
    """
    Limpar sessões expiradas.
    
    Args:
        memory_manager: Gerenciador de memória
        batch_size: Tamanho do lote para processar
        
    Returns:
        Número de sessões removidas
    """
```

---

## ❌ Exceções

### MemoryError

```python
class MemoryError(Exception):
    """Erro base do sistema de memória."""

class SessionNotFoundError(MemoryError):
    """Sessão não encontrada."""

class ContextTooLargeError(MemoryError):
    """Contexto muito grande para armazenar."""

class InvalidEmbeddingError(MemoryError):
    """Embedding inválido (dimensão incorreta)."""

class DatabaseConnectionError(MemoryError):
    """Erro de conexão com banco de dados."""

class SessionExpiredError(MemoryError):
    """Sessão expirou."""
```

---

## 📈 Métricas e Monitoring

### Interface de Métricas

```python
class MemoryMetrics:
    """Métricas do sistema de memória."""
    
    @staticmethod
    async def get_session_stats(memory_manager: BaseMemoryManager) -> Dict[str, Any]:
        """Estatísticas de sessões."""
        
    @staticmethod
    async def get_performance_metrics(memory_manager: BaseMemoryManager) -> Dict[str, Any]:
        """Métricas de performance."""
        
    @staticmethod
    async def get_storage_usage(memory_manager: BaseMemoryManager) -> Dict[str, Any]:
        """Uso de armazenamento."""
```

### Exemplo de Uso

```python
from src.memory import SupabaseMemoryManager, MemoryMetrics

# Criar gerenciador
memory_manager = SupabaseMemoryManager("my_agent")

# Obter métricas
stats = await MemoryMetrics.get_session_stats(memory_manager)
print(f"Sessões ativas: {stats['active_sessions']}")
print(f"Total de conversações: {stats['total_conversations']}")

performance = await MemoryMetrics.get_performance_metrics(memory_manager)
print(f"Tempo médio de resposta: {performance['avg_response_time_ms']}ms")
print(f"Cache hit rate: {performance['cache_hit_rate']:.2%}")
```

---

## 🔗 Links Relacionados

- **Arquitetura**: [sistema-memoria-arquitetura.md](./sistema-memoria-arquitetura.md)
- **Guia de Desenvolvimento**: [guia-desenvolvimento-memoria.md](./guia-desenvolvimento-memoria.md)
- **Testes**: [../tests/memory/README.md](../tests/memory/README.md)
- **Migrations**: [../migrations/0005_agent_memory_tables.sql](../migrations/0005_agent_memory_tables.sql)

---

**Versão da API**: 1.0.0  
**Última atualização**: Janeiro 2025