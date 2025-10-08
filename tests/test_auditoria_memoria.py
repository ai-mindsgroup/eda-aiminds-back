"""
Teste automatizado do script de auditoria de memória conversacional.
"""
from src.memory.supabase_memory import (
    save_agent_context, get_agent_context,
    save_agent_session, get_agent_session
)
from src.memory.models import AgentContext, AgentSession

def test_auditoria_memoria():
    # Insere contexto
    c_resp = save_agent_context(AgentContext(agent_id="agente_1", session_id="sess_audit", context={"context": "Contexto de teste"}))
    assert c_resp is not None
    ctx = get_agent_context("agente_1", "sess_audit")
    assert ctx is not None
    assert ctx.context["context"] == "Contexto de teste"

    # Insere sessão
    s_resp = save_agent_session(AgentSession(session_id="sess_audit", user_id="u123", start_time="2025-10-04"))
    assert s_resp is not None
    sess = get_agent_session("sess_audit")
    assert sess is not None
    assert sess.user_id == "u123"
    assert str(sess.start_time).startswith("2025-10-04")
