"""
Script para reingerir o CSV com source_id correto após correção.
"""

from src.agent.rag_agent import RAGAgent
from src.utils.logging_config import get_logger

logger = get_logger("reingest_creditcard")

def reingest_creditcard():
    """Reingere o dataset creditcard.csv com source_id correto."""
    
    logger.info("🚀 Iniciando reingestão do dataset creditcard com source_id correto...")
    
    try:
        # Criar agente RAG
        agent = RAGAgent()
        
        # Ingerir CSV com source_id correto
        result = agent.ingest_csv_data(
            csv_path='data/processado/creditcard.csv',
            source_id='creditcard_7e30850a'
        )
        
        logger.info("\n" + "="*80)
        logger.info("✅ RESULTADO DA INGESTÃO:")
        logger.info("="*80)
        logger.info(result['response'])
        logger.info("\nMetadados:")
        for key, value in result.get('metadata', {}).items():
            logger.info(f"  • {key}: {value}")
        
        logger.info("\n📌 Próximo passo: Verificar source_id dos embeddings")
        logger.info("   python check_source_ids.py")
    
    except Exception as e:
        logger.error(f"❌ Erro na reingestão: {e}")
        raise


if __name__ == "__main__":
    reingest_creditcard()
