#!/usr/bin/env python3
"""Script para listar arquivos no Google Drive e testar deleção."""
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.integrations.google_drive_client import GoogleDriveClient
from src.settings import (
    GOOGLE_DRIVE_CREDENTIALS_FILE,
    GOOGLE_DRIVE_TOKEN_FILE,
    GOOGLE_DRIVE_FOLDER_ID
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Lista arquivos disponíveis no Google Drive."""
    try:
        logger.info("=" * 70)
        logger.info("🔍 VERIFICANDO ARQUIVOS NO GOOGLE DRIVE")
        logger.info("=" * 70)
        
        # Inicializa cliente
        client = GoogleDriveClient(
            credentials_file=GOOGLE_DRIVE_CREDENTIALS_FILE,
            token_file=GOOGLE_DRIVE_TOKEN_FILE,
            folder_id=GOOGLE_DRIVE_FOLDER_ID
        )
        
        # Autentica
        logger.info("🔐 Autenticando...")
        client.authenticate()
        logger.info("✅ Autenticação bem-sucedida")
        
        # Lista arquivos
        logger.info(f"📁 Listando arquivos na pasta: {GOOGLE_DRIVE_FOLDER_ID}")
        files = client.list_csv_files()
        
        if not files:
            logger.warning("⚠️ Nenhum arquivo encontrado no Google Drive")
            logger.info("💡 Faça upload de um arquivo CSV para testar o sistema")
        else:
            logger.info(f"✅ Encontrados {len(files)} arquivo(s):")
            for i, file_info in enumerate(files, 1):
                logger.info(f"  {i}. {file_info['name']} (ID: {file_info['id']})")
        
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar arquivos: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
