import types
import pytest


class FakeLLMResponse:
    def __init__(self, content: str = "RESPOSTA_FAKE", success: bool = True, error: str | None = None):
        self.content = content
        self.success = success
        self.error = error
        self.provider = None
        self.model = "fake"
        self.processing_time = 0.01


class FakeLLMManager:
    def chat(self, prompt, config=None):
        # Retorna resposta determinística
        return FakeLLMResponse(content="Analise OK - resposta sintetizada para testes.")


class FakeHybridProcessor:
    def process_query(self, query: str, source_id: str, session_id=None):
        return {
            'status': 'success',
            'strategy': 'metadata_only',
            'context': 'Resumo de metadados simulados',
            'chunks_used': [],
            'csv_accessed': False,
            'new_chunks_generated': 0,
            'query_analysis': {'intent': 'overview'},
            'dataframe_shape': None,
            'covered_aspects': ['overview'],
            'required_gaps': [],
            'csv_analysis': {}
        }


def test_rag_agent_process_query_hybrid_with_mock_llm(monkeypatch):
    # Import depois para permitir monkeypatch da função de fábrica
    import src.agent.rag_agent as rag_agent

    # Monkeypatch do LLM Manager para evitar chamadas externas
    monkeypatch.setattr(rag_agent, "get_llm_manager", lambda: FakeLLMManager(), raising=True)

    agent = rag_agent.RAGAgent()

    # Substitui o HybridProcessor por uma implementação fake para não acessar vector store
    agent.hybrid_processor = FakeHybridProcessor()

    result = agent.process_query_hybrid(query="Quais colunas existem?", source_id="dataset_teste")

    assert result["status"] == "success"
    assert isinstance(result.get("content"), str) and len(result["content"]) > 0
    # Metadados principais expostos no nível raiz
    assert result.get("strategy") == "metadata_only"
    assert result.get("csv_accessed") is False
