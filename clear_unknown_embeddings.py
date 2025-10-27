"""
Script para limpar embeddings com source_id='unknown' antes de refazer a ingestão correta.
"""

from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger("clear_unknown_embeddings")

def clear_unknown_embeddings():
    """Remove todos os embeddings com source_id='unknown' ou null."""
    
    logger.info("🗑️ Removendo embeddings com source_id='unknown' ou null...")
    
    try:
        # Buscar embeddings com source_id='unknown' ou null
        response = supabase.table('embeddings')\
            .select('id, metadata')\
            .or_('metadata->>source_id.eq.unknown,metadata->>source_id.is.null')\
            .execute()
        
        if not response.data:
            logger.info("✅ Nenhum embedding com source_id='unknown' encontrado")
            return
        
        ids_to_delete = [row['id'] for row in response.data]
        
        logger.info(f"📊 Encontrados {len(ids_to_delete)} embeddings com source_id='unknown'")
        
        # Confirmar antes de deletar
        confirm = input(f"\n⚠️  ATENÇÃO: Você está prestes a deletar {len(ids_to_delete)} embeddings.\nDigite 'SIM' para confirmar: ")
        
        if confirm != 'SIM':
            logger.info("❌ Operação cancelada pelo usuário")
            return
        
        # Deletar em lote
        logger.info("🗑️ Deletando embeddings...")
        
        for embedding_id in ids_to_delete:
            supabase.table('embeddings').delete().eq('id', embedding_id).execute()
        
        logger.info(f"✅ {len(ids_to_delete)} embeddings removidos com sucesso!")
        logger.info("\n📌 Próximo passo: Execute a reingestão com:")
        logger.info("   python reingest_csv.py <SEU_ARQUIVO.csv>")
        logger.info("\nExemplo:")
        logger.info("   python reingest_csv.py creditcard.csv")
    
    except Exception as e:
        logger.error(f"❌ Erro ao limpar embeddings: {e}")
        raise


if __name__ == "__main__":
    clear_unknown_embeddings()
