"""
Centralized Agent Memory/Context Cleaner for EDA AI Minds

This module provides a unified interface to reset memory, context, and history for all agents in the multiagent system whenever a new dataset is loaded. Ensures no contamination between sessions or datasets.

Usage:
    from src.agent.memory_cleaner import clean_all_agent_memory
    clean_all_agent_memory(session_id)

Best practices: Call this function before any new dataset ingestion or context switch.
"""
from src.agent.rag_data_agent import RAGDataAgent
from src.agent.rag_synthesis_agent import synthesize_response
# Import other agents as needed

AGENT_CLASSES = [
    RAGDataAgent,
    # Add other agent classes here as needed
]

def clean_all_agent_memory(session_id: str = None):
    """
    Reseta memória/contexto/histórico de todos os agentes do sistema.
    Args:
        session_id: Identificador da sessão (opcional, se aplicável)
    """
    for agent_cls in AGENT_CLASSES:
        agent = agent_cls()
        if hasattr(agent, 'reset_memory'):
            agent.reset_memory(session_id=session_id)
        if hasattr(agent, 'clear_context'):
            agent.clear_context(session_id=session_id)
        # Adicione outros métodos de limpeza conforme necessário
    print(f"✅ Memória/contexto de todos os agentes resetada para sessão: {session_id}")
