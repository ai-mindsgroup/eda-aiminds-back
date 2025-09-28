#!/usr/bin/env python3
"""
Teste: Verificar se consultas LLM são armazenadas no banco vetorial
==================================================================
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.embeddings.vector_store import VectorStore
from src.agent.orchestrator_agent import OrchestratorAgent

def main():
    print('🔍 VERIFICANDO INTEGRAÇÃO LLM + BANCO VETORIAL')
    print('=' * 60)

    # Verificar estado atual do banco vetorial
    try:
        vector_store = VectorStore()
        # Contar embeddings diretamente
        from src.vectorstore.supabase_client import supabase
        result = supabase.table('embeddings').select('id').execute()
        embeddings_before = len(result.data)
        
        print('📊 Estado inicial do banco vetorial:')
        print(f'   Total embeddings: {embeddings_before}')
        print()
    except Exception as e:
        print(f'❌ Erro ao acessar banco vetorial: {e}')
        embeddings_before = 0
        print()

    # Testar consulta LLM
    print('🤖 Inicializando orquestrador...')
    orchestrator = OrchestratorAgent()
    print()

    print('🧪 Testando consulta LLM:')
    query = 'explique os padrões de fraude em dados financeiros'
    print(f'Query: "{query}"')
    print()

    result = orchestrator.process(query)

    # Verificar se foi para LLM
    metadata = result.get('metadata', {})
    orchestrator_meta = metadata.get('orchestrator', {})  
    agents_used = orchestrator_meta.get('agents_used', [])
    llm_used = metadata.get('llm_used', False)

    print('📋 Resultado da consulta:')
    print(f'   Agentes usados: {agents_used}')
    print(f'   LLM usado: {llm_used}')
    print(f'   Resposta gerada: {len(result.get("content", ""))} caracteres')
    print()

    # Verificar se algo foi salvo no banco vetorial APÓS a consulta
    try:
        result_after = supabase.table('embeddings').select('id').execute()
        embeddings_after = len(result_after.data)
        new_embeddings = embeddings_after - embeddings_before
        
        print('📊 Comparação banco vetorial:')
        print(f'   Embeddings antes: {embeddings_before}')
        print(f'   Embeddings depois: {embeddings_after}')
        print(f'   ➡️ Novos embeddings criados: {new_embeddings}')
        print()
        
        if new_embeddings == 0:
            print('⚠️ DESCOBERTA: Consulta LLM NÃO foi armazenada no banco vetorial')
            print('   ❌ O GoogleLLMAgent funciona independentemente do sistema RAG')
            print('   📝 Consultas e respostas não são persistidas para busca futura')
        else:
            print('✅ DESCOBERTA: Consulta LLM foi armazenada no banco vetorial')
            print('   ✅ Sistema integrado - pode reusar conhecimento de consultas passadas')
            
    except Exception as e:
        print(f'❌ Erro ao verificar novos embeddings: {e}')

if __name__ == "__main__":
    main()