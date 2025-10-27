"""
Script genérico para reingerir qualquer CSV com source_id automático.

Uso:
    python reingest_csv.py <nome_arquivo.csv>

Exemplo:
    python reingest_csv.py creditcard.csv
    python reingest_csv.py vendas.csv

O source_id será gerado automaticamente baseado no nome do arquivo + UUID.
"""
import sys
import uuid
from pathlib import Path
from src.agent.rag_agent import RAGAgent
from src.utils.logging_config import get_logger
from src.settings import EDA_DATA_DIR_PROCESSADO

logger = get_logger("reingest_csv")

def reingest_csv(csv_filename: str):
    """
    Reingere qualquer dataset CSV com source_id automático.
    
    Args:
        csv_filename: Nome do arquivo CSV (ex: 'creditcard.csv')
    """
    csv_path = EDA_DATA_DIR_PROCESSADO / csv_filename
    
    # Validar existência do arquivo
    if not csv_path.exists():
        logger.error(f"❌ Arquivo não encontrado: {csv_path}")
        logger.info(f"\nVerifique se o arquivo está em: {EDA_DATA_DIR_PROCESSADO}")
        return False
    
    # Gerar source_id automático (nome do arquivo sem extensão + UUID)
    # Garantir que apenas o nome base seja usado, mesmo que um caminho relativo seja passado
    base_name = Path(csv_filename).stem
    source_id = f"{base_name}_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"🚀 Iniciando reingestão do dataset: {csv_filename}")
    logger.info(f"   Caminho: {csv_path}")
    logger.info(f"   Source ID gerado: {source_id}")
    
    try:
        # Criar agente RAG
        agent = RAGAgent()

        # Ingerir CSV a partir do arquivo (assinatura correta)
        result = agent.ingest_csv_file(
            file_path=str(csv_path),
            source_id=source_id
        )

        logger.info("\n" + "="*80)
        logger.info("✅ RESULTADO DA INGESTÃO:")
        logger.info("="*80)
        logger.info(result.get('content', ''))
        logger.info("\nMetadados:")
        for key, value in result.get('metadata', {}).items():
            logger.info(f"  • {key}: {value}")

        logger.info(f"\n📌 Dataset: {csv_filename}")
        logger.info(f"   Source ID: {source_id}")
        logger.info("\n💡 Próximo passo: Verificar source_id dos embeddings")
        logger.info("   python check_source_ids.py")

        return True
    
    except Exception as e:
        logger.error(f"❌ Erro na reingestão: {e}")
        return False


if __name__ == "__main__":
    # Validar argumentos CLI
    if len(sys.argv) < 2:
        print("❌ Uso: python reingest_csv.py <nome_arquivo.csv>")
        print("\nExemplo:")
        print("  python reingest_csv.py creditcard.csv")
        print("  python reingest_csv.py vendas.csv")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    success = reingest_csv(csv_filename)
    
    sys.exit(0 if success else 1)
