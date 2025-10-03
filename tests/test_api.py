"""
Testes da API REST
=================

Testes unitários e de integração para todos os endpoints.
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Importar aplicação
from src.api.main import app

# Cliente de teste
client = TestClient(app)


class TestHealthEndpoints:
    """Testes dos endpoints de saúde."""
    
    def test_health_live(self):
        """Teste do liveness probe."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    def test_health_ready(self):
        """Teste do readiness probe."""
        response = client.get("/health/ready")
        # Pode ser 200 ou 503 dependendo da configuração
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
    
    def test_health_complete(self):
        """Teste do health check completo."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime_seconds" in data
        assert "database" in data
        assert "vectorstore" in data
        assert "llm_services" in data
    
    def test_health_metrics(self):
        """Teste das métricas básicas."""
        response = client.get("/health/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "memory_usage_mb" in data


class TestCSVEndpoints:
    """Testes dos endpoints de CSV."""
    
    def test_csv_upload_success(self):
        """Teste de upload bem-sucedido."""
        csv_content = "id,name,value\n1,test,100\n2,example,200"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {
            "delimiter": ",",
            "encoding": "utf-8",
            "has_header": True,
            "preview_rows": 2
        }
        
        response = client.post("/csv/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "file_id" in result
        assert result["filename"] == "test.csv"
        assert result["rows_count"] == 2
        assert result["columns_count"] == 3
    
    def test_csv_upload_invalid_file(self):
        """Teste de upload com arquivo inválido."""
        files = {"file": ("test.txt", "not a csv", "text/plain")}
        
        response = client.post("/csv/upload", files=files)
        assert response.status_code == 422
    
    def test_csv_upload_empty_file(self):
        """Teste de upload com arquivo vazio."""
        files = {"file": ("empty.csv", "", "text/csv")}
        
        response = client.post("/csv/upload", files=files)
        assert response.status_code == 400
    
    def test_list_files_empty(self):
        """Teste de listagem de arquivos vazia."""
        response = client.get("/csv/files")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "files" in data
    
    @patch('src.agent.orchestrator_agent.OrchestratorAgent')
    def test_csv_analysis(self, mock_orchestrator):
        """Teste de análise de CSV."""
        # Mock do orquestrador
        mock_instance = Mock()
        mock_instance.process.return_value = {
            "content": "Análise realizada com sucesso",
            "statistics": {"mean": 150.0},
            "confidence_score": 0.9
        }
        mock_orchestrator.return_value = mock_instance
        
        # Primeiro fazer upload
        csv_content = "id,value\n1,100\n2,200"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        upload_response = client.post("/csv/upload", files=files)
        file_id = upload_response.json()["file_id"]
        
        # Então analisar
        analysis_data = {
            "file_id": file_id,
            "analysis_type": "statistical",
            "include_visualizations": False
        }
        
        response = client.post("/csv/analyze", json=analysis_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "result" in result
    
    def test_csv_analysis_file_not_found(self):
        """Teste de análise com arquivo inexistente."""
        analysis_data = {
            "file_id": "nonexistent_file",
            "analysis_type": "statistical"
        }
        
        response = client.post("/csv/analyze", json=analysis_data)
        assert response.status_code == 404


class TestRAGEndpoints:
    """Testes dos endpoints RAG."""
    
    @patch('src.agent.orchestrator_agent.OrchestratorAgent')
    def test_rag_search(self, mock_orchestrator):
        """Teste de busca semântica."""
        # Mock do orquestrador
        mock_instance = Mock()
        mock_instance.process.return_value = {
            "content": "Resposta da busca semântica",
            "sources": [
                {
                    "content": "Documento encontrado",
                    "source": "test_doc",
                    "similarity": 0.9,
                    "metadata": {}
                }
            ],
            "confidence_score": 0.8
        }
        mock_orchestrator.return_value = mock_instance
        
        search_data = {
            "query": "Como detectar fraudes?",
            "query_type": "semantic_search",
            "max_results": 5,
            "similarity_threshold": 0.7
        }
        
        response = client.post("/rag/search", json=search_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "answer" in result
        assert "sources" in result
    
    def test_rag_search_empty_query(self):
        """Teste de busca com query vazia."""
        search_data = {
            "query": "",
            "query_type": "semantic_search"
        }
        
        response = client.post("/rag/search", json=search_data)
        assert response.status_code == 400
    
    @patch('src.agent.orchestrator_agent.OrchestratorAgent')
    def test_chat(self, mock_orchestrator):
        """Teste de chat."""
        # Mock do orquestrador
        mock_instance = Mock()
        mock_instance.process.return_value = {
            "content": "Olá! Como posso ajudar?",
            "confidence_score": 0.9
        }
        mock_orchestrator.return_value = mock_instance
        
        chat_data = {
            "message": "Olá",
            "session_id": "test_session",
            "include_memory": True,
            "temperature": 0.7
        }
        
        response = client.post("/rag/chat", json=chat_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "message" in result
        assert result["session_id"] == "test_session"
    
    def test_chat_empty_message(self):
        """Teste de chat com mensagem vazia."""
        chat_data = {
            "message": "",
            "session_id": "test_session"
        }
        
        response = client.post("/rag/chat", json=chat_data)
        assert response.status_code == 400
    
    def test_chat_history_not_found(self):
        """Teste de histórico de sessão inexistente."""
        response = client.get("/rag/chat/nonexistent_session/history")
        assert response.status_code == 404
    
    def test_list_sessions(self):
        """Teste de listagem de sessões."""
        response = client.get("/rag/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sessions" in data


class TestAnalysisEndpoints:
    """Testes dos endpoints de análise."""
    
    def test_system_stats(self):
        """Teste de estatísticas do sistema."""
        response = client.get("/analysis/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_files_processed" in data
        assert "vectorstore_embeddings" in data
    
    def test_analysis_history(self):
        """Teste de histórico de análises."""
        response = client.get("/analysis/history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analyses" in data
    
    def test_analysis_history_with_filter(self):
        """Teste de histórico com filtro."""
        response = client.get("/analysis/history?analysis_type=fraud_detection")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAuthEndpoints:
    """Testes dos endpoints de autenticação."""
    
    def test_create_api_key(self):
        """Teste de criação de API key."""
        key_data = {
            "name": "Test Key",
            "permissions": ["read", "write"]
        }
        
        response = client.post("/auth/api-key", json=key_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "api_key" in result
        assert result["name"] == "Test Key"
        assert result["permissions"] == ["read", "write"]
    
    def test_list_api_keys(self):
        """Teste de listagem de API keys."""
        response = client.get("/auth/api-keys")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_keys" in data
    
    def test_validate_auth_without_token(self):
        """Teste de validação sem token."""
        response = client.get("/auth/validate")
        assert response.status_code == 401
    
    def test_validate_auth_with_invalid_token(self):
        """Teste de validação com token inválido."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/validate", headers=headers)
        assert response.status_code == 401


