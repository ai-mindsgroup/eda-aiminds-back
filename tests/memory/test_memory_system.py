"""
Testes para o sistema de memória dos agentes.

Este módulo contém testes automatizados para validar:
- Persistência de conversações e contexto
- Performance do sistema de memória
- Integridade dos dados
- Funcionalidades de cache e limpeza
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Importações do sistema de memória
try:
    from src.memory import (
        SupabaseMemoryManager,
        MemoryMixin,
        SessionInfo,
        ConversationMessage,
        AgentContext,
        MemoryEmbedding,
        SessionType,
        SessionStatus,
        MessageType,
        ContextType,
        EmbeddingType,
        MemoryConfig
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    pytest.skip("Sistema de memória não disponível", allow_module_level=True)


class TestMemoryTypes:
    """Testes para tipos e estruturas de dados de memória."""
    
    def test_session_info_creation(self):
        """Testa criação de SessionInfo."""
        session = SessionInfo(
            session_id="test_session_123",
            user_id="user_456",
            agent_name="test_agent"
        )
        
        assert session.session_id == "test_session_123"
        assert session.user_id == "user_456"
        assert session.agent_name == "test_agent"
        assert session.session_type == SessionType.INTERACTIVE
        assert session.status == SessionStatus.ACTIVE
        assert not session.is_expired()
    
    def test_session_expiry(self):
        """Testa expiração de sessão."""
        # Sessão expirada
        expired_session = SessionInfo(
            session_id="expired_session",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        assert expired_session.is_expired()
        
        # Sessão válida
        valid_session = SessionInfo(
            session_id="valid_session",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        assert not valid_session.is_expired()
    
    def test_conversation_message_creation(self):
        """Testa criação de ConversationMessage."""
        session_id = uuid4()
        message = ConversationMessage(
            session_id=session_id,
            agent_name="test_agent",
            conversation_turn=1,
            message_type=MessageType.QUERY,
            content="Qual é o resumo dos dados?"
        )
        
        assert message.session_id == session_id
        assert message.agent_name == "test_agent"
        assert message.conversation_turn == 1
        assert message.message_type == MessageType.QUERY
        assert message.content == "Qual é o resumo dos dados?"
        
        # Testa conversão para dict
        message_dict = message.to_dict()
        assert message_dict['agent_name'] == "test_agent"
        assert message_dict['message_type'] == "query"
    
    def test_agent_context_creation(self):
        """Testa criação de AgentContext."""
        session_id = uuid4()
        context = AgentContext(
            session_id=session_id,
            agent_name="test_agent",
            context_type=ContextType.DATA,
            context_key="current_dataset",
            context_data={"file_path": "test.csv", "rows": 1000}
        )
        
        assert context.session_id == session_id
        assert context.agent_name == "test_agent"
        assert context.context_type == ContextType.DATA
        assert context.context_key == "current_dataset"
        assert context.context_data["file_path"] == "test.csv"
        assert context.access_count == 0
        assert not context.is_expired()
        
        # Testa acesso
        context.access()
        assert context.access_count == 1
    
    def test_memory_embedding_creation(self):
        """Testa criação de MemoryEmbedding."""
        session_id = uuid4()
        embedding = MemoryEmbedding(
            session_id=session_id,
            agent_name="test_agent",
            embedding_type=EmbeddingType.QUERY,
            source_text="Como analisar fraudes?",
            embedding=[0.1, 0.2, 0.3] * 512  # 1536 dimensões
        )
        
        assert embedding.session_id == session_id
        assert embedding.agent_name == "test_agent"
        assert embedding.embedding_type == EmbeddingType.QUERY
        assert embedding.source_text == "Como analisar fraudes?"
        assert len(embedding.embedding) == 1536
        assert embedding.similarity_threshold == 0.800


class TestMemoryUtils:
    """Testes para utilitários de memória."""
    
    def test_session_id_generation(self):
        """Testa geração de IDs de sessão."""
        from src.memory.memory_utils import generate_session_id
        
        # Teste com prefixo padrão
        session_id = generate_session_id()
        assert session_id.startswith("session_")
        assert len(session_id) > 20
        
        # Teste com prefixo customizado
        custom_id = generate_session_id("agent_test")
        assert custom_id.startswith("agent_test_")
        
        # Teste sem timestamp
        no_timestamp_id = generate_session_id("test", include_timestamp=False)
        assert no_timestamp_id.startswith("test_")
        assert len(no_timestamp_id.split("_")) == 2
    
    def test_data_size_calculation(self):
        """Testa cálculo de tamanho de dados."""
        from src.memory.memory_utils import calculate_data_size
        
        # Teste com string
        text_size = calculate_data_size("Hello World")
        assert text_size > 0
        
        # Teste com dict
        dict_data = {"key": "value", "number": 123}
        dict_size = calculate_data_size(dict_data)
        assert dict_size > 0
        
        # Teste com lista
        list_data = [1, 2, 3, "test"]
        list_size = calculate_data_size(list_data)
        assert list_size > 0
    
    def test_content_truncation(self):
        """Testa truncamento de conteúdo."""
        from src.memory.memory_utils import truncate_content
        
        # Conteúdo pequeno - não trunca
        short_content = "Este é um conteúdo curto"
        truncated = truncate_content(short_content, max_length=100)
        assert truncated == short_content
        
        # Conteúdo longo - trunca
        long_content = "A" * 1000
        truncated = truncate_content(long_content, max_length=100)
        assert len(truncated) <= 100
        assert "TRUNCADO" in truncated
    
    def test_validation_functions(self):
        """Testa funções de validação."""
        from src.memory.memory_utils import (
            sanitize_agent_name,
            sanitize_session_id,
            validate_context_data
        )
        
        # Sanitização de nome de agente
        clean_name = sanitize_agent_name("Agent-Test_123")
        assert clean_name == "agent-test_123"
        
        # Sanitização de session ID
        clean_session = sanitize_session_id("session@#$%_123")
        assert clean_session == "session_123"
        
        # Validação de dados de contexto
        valid_data = {"key": "value", "number": 123}
        is_valid, error = validate_context_data(valid_data)
        assert is_valid
        assert error is None
        
        # Dados inválidos
        invalid_data = "not a dict"
        is_valid, error = validate_context_data(invalid_data)
        assert not is_valid
        assert error is not None


@pytest.mark.asyncio
class TestSupabaseMemoryManager:
    """Testes para SupabaseMemoryManager."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock do cliente Supabase."""
        with patch('src.memory.supabase_memory.supabase') as mock:
            yield mock
    
    @pytest.fixture
    def memory_manager(self, mock_supabase):
        """Instância de SupabaseMemoryManager para testes."""
        with patch('src.memory.supabase_memory.SUPABASE_URL', 'test_url'), \
             patch('src.memory.supabase_memory.SUPABASE_KEY', 'test_key'):
            return SupabaseMemoryManager("test_agent")
    
    async def test_create_session(self, memory_manager, mock_supabase):
        """Testa criação de sessão."""
        # Mock da resposta do Supabase
        mock_response = Mock()
        mock_response.data = [{
            'id': str(uuid4()),
            'session_id': 'test_session_123',
            'user_id': 'user_456',
            'agent_name': 'test_agent',
            'session_type': 'interactive',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'metadata': {}
        }]
        
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Criar sessão
        session = await memory_manager.create_session(
            session_id="test_session_123",
            user_id="user_456"
        )
        
        assert session.session_id == "test_session_123"
        assert session.user_id == "user_456"
        assert session.agent_name == "test_agent"
        
        # Verificar chamada ao Supabase
        mock_supabase.table.assert_called_with('agent_sessions')
    
    async def test_get_session(self, memory_manager, mock_supabase):
        """Testa recuperação de sessão."""
        # Mock da resposta do Supabase
        mock_response = Mock()
        mock_response.data = [{
            'id': str(uuid4()),
            'session_id': 'test_session_123',
            'user_id': 'user_456',
            'agent_name': 'test_agent',
            'session_type': 'interactive',
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'metadata': {}
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Recuperar sessão
        session = await memory_manager.get_session("test_session_123")
        
        assert session is not None
        assert session.session_id == "test_session_123"
        
        # Verificar chamada ao Supabase
        mock_supabase.table.assert_called_with('agent_sessions')
    
    async def test_get_session_not_found(self, memory_manager, mock_supabase):
        """Testa recuperação de sessão não encontrada."""
        # Mock de resposta vazia
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Tentar recuperar sessão inexistente
        session = await memory_manager.get_session("nonexistent_session")
        
        assert session is None
    
    async def test_save_conversation(self, memory_manager, mock_supabase):
        """Testa salvamento de conversação."""
        # Mock para obter UUID da sessão
        session_uuid = uuid4()
        mock_session_response = Mock()
        mock_session_response.data = [{'id': str(session_uuid)}]
        
        # Mock para obter próximo turn number
        mock_turn_response = Mock()
        mock_turn_response.data = [{'conversation_turn': 1}]
        
        # Mock para inserção da conversação
        mock_insert_response = Mock()
        mock_insert_response.data = [{
            'id': str(uuid4()),
            'session_id': str(session_uuid),
            'agent_name': 'test_agent',
            'conversation_turn': 2,
            'message_type': 'query',
            'content': 'Teste de mensagem',
            'content_format': 'text',
            'metadata': {},
            'timestamp': datetime.now().isoformat()
        }]
        
        # Configurar mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_session_response
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_turn_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        # Salvar conversação
        message = await memory_manager.save_conversation(
            session_id="test_session",
            message_type=MessageType.QUERY,
            content="Teste de mensagem"
        )
        
        assert message.agent_name == "test_agent"
        assert message.content == "Teste de mensagem"
        assert message.conversation_turn == 2
    
    async def test_save_context(self, memory_manager, mock_supabase):
        """Testa salvamento de contexto."""
        # Mock para obter UUID da sessão
        session_uuid = uuid4()
        mock_session_response = Mock()
        mock_session_response.data = [{'id': str(session_uuid)}]
        
        # Mock para inserção do contexto
        mock_insert_response = Mock()
        mock_insert_response.data = [{
            'id': str(uuid4()),
            'session_id': str(session_uuid),
            'agent_name': 'test_agent',
            'context_type': 'data',
            'context_key': 'test_data',
            'context_data': {'key': 'value'},
            'data_size_bytes': 100,
            'access_count': 0,
            'priority': 5,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_accessed_at': datetime.now().isoformat(),
            'metadata': {}
        }]
        
        # Configurar mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_session_response,  # Para _get_session_uuid
            Mock(data=[])           # Para verificar contexto existente
        ]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        # Salvar contexto
        context = await memory_manager.save_context(
            session_id="test_session",
            context_type=ContextType.DATA,
            context_key="test_data",
            context_data={"key": "value"}
        )
        
        assert context.agent_name == "test_agent"
        assert context.context_type == ContextType.DATA
        assert context.context_key == "test_data"
        assert context.context_data == {"key": "value"}


@pytest.mark.asyncio 
class TestMemoryMixin:
    """Testes para MemoryMixin."""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock do memory manager."""
        mock_manager = AsyncMock()
        mock_manager.initialize_session = AsyncMock(return_value="test_session_123")
        mock_manager.add_user_query = AsyncMock()
        mock_manager.add_agent_response = AsyncMock()
        mock_manager.store_data_context = AsyncMock()
        mock_manager.get_recent_context = AsyncMock(return_value={})
        return mock_manager
    
    def test_memory_mixin_initialization(self, mock_memory_manager):
        """Testa inicialização do MemoryMixin."""
        mixin = MemoryMixin(mock_memory_manager)
        
        assert mixin.has_memory
        assert mixin.current_session is None
    
    async def test_init_memory(self, mock_memory_manager):
        """Testa inicialização de memória."""
        mixin = MemoryMixin(mock_memory_manager)
        
        session_id = await mixin.init_memory()
        
        assert session_id == "test_session_123"
        assert mixin.current_session == "test_session_123"
        mock_memory_manager.initialize_session.assert_called_once()
    
    async def test_remember_query(self, mock_memory_manager):
        """Testa lembrança de consulta."""
        mixin = MemoryMixin(mock_memory_manager)
        mixin._current_session_id = "test_session"
        
        success = await mixin.remember_query("Como analisar dados?")
        
        assert success
        mock_memory_manager.add_user_query.assert_called_once_with(
            "Como analisar dados?", "test_session", None
        )
    
    async def test_remember_response(self, mock_memory_manager):
        """Testa lembrança de resposta."""
        mixin = MemoryMixin(mock_memory_manager)
        mixin._current_session_id = "test_session"
        
        success = await mixin.remember_response(
            "Aqui está a análise dos dados...",
            processing_time_ms=1500,
            confidence=0.95
        )
        
        assert success
        mock_memory_manager.add_agent_response.assert_called_once()
    
    async def test_recall_context(self, mock_memory_manager):
        """Testa recuperação de contexto."""
        mock_memory_manager.get_recent_context.return_value = {
            "recent_conversations": [{"type": "query", "content": "teste"}],
            "data_context": {"file": "test.csv"}
        }
        
        mixin = MemoryMixin(mock_memory_manager)
        mixin._current_session_id = "test_session"
        
        context = await mixin.recall_context()
        
        assert "recent_conversations" in context
        assert "data_context" in context
        mock_memory_manager.get_recent_context.assert_called_once_with("test_session", 24)


class TestMemoryPerformance:
    """Testes de performance do sistema de memória."""
    
    def test_memory_config_limits(self):
        """Testa limites de configuração de memória."""
        assert MemoryConfig.MAX_CONTEXT_SIZE_BYTES == 1024 * 1024  # 1MB
        assert MemoryConfig.DEFAULT_SESSION_DURATION_HOURS == 24
        assert MemoryConfig.EMBEDDING_DIMENSION == 1536
        assert MemoryConfig.DEFAULT_SIMILARITY_THRESHOLD == 0.800
    
    def test_large_context_validation(self):
        """Testa validação de contexto grande."""
        from src.memory.memory_utils import validate_context_data
        
        # Contexto dentro do limite
        small_context = {"data": "x" * 1000}
        is_valid, error = validate_context_data(small_context)
        assert is_valid
        
        # Contexto muito grande
        large_context = {"data": "x" * (2 * 1024 * 1024)}  # 2MB
        is_valid, error = validate_context_data(large_context)
        assert not is_valid
        assert "muito grande" in error.lower()
    
    def test_conversation_compression(self):
        """Testa compressão de conversações longas."""
        from src.memory.memory_utils import compress_old_conversations
        
        # Criar muitas mensagens
        messages = []
        for i in range(100):
            message = ConversationMessage(
                agent_name="test_agent",
                conversation_turn=i+1,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                content=f"Mensagem {i+1}"
            )
            messages.append(message)
        
        # Comprimir
        compressed = compress_old_conversations(messages, max_turns=20)
        
        assert len(compressed) <= 20
        assert any("SUMÁRIO" in msg.content for msg in compressed)


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])