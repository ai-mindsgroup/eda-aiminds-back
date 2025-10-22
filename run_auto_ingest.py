#!/usr/bin/env python3
"""Script principal para executar o serviço de ingestão automática de CSV.

Este script inicia o Auto Ingest Service que:
1. Monitora pasta do Google Drive
2. Baixa novos arquivos CSV automaticamente
3. Processa com RAGAgent (análise + embeddings)
4. Gerencia ciclo de vida dos arquivos (data -> processando -> processado)

Uso:
    python run_auto_ingest.py

    ou

    python run_auto_ingest.py --once  # Executa apenas um ciclo

Configuração:
    Configure as variáveis em configs/.env:
    - GOOGLE_DRIVE_ENABLED=true
    - GOOGLE_DRIVE_CREDENTIALS_FILE=...
    - GOOGLE_DRIVE_FOLDER_ID=...
    - AUTO_INGEST_POLLING_INTERVAL=300

Requisitos:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""
import sys
import argparse
import logging
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

# --- Verificação rápida de dependências críticas (evitar falhas quando chamado por outro processo)
def _ensure_dependency(module_name: str, pip_name: str | None = None) -> bool:
    """Tenta importar o módulo e, se não existir, instala usando o pip do Python atual.

    module_name: nome do módulo usado pelo Python (ex: 'googleapiclient')
    pip_name: nome do pacote PyPI (ex: 'google-api-python-client'). Se None, usa module_name.

    Retorna True se o módulo estiver disponível após a checagem/instalação.
    """
    try:
        __import__(module_name)
        return True
    except Exception:
        # Tenta instalar usando o pip do mesmo Python que executa este script
        try:
            import subprocess, sys
            logger = logging.getLogger(__name__)
            pkg = pip_name or module_name
            logger.info(f"Módulo '{module_name}' não encontrado. Instalando pacote PyPI '{pkg}'...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
            # tenta importar novamente
            __import__(module_name)
            logger.info(f"Pacote '{pkg}' instalado com sucesso e módulo '{module_name}' disponível.")
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Falha ao instalar pacote '{pkg}' para módulo '{module_name}': {e}")
            return False

# Verifica googleapiclient (módulo) mas instala pacote PyPI correto
_ensure_dependency('googleapiclient', 'google-api-python-client')

from src.services.auto_ingest_service import create_auto_ingest_service
from src.settings import (
    LOG_LEVEL,
    GOOGLE_DRIVE_ENABLED,
    AUTO_INGEST_POLLING_INTERVAL
)
from src.utils.logging_config import get_logger

# Configura logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/auto_ingest.log', encoding='utf-8')
    ]
)

logger = get_logger(__name__)


def print_banner():
    """Exibe banner de inicialização."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        📥 EDA AI MINDS - AUTO INGEST SERVICE 📥                 ║
║                                                                  ║
║   Sistema de Ingestão Automática de CSV do Google Drive         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

Configuração:
  • Google Drive: {"✅ Habilitado" if GOOGLE_DRIVE_ENABLED else "❌ Desabilitado"}
  • Polling: {AUTO_INGEST_POLLING_INTERVAL}s
  • Log Level: {LOG_LEVEL}

═══════════════════════════════════════════════════════════════════
"""
    print(banner)


def run_once():
    """Executa apenas um ciclo de verificação e processamento."""
    logger.info("🔄 Modo single-run: executando apenas um ciclo")
    
    try:
        # Arquivar último arquivo processado antes de novo processamento
        from src.data.csv_file_manager import create_csv_file_manager
        file_manager = create_csv_file_manager()
        file_manager.archive_last_processed_file()

        service = create_auto_ingest_service()

        # Inicializa Google Drive client se habilitado (necessário antes de _polling_cycle)
        if GOOGLE_DRIVE_ENABLED:
            logger.info("📁 Inicializando Google Drive client...")
            service._initialize_google_drive()

        service._polling_cycle()
        service._print_stats()
        logger.info("✅ Ciclo único concluído com sucesso")
        return 0
    except Exception as e:
        logger.error(f"❌ Erro no ciclo único: {e}", exc_info=True)
        return 1


def run_continuous():
    """Executa serviço em modo contínuo (loop de polling)."""
    logger.info("🔁 Modo contínuo: iniciando loop de polling")
    
    try:
        # Arquivar último arquivo processado antes de novo processamento
        from src.data.csv_file_manager import create_csv_file_manager
        file_manager = create_csv_file_manager()
        file_manager.archive_last_processed_file()

        service = create_auto_ingest_service()
        service.start()
        return 0
    except Exception as e:
        logger.error(f"❌ Erro fatal no serviço: {e}", exc_info=True)
        return 1


def main():
    # Teste inline: valida ingestão e loga resultado
    def test_ingest_flow():
        try:
            logger.info("[TESTE INLINE] Iniciando teste do fluxo de ingestão...")
            from src.vectorstore.supabase_client import supabase
            from src.embeddings.vector_store import VectorStore
            from src.agent.data_ingestor import atomic_ingestion_and_query
            import tempfile
            import shutil
            # Cria arquivo CSV temporário pequeno para teste
            temp_dir = tempfile.mkdtemp()
            temp_csv = Path(temp_dir) / "test_chunking.csv"
            with open(temp_csv, "w", encoding="utf-8") as f:
                f.write("col1,col2,col3\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n")
            vector_store = VectorStore()
            atomic_ingestion_and_query(str(temp_csv), supabase, vector_store)
            logger.info("[TESTE INLINE] Ingestão de teste concluída com sucesso.")
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"[TESTE INLINE] Erro no teste de ingestão: {e}")

    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Serviço de Ingestão Automática de CSV do Google Drive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Modo contínuo (padrão)
  python run_auto_ingest.py
  
  # Executa apenas um ciclo
  python run_auto_ingest.py --once
  
  # Define intervalo customizado (sobrescreve .env)
  python run_auto_ingest.py --interval 60

Configuração:
  Configure configs/.env com as variáveis necessárias:
  - GOOGLE_DRIVE_ENABLED=true
  - GOOGLE_DRIVE_CREDENTIALS_FILE=configs/google_drive_credentials.json
  - GOOGLE_DRIVE_FOLDER_ID=your_folder_id
  - AUTO_INGEST_POLLING_INTERVAL=300

Google Drive Setup:
  1. Acesse https://console.cloud.google.com/apis/credentials
  2. Crie credenciais OAuth 2.0
  3. Baixe o arquivo JSON como google_drive_credentials.json
  4. Configure o ID da pasta a monitorar
  5. Na primeira execução, autorize via navegador
        """
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Executa apenas um ciclo de verificação ao invés de loop contínuo'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        help='Intervalo de polling em segundos (sobrescreve .env)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Habilita modo debug (logging verbose)'
    )
    
    args = parser.parse_args()
    
    # Configura debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Modo debug habilitado")
    
    # Configura intervalo customizado
    if args.interval:
        import src.settings as settings
        settings.AUTO_INGEST_POLLING_INTERVAL = args.interval
        logger.info(f"Intervalo de polling customizado: {args.interval}s")
    
    # Verifica diretório de logs
    Path('logs').mkdir(exist_ok=True)
    
    # Exibe banner
    print_banner()
    
    # Executa serviço
    try:
        test_ingest_flow()
        if args.once:
            exit_code = run_once()
        else:
            exit_code = run_continuous()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 Encerrado pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erro não tratado: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
