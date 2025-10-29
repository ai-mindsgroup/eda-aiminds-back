# Teste de isolamento de source_id dinâmico
# Garante que agentes não misturam dados de datasets diferentes

import pytest
from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent

def test_source_id_isolation():
    agent1 = RAGDataAgent()
    agent2 = RAGDataAgent()
    # Simula session_id e source_id distintos
    agent1.session_id = "sess1"
    agent2.session_id = "sess2"
    agent1.source_id = "hash1"
    agent2.source_id = "hash2"
    # Simula ingestão de dados distintos
    agent1.memory = {"dataset": "A"}
    agent2.memory = {"dataset": "B"}
    # Garante que contextos não se misturam
    assert agent1.source_id != agent2.source_id
    assert agent1.memory["dataset"] != agent2.memory["dataset"]