class TestRootEndpoint:
    """Testes do endpoint raiz."""
    
    def test_root_endpoint(self):
        """Teste do endpoint raiz."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "features" in data
        assert data["name"] == "EDA AI Minds - API Multiagente"


class TestValidation:
    """Testes de validação de dados."""
    
    def test_invalid_json(self):
        """Teste com JSON inválido."""
        response = client.post(
            "/csv/analyze",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Teste com campos obrigatórios ausentes."""
        incomplete_data = {
            "analysis_type": "statistical"
            # file_id ausente
        }
        
        response = client.post("/csv/analyze", json=incomplete_data)
        assert response.status_code == 422
        
        error = response.json()
        assert "details" in error
    
    def test_invalid_analysis_type(self):
        """Teste com tipo de análise inválido."""
        invalid_data = {
            "file_id": "test_file",
            "analysis_type": "invalid_type"
        }
        
        response = client.post("/csv/analyze", json=invalid_data)
        assert response.status_code == 422


# ============================================================================
# FIXTURES E CONFIGURAÇÃO DE TESTES
# ============================================================================

@pytest.fixture
def sample_csv_content():
    """CSV de exemplo para testes."""
    return """id,name,amount,date,category
1,Transaction 1,100.50,2023-01-01,food
2,Transaction 2,250.00,2023-01-02,transport
3,Transaction 3,75.25,2023-01-03,shopping
4,Transaction 4,500.00,2023-01-04,food
5,Transaction 5,125.75,2023-01-05,transport"""


@pytest.fixture
def uploaded_file_id(sample_csv_content):
    """Fixture que faz upload e retorna file_id."""
    files = {"file": ("test_transactions.csv", sample_csv_content, "text/csv")}
    response = client.post("/csv/upload", files=files)
    return response.json()["file_id"]


def test_end_to_end_workflow(sample_csv_content):
    """Teste de fluxo completo end-to-end."""
    # 1. Upload de arquivo
    files = {"file": ("e2e_test.csv", sample_csv_content, "text/csv")}
    upload_response = client.post("/csv/upload", files=files)
    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]
    
    # 2. Listar arquivos
    list_response = client.get("/csv/files")
    assert list_response.status_code == 200
    files_list = list_response.json()["files"]
    assert any(f["file_id"] == file_id for f in files_list)
    
    # 3. Chat sobre o arquivo
    chat_data = {
        "message": f"Analise o arquivo {file_id}",
        "session_id": "e2e_session",
        "include_memory": True
    }
    
    with patch('src.agent.orchestrator_agent.OrchestratorAgent') as mock_orchestrator:
        mock_instance = Mock()
        mock_instance.process.return_value = {
            "content": "Arquivo analisado com sucesso",
            "confidence_score": 0.9
        }
        mock_orchestrator.return_value = mock_instance
        
        chat_response = client.post("/rag/chat", json=chat_data)
        assert chat_response.status_code == 200
    
    # 4. Verificar sessão ativa
    sessions_response = client.get("/rag/sessions")
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()["sessions"]
    assert any(s["session_id"] == "e2e_session" for s in sessions)
    
    # 5. Limpar arquivo
    delete_response = client.delete(f"/csv/files/{file_id}")
    assert delete_response.status_code == 200


if __name__ == "__main__":
    # Executar testes específicos
    pytest.main([__file__, "-v"])