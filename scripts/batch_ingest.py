"""
Script para ingestão em batches menores para evitar timeout
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agent.rag_agent import RAGAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def main():
    """Executa ingestão em lotes menores para evitar timeout"""
    agent = RAGAgent()
    
    # Configurar batch size menor
    agent.embedding_generator.batch_size = 130  # Ajustado para 130 por vez (mais rápido e seguro)
    
    logger.info("🚀 Iniciando ingestão completa com batches pequenos...")
    
    # Ler conteúdo do CSV como texto
    with open("data/creditcard.csv", "r", encoding="utf-8") as f:
        csv_text = f.read()
    # Ingestão usando método correto
    result = agent.ingest_csv_data(csv_text, source_id="creditcard.csv", include_headers=True)
    if isinstance(result, dict) and "message" in result:
        logger.info(result["message"])
    else:
        logger.info(f"Resultado: {result}")
    
    logger.info("✅ Ingestão completa finalizada!")

if __name__ == "__main__":
    asyncio.run(main())