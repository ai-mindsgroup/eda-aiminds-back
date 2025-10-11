"""
Testes automatizados para integração das tabelas de memória conversacional Supabase.
"""
import pytest
from src.memory.models import AgentContext, AgentConversation, AgentMemoryEmbedding, AgentSession
from src.memory.supabase_memory import (
    save_agent_context, get_agent_context,
    save_agent_conversation, get_agent_conversations,
    save_agent_memory_embedding, get_agent_memory_embeddings,
    save_agent_session, get_agent_session
)

@pytest.fixture
def session_id():
    return "test_session_001"

@pytest.fixture
def agent_id():
    return "test_agent"

def test_context_rw(agent_id, session_id):
    ctx = AgentContext(agent_id=agent_id, session_id=session_id, context={"foo": "bar"})
    id_saved = save_agent_context(ctx)
    assert id_saved is not None
    ctx_loaded = get_agent_context(agent_id, session_id)
    assert ctx_loaded is not None
    assert ctx_loaded.context["foo"] == "bar"

def test_conversation_rw(agent_id, session_id):
    conv = AgentConversation(agent_id=agent_id, session_id=session_id, user_message="Oi", agent_response="Olá")
    id_saved = save_agent_conversation(conv)
    assert id_saved is not None
    convs = get_agent_conversations(agent_id, session_id)
    assert any(c.user_message == "Oi" for c in convs)

def test_embedding_rw(agent_id, session_id):
    emb = AgentMemoryEmbedding(agent_id=agent_id, session_id=session_id, embedding=[0.1,0.2,0.3], metadata={"type": "test"})
    id_saved = save_agent_memory_embedding(emb)
    assert id_saved is not None
    embs = get_agent_memory_embeddings(agent_id, session_id)
    assert any(abs(e.embedding[0] - 0.1) < 1e-6 for e in embs)

def test_session_rw(session_id):
    sess = AgentSession(session_id=session_id, user_id="user_001")
    id_saved = save_agent_session(sess)
    assert id_saved is not None
    sess_loaded = get_agent_session(session_id)
    assert sess_loaded is not None
    assert sess_loaded.user_id == "user_001"
