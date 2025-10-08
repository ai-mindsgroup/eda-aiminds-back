#!/usr/bin/env python3
"""
Script de debug para testar resposta do RAGDataAgent.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agent.rag_data_agent import RAGDataAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def main():
    """Testa pergunta sobre intervalos diretamente no RAGDataAgent."""
    
    print("="*80)
    print("🔍 DEBUG: Testando RAGDataAgent diretamente")
    print("="*80)
    
    # Inicializar agente
    print("\n1️⃣ Inicializando RAGDataAgent...")
    agent = RAGDataAgent()
    print("✅ Agente inicializado")
    
    # Pergunta sobre intervalos
    query = "Qual o intervalo de cada variável (mínimo, máximo)?"
    print(f"\n2️⃣ Pergunta: {query}")
    
    # Processar
    print("\n3️⃣ Processando query...")
    result = await agent.process(query=query, context={})
    
    # Mostrar resultado
    print("\n" + "="*80)
    print("📊 RESULTADO:")
    print("="*80)
    
    if isinstance(result, dict):
        print(f"\n✅ Resposta:\n{result.get('response', result.get('content', 'N/A'))}")
        
        metadata = result.get('metadata', {})
        print(f"\n📋 Metadados:")
        print(f"  - Chunks encontrados: {metadata.get('chunks_found', 0)}")
        print(f"  - Chunks usados: {metadata.get('chunks_used', 0)}")
        print(f"  - Similaridade média: {metadata.get('avg_similarity', 0):.3f}")
        print(f"  - Similaridade top: {metadata.get('top_similarity', 0):.3f}")
        print(f"  - Método: {metadata.get('method', 'N/A')}")
        print(f"  - Fallback usado: {metadata.get('fallback_used', False)}")
    else:
        print(f"\n❌ Resultado inesperado: {result}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(main())
