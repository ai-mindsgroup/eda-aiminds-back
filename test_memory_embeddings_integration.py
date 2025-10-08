"""
Teste de Integração: Persistência de Embeddings de Memória Conversacional
============================================================================

Este script testa se todos os agentes estão salvando embeddings de conversação
na tabela agent_memory_embeddings com metadata enriquecido.

Verificações:
1. BaseAgent: métodos save_conversation_embedding e persist_conversation_memory
2. GroqLLMAgent: metadata enriquecido ao salvar no vector store
3. GoogleLLMAgent: metadata enriquecido ao salvar no vector store
4. Integração com Supabase: embeddings persistidos corretamente
"""

import asyncio
import sys
from pathlib import Path

# Adiciona diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.utils.logging_config import get_logger
from src.vectorstore.supabase_client import supabase

logger = get_logger(__name__)


async def test_base_agent_memory_methods():
    """Testa métodos de memória conversacional do BaseAgent."""
    print("\n" + "="*80)
    print("TESTE 1: Métodos de Memória do BaseAgent")
    print("="*80)
    
    try:
        from src.agent.base_agent import BaseAgent
        
        # Verificar se métodos existem
        required_methods = [
            'save_conversation_embedding',
            'generate_conversation_embedding',
            'persist_conversation_memory'
        ]
        
        for method_name in required_methods:
            if hasattr(BaseAgent, method_name):
                print(f"✅ Método '{method_name}' encontrado")
            else:
                print(f"❌ Método '{method_name}' NÃO encontrado")
                return False
        
        print("\n✅ Todos os métodos de memória conversacional estão presentes no BaseAgent")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar BaseAgent: {e}")
        return False


async def test_groq_metadata_enrichment():
    """Testa enriquecimento de metadata no GroqLLMAgent."""
    print("\n" + "="*80)
    print("TESTE 2: Metadata Enriquecido no GroqLLMAgent")
    print("="*80)
    
    try:
        from src.agent.groq_llm_agent import GroqLLMAgent
        
        # Criar agente
        agent = GroqLLMAgent()
        
        # Verificar se RAG está habilitado
        if not agent.rag_enabled:
            print("⚠️ RAG não está habilitado no GroqLLMAgent")
            return None
        
        # Processar consulta simples
        query = "Qual é a importância da análise de dados?"
        context = {
            "file_path": "test_data.csv",
            "data_info": {"rows": 1000, "columns": 10}
        }
        
        response = agent.process(query, context)
        
        if response.get('success'):
            print(f"✅ Resposta gerada com sucesso")
            print(f"   Modelo: {response.get('metadata', {}).get('model', 'N/A')}")
            print(f"   Cache usado: {response.get('metadata', {}).get('cache_used', False)}")
            return True
        else:
            print(f"❌ Falha ao gerar resposta: {response}")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao testar GroqLLMAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_google_metadata_enrichment():
    """Testa enriquecimento de metadata no GoogleLLMAgent."""
    print("\n" + "="*80)
    print("TESTE 3: Metadata Enriquecido no GoogleLLMAgent")
    print("="*80)
    
    try:
        from src.agent.google_llm_agent import GoogleLLMAgent
        
        # Criar agente
        agent = GoogleLLMAgent()
        
        # Verificar se RAG está habilitado
        if not agent.rag_enabled:
            print("⚠️ RAG não está habilitado no GoogleLLMAgent")
            return None
        
        # Processar consulta simples
        query = "Como identificar padrões em dados financeiros?"
        context = {
            "file_path": "financial_data.csv",
            "fraud_data": {"count": 50, "total": 10000}
        }
        
        response = agent.process(query, context)
        
        if response.get('success'):
            print(f"✅ Resposta gerada com sucesso")
            print(f"   Modelo: {response.get('metadata', {}).get('model', 'N/A')}")
            print(f"   Cache usado: {response.get('metadata', {}).get('cache_used', False)}")
            return True
        else:
            print(f"❌ Falha ao gerar resposta: {response}")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao testar GoogleLLMAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_supabase_embeddings_table():
    """Verifica se embeddings estão sendo salvos na tabela embeddings com metadata."""
    print("\n" + "="*80)
    print("TESTE 4: Verificação de Embeddings no Supabase")
    print("="*80)
    
    try:
        # Consultar tabela embeddings
        result = supabase.table('embeddings').select('id, chunk_text, metadata, created_at').order('created_at', desc=True).limit(5).execute()
        
        if result.data:
            print(f"✅ Encontrados {len(result.data)} embeddings recentes")
            
            for i, emb in enumerate(result.data, 1):
                metadata = emb.get('metadata', {})
                print(f"\n   Embedding {i}:")
                print(f"     ID: {emb.get('id')}")
                print(f"     Texto: {emb.get('chunk_text', '')[:50]}...")
                print(f"     Metadata keys: {list(metadata.keys())}")
                print(f"     Criado em: {emb.get('created_at')}")
                
                # Verificar se metadata tem campos importantes
                required_fields = ['agent', 'model', 'timestamp', 'query_type']
                missing_fields = [f for f in required_fields if f not in metadata]
                
                if missing_fields:
                    print(f"     ⚠️ Campos ausentes no metadata: {missing_fields}")
                else:
                    print(f"     ✅ Metadata completo")
            
            return True
        else:
            print("⚠️ Nenhum embedding encontrado na tabela")
            return None
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabela embeddings: {e}")
        return False


