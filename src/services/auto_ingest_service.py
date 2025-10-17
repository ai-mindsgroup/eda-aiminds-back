"""Serviço de Ingestão Automática de CSV do Google Drive.

Este serviço orquestra todo o fluxo de ingestão automática:
1. Monitora pasta do Google Drive (polling)
2. Baixa novos arquivos CSV
3. Move para pasta 'processando'
4. Dispara fluxo de ingestão (DataIngestor)
5. Move para pasta 'processado' após sucesso
6. Atualiza referências para RAG agents

Funcionalidades:
- Polling configurável
- Tratamento robusto de erros
- Logging detalhado
- Retry em caso de falhas
- Limpeza automática de arquivos antigos

⚠️ COMPATIBILIDADE (2025-10-10):
Usa DataIngestor para manter a mesma lógica do interface_interativa.py:
- Limpa base vetorial antes da ingestão
- Gera análise estatística do CSV (2 chunks)
- Metadata simples: {'source': caminho_arquivo}
- Mesma qualidade/resultado que interface_interativa.py
"""
from __future__ import annotations

import time
import signal
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

from src.integrations.google_drive_client import (
    GoogleDriveClient,
    GoogleDriveClientError,
    create_google_drive_client,
    GOOGLE_DRIVE_AVAILABLE
)
from src.data.csv_file_manager import CSVFileManager, CSVFileManagerError, create_csv_file_manager
from src.agent.data_ingestor import DataIngestor
from src.embeddings.generator import EmbeddingProvider
from src.settings import (
    AUTO_INGEST_POLLING_INTERVAL,
    GOOGLE_DRIVE_ENABLED,
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_DRIVE_PROCESSED_FOLDER_ID,
    GOOGLE_DRIVE_POST_PROCESS_ACTION,
    EDA_DATA_DIR,
    EDA_DATA_DIR_PROCESSADO
)

logger = logging.getLogger("eda.auto_ingest_service")


class AutoIngestServiceError(Exception):
    """Exceção base para erros do serviço de ingestão automática."""
    pass


