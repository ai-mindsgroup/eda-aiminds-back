"""
Script de auditoria para inserção e leitura nas tabelas de memória conversacional Supabase.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.memory.supabase_memory import (
    save_agent_context, get_agent_context,
    save_agent_session, get_agent_session
)
from src.memory.models import AgentContext, AgentSession

def save_context(agent_id, context):
    import uuid
    ctx = AgentContext(id=str(uuid.uuid4()), agent_id=agent_id, session_id="sess_audit", context={"context": context})
    return save_agent_context(ctx)

def get_contexts(agent_id):
    return get_agent_context(agent_id, "sess_audit")

def save_session(user_id, session):
    import uuid
    existing = get_agent_session("sess_audit")
    if existing:
        return existing
    sess = AgentSession(id=str(uuid.uuid4()), session_id="sess_audit", user_id=user_id, start_time=session.get("inicio"))
    return save_agent_session(sess)

def get_sessions(user_id):
    # Busca por user_id (adaptação, pois modelo original busca por session_id)
    sess = get_agent_session("sess_audit")
    if sess and sess.user_id == user_id:
        return [sess]
    return []

def auditoria_memoria():
    # Insere sessão primeiro
    s_resp = save_session(user_id="u123", session={"inicio": "2025-10-04"})
    print("Inserted Session:", s_resp)

    # Agora insere e lê registros de contexto
    c_resp = save_context(agent_id="agente_1", context="Contexto de teste")
    print("Inserted Context:", c_resp)

    # Consulta registros inseridos
    contexts = get_contexts(agent_id="agente_1")
    print("Contexts Read:", contexts)

    sessions = get_sessions(user_id="u123")
    print("Sessions Read:", sessions)

    # Relatório
    print("Auditoria concluída: registros foram inseridos/lidos nas tabelas de memória.")

if __name__ == "__main__":
    auditoria_memoria()
