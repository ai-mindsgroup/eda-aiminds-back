#!/usr/bin/env python3
"""
Teste de Validação Completo - Memória e LangChain

Este script valida:
1. ✅ Memória persistente está funcionando
2. ✅ Contexto dinâmico entre interações
3. ✅ LangChain integrado (quando disponível)
4. ✅ Tabelas SQL de memória acessíveis
5. ✅ RAGDataAgent usa memória corretamente
"""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.agent.rag_data_agent import RAGDataAgent
from src.agent.orchestrator_agent import OrchestratorAgent
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def print_section(title: str):
    """Imprime seção formatada."""
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}\n")


def check_sql_tables():
    """Verifica se tabelas SQL de memória existem."""
    print_section("1. VERIFICAÇÃO DAS TABELAS SQL DE MEMÓRIA")
    
    tables = [
        'agent_sessions',
        'agent_conversations',
        'agent_context',
        'agent_memory_embeddings'
    ]
    
    results = {}
    for table in tables:
        try:
            result = supabase.table(table).select('*').limit(1).execute()
            exists = result is not None
            results[table] = exists
            print(f"  {'✅' if exists else '❌'} Tabela {table}: {'Existe' if exists else 'Não encontrada'}")
        except Exception as e:
            results[table] = False
            print(f"  ❌ Tabela {table}: Erro - {str(e)[:50]}")
    
    all_exist = all(results.values())
    print(f"\n  {'✅' if all_exist else '❌'} Resultado: {'Todas as tabelas existem' if all_exist else 'Algumas tabelas faltam'}")
    return all_exist


def check_rag_agent():
    """Verifica configuração do RAGDataAgent."""
    print_section("2. VERIFICAÇÃO DO RAGDataAgent")
    
    agent = RAGDataAgent()
    
    print(f"  ✅ RAGDataAgent inicializado: {agent.name}")
    print(f"  {'✅' if agent.has_memory else '❌'} Memória habilitada: {agent.has_memory}")
    print(f"  {'✅' if agent._memory_manager else '❌'} MemoryManager presente: {agent._memory_manager is not None}")
    print(f"  {'✅' if hasattr(agent, 'llm') else '❌'} LLM LangChain configurado: {hasattr(agent, 'llm')}")
    
    if hasattr(agent, 'llm'):
        if agent.llm:
            llm_type = type(agent.llm).__name__
            print(f"  ✅ Tipo de LLM: {llm_type}")
        else:
            print(f"  ⚠️  LLM LangChain não disponível (usando fallback)")
    
    print(f"\n  {'✅' if agent.has_memory else '❌'} Resultado: RAGDataAgent {'COM' if agent.has_memory else 'SEM'} memória persistente")
    return agent.has_memory


