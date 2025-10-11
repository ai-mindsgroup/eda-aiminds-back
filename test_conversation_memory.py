#!/usr/bin/env python3
"""Script para testar memória conversacional do RAGDataAgent."""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.rag_data_agent import RAGDataAgent

async def main():
    """Testa sequência de perguntas com memória."""
    print("🧪 Testando memória conversacional do RAGDataAgent...\n")
    
    # Inicializar agente
    agent = RAGDataAgent()
    print("✅ Agente inicializado\n")
    
    # Inicializar sessão de memória (gera session_id automaticamente)
    session_id = await agent.init_memory_session()
    print(f"✅ Sessão criada: {session_id}\n")
    
    # Query 1: Pergunta inicial sobre tipos de dados
    query1 = "Quais são os tipos de dados (numéricos, categóricos)?"
    print(f"📝 Query 1: {query1}")
    result1 = await agent.process(query1, session_id=session_id)
    print(f"📊 RESPOSTA 1:")
    print("=" * 70)
    print(result1['content'][:500])  # Primeiros 500 chars
    print("=" * 70)
    print()
    
    # Query 2: Pergunta de follow-up sobre variabilidade
    await asyncio.sleep(2)  # Aguardar 2 segundos
    query2 = "Qual a variabilidade dos dados (desvio padrão, variância)?"
    print(f"📝 Query 2 (follow-up): {query2}")
    result2 = await agent.process(query2, session_id=session_id)
    print(f"📊 RESPOSTA 2:")
    print("=" * 70)
    print(result2['content'][:800])  # Primeiros 800 chars
    print("=" * 70)
    print()
    
    # Verificar se o histórico foi usado
    if "anterior" in result2['content'].lower() or "pergunta" in result2['content'].lower():
        print("✅ SUCESSO: Agente usou o histórico da conversa!")
    else:
        print("⚠️ ATENÇÃO: Agente pode não ter usado o histórico corretamente")

if __name__ == "__main__":
    asyncio.run(main())
