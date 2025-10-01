"""
Testes de performance e stress para o sistema de memória.

Este módulo contém testes para validar:
- Performance com grandes volumes de dados
- Stress testing com múltiplas sessões simultâneas
- Otimizações de cache e embedding
- Limpeza automática de dados antigos
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch, AsyncMock
import random
import string
from typing import List, Dict, Any

# Importações do sistema de memória
try:
    from src.memory import (
        SupabaseMemoryManager,
        MemoryMixin,
        SessionInfo,
        ConversationMessage,
        AgentContext,
        MemoryEmbedding,
        MemoryConfig,
        MessageType,
        ContextType,
        EmbeddingType
    )
    from src.memory.memory_utils import (
        generate_session_id,
        calculate_data_size,
        compress_old_conversations,
        cleanup_expired_sessions
    )
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    pytest.skip("Sistema de memória não disponível", allow_module_level=True)


class TestMemoryPerformance:
    """Testes de performance básica do sistema de memória."""
    
    def test_session_creation_performance(self):
        """Testa performance de criação de sessões."""
        start_time = time.time()
        
        # Criar múltiplas sessões
        sessions = []
        for i in range(100):
            session = SessionInfo(
                session_id=f"perf_session_{i}",
                user_id=f"user_{i}",
                agent_name="performance_agent"
            )
            sessions.append(session)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verificar que criação é rápida (< 100ms para 100 sessões)
        assert creation_time < 0.1
        assert len(sessions) == 100
        
        print(f"Criação de 100 sessões: {creation_time:.4f}s")
    
    def test_conversation_message_performance(self):
        """Testa performance de criação de mensagens de conversação."""
        session_id = uuid4()
        
        start_time = time.time()
        
        # Criar muitas mensagens
        messages = []
        for i in range(1000):
            message = ConversationMessage(
                session_id=session_id,
                agent_name="perf_agent",
                conversation_turn=i+1,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                content=f"Mensagem de teste número {i+1} com conteúdo variado"
            )
            messages.append(message)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verificar performance (< 500ms para 1000 mensagens)
        assert creation_time < 0.5
        assert len(messages) == 1000
        
        print(f"Criação de 1000 mensagens: {creation_time:.4f}s")
    
    def test_context_data_size_calculation(self):
        """Testa performance de cálculo de tamanho de dados."""
        # Criar contextos de diferentes tamanhos
        contexts = {
            "small": {"key": "value"},
            "medium": {"data": "x" * 1000, "numbers": list(range(100))},
            "large": {"content": "y" * 10000, "array": list(range(1000))}
        }
        
        start_time = time.time()
        
        sizes = {}
        for name, context_data in contexts.items():
            size = calculate_data_size(context_data)
            sizes[name] = size
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Verificar que cálculo é rápido
        assert calculation_time < 0.01
        
        # Verificar que tamanhos fazem sentido
        assert sizes["small"] < sizes["medium"] < sizes["large"]
        
        print(f"Cálculo de tamanhos: {calculation_time:.4f}s")
        print(f"Tamanhos: {sizes}")
    
    def test_conversation_compression_performance(self):
        """Testa performance de compressão de conversações."""
        # Criar muitas mensagens para comprimir
        session_id = uuid4()
        messages = []
        
        for i in range(500):
            message = ConversationMessage(
                session_id=session_id,
                agent_name="compress_agent",
                conversation_turn=i+1,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                content=f"Esta é uma mensagem longa de teste número {i+1} " + "x" * random.randint(50, 200)
            )
            messages.append(message)
        
        start_time = time.time()
        
        # Comprimir para 50 mensagens
        compressed = compress_old_conversations(messages, max_turns=50)
        
        end_time = time.time()
        compression_time = end_time - start_time
        
        # Verificar performance e resultado
        assert compression_time < 1.0  # < 1 segundo
        assert len(compressed) <= 50
        
        # Verificar que sumário foi criado
        has_summary = any("SUMÁRIO" in msg.content for msg in compressed)
        assert has_summary
        
        print(f"Compressão de 500 → 50 mensagens: {compression_time:.4f}s")


@pytest.mark.asyncio
class TestMemoryStress:
    """Testes de stress para o sistema de memória."""
    
    @pytest.fixture
    def mock_supabase_high_load(self):
        """Mock do Supabase otimizado para testes de alta carga."""
        with patch('src.memory.supabase_memory.supabase') as mock:
            # Simular resposta rápida
            mock.table.return_value.insert.return_value.execute.return_value.data = [{'id': str(uuid4())}]
            mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{'id': str(uuid4())}]
            
            # Simular latência baixa
            def fast_response(*args, **kwargs):
                return Mock(data=[{'id': str(uuid4())}])
            
            mock.table.return_value.insert.return_value.execute = fast_response
            
            yield mock
    
    async def test_concurrent_sessions(self, mock_supabase_high_load):
        """Testa criação de sessões concorrentes."""
        memory_manager = SupabaseMemoryManager("stress_agent")
        
        async def create_session_task(session_num):
            """Task para criar uma sessão."""
            session_id = f"stress_session_{session_num}"
            try:
                session = await memory_manager.create_session(
                    session_id=session_id,
                    user_id=f"stress_user_{session_num}"
                )
                return session_id, True
            except Exception as e:
                return session_id, False
        
        start_time = time.time()
        
        # Criar 50 sessões simultaneamente
        tasks = [create_session_task(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar resultados
        successful = sum(1 for result in results if isinstance(result, tuple) and result[1])
        
        print(f"Criação concorrente de 50 sessões: {total_time:.4f}s")
        print(f"Sucessos: {successful}/50")
        
        # Aceitar pelo menos 80% de sucesso em teste de stress
        assert successful >= 40
        assert total_time < 10.0  # Deve completar em menos de 10s
    
    async def test_high_volume_conversations(self, mock_supabase_high_load):
        """Testa salvamento de alto volume de conversações."""
        memory_manager = SupabaseMemoryManager("volume_agent")
        
        # Criar sessão
        session_id = "high_volume_session"
        await memory_manager.create_session(session_id=session_id, user_id="volume_user")
        
        async def save_conversation_task(turn_num):
            """Task para salvar uma conversação."""
            try:
                message = await memory_manager.save_conversation(
                    session_id=session_id,
                    message_type=MessageType.QUERY if turn_num % 2 == 0 else MessageType.RESPONSE,
                    content=f"Mensagem de alto volume número {turn_num}"
                )
                return turn_num, True
            except Exception as e:
                return turn_num, False
        
        start_time = time.time()
        
        # Salvar 200 mensagens simultaneamente
        tasks = [save_conversation_task(i) for i in range(200)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar resultados
        successful = sum(1 for result in results if isinstance(result, tuple) and result[1])
        
        print(f"Salvamento de 200 conversações: {total_time:.4f}s")
        print(f"Sucessos: {successful}/200")
        
        # Aceitar pelo menos 80% de sucesso
        assert successful >= 160
        assert total_time < 15.0
    
    async def test_memory_mixin_stress(self, mock_supabase_high_load):
        """Testa MemoryMixin sob stress."""
        memory_manager = SupabaseMemoryManager("mixin_stress_agent")
        mixin = MemoryMixin(memory_manager)
        
        # Inicializar memória
        await mixin.init_memory()
        
        async def memory_operation_task(op_num):
            """Task para operação de memória."""
            try:
                if op_num % 3 == 0:
                    # Lembrar query
                    success = await mixin.remember_query(f"Query de stress {op_num}")
                elif op_num % 3 == 1:
                    # Lembrar resposta
                    success = await mixin.remember_response(
                        f"Resposta de stress {op_num}",
                        processing_time_ms=random.randint(100, 1000)
                    )
                else:
                    # Recuperar contexto
                    context = await mixin.recall_context()
                    success = context is not None
                
                return op_num, success
            except Exception as e:
                return op_num, False
        
        start_time = time.time()
        
        # Executar 150 operações mistas
        tasks = [memory_operation_task(i) for i in range(150)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar resultados
        successful = sum(1 for result in results if isinstance(result, tuple) and result[1])
        
        print(f"150 operações mistas de memória: {total_time:.4f}s")
        print(f"Sucessos: {successful}/150")
        
        # Aceitar pelo menos 85% de sucesso
        assert successful >= 125
        assert total_time < 20.0


class TestMemoryOptimization:
    """Testes para otimizações do sistema de memória."""
    
    def test_embedding_dimension_validation(self):
        """Testa validação de dimensões de embedding."""
        session_id = uuid4()
        
        # Embedding com dimensão correta
        valid_embedding = MemoryEmbedding(
            session_id=session_id,
            agent_name="test_agent",
            embedding_type=EmbeddingType.QUERY,
            source_text="Texto de teste",
            embedding=[0.1] * MemoryConfig.EMBEDDING_DIMENSION
        )
        
        assert len(valid_embedding.embedding) == MemoryConfig.EMBEDDING_DIMENSION
        
        # Embedding com dimensão incorreta
        with pytest.raises(ValueError):
            invalid_embedding = MemoryEmbedding(
                session_id=session_id,
                agent_name="test_agent",
                embedding_type=EmbeddingType.QUERY,
                source_text="Texto de teste",
                embedding=[0.1] * 512  # Dimensão incorreta
            )
    
    def test_context_size_limits(self):
        """Testa limites de tamanho de contexto."""
        from src.memory.memory_utils import validate_context_data
        
        # Contexto pequeno - válido
        small_context = {"key": "value"}
        is_valid, error = validate_context_data(small_context)
        assert is_valid
        assert error is None
        
        # Contexto no limite - válido
        limit_context = {"data": "x" * (MemoryConfig.MAX_CONTEXT_SIZE_BYTES - 100)}
        is_valid, error = validate_context_data(limit_context)
        assert is_valid
        
        # Contexto muito grande - inválido
        large_context = {"data": "x" * (MemoryConfig.MAX_CONTEXT_SIZE_BYTES + 1000)}
        is_valid, error = validate_context_data(large_context)
        assert not is_valid
        assert "muito grande" in error.lower()
    
    def test_session_expiry_optimization(self):
        """Testa otimização de expiração de sessões."""
        now = datetime.now()
        
        # Sessão que expira em 1 hora - válida
        valid_session = SessionInfo(
            session_id="valid_session",
            expires_at=now + timedelta(hours=1)
        )
        assert not valid_session.is_expired()
        
        # Sessão que expirou há 1 hora - inválida
        expired_session = SessionInfo(
            session_id="expired_session", 
            expires_at=now - timedelta(hours=1)
        )
        assert expired_session.is_expired()
        
        # Sessão que expira em poucos minutos - ainda válida mas próxima
        almost_expired = SessionInfo(
            session_id="almost_expired",
            expires_at=now + timedelta(minutes=5)
        )
        assert not almost_expired.is_expired()
    
    def test_conversation_turn_optimization(self):
        """Testa otimização de turnos de conversação."""
        session_id = uuid4()
        
        # Criar mensagens com turnos sequenciais
        messages = []
        for i in range(10):
            message = ConversationMessage(
                session_id=session_id,
                agent_name="test_agent",
                conversation_turn=i+1,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                content=f"Mensagem {i+1}"
            )
            messages.append(message)
        
        # Verificar ordem sequencial
        turns = [msg.conversation_turn for msg in messages]
        assert turns == list(range(1, 11))
        
        # Verificar alternância de tipos
        types = [msg.message_type for msg in messages]
        expected_types = [MessageType.QUERY, MessageType.RESPONSE] * 5
        assert types == expected_types


class TestMemoryCleanup:
    """Testes para limpeza automática de memória."""
    
    def test_expired_session_cleanup(self):
        """Testa limpeza de sessões expiradas."""
        now = datetime.now()
        
        # Criar sessões mistas (válidas e expiradas)
        sessions = [
            SessionInfo(
                session_id="valid_1",
                expires_at=now + timedelta(hours=1)
            ),
            SessionInfo(
                session_id="expired_1",
                expires_at=now - timedelta(hours=1)
            ),
            SessionInfo(
                session_id="valid_2", 
                expires_at=now + timedelta(hours=2)
            ),
            SessionInfo(
                session_id="expired_2",
                expires_at=now - timedelta(minutes=30)
            )
        ]
        
        # Filtrar sessões válidas
        valid_sessions = [s for s in sessions if not s.is_expired()]
        expired_sessions = [s for s in sessions if s.is_expired()]
        
        assert len(valid_sessions) == 2
        assert len(expired_sessions) == 2
        
        # Verificar IDs corretos
        valid_ids = {s.session_id for s in valid_sessions}
        expired_ids = {s.session_id for s in expired_sessions}
        
        assert valid_ids == {"valid_1", "valid_2"}
        assert expired_ids == {"expired_1", "expired_2"}
    
    def test_old_conversation_compression(self):
        """Testa compressão de conversações antigas."""
        session_id = uuid4()
        
        # Criar muitas mensagens antigas
        old_messages = []
        for i in range(100):
            # Mensagens de uma semana atrás
            timestamp = datetime.now() - timedelta(days=7, hours=i)
            message = ConversationMessage(
                session_id=session_id,
                agent_name="cleanup_agent",
                conversation_turn=i+1,
                message_type=MessageType.QUERY if i % 2 == 0 else MessageType.RESPONSE,
                content=f"Mensagem antiga {i+1}",
                timestamp=timestamp
            )
            old_messages.append(message)
        
        # Comprimir para as 20 mais recentes
        compressed = compress_old_conversations(old_messages, max_turns=20)
        
        # Verificar resultado
        assert len(compressed) <= 20
        
        # Verificar que há um sumário das mensagens antigas
        has_summary = any("SUMÁRIO" in msg.content for msg in compressed)
        assert has_summary
        
        # Verificar que as mensagens mais recentes foram preservadas
        recent_turns = [msg.conversation_turn for msg in compressed if "SUMÁRIO" not in msg.content]
        assert max(recent_turns) == 100  # Última mensagem preservada
    
    def test_context_access_tracking(self):
        """Testa rastreamento de acesso a contexto."""
        session_id = uuid4()
        
        # Criar contexto
        context = AgentContext(
            session_id=session_id,
            agent_name="tracking_agent",
            context_type=ContextType.USER_PREFERENCE,
            context_key="language_preference",
            context_data={"language": "pt-BR", "format": "detailed"}
        )
        
        # Verificar estado inicial
        assert context.access_count == 0
        assert context.last_accessed_at is None
        
        # Acessar contexto
        initial_time = context.last_accessed_at
        context.access()
        
        # Verificar que acesso foi registrado
        assert context.access_count == 1
        assert context.last_accessed_at != initial_time
        
        # Acessar novamente
        context.access()
        assert context.access_count == 2


if __name__ == "__main__":
    # Executar testes de performance
    pytest.main([__file__, "-v", "--tb=short", "-s"])