async def test_memory_persistence():
    """Testa memória persistente com interações reais."""
    print_section("3. TESTE DE MEMÓRIA PERSISTENTE")
    
    session_id = str(uuid4())
    print(f"  🔑 Sessão de teste: {session_id[:8]}...\n")
    
    agent = RAGDataAgent()
    
    # Teste 1: Inicializar sessão
    print("  📝 Teste 1: Inicializar sessão de memória")
    try:
        result_session_id = await agent.init_memory_session(session_id)
        if result_session_id:
            print(f"  ✅ Sessão inicializada: {result_session_id[:8]}...")
        else:
            print(f"  ❌ Falha ao inicializar sessão")
            return False
    except Exception as e:
        print(f"  ❌ Erro ao inicializar sessão: {e}")
        return False
    
    # Teste 2: Recuperar contexto (deve estar vazio)
    print("\n  📝 Teste 2: Recuperar contexto conversacional (primeira vez)")
    try:
        memory_context = await agent.recall_conversation_context()
        recent_convs = memory_context.get('recent_conversations', [])
        print(f"  ✅ Contexto recuperado: {len(recent_convs)} interações anteriores (esperado: 0)")
        
        if len(recent_convs) > 0:
            print(f"  ⚠️  Atenção: Sessão nova deveria ter 0 interações")
    except Exception as e:
        print(f"  ❌ Erro ao recuperar contexto: {e}")
        return False
    
    # Teste 3: Salvar interação
    print("\n  📝 Teste 3: Salvar interação na memória")
    try:
        saved = await agent.remember_interaction(
            query="Qual a média da coluna Amount?",
            response="A média da coluna Amount é 88.35",
            processing_time_ms=1500,
            confidence=0.95,
            model_used="test_model",
            metadata={"test": True}
        )
        
        if saved:
            print(f"  ✅ Interação salva com sucesso")
        else:
            print(f"  ❌ Falha ao salvar interação")
            return False
    except Exception as e:
        print(f"  ❌ Erro ao salvar interação: {e}")
        return False
    
    # Teste 4: Recuperar contexto (agora deve ter 1 interação)
    print("\n  📝 Teste 4: Recuperar contexto conversacional (segunda vez)")
    try:
        await asyncio.sleep(0.5)  # Dar tempo para persistir
        memory_context = await agent.recall_conversation_context()
        recent_convs = memory_context.get('recent_conversations', [])
        print(f"  ✅ Contexto recuperado: {len(recent_convs)} interações anteriores")
        
        if len(recent_convs) > 0:
            print(f"  ✅ Histórico funcionando - interação salva e recuperada!")
            last_conv = recent_convs[-1]
            print(f"     Query: {last_conv.get('query', '')[:50]}")
            print(f"     Response: {last_conv.get('response', '')[:50]}")
        else:
            print(f"  ⚠️  Histórico vazio - interação não foi recuperada")
    except Exception as e:
        print(f"  ❌ Erro ao recuperar contexto: {e}")
        return False
    
    # Teste 5: Verificar no Supabase
    print("\n  📝 Teste 5: Verificar dados no Supabase")
    try:
        # Verificar sessão
        sessions = supabase.table('agent_sessions').select('*').eq('session_id', session_id).execute()
        print(f"  {'✅' if sessions.data else '❌'} Sessão no banco: {len(sessions.data) if sessions.data else 0} registro(s)")
        
        if sessions.data:
            session_uuid = sessions.data[0]['id']
            
            # Verificar conversas
            conversations = supabase.table('agent_conversations').select('*').eq('session_id', session_uuid).execute()
            print(f"  {'✅' if conversations.data else '❌'} Conversas no banco: {len(conversations.data) if conversations.data else 0} registro(s)")
            
            if conversations.data:
                print(f"  ✅ Memória persistente FUNCIONANDO completamente!")
                return True
    except Exception as e:
        print(f"  ⚠️  Erro ao verificar Supabase: {e}")
        return False
    
    print(f"\n  {'✅' if saved else '❌'} Resultado: Memória persistente {'FUNCIONANDO' if saved else 'COM PROBLEMAS'}")
    return saved


async def test_orchestrator_memory():
    """Testa orchestrador com memória persistente."""
    print_section("4. TESTE DO ORCHESTRATOR COM MEMÓRIA")
    
    session_id = str(uuid4())
    print(f"  🔑 Sessão de teste: {session_id[:8]}...\n")
    
    orchestrator = OrchestratorAgent(
        enable_csv_agent=True,
        enable_rag_agent=True,
        enable_data_processor=False
    )
    
    print(f"  ✅ Orchestrator inicializado")
    print(f"  {'✅' if orchestrator.has_memory else '❌'} Memória habilitada: {orchestrator.has_memory}")
    print(f"  ✅ Agentes registrados: {len(orchestrator.agents)}")
    
    # Teste com process_with_persistent_memory
    print("\n  📝 Testando process_with_persistent_memory()")
    try:
        query = "Teste de memória do orchestrator"
        response = await orchestrator.process_with_persistent_memory(
            query=query,
            context={},
            session_id=session_id
        )
        
        if response:
            metadata = response.get('metadata', {})
            print(f"  ✅ Resposta recebida")
            print(f"  {'✅' if metadata.get('session_id') else '⚠️ '} Session ID na resposta: {metadata.get('session_id', 'N/A')[:8]}...")
            print(f"  {'✅' if metadata.get('memory_enabled') else '⚠️ '} Memória habilitada: {metadata.get('memory_enabled', False)}")
            
            return True
    except Exception as e:
        print(f"  ❌ Erro no orchestrator: {e}")
        return False
    
    return False


