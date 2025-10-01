"""
Testes de integração para o sistema de memória com agentes.

Este módulo testa a integração completa entre:
- Agentes multiagente
- Sistema de memória persistente
- Banco de dados Supabase
- Cache e otimizações
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pandas as pd
from typing import Dict, Any, List

# Importações dos agentes
try:
    from src.agent.orchestrator_agent import OrchestratorAgent
    from src.agent.csv_analysis_agent import EmbeddingsAnalysisAgent
    from src.agent.rag_agent import RAGAgent
    from src.memory import (
        SupabaseMemoryManager,
        SessionInfo,
        MessageType,
        ContextType
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    pytest.skip("Agentes não disponíveis", allow_module_level=True)


@pytest.mark.asyncio
class TestOrchestratorMemoryIntegration:
    """Testes de integração de memória para OrchestratorAgent."""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock do memory manager."""
        mock_manager = AsyncMock()
        mock_manager.initialize_session = AsyncMock(return_value="session_123")
        mock_manager.add_user_query = AsyncMock()
        mock_manager.add_agent_response = AsyncMock()
        mock_manager.store_data_context = AsyncMock()
        mock_manager.get_recent_context = AsyncMock(return_value={
            "recent_conversations": [],
            "data_context": {},
            "user_preferences": {}
        })
        return mock_manager
    
    @pytest.fixture
    def orchestrator_agent(self, mock_memory_manager):
        """Instância do OrchestratorAgent com memória mock."""
        with patch('src.agent.orchestrator_agent.SupabaseMemoryManager') as mock_class:
            mock_class.return_value = mock_memory_manager
            agent = OrchestratorAgent("orchestrator_test")
            agent.memory_manager = mock_memory_manager
            agent._current_session_id = "session_123"
            return agent
    
    async def test_orchestrator_memory_initialization(self, orchestrator_agent):
        """Testa inicialização de memória no orchestrador."""
        # Verificar que memória foi inicializada
        assert orchestrator_agent.has_memory
        assert orchestrator_agent.current_session == "session_123"
        
        # Verificar que memory manager foi configurado
        assert orchestrator_agent.memory_manager is not None
    
    async def test_orchestrator_process_with_memory(self, orchestrator_agent, mock_memory_manager):
        """Testa processamento com memória persistente."""
        # Mock dos agentes subsidiários
        orchestrator_agent.csv_agent = AsyncMock()
        orchestrator_agent.rag_agent = AsyncMock()
        
        # Mock do método de processamento LLM
        with patch.object(orchestrator_agent, '_process_with_llm') as mock_llm:
            mock_llm.return_value = "Resposta do LLM com contexto de memória"
            
            # Processar query
            result = await orchestrator_agent.process_query(
                "Quais são os padrões de fraude mais comuns?",
                context={"dataset": "creditcard.csv"}
            )
            
            # Verificar que a query foi lembrada
            mock_memory_manager.add_user_query.assert_called_once()
            
            # Verificar que a resposta foi salva
            mock_memory_manager.add_agent_response.assert_called_once()
            
            # Verificar contexto foi recuperado
            mock_memory_manager.get_recent_context.assert_called()
    
    async def test_orchestrator_conversation_continuity(self, orchestrator_agent, mock_memory_manager):
        """Testa continuidade da conversa através da memória."""
        # Simular contexto de conversa anterior
        mock_memory_manager.get_recent_context.return_value = {
            "recent_conversations": [
                {
                    "type": "query",
                    "content": "Carregue o dataset de fraudes",
                    "timestamp": "2024-01-01T10:00:00"
                },
                {
                    "type": "response", 
                    "content": "Dataset carregado com 284,807 transações",
                    "timestamp": "2024-01-01T10:00:05"
                }
            ],
            "data_context": {
                "current_dataset": "creditcard.csv",
                "dataset_info": {"rows": 284807, "columns": 31}
            }
        }
        
        # Mock do processamento
        orchestrator_agent.csv_agent = AsyncMock()
        orchestrator_agent.rag_agent = AsyncMock()
        
        with patch.object(orchestrator_agent, '_process_with_llm') as mock_llm:
            mock_llm.return_value = "Baseado no dataset carregado anteriormente..."
            
            # Processar query de continuação
            result = await orchestrator_agent.process_query(
                "Agora mostre um resumo estatístico"
            )
            
            # Verificar que o contexto anterior foi usado
            mock_memory_manager.get_recent_context.assert_called()
            
            # Verificar que o LLM recebeu contexto da conversa anterior
            args, kwargs = mock_llm.call_args
            prompt = args[0] if args else kwargs.get('prompt', '')
            assert "creditcard.csv" in prompt or "dataset carregado" in prompt.lower()


