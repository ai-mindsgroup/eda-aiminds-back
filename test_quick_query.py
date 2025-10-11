#!/usr/bin/env python3
"""Script rápido para testar uma query específica sem interface completa."""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.rag_data_agent import RAGDataAgent

async def main():
    """Testa query diretamente no RAGDataAgent."""
    print("🧪 Testando RAGDataAgent diretamente...")
    
    # Inicializar agente
    agent = RAGDataAgent()
    print("✅ Agente inicializado\n")
    
    # Query de teste
    query = "Quais são os tipos de dados (numéricos, categóricos)?"
    print(f"📝 Query: {query}\n")
    
    # Processar (método assíncrono)
    result = await agent.process(query, {})
    print("📊 RESPOSTA:")
    print("=" * 70)
    print(result)
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
