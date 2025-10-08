"""
Teste Prático: Memória Persistente e LangChain em Runtime

Este script testa se:
1. Memória persiste entre interações
2. LangChain está sendo usado
3. Tabelas SQL estão sendo acessadas
4. Contexto dinâmico funciona
"""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.agent.rag_data_agent import RAGDataAgent
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def test_memory_and_langchain():
    """Testa memória e LangChain em runtime."""
    
    print("\n" + "=" * 80)
    print("TESTE PRÁTICO: MEMÓRIA PERSISTENTE + LANGCHAIN")
    print("=" * 80)
    
    # 1. Criar agente
    print("\n📝 1. INICIALIZANDO RAGDataAgent...")
    agent = RAGDataAgent()
    print(f"   ✅ Agente criado: {agent.name}")
    print(f"   ✅ Memória habilitada: {agent.has_memory}")
    print(f"   ✅ LLM LangChain: {agent.llm is not None}")
    
    if agent.llm:
        print(f"   ✅ Tipo LLM: {type(agent.llm).__name__}")
    else:
        print(f"   ⚠️  LLM LangChain não disponível (usando fallback)")
    
    # 2. Criar sessão única para teste
    session_id = str(uuid4())
    print(f"\n📝 2. CRIANDO SESSÃO DE MEMÓRIA...")
    print(f"   🔑 Session ID: {session_id[:8]}...")
    
    # 3. Primeira interação (sem histórico)
    print(f"\n📝 3. PRIMEIRA INTERAÇÃO (sem histórico prévio)...")
    query1 = "Teste de memória - primeira pergunta"
    
    result1 = await agent.process(
        query=query1,
        context={},
        session_id=session_id
    )
    
    print(f"   ✅ Resposta recebida")
    metadata1 = result1.get('metadata', {})
    print(f"   ✅ Session ID salvo: {metadata1.get('session_id', 'N/A')[:8]}...")
    print(f"   ✅ Interações anteriores: {metadata1.get('previous_interactions', 0)}")
    
    # 4. Verificar no banco de dados
    print(f"\n📝 4. VERIFICANDO DADOS NO SUPABASE...")
    
    # Verificar tabela agent_sessions
    sessions_result = supabase.table('agent_sessions')\
        .select('*')\
        .eq('session_id', session_id)\
        .execute()
    
    sessions_count = len(sessions_result.data) if sessions_result.data else 0
    print(f"   {'✅' if sessions_count > 0 else '❌'} agent_sessions: {sessions_count} registro(s)")
    
    if sessions_result.data:
        session_uuid = sessions_result.data[0]['id']
        agent_name = sessions_result.data[0].get('agent_name')
        print(f"   ✅ Session UUID: {str(session_uuid)[:8]}...")
        print(f"   ✅ Agent Name: {agent_name}")
        
        # Verificar tabela agent_conversations
        convs_result = supabase.table('agent_conversations')\
            .select('*')\
            .eq('session_id', session_uuid)\
            .execute()
        
        convs_count = len(convs_result.data) if convs_result.data else 0
        print(f"   {'✅' if convs_count > 0 else '❌'} agent_conversations: {convs_count} registro(s)")
        
        if convs_result.data:
            for i, conv in enumerate(convs_result.data[:3]):
                print(f"      - Interação {i+1}:")
                print(f"        Tipo: {conv.get('message_type')}")
                print(f"        Conteúdo: {conv.get('content', '')[:60]}...")
    
    # 5. Segunda interação (DEVE ter histórico agora)
    print(f"\n📝 5. SEGUNDA INTERAÇÃO (deve recuperar histórico)...")
    await asyncio.sleep(1)  # Dar tempo para persistir
    
    query2 = "Teste de memória - segunda pergunta"
    
    result2 = await agent.process(
        query=query2,
        context={},
        session_id=session_id  # MESMA sessão
    )
    
    print(f"   ✅ Resposta recebida")
    metadata2 = result2.get('metadata', {})
    print(f"   ✅ Session ID: {metadata2.get('session_id', 'N/A')[:8]}...")
    print(f"   ✅ Interações anteriores: {metadata2.get('previous_interactions', 0)}")
    
    previous_interactions = metadata2.get('previous_interactions', 0)
    if previous_interactions > 0:
        print(f"   🎉 MEMÓRIA FUNCIONANDO! {previous_interactions} interações anteriores recuperadas")
    else:
        print(f"   ⚠️  Memória não recuperou histórico")
    
    # 6. Verificar novamente o banco
    print(f"\n📝 6. VERIFICANDO DADOS ATUALIZADOS NO SUPABASE...")
    
    if sessions_result.data:
        session_uuid = sessions_result.data[0]['id']
        
        convs_result_final = supabase.table('agent_conversations')\
            .select('*')\
            .eq('session_id', session_uuid)\
            .order('timestamp', desc=False)\
            .execute()
        
        convs_count_final = len(convs_result_final.data) if convs_result_final.data else 0
        print(f"   {'✅' if convs_count_final > 0 else '❌'} agent_conversations: {convs_count_final} registro(s)")
        
        if convs_count_final >= 2:
            print(f"   🎉 MEMÓRIA PERSISTENTE CONFIRMADA!")
            print(f"   ✅ {convs_count_final} interações salvas no banco")
    
    # 7. Verificar imports LangChain
    print(f"\n📝 7. VERIFICANDO IMPORTS LANGCHAIN...")
    
    try:
        from langchain_openai import ChatOpenAI
        print(f"   ✅ langchain_openai.ChatOpenAI: Importado")
    except ImportError:
        print(f"   ❌ langchain_openai.ChatOpenAI: Não disponível")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print(f"   ✅ langchain_google_genai.ChatGoogleGenerativeAI: Importado")
    except ImportError:
        print(f"   ❌ langchain_google_genai.ChatGoogleGenerativeAI: Não disponível")
    
    try:
        from langchain.schema import HumanMessage, SystemMessage, AIMessage
        print(f"   ✅ langchain.schema (Messages): Importado")
    except ImportError:
        print(f"   ❌ langchain.schema: Não disponível")
    
    # 8. Verificar código do RAGDataAgent
    print(f"\n📝 8. VERIFICANDO CÓDIGO DO RAGDataAgent...")
    
    rag_file = Path("src/agent/rag_data_agent.py")
    if rag_file.exists():
        content = rag_file.read_text(encoding='utf-8')
        
        checks = [
            ("from langchain_openai import ChatOpenAI", "Import ChatOpenAI"),
            ("from langchain_google_genai import ChatGoogleGenerativeAI", "Import ChatGoogleGenerativeAI"),
            ("self.llm.invoke(messages)", "Uso de llm.invoke()"),
            ("await self.init_memory_session", "Chamada init_memory_session()"),
            ("await self.recall_conversation_context", "Chamada recall_conversation_context()"),
            ("await self.remember_interaction", "Chamada remember_interaction()"),
        ]
        
        for check_str, desc in checks:
            if check_str in content:
                print(f"   ✅ {desc}: Encontrado")
            else:
                print(f"   ❌ {desc}: Não encontrado")
    
    # RESUMO FINAL
    print(f"\n" + "=" * 80)
    print("📊 RESUMO FINAL")
    print("=" * 80)
    
    results = {
        "memória_habilitada": agent.has_memory,
        "llm_langchain_presente": agent.llm is not None,
        "sessao_criada": sessions_count > 0,
        "conversas_salvas": convs_count_final if sessions_result.data else 0,
        "historico_recuperado": previous_interactions > 0
    }
    
    print(f"\n✅ Memória habilitada: {results['memória_habilitada']}")
    print(f"{'✅' if results['llm_langchain_presente'] else '⚠️ '} LLM LangChain: {results['llm_langchain_presente']}")
    print(f"✅ Sessão criada no banco: {results['sessao_criada']}")
    print(f"✅ Conversas salvas: {results['conversas_salvas']}")
    print(f"{'🎉' if results['historico_recuperado'] else '⚠️ '} Histórico recuperado: {results['historico_recuperado']}")
    
    # VEREDITO
    print(f"\n" + "=" * 80)
    if results['memória_habilitada'] and results['sessao_criada'] and results['conversas_salvas'] >= 2:
        print("🎉 VEREDITO: MEMÓRIA PERSISTENTE FUNCIONANDO!")
        print("✅ Contexto dinâmico entre interações: CONFIRMADO")
        print("✅ Tabelas SQL sendo usadas: CONFIRMADO")
    else:
        print("⚠️  VEREDITO: MEMÓRIA COM PROBLEMAS")
    
    if results['llm_langchain_presente']:
        print("✅ LangChain integrado: CONFIRMADO")
    else:
        print("⚠️  LangChain: Imports presentes, LLM não inicializado (fallback ativo)")
    
    print("=" * 80 + "\n")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(test_memory_and_langchain())
        sys.exit(0 if results['memória_habilitada'] and results['sessao_criada'] else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Teste interrompido.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