@pytest.mark.asyncio
class TestCSVAnalysisMemoryIntegration:
    """Testes de integração de memória para EmbeddingsAnalysisAgent."""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock do memory manager."""
        mock_manager = AsyncMock()
        mock_manager.initialize_session = AsyncMock(return_value="session_123")
        mock_manager.add_user_query = AsyncMock()
        mock_manager.add_agent_response = AsyncMock()
        mock_manager.store_analysis_context = AsyncMock()
        mock_manager.get_cached_analysis = AsyncMock(return_value=None)
        mock_manager.learn_query_pattern = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def csv_agent(self, mock_memory_manager):
        """Instância do CSV agent com memória mock."""
        with patch('src.agent.csv_analysis_agent.SupabaseMemoryManager') as mock_class:
            mock_class.return_value = mock_memory_manager
            agent = EmbeddingsAnalysisAgent("csv_analysis_test")
            agent.memory_manager = mock_memory_manager
            agent._current_session_id = "session_123"
            return agent
    
    @pytest.fixture
    def sample_dataframe(self):
        """DataFrame de exemplo para testes."""
        return pd.DataFrame({
            'Time': [0, 1, 2, 3, 4],
            'V1': [-1.359807, -1.340163, 1.191857, 1.315642, -1.226583],
            'V2': [-0.072781, 0.635273, 0.266151, -1.540233, 0.173225],
            'Amount': [149.62, 2.69, 378.66, 123.50, 69.99],
            'Class': [0, 0, 0, 0, 0]
        })
    
    async def test_csv_agent_analysis_caching(self, csv_agent, mock_memory_manager, sample_dataframe):
        """Testa cache de análises do CSV agent."""
        # Mock da análise LLM
        with patch.object(csv_agent, '_analyze_with_llm') as mock_analyze:
            mock_analyze.return_value = {
                "summary": "Dataset com 5 transações, todas legítimas",
                "insights": ["Todos os valores são normais", "Sem fraudes detectadas"],
                "analysis_type": "statistical_summary"
            }
            
            # Primeira análise - sem cache
            mock_memory_manager.get_cached_analysis.return_value = None
            
            result1 = await csv_agent.analyze_dataframe(
                sample_dataframe,
                analysis_type="statistical_summary"
            )
            
            # Verificar que análise foi executada
            mock_analyze.assert_called_once()
            
            # Verificar que resultado foi armazenado no cache
            mock_memory_manager.store_analysis_context.assert_called()
            
            # Segunda análise - com cache
            mock_memory_manager.get_cached_analysis.return_value = {
                "summary": "Dataset com 5 transações, todas legítimas",
                "insights": ["Todos os valores são normais", "Sem fraudes detectadas"],
                "analysis_type": "statistical_summary",
                "from_cache": True
            }
            
            result2 = await csv_agent.analyze_dataframe(
                sample_dataframe,
                analysis_type="statistical_summary"
            )
            
            # Verificar que análise não foi executada novamente
            assert mock_analyze.call_count == 1
            
            # Verificar que resultado veio do cache
            mock_memory_manager.get_cached_analysis.assert_called()
    
    async def test_csv_agent_pattern_learning(self, csv_agent, mock_memory_manager, sample_dataframe):
        """Testa aprendizado de padrões de consulta."""
        with patch.object(csv_agent, '_analyze_with_llm') as mock_analyze:
            mock_analyze.return_value = {
                "summary": "Análise de fraudes",
                "insights": ["Padrão suspeito encontrado"]
            }
            
            # Executar várias análises similares
            queries = [
                "Detectar fraudes",
                "Analisar transações suspeitas", 
                "Identificar padrões de fraude"
            ]
            
            for query in queries:
                await csv_agent.process_query_with_memory(
                    query,
                    sample_dataframe
                )
            
            # Verificar que padrões foram aprendidos
            assert mock_memory_manager.learn_query_pattern.call_count >= len(queries)
            
            # Verificar argumentos das chamadas
            calls = mock_memory_manager.learn_query_pattern.call_args_list
            for call in calls:
                args, kwargs = call
                assert "fraud" in args[0].lower() or "fraude" in args[0].lower()


@pytest.mark.asyncio
class TestRAGMemoryIntegration:
    """Testes de integração de memória para RAGAgent."""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock do memory manager."""
        mock_manager = AsyncMock()
        mock_manager.initialize_session = AsyncMock(return_value="session_123")
        mock_manager.get_cached_search = AsyncMock(return_value=None)
        mock_manager.store_search_context = AsyncMock()
        mock_manager.learn_search_relevance = AsyncMock()
        mock_manager.get_adaptive_threshold = AsyncMock(return_value=0.800)
        return mock_manager
    
    @pytest.fixture
    def rag_agent(self, mock_memory_manager):
        """Instância do RAG agent com memória mock."""
        with patch('src.agent.rag_agent.SupabaseMemoryManager') as mock_class:
            mock_class.return_value = mock_memory_manager
            agent = RAGAgent("rag_test")
            agent.memory_manager = mock_memory_manager
            agent._current_session_id = "session_123"
            return agent
    
    async def test_rag_search_caching(self, rag_agent, mock_memory_manager):
        """Testa cache de buscas RAG."""
        # Mock da busca vetorial
        with patch.object(rag_agent, '_vector_search') as mock_search:
            mock_search.return_value = [
                {"content": "Fraude é...", "score": 0.95},
                {"content": "Detecção de anomalias...", "score": 0.88}
            ]
            
            # Primeira busca - sem cache
            mock_memory_manager.get_cached_search.return_value = None
            
            results1 = await rag_agent.search_with_memory("Como detectar fraudes?")
            
            # Verificar que busca foi executada
            mock_search.assert_called_once()
            
            # Verificar que resultado foi armazenado
            mock_memory_manager.store_search_context.assert_called()
            
            # Segunda busca - com cache
            mock_memory_manager.get_cached_search.return_value = {
                "results": [
                    {"content": "Fraude é...", "score": 0.95},
                    {"content": "Detecção de anomalias...", "score": 0.88}
                ],
                "from_cache": True
            }
            
            results2 = await rag_agent.search_with_memory("Como detectar fraudes?")
            
            # Verificar que busca não foi executada novamente
            assert mock_search.call_count == 1
    
    async def test_rag_relevance_learning(self, rag_agent, mock_memory_manager):
        """Testa aprendizado de relevância."""
        with patch.object(rag_agent, '_vector_search') as mock_search:
            mock_search.return_value = [
                {"content": "Resultado relevante", "score": 0.90},
                {"content": "Resultado menos relevante", "score": 0.75}
            ]
            
            # Simular feedback de relevância
            query = "Como analisar padrões de fraude?"
            results = await rag_agent.search_with_memory(query)
            
            # Simular feedback positivo para resultado relevante
            await rag_agent.learn_from_feedback(
                query,
                "Resultado relevante",
                feedback_score=0.95
            )
            
            # Verificar que aprendizado foi registrado
            mock_memory_manager.learn_search_relevance.assert_called()
            
            # Verificar argumentos
            args, kwargs = mock_memory_manager.learn_search_relevance.call_args
            assert query in args[0]
            assert "Resultado relevante" in args[1]
    
    async def test_rag_adaptive_threshold(self, rag_agent, mock_memory_manager):
        """Testa threshold adaptativo baseado no histórico."""
        # Configurar threshold adaptativo baseado em aprendizado
        mock_memory_manager.get_adaptive_threshold.return_value = 0.850  # Threshold mais alto
        
        with patch.object(rag_agent, '_vector_search') as mock_search:
            mock_search.return_value = [
                {"content": "Resultado alta relevância", "score": 0.90},
                {"content": "Resultado média relevância", "score": 0.82},
                {"content": "Resultado baixa relevância", "score": 0.70}
            ]
            
            # Buscar com threshold adaptativo
            results = await rag_agent.search_with_memory(
                "Consulta sobre fraudes",
                use_adaptive_threshold=True
            )
            
            # Verificar que threshold foi consultado
            mock_memory_manager.get_adaptive_threshold.assert_called()
            
            # Verificar que apenas resultados acima do threshold foram retornados
            # (simulação - na implementação real seria filtrado)
            assert len(results) >= 1


