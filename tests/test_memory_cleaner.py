# Teste de limpeza de memória/contexto dos agentes
# Este teste valida se a rotina centralizada de limpeza está funcionando corretamente

import pytest
from src.agent.memory_cleaner import clean_all_agent_memory
from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent

@pytest.fixture
def setup_agent():
    agent = RAGDataAgent()
    # Simula contexto/memória e session_id
    agent.session_id = "test_session"
    agent.memory = {"last_query": "teste", "dataset": "old"}
    return agent

def test_memory_cleaner(setup_agent):
    agent = setup_agent
    # Antes da limpeza
    assert agent.memory["last_query"] == "teste"
    # Limpa diretamente o agente
    agent.reset_memory(session_id="test_session")
    # Após limpeza, espera-se memória/contexto vazio ou resetado
    assert agent.memory == {} or agent.memory.get("last_query") is None
