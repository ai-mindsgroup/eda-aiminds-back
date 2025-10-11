"""
Script de debug para consulta e diagnóstico das tabelas de memória conversacional Supabase.
"""
from src.vectorstore.supabase_client import supabase
from pprint import pprint

def debug_agent_context():
    print("\n=== agent_context ===")
    res = supabase.table('agent_context').select('*').limit(5).execute()
    pprint(res.data)

def debug_agent_conversations():
    print("\n=== agent_conversations ===")
    res = supabase.table('agent_conversations').select('*').limit(5).execute()
    pprint(res.data)

def debug_agent_memory_embeddings():
    print("\n=== agent_memory_embeddings ===")
    res = supabase.table('agent_memory_embeddings').select('*').limit(5).execute()
    pprint(res.data)

def debug_agent_sessions():
    print("\n=== agent_sessions ===")
    res = supabase.table('agent_sessions').select('*').limit(5).execute()
    pprint(res.data)

if __name__ == "__main__":
    debug_agent_context()
    debug_agent_conversations()
    debug_agent_memory_embeddings()
    debug_agent_sessions()
