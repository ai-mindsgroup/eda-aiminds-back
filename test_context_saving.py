import asyncio
from src.agent.rag_data_agent import RAGDataAgent

async def test_context_saving():
    agent = RAGDataAgent()
    session_id = await agent.init_memory_session()
    print(f'Sessão criada: {session_id}')

    # Processar uma query que contenha termos dos chunks
    result = await agent.process('Análise de detecção de fraude em cartão de crédito com features PCA', session_id=session_id)
    content = result.get('content', 'Sem conteúdo')
    print(f'Resultado: {content[:100]}...')

    # Verificar se contexto foi salvo
    from src.vectorstore.supabase_client import supabase
    
    # Buscar UUID da sessão
    session_result = supabase.table('agent_sessions').select('id').eq('session_id', session_id).execute()
    if session_result.data:
        session_uuid = session_result.data[0]['id']
        print(f'UUID da sessão encontrado: {session_uuid}')
        
        context_result = supabase.table('agent_context').select('*').eq('session_id', session_uuid).execute()
        print(f'Contextos salvos: {len(context_result.data)}')
        if context_result.data:
            for ctx in context_result.data:
                print(f'  - Tipo: {ctx["context_type"]}, Chave: {ctx["context_key"]}')
                print(f'  - Dados: {ctx["context_data"]}')
    else:
        print('UUID da sessão não encontrado')

if __name__ == "__main__":
    asyncio.run(test_context_saving())