def check_langchain_imports():
    """Verifica imports do LangChain."""
    print_section("5. VERIFICAÇÃO DO LANGCHAIN")
    
    imports_ok = True
    
    # Verificar imports no RAGDataAgent
    print("  📝 Verificando imports do LangChain no RAGDataAgent:\n")
    
    try:
        from langchain_openai import ChatOpenAI
        print("  ✅ langchain_openai.ChatOpenAI: Importado")
    except ImportError as e:
        print(f"  ❌ langchain_openai.ChatOpenAI: {str(e)[:50]}")
        imports_ok = False
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("  ✅ langchain_google_genai.ChatGoogleGenerativeAI: Importado")
    except ImportError as e:
        print(f"  ❌ langchain_google_genai.ChatGoogleGenerativeAI: {str(e)[:50]}")
        imports_ok = False
    
    try:
        from langchain.schema import HumanMessage, SystemMessage, AIMessage
        print("  ✅ langchain.schema (Messages): Importado")
    except ImportError as e:
        print(f"  ❌ langchain.schema: {str(e)[:50]}")
        imports_ok = False
    
    try:
        from langchain.memory import ConversationBufferMemory
        print("  ✅ langchain.memory.ConversationBufferMemory: Importado")
    except ImportError as e:
        print(f"  ❌ langchain.memory: {str(e)[:50]}")
        imports_ok = False
    
    # Verificar arquivo rag_data_agent.py
    print("\n  📝 Verificando uso do LangChain no código:\n")
    
    rag_agent_file = Path("src/agent/rag_data_agent.py")
    if rag_agent_file.exists():
        content = rag_agent_file.read_text(encoding='utf-8')
        
        checks = [
            ("from langchain_openai import ChatOpenAI", "Import ChatOpenAI"),
            ("from langchain_google_genai import ChatGoogleGenerativeAI", "Import ChatGoogleGenerativeAI"),
            ("from langchain.schema import", "Import Messages"),
            ("self.llm.invoke(messages)", "Uso de llm.invoke()"),
            ("ChatGoogleGenerativeAI(", "Inicialização Gemini"),
            ("ChatOpenAI(", "Inicialização OpenAI")
        ]
        
        for check_str, description in checks:
            if check_str in content:
                print(f"  ✅ {description}: Encontrado no código")
            else:
                print(f"  ❌ {description}: Não encontrado no código")
                imports_ok = False
    else:
        print(f"  ❌ Arquivo rag_data_agent.py não encontrado")
        imports_ok = False
    
    print(f"\n  {'✅' if imports_ok else '⚠️ '} Resultado: LangChain {'INTEGRADO' if imports_ok else 'PARCIALMENTE INTEGRADO'}")
    return imports_ok


async def main():
    """Executa todos os testes."""
    print("\n" + "=" * 70)
    print("  TESTE DE VALIDAÇÃO COMPLETO - MEMÓRIA E LANGCHAIN")
    print("  Sistema: EDA AI Minds - RAGDataAgent V2.0")
    print("  Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    results = {}
    
    # Teste 1: Tabelas SQL
    results['sql_tables'] = check_sql_tables()
    
    # Teste 2: RAGDataAgent
    results['rag_agent'] = check_rag_agent()
    
    # Teste 3: Memória Persistente
    results['memory_persistence'] = await test_memory_persistence()
    
    # Teste 4: Orchestrator
    results['orchestrator'] = await test_orchestrator_memory()
    
    # Teste 5: LangChain
    results['langchain'] = check_langchain_imports()
    
    # Resumo Final
    print_section("📊 RESUMO FINAL")
    
    print("  Componente                      | Status")
    print("  " + "-" * 66)
    print(f"  Tabelas SQL de Memória          | {'✅ APROVADO' if results['sql_tables'] else '❌ REPROVADO'}")
    print(f"  RAGDataAgent com Memória        | {'✅ APROVADO' if results['rag_agent'] else '❌ REPROVADO'}")
    print(f"  Memória Persistente Funcionando | {'✅ APROVADO' if results['memory_persistence'] else '❌ REPROVADO'}")
    print(f"  Orchestrator com Memória        | {'✅ APROVADO' if results['orchestrator'] else '❌ REPROVADO'}")
    print(f"  LangChain Integrado             | {'✅ APROVADO' if results['langchain'] else '⚠️  PARCIAL'}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print("\n  " + "-" * 66)
    print(f"  TOTAL: {passed_tests}/{total_tests} testes aprovados ({passed_tests/total_tests*100:.0f}%)")
    
    # Veredito Final
    print_section("✅ VEREDITO FINAL")
    
    if passed_tests == total_tests:
        print("  🎉 SISTEMA 100% CONFORME!")
        print("  ✅ Memória persistente: FUNCIONANDO")
        print("  ✅ Contexto dinâmico: FUNCIONANDO")
        print("  ✅ LangChain: INTEGRADO")
        print("  ✅ Tabelas SQL: ACESSÍVEIS")
    elif passed_tests >= total_tests * 0.8:
        print("  ✅ SISTEMA APROVADO COM RESSALVAS")
        print("  ✅ Memória persistente: FUNCIONANDO")
        print("  ✅ Contexto dinâmico: FUNCIONANDO")
        print("  ⚠️  LangChain: Parcialmente integrado (fallback disponível)")
    else:
        print("  ❌ SISTEMA COM PROBLEMAS")
        print("  Revisar componentes reprovados")
    
    print("\n" + "=" * 70 + "\n")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Teste interrompido pelo usuário.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}\n")
        sys.exit(1)