class AutoIngestService:
    """Serviço principal de ingestão automática de CSV.
    
    Responsabilidades:
    - Coordenar Google Drive client, File Manager e Data Ingestor
    - Implementar loop de polling
    - Gerenciar erros e retries
    - Fornecer interface de controle (start/stop)
    
    ⚠️ COMPATIBILIDADE: Usa DataIngestor para manter mesma lógica do interface_interativa.py
    """
    
    def __init__(
        self,
        google_drive_client: Optional[GoogleDriveClient] = None,
        file_manager: Optional[CSVFileManager] = None,
        data_ingestor: Optional[DataIngestor] = None,
        polling_interval: Optional[int] = None
    ):
        """Inicializa o serviço de ingestão automática.
        
        Args:
            google_drive_client: Cliente Google Drive (criado automaticamente se None)
            file_manager: Gerenciador de arquivos CSV
            data_ingestor: Ingestor de dados (mesma lógica do interface_interativa.py)
            polling_interval: Intervalo entre verificações (segundos)
        """
        self.polling_interval = polling_interval or AUTO_INGEST_POLLING_INTERVAL
        self.running = False
        self._stop_requested = False
        
        # Componentes
        self.google_drive_client = google_drive_client
        self.google_drive_processed_folder_id = None  # ID da pasta "processados" no Drive
        self.file_manager = file_manager or create_csv_file_manager()
        
        # ✅ COMPATIBILIDADE: Usa DataIngestor (mesma lógica do interface_interativa.py)
        self.data_ingestor = data_ingestor or DataIngestor()
        
        # Estatísticas
        self.stats = {
            "total_files_processed": 0,
            "total_files_failed": 0,
            "last_check": None,
            "last_success": None,
            "last_error": None,
            "uptime_start": None
        }
        
        logger.info("Auto Ingest Service inicializado")
        logger.info(f"  Polling interval: {self.polling_interval}s")
        logger.info(f"  Google Drive enabled: {GOOGLE_DRIVE_ENABLED}")
        logger.info(f"  Google Drive available: {GOOGLE_DRIVE_AVAILABLE}")
        logger.info(f"  ✅ Usando DataIngestor (compatibilidade interface_interativa.py)")
        
        # Configura tratamento de sinais para shutdown gracioso
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Configura handlers para sinais de interrupção."""
        def signal_handler(sig, frame):
            logger.info(f"\n🛑 Sinal {sig} recebido. Encerrando serviço...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _initialize_google_drive(self) -> bool:
        """Inicializa e autentica com Google Drive.
        
        Returns:
            True se sucesso, False caso contrário
        """
        if not GOOGLE_DRIVE_ENABLED:
            logger.warning("Google Drive está desabilitado (GOOGLE_DRIVE_ENABLED=false)")
            return False
        
        if not GOOGLE_DRIVE_AVAILABLE:
            logger.error("Bibliotecas do Google Drive não instaladas")
            logger.error("Execute: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False
        
        try:
            if not self.google_drive_client:
                logger.info("Criando e autenticando cliente Google Drive...")
                self.google_drive_client = create_google_drive_client()
                logger.info("✅ Cliente Google Drive autenticado com sucesso")
            
            # Configura pasta "processados" se usar ação "move"
            if GOOGLE_DRIVE_POST_PROCESS_ACTION == "move":
                self._setup_processed_folder()
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Google Drive: {e}")
            return False
    
    def _setup_processed_folder(self) -> None:
        """Configura pasta 'processados' no Google Drive."""
        try:
            # Usa ID fornecido ou cria/encontra pasta automaticamente
            if GOOGLE_DRIVE_PROCESSED_FOLDER_ID:
                self.google_drive_processed_folder_id = GOOGLE_DRIVE_PROCESSED_FOLDER_ID
                logger.info(f"📁 Pasta processados configurada: {self.google_drive_processed_folder_id}")
            else:
                # Cria/encontra pasta "processados" dentro da pasta monitorada
                folder_name = "processados"
                logger.info(f"📁 Procurando/criando pasta '{folder_name}'...")
                self.google_drive_processed_folder_id = self.google_drive_client.get_or_create_folder(
                    folder_name=folder_name,
                    parent_folder_id=GOOGLE_DRIVE_FOLDER_ID
                )
                logger.info(f"✅ Pasta processados pronta: {self.google_drive_processed_folder_id}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao configurar pasta processados: {e}")
            logger.warning(f"   Arquivos serão deletados em vez de movidos")
    
    def _process_file(self, file_path: Path) -> bool:
        """Processa um único arquivo CSV.
        
        Args:
            file_path: Caminho do arquivo a processar
        
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            logger.info(f"📄 Processando arquivo: {file_path.name}")
            # 1. Move para pasta 'processando'
            logger.info("  → Movendo para pasta 'processando'...")
            processing_path = self.file_manager.move_to_processing(file_path)
            # 2. Executa fluxo atômico de ingestão
            logger.info("  → Executando fluxo atômico de ingestão...")
            from src.vectorstore.supabase_client import supabase
            from src.embeddings.vector_store import VectorStore
            from src.agent.data_ingestor import atomic_ingestion_and_query
            vector_store = VectorStore()
            atomic_ingestion_and_query(str(processing_path), supabase, vector_store)
            logger.info("  ✅ Fluxo atômico de ingestão concluído com sucesso")
            # 3. Move para pasta 'processado'
            logger.info("  → Movendo para pasta 'processado'...")
            processed_path = self.file_manager.move_to_processed(processing_path)
            # 4. Atualiza estatísticas
            self.stats["total_files_processed"] += 1
            self.stats["last_success"] = datetime.now().isoformat()
            logger.info(f"✅ Arquivo processado com sucesso: {file_path.name}")
            logger.info(f"   Localização final: {processed_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao processar arquivo {file_path.name}: {e}")
            self.stats["total_files_failed"] += 1
            self.stats["last_error"] = str(e)
            return False

    def _check_and_process_new_files(self) -> int:
        """Verifica o Google Drive por novos CSVs e processa cada um.

        Retorna o número de arquivos processados neste ciclo.
        """
        files_processed = 0
        try:
            logger.debug("Verificando novos arquivos no Google Drive...")
            if not self.google_drive_client:
                logger.debug("Google Drive client não inicializado")
                return 0

            csv_files = self.google_drive_client.list_csv_files(only_new=True)
            if not csv_files:
                logger.debug("Nenhum arquivo novo encontrado")
                return 0

            logger.info(f"📥 Encontrados {len(csv_files)} novos arquivos CSV")

            for file_info in csv_files:
                file_id = file_info['id']
                file_name = file_info['name']
                try:
                    logger.info(f"  ⬇️ Baixando: {file_name}")
                    from src.settings import EDA_DATA_DIR_PROCESSANDO
                    download_path = EDA_DATA_DIR_PROCESSANDO / file_name
                    download_path.parent.mkdir(parents=True, exist_ok=True)
                    self.google_drive_client.download_file(file_id, download_path)
                    logger.info(f"  ✅ Arquivo baixado para: {download_path}")

                    # Processa usando o fluxo atômico (clean + ingest + refresh)
                    logger.info(f"  🔄 Iniciando processamento (fluxo atômico)...")
                    from src.vectorstore.supabase_client import supabase
                    from src.embeddings.vector_store import VectorStore
                    from src.agent.data_ingestor import atomic_ingestion_and_query
                    vector_store = VectorStore()
                    atomic_ingestion_and_query(str(download_path), supabase, vector_store)

                    # Move para processado
                    processed_path = self.file_manager.move_to_processed(download_path)
                    files_processed += 1
                    self.stats["total_files_processed"] += 1
                    self.stats["last_success"] = datetime.now().isoformat()

                    # Pós-processamento no Drive (move ou delete)
                    try:
                        if GOOGLE_DRIVE_POST_PROCESS_ACTION == "move" and self.google_drive_processed_folder_id:
                            logger.info(f"  📦 Movendo arquivo no Google Drive: {file_name} (ID: {file_id})")
                            self.google_drive_client.move_file(file_id, self.google_drive_processed_folder_id)
                            logger.info(f"  ✅ Arquivo movido para pasta 'processados' no Google Drive")
                        else:
                            logger.info(f"  🗑️ Removendo arquivo do Google Drive: {file_name} (ID: {file_id})")
                            self.google_drive_client.delete_file(file_id)
                            logger.info(f"  ✅ Arquivo removido do Google Drive com sucesso")
                        logger.info(f"  📋 Arquivo local salvo em: {processed_path}")
                    except Exception as del_error:
                        logger.error(f"  ⚠️ Erro ao finalizar arquivo no Drive: {del_error}")
                        logger.warning(f"  ⚠️ O arquivo permanecerá no Google Drive e pode ser reprocessado")

                except Exception as e:
                    logger.error(f"❌ Erro ao processar {file_name}: {e}")
                    self.stats["total_files_failed"] += 1
                    self.stats["last_error"] = str(e)
                    # Tentativa de fallback: se o arquivo local foi baixado, tentar fluxo atômico
                    try:
                        if 'download_path' in locals() and download_path.exists():
                            from src.vectorstore.supabase_client import supabase
                            from src.embeddings.vector_store import VectorStore
                            from src.agent.data_ingestor import atomic_ingestion_and_query
                            vector_store = VectorStore()
                            atomic_ingestion_and_query(str(download_path), supabase, vector_store)
                            logger.info("  ✅ Fluxo atômico de ingestão (fallback) concluído com sucesso")
                    except Exception as fallback_err:
                        logger.error(f"  ⚠️ Fallback de ingestão falhou: {fallback_err}")

        except Exception as e:
            logger.error(f"Erro ao verificar/processar arquivos do Drive: {e}")

        return files_processed

    def _check_local_files(self) -> int:
        """Verifica arquivos locais em `data/` e processa aqueles encontrados.

        Retorna o número de arquivos processados.
        """
        files_processed = 0
        try:
            local_files = self.file_manager.list_files_in_data()
            if not local_files:
                return 0

            logger.info(f"📂 Encontrados {len(local_files)} arquivos locais para processar")
            for file_path in local_files:
                if self._process_file(file_path):
                    files_processed += 1

            return files_processed
        except Exception as e:
            logger.error(f"Erro ao verificar arquivos locais: {e}")
            return files_processed
            
            return files_processed
            
        except Exception as e:
            logger.error(f"Erro ao verificar arquivos locais: {e}")
            return files_processed
    
    def _polling_cycle(self) -> None:
        """Executa um ciclo de verificação e processamento."""
        try:
            self.stats["last_check"] = datetime.now().isoformat()
            
            logger.info(f"🔍 Iniciando ciclo de verificação ({datetime.now().strftime('%H:%M:%S')})")
            
            total_processed = 0
            
            # 1. Verifica arquivos locais (colocados manualmente)
            local_processed = self._check_local_files()
            total_processed += local_processed
            
            # 2. Verifica Google Drive (se habilitado)
            if GOOGLE_DRIVE_ENABLED and self.google_drive_client:
                drive_processed = self._check_and_process_new_files()
                total_processed += drive_processed
            
            # 3. Limpeza de arquivos antigos (a cada 10 ciclos)
            if self.stats["total_files_processed"] % 10 == 0:
                logger.debug("🧹 Executando limpeza de arquivos antigos...")
                removed = self.file_manager.clean_old_processed_files(days_old=30)
                if removed > 0:
                    logger.info(f"  🗑️ Removidos {removed} arquivos antigos")
            
            if total_processed > 0:
                logger.info(f"✅ Ciclo concluído: {total_processed} arquivos processados")
            else:
                logger.debug("Ciclo concluído: nenhum arquivo novo")
            
        except Exception as e:
            logger.error(f"Erro no ciclo de polling: {e}")
    
    def start(self) -> None:
        """Inicia o serviço de ingestão automática (loop de polling)."""
        if self.running:
            logger.warning("Serviço já está em execução")
            return
        
        logger.info("=" * 70)
        logger.info("🚀 INICIANDO SERVIÇO DE INGESTÃO AUTOMÁTICA")
        logger.info("=" * 70)
        
        # Inicializa Google Drive se habilitado
        if GOOGLE_DRIVE_ENABLED:
            if not self._initialize_google_drive():
                logger.warning("⚠️ Google Drive não disponível - apenas arquivos locais serão processados")
        
        self.running = True
        self.stats["uptime_start"] = datetime.now().isoformat()
        
        logger.info(f"✅ Serviço iniciado com sucesso")
        logger.info(f"⏰ Intervalo de polling: {self.polling_interval}s")
        logger.info(f"📁 Diretório de dados: {EDA_DATA_DIR}")
        logger.info(f"📊 Diretório processado: {EDA_DATA_DIR_PROCESSADO}")
        logger.info("=" * 70)
        logger.info("💡 Pressione Ctrl+C para encerrar")
        logger.info("=" * 70)
        
        # Loop principal
        try:
            while self.running and not self._stop_requested:
                self._polling_cycle()
                
                # Aguarda próximo ciclo
                logger.debug(f"⏳ Aguardando {self.polling_interval}s até próxima verificação...")
                time.sleep(self.polling_interval)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Interrupção recebida via teclado")
        except Exception as e:
            logger.error(f"❌ Erro fatal no serviço: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Para o serviço de ingestão automática."""
        if not self.running:
            return
        
        logger.info("🛑 Encerrando serviço...")
        self._stop_requested = True
        self.running = False
        
        # Mostra estatísticas finais
        self._print_stats()
        
        logger.info("👋 Serviço encerrado")
    
    def _print_stats(self) -> None:
        """Imprime estatísticas do serviço."""
        logger.info("=" * 70)
        logger.info("📊 ESTATÍSTICAS DO SERVIÇO")
        logger.info("=" * 70)
        logger.info(f"  Arquivos processados: {self.stats['total_files_processed']}")
        logger.info(f"  Arquivos com erro: {self.stats['total_files_failed']}")
        
        if self.stats['uptime_start']:
            uptime_start = datetime.fromisoformat(self.stats['uptime_start'])
            uptime = datetime.now() - uptime_start
            logger.info(f"  Tempo de execução: {uptime}")
        
        if self.stats['last_success']:
            logger.info(f"  Último sucesso: {self.stats['last_success']}")
        
        if self.stats['last_error']:
            logger.info(f"  Último erro: {self.stats['last_error']}")
        
        logger.info("=" * 70)
    
    def get_status(self) -> dict:
        """Retorna status atual do serviço.
        
        Returns:
            Dicionário com informações de status
        """
        return {
            "running": self.running,
            "polling_interval": self.polling_interval,
            "google_drive_enabled": GOOGLE_DRIVE_ENABLED,
            "google_drive_available": GOOGLE_DRIVE_AVAILABLE and self.google_drive_client is not None,
            "stats": self.stats.copy(),
            "directories": {
                "data": str(EDA_DATA_DIR),
                "processando": str(self.file_manager.processando_dir),
                "processado": str(EDA_DATA_DIR_PROCESSADO)
            }
        }


def create_auto_ingest_service() -> AutoIngestService:
    """Factory function para criar serviço de ingestão automática.
    
    Returns:
        Instância de AutoIngestService
    """
    return AutoIngestService()
