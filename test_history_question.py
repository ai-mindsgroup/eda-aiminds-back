"""
Teste específico para pergunta sobre histórico da conversa.
Valida se o agente consegue responder "qual foi a pergunta anterior?"
"""

import asyncio
from src.agent.rag_data_agent import RAGDataAgent

async def test_history_question():
    print("🧪 Testando resposta sobre HISTÓRICO da conversa...\n")
    
    # Criar agente e inicializar sessão de memória (sem hardcode)
    agent = RAGDataAgent()
    session_id = await agent.init_memory_session()
    print(f"✅ Sessão criada: {session_id}\n")
    print("✅ Agente inicializado\n")
    
    # Primeira pergunta: sobre tipos
    print("📝 Query 1: Quais são os tipos de dados?")
    response1 = await agent.process("Quais são os tipos de dados?", session_id=session_id)
    print("📊 RESPOSTA 1:")
    print("=" * 70)
    print(response1.get('content', 'Sem resposta')[:500])
    print("=" * 70)
    print()
    
    # Aguardar para garantir que conversa foi salva
    await asyncio.sleep(2)
    
    # Segunda pergunta: sobre variabilidade
    print("📝 Query 2: Qual a variabilidade dos dados?")
    response2 = await agent.process("Qual a variabilidade dos dados?", session_id=session_id)
    print("📊 RESPOSTA 2:")
    print("=" * 70)
    print(response2.get('content', 'Sem resposta')[:500])
    print("=" * 70)
    print()
    
    # Aguardar para garantir que conversa foi salva
    await asyncio.sleep(2)
    
    # Terceira pergunta: SOBRE O HISTÓRICO
    print("📝 Query 3 (HISTÓRICO): Qual foi a pergunta anterior?")
    response3 = await agent.process("Qual foi a pergunta anterior?", session_id=session_id)
    print("📊 RESPOSTA 3:")
    print("=" * 70)
    print(response3.get('content', 'Sem resposta'))
    print("=" * 70)
    print()
    
    # Validar se resposta referencia histórico
    answer3 = (response3.get('content') or '').lower()
    if any(term in answer3 for term in ['variabilidade', 'desvio', 'pergunta anterior', 'você perguntou']):
        print("✅ SUCESSO: Agente respondeu corretamente sobre o histórico!")
    else:
        print("❌ FALHA: Agente não identificou a pergunta anterior")
        print(f"Resposta completa: {response3.get('answer')}")

if __name__ == "__main__":
    asyncio.run(test_history_question())
