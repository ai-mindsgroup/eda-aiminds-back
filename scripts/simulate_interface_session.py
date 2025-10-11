"""
Simula uma sessão equivalente à `interface_interativa.py` de forma não-interativa.
Executa: ingestão -> inicialização do Orchestrator -> sequência de queries com memória persistente.
"""
import asyncio
from uuid import uuid4
from pathlib import Path

from src.agent.data_ingestor import DataIngestor
from src.agent.orchestrator_agent import OrchestratorAgent

async def run_session():
    session_id = str(uuid4())
    print(f"🔑 Sessão simulada: {session_id}")

    # Ingestão (igual interface)
    print("🧹 Ingestão: limpando e carregando dataset...")
    ingestor = DataIngestor()
    ingestor.ingest_csv('data/creditcard.csv')
    print("✅ Ingestão concluída")

    # Inicializar orchestrator
    orchestrator = OrchestratorAgent(enable_csv_agent=True, enable_rag_agent=True, enable_data_processor=True)
    print("✅ Orchestrator inicializado")

    queries = [
        'status',
        'Quais são os tipos de dados?',
        'Qual a distribuição de cada variável (histogramas)?',
        'Qual foi a pergunta anterior?'
    ]

    for q in queries:
        print('\n' + '-'*60)
        print(f"👤 Usuário: {q}")
        if q.lower() == 'status':
            print("📊 (Comando status) — exibindo informações...")
            print(f"  • Agentes ativos: {len(orchestrator.agents)}")
            continue

        print("🤖 Processando...")
        response = await orchestrator.process_with_persistent_memory(q, context={}, session_id=session_id)
        print("🤖 Agente respondeu:")
        print(response.get('content') or response.get('response'))
        meta = response.get('metadata', {})
        print("-- METADADOS --")
        for k, v in meta.items():
            print(f"  {k}: {v}")

if __name__ == '__main__':
    asyncio.run(run_session())
