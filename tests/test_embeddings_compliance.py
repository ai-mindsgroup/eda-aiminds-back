"""Testes de conformidade para garantir regra embeddings-only.

Este módulo testa que todos os agentes de resposta a consultas
seguem a regra: APENAS a tabela embeddings pode ser acessada.
Agentes de resposta NÃO podem acessar CSV diretamente.
"""
import pytest
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.data_processor import DataProcessor, UnauthorizedCSVAccessError
from src.data.data_loader import DataLoader, UnauthorizedCSVAccessError as DataLoaderUnauthorizedError
from src.tools.python_analyzer import PythonDataAnalyzer, UnauthorizedCSVAccessError as AnalyzerUnauthorizedError
from src.agent.csv_analysis_agent import EmbeddingsAnalysisAgent


class TestEmbeddingsCompliance:
    """Suite de testes para validar conformidade embeddings-only."""
    
    def test_data_processor_blocks_unauthorized_csv_access(self):
        """DataProcessor deve bloquear acesso CSV para agentes não autorizados."""
        
        # Agentes não autorizados devem ser bloqueados na inicialização
        unauthorized_agents = [
            'analysis_agent',
            'orchestrator_agent', 
            'rag_agent',
            'unknown_caller'
        ]
        
        for agent in unauthorized_agents:
            with pytest.raises(UnauthorizedCSVAccessError) as exc_info:
                processor = DataProcessor(caller_agent=agent)
            
            assert "VIOLAÇÃO DE CONFORMIDADE DETECTADA" in str(exc_info.value)
            assert agent in str(exc_info.value)
    
    def test_data_processor_allows_authorized_csv_access(self):
        """DataProcessor deve permitir acesso CSV para agentes autorizados."""
        
        # Agentes autorizados devem ter acesso
        authorized_agents = [
            'ingestion_agent',
            'data_loading_system',
            'test_system'
        ]
        
        for agent in authorized_agents:
            processor = DataProcessor(caller_agent=agent)
            
            # Não deve lançar exceção na validação
            try:
                processor._validate_csv_access_authorization()
            except UnauthorizedCSVAccessError:
                pytest.fail(f"Agente autorizado {agent} foi bloqueado incorretamente")
    
    def test_data_loader_blocks_unauthorized_csv_access(self):
        """DataLoader deve bloquear acesso CSV para agentes não autorizados."""
        
        unauthorized_agents = [
            'analysis_agent',
            'rag_agent',
            'unknown_caller'
        ]
        
        for agent in unauthorized_agents:
            loader = DataLoader(caller_agent=agent)
            
            with pytest.raises(DataLoaderUnauthorizedError) as exc_info:
                loader.load_from_file("dummy_file.csv")
            
            assert "VIOLAÇÃO DE CONFORMIDADE DETECTADA" in str(exc_info.value)
            assert agent in str(exc_info.value)
    
    def test_data_loader_allows_authorized_csv_access(self):
        """DataLoader deve permitir acesso CSV para agentes autorizados."""
        
        authorized_agents = [
            'ingestion_agent',
            'data_processor',
            'test_system'
        ]
        
        for agent in authorized_agents:
            loader = DataLoader(caller_agent=agent)
            
            # Não deve lançar exceção na validação
            try:
                loader._validate_csv_access_authorization()
            except DataLoaderUnauthorizedError:
                pytest.fail(f"Agente autorizado {agent} foi bloqueado incorretamente")
    
    def test_python_analyzer_blocks_unauthorized_csv_access(self):
        """PythonDataAnalyzer deve bloquear acesso CSV para agentes não autorizados."""
        
        unauthorized_agents = [
            'analysis_agent',
            'rag_agent',
            'unknown_caller'
        ]
        
        for agent in unauthorized_agents:
            analyzer = PythonDataAnalyzer(caller_agent=agent)
            
            # Verificar que agente é detectado corretamente como não autorizado
            assert analyzer.caller_agent == agent
            
            # PythonDataAnalyzer tem lógica de fallback via embeddings, 
            # mas bloqueia acesso direto a outras tabelas
            with pytest.raises(AnalyzerUnauthorizedError) as exc_info:
                # Tentar acessar tabela não-embeddings (ex: 'chunks', 'raw_data')
                analyzer.get_data_from_supabase(table='chunks')
            
            assert "VIOLAÇÃO DE CONFORMIDADE DETECTADA" in str(exc_info.value)
            assert agent in str(exc_info.value)
    
    def test_python_analyzer_allows_authorized_csv_access(self):
        """PythonDataAnalyzer deve permitir acesso CSV para agentes autorizados."""
        
        authorized_agents = [
            'ingestion_agent',
            'test_system'
        ]
        
        for agent in authorized_agents:
            analyzer = PythonDataAnalyzer(caller_agent=agent)
            
            # Não deve lançar exceção na validação
            try:
                analyzer._validate_csv_access_authorization()
            except AnalyzerUnauthorizedError:
                pytest.fail(f"Agente autorizado {agent} foi bloqueado incorretamente")
    
    def test_embeddings_analysis_agent_uses_embeddings_only(self):
        """EmbeddingsAnalysisAgent deve usar APENAS dados da tabela embeddings."""
        
        agent = EmbeddingsAnalysisAgent()
        
        # Verificar que load_from_embeddings existe
        assert hasattr(agent, 'load_from_embeddings'), "EmbeddingsAnalysisAgent deve ter método load_from_embeddings"
        
        # Verificar que validate_architecture_compliance existe
        assert hasattr(agent, 'validate_architecture_compliance'), "EmbeddingsAnalysisAgent deve ter validate_architecture_compliance"
        
        # Chamar validação (não deve lançar exceção)
        try:
            compliance_result = agent.validate_architecture_compliance()
            assert compliance_result['compliance_score'] == 1.0, "EmbeddingsAnalysisAgent deve ter 100% de conformidade"
        except Exception as e:
            pytest.fail(f"Validação de conformidade falhou: {str(e)}")
    
    def test_caller_agent_detection_works(self):
        """Detecção automática de caller_agent deve funcionar."""
        
        # DataProcessor com agente autorizado explícito
        processor = DataProcessor(caller_agent='test_system')
        assert processor.caller_agent == 'test_system'
        
        # DataLoader com agente autorizado explícito  
        loader = DataLoader(caller_agent='test_system')
        assert loader.caller_agent == 'test_system'
        
        # PythonDataAnalyzer com agente autorizado explícito
        analyzer = PythonDataAnalyzer(caller_agent='test_system')
        assert analyzer.caller_agent == 'test_system'


class TestEmbeddingsIntegration:
    """Testes de integração para verificar fluxo embeddings-only."""
    
    def test_orchestrator_checks_embeddings_availability(self):
        """OrchestratorAgent deve verificar disponibilidade de dados via embeddings."""
        
        from src.agent.orchestrator_agent import OrchestratorAgent
        
        orchestrator = OrchestratorAgent()
        
        # Verificar que método de verificação existe
        assert hasattr(orchestrator, '_check_embeddings_data_availability'), "OrchestratorAgent deve verificar disponibilidade de embeddings"
        assert hasattr(orchestrator, '_ensure_embeddings_compliance'), "OrchestratorAgent deve garantir conformidade"
        
        # Chamar método de verificação (pode retornar False se não há dados, mas não deve falhar)
        try:
            availability = orchestrator._check_embeddings_data_availability()
            assert isinstance(availability, bool), "Verificação deve retornar boolean"
        except Exception as e:
            pytest.fail(f"Verificação de disponibilidade de embeddings falhou: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])