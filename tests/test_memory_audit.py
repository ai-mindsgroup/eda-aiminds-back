import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import uuid
from src.memory.supabase_memory import (
    save_agent_context, get_agent_context,
    save_agent_session, get_agent_session
)
from src.memory.models import AgentContext, AgentSession

def test_memory_audit_context_insert_and_read(caplog):
    agent_id = "test_agent"
    session_id = "sess_test_audit"
    context_data = {"context": "Teste de persistência"}

    # Busca sessão existente ou cria nova
    read_sess = get_agent_session(session_id)
    if read_sess is None:
        sess = AgentSession(id=str(uuid.uuid4()), session_id=session_id, user_id="u_test", start_time=None)
        save_agent_session(sess)

    # Insere contexto
    ctx = AgentContext(id=str(uuid.uuid4()), agent_id=agent_id, session_id=session_id, context=context_data)
    result = save_agent_context(ctx)
    assert result is not None, "Falha ao inserir contexto na memória."
    caplog.clear()

    # Consulta contexto
    read_ctx = get_agent_context(agent_id, session_id)
    assert read_ctx is not None, "Falha ao ler contexto inserido."
    if hasattr(read_ctx, "context_data"):
        assert read_ctx.context_data == context_data, "Dados do contexto divergentes após leitura."
    elif hasattr(read_ctx, "context"):
        assert read_ctx.context == context_data, "Dados do contexto divergentes após leitura."
    else:
        pytest.fail("Estrutura de contexto inesperada.")
    
    # Logging
    print(f"[LOG] Contexto inserido: {result}")
    print(f"[LOG] Contexto lido: {read_ctx}")

def test_memory_audit_session_insert_and_read(caplog):
    user_id = "u_test"
    session_id = "sess_test_audit"

    # Busca sessão existente ou cria nova
    read_sess = get_agent_session(session_id)
    if read_sess is None:
        sess = AgentSession(id=str(uuid.uuid4()), session_id=session_id, user_id=user_id, start_time=None)
        result = save_agent_session(sess)
        assert result is not None, "Falha ao inserir sessão na memória."
        read_sess = get_agent_session(session_id)
    else:
        result = read_sess
    caplog.clear()

    # Verifica sessão
    assert read_sess is not None, "Falha ao ler sessão inserida."
    assert getattr(read_sess, "session_id", None) == session_id, "Session_id divergente após leitura."
    assert getattr(read_sess, "user_id", None) == user_id, "User_id divergente após leitura."

    # Logging
    print(f"[LOG] Sessão inserida/lida: {result}")
    print(f"[LOG] Sessão lida: {read_sess}")