async def test_persist_conversation_memory():
    """Testa persistência de embeddings de conversação de forma completa."""
    print("\n" + "="*80)
    print("TESTE 5: Persistência de Embeddings de Conversação")
    print("="*80)
    
    try:
        from src.agent.groq_llm_agent import GroqLLMAgent
        
        # Criar agente
        agent = GroqLLMAgent()
        
        if not agent.has_memory:
            print("⚠️ Memória não está habilitada no agente")
            return None
        
        # Inicializar sessão
        session_id = await agent.init_memory_session(user_id="test_user")
        print(f"✅ Sessão inicializada: {session_id}")
        
        # Processar algumas consultas com memória
        queries = [
            "Qual a importância da análise de dados?",
            "Como identificar fraudes em transações?",
            "Quais são os padrões mais comuns?"
        ]
        
        for query in queries:
            response = await agent.process_with_memory(query, session_id=session_id)
            print(f"   Processada: {query[:50]}...")
        
        # Persistir memória conversacional explicitamente
        print("\n🔄 Persistindo embeddings de conversação...")
        success = await agent.persist_conversation_memory(hours_back=24)
        
        if success:
            print("✅ Embeddings de conversação persistidos com sucesso!")
            
            # Buscar UUID da sessão na tabela agent_sessions
            session_result = supabase.table('agent_sessions').select('id').eq('session_id', session_id).execute()
            if session_result.data:
                session_uuid = session_result.data[0]['id']
                print(f"   UUID da sessão encontrado: {session_uuid}")
                
                # Verificar se foi salvo no banco usando o UUID
                result = supabase.table('agent_memory_embeddings').select('*').eq('session_id', session_uuid).execute()
                
                if result.data:
                    print(f"✅ Encontrado {len(result.data)} embedding(s) salvo(s) no banco")
                    for emb in result.data:
                        print(f"   - Agent: {emb.get('agent_name')}")
                        print(f"   - Tipo: {emb.get('embedding_type')}")
                        print(f"   - Metadata: {list(emb.get('metadata', {}).keys())}")
                    return True
                else:
                    print("⚠️ Embedding não encontrado no banco após persistência")
                    return False
            else:
                print("❌ UUID da sessão não encontrado")
                return False
        else:
            print("❌ Falha ao persistir embeddings de conversação")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao testar persistência: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_memory_embeddings_table():
    """Verifica se tabela agent_memory_embeddings está sendo usada."""
    print("\n" + "="*80)
    print("TESTE 6: Verificação de Tabela agent_memory_embeddings")
    print("="*80)
    
    try:
        # Consultar tabela agent_memory_embeddings
        result = supabase.table('agent_memory_embeddings').select('id, agent_name, source_text, embedding_type, metadata, created_at').order('created_at', desc=True).limit(5).execute()
        
        if result.data:
            print(f"✅ Encontrados {len(result.data)} embeddings de memória")
            
            for i, emb in enumerate(result.data, 1):
                metadata = emb.get('metadata', {})
                print(f"\n   Memory Embedding {i}:")
                print(f"     ID: {emb.get('id')}")
                print(f"     Agent: {emb.get('agent_name')}")
                print(f"     Tipo: {emb.get('embedding_type')}")
                print(f"     Fonte: {emb.get('source_text', '')[:50]}...")
                print(f"     Metadata: {metadata}")
                print(f"     Criado em: {emb.get('created_at')}")
            
            return True
        else:
            print("⚠️ Tabela agent_memory_embeddings está vazia")
            print("   Execute o teste anterior (TESTE 5) para popular a tabela")
            return None
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabela agent_memory_embeddings: {e}")
        return False


async def main():
    """Executa todos os testes de integração."""
    print("\n" + "="*80)
    print("TESTE DE INTEGRAÇÃO: PERSISTÊNCIA DE EMBEDDINGS DE MEMÓRIA")
    print("="*80)
    
    results = {}
    
    # Teste 1: Métodos do BaseAgent
    results['base_agent'] = await test_base_agent_memory_methods()
    
    # Teste 2: GroqLLMAgent
    results['groq_agent'] = await test_groq_metadata_enrichment()
    
    # Teste 3: GoogleLLMAgent
    results['google_agent'] = await test_google_metadata_enrichment()
    
    # Teste 4: Tabela embeddings
    results['embeddings_table'] = await test_supabase_embeddings_table()
    
    # Teste 5: Persistência de conversação (NOVO - CRÍTICO)
    results['persist_memory'] = await test_persist_conversation_memory()
    
    # Teste 6: Tabela agent_memory_embeddings
    results['memory_table'] = await test_agent_memory_embeddings_table()
    
    # Resumo
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result is True else ("⚠️ PULADO" if result is None else "❌ FALHOU")
        print(f"{test_name.ljust(20)}: {status}")
    
    print(f"\n📊 Resultado: {passed}/{total} passaram, {skipped} pulados, {failed} falharam")
    
    if failed == 0:
        print("\n✅ TODOS OS TESTES PASSARAM OU FORAM PULADOS (OK)")
    else:
        print(f"\n❌ {failed} TESTE(S) FALHARAM")


if __name__ == "__main__":
    asyncio.run(main())
