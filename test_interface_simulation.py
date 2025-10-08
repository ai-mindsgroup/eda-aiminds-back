"""
Simula as interações da `interface_interativa.py` sem entrar em modo interativo.
Envia uma sequência de queries e imprime respostas e metadados.
"""
import asyncio
from uuid import uuid4
from src.agent.data_ingestor import DataIngestor
from src.agent.orchestrator_agent import OrchestratorAgent

async def run_simulation():
    session_id = str(uuid4())
    print(f"Sessão simulada: {session_id}")

    # Ingestão (igual ao que a interface faz)
    ingestor = DataIngestor()
    ingestor.ingest_csv('data/creditcard.csv')

    # Inicializar orchestrator
    orchestrator = OrchestratorAgent(enable_csv_agent=True, enable_rag_agent=True, enable_data_processor=True)

    queries = [
        'status',
        'Quais são os tipos de dados?',
        'Qual a distribuição de cada variável (histogramas)?',
        'Qual foi a pergunta anterior?'
    ]

    for q in queries:
        print('\n' + '-'*60)
        print(f'Query: {q}')
        if q == 'status':
            print('STATUS (local)')
            continue
        resp = await orchestrator.process_with_persistent_memory(q, context={}, session_id=session_id)
        print('Resposta:', resp.get('content')[:300] if resp.get('content') else 'Nenhuma')
        print('Metadata:', resp.get('metadata'))

if __name__ == '__main__':
    asyncio.run(run_simulation())