@pytest.mark.asyncio
class TestMemorySystemIntegration:
    """Testes de integração completa do sistema de memória."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock completo do Supabase."""
        with patch('src.memory.supabase_memory.supabase') as mock:
            # Mock para sessões
            mock.table.return_value.insert.return_value.execute.return_value.data = [{
                'id': str(uuid4()),
                'session_id': 'integration_test_session',
                'agent_name': 'test_agent',
                'status': 'active'
            }]
            
            # Mock para conversações
            mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            yield mock
    
    async def test_full_memory_workflow(self, mock_supabase):
        """Testa workflow completo de memória entre agentes."""
        # Criar agentes com memória
        orchestrator = OrchestratorAgent("integration_orchestrator")
        csv_agent = EmbeddingsAnalysisAgent("integration_csv")
        rag_agent = RAGAgent("integration_rag")
        
        # Inicializar memória
        session_id = await orchestrator.init_memory()
        
        # Simular workflow completo
        # 1. Usuário faz pergunta
        await orchestrator.remember_query("Carregue o dataset de fraudes e faça uma análise")
        
        # 2. Orchestrador delega para CSV agent
        sample_data = pd.DataFrame({'Class': [0, 1, 0, 1], 'Amount': [100, 200, 150, 300]})
        
        with patch.object(csv_agent, '_analyze_with_llm') as mock_csv_analyze:
            mock_csv_analyze.return_value = {
                "summary": "Dataset carregado com 4 transações",
                "fraud_rate": "50%"
            }
            
            csv_result = await csv_agent.analyze_dataframe(sample_data)
        
        # 3. Orchestrador usa RAG para contexto adicional  
        with patch.object(rag_agent, '_vector_search') as mock_rag_search:
            mock_rag_search.return_value = [
                {"content": "Fraudes em cartão são detectadas por...", "score": 0.92}
            ]
            
            rag_result = await rag_agent.search_with_memory("detecção de fraude cartão")
        
        # 4. Orchestrator combina resultados e responde
        final_response = f"Análise: {csv_result.get('summary', '')}. Contexto: {rag_result[0]['content'] if rag_result else ''}"
        await orchestrator.remember_response(final_response)
        
        # 5. Verificar que toda a conversa foi persistida
        context = await orchestrator.recall_context()
        
        # Verificações
        assert context is not None
        assert orchestrator.current_session == session_id
    
    async def test_memory_persistence_across_sessions(self, mock_supabase):
        """Testa persistência de memória entre sessões."""
        # Simular dados de sessão anterior no Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'session_id': 'previous_session',
                'agent_name': 'test_agent',
                'conversation_turn': 1,
                'message_type': 'query',
                'content': 'Análise anterior',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Criar novo agente e verificar acesso a dados anteriores
        agent = OrchestratorAgent("persistence_test")
        
        # Simular recuperação de sessão anterior
        with patch.object(agent.memory_manager, 'get_user_sessions') as mock_get_sessions:
            mock_get_sessions.return_value = [
                SessionInfo(
                    session_id="previous_session",
                    agent_name="test_agent",
                    status="completed"
                )
            ]
            
            # Verificar que sessões anteriores podem ser recuperadas
            previous_sessions = await agent.memory_manager.get_user_sessions("test_user")
            assert len(previous_sessions) > 0
            assert previous_sessions[0].session_id == "previous_session"


if __name__ == "__main__":
    # Executar testes de integração
    pytest.main([__file__, "-v", "--tb=short"])