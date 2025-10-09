"""Gerenciador de arquivos CSV para fluxo de ingestão automática.

Este módulo gerencia o ciclo de vida dos arquivos CSV:
1. data/ - Arquivos baixados do Google Drive
2. data/processando/ - Arquivos em processamento
3. data/processado/ - Arquivos já processados

Fornece:
- Movimentação segura de arquivos entre diretórios
- Validação de arquivos CSV
- Limpeza de arquivos antigos
- Tracking de estado de processamento
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import csv

from src.settings import (
    EDA_DATA_DIR,
    EDA_DATA_DIR_PROCESSANDO,
    EDA_DATA_DIR_PROCESSADO
)

logger = logging.getLogger("eda.csv_file_manager")


class CSVFileManagerError(Exception):
    """Exceção base para erros do gerenciador de arquivos CSV."""
    pass


class CSVFileManager:
    """Gerencia o ciclo de vida de arquivos CSV no sistema de ingestão.
    
    Responsabilidades:
    - Validar arquivos CSV
    - Mover arquivos entre estágios (download -> processando -> processado)
    - Listar arquivos em cada estágio
    - Limpar arquivos antigos processados
    - Fornecer caminhos centralizados
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        processando_dir: Optional[Path] = None,
        processado_dir: Optional[Path] = None
    ):
        """Inicializa o gerenciador de arquivos CSV.
        
        Args:
            data_dir: Diretório base para arquivos baixados
            processando_dir: Diretório para arquivos em processamento
            processado_dir: Diretório para arquivos já processados
        """
        self.data_dir = data_dir or EDA_DATA_DIR
        self.processando_dir = processando_dir or EDA_DATA_DIR_PROCESSANDO
        self.processado_dir = processado_dir or EDA_DATA_DIR_PROCESSADO
        
        # Cria diretórios se não existirem
        self._ensure_directories()
        
        logger.info("CSV File Manager inicializado")
        logger.info(f"  Data dir: {self.data_dir}")
        logger.info(f"  Processando dir: {self.processando_dir}")
        logger.info(f"  Processado dir: {self.processado_dir}")
    
    def _ensure_directories(self) -> None:
        """Garante que todos os diretórios necessários existam."""
        for directory in [self.data_dir, self.processando_dir, self.processado_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Diretório verificado: {directory}")
    
    def validate_csv(self, file_path: Path) -> bool:
        """Valida se o arquivo é um CSV válido.
        
        Args:
            file_path: Caminho do arquivo a validar
        
        Returns:
            True se válido, False caso contrário
        """
        try:
            # Verifica se arquivo existe
            if not file_path.exists():
                logger.warning(f"Arquivo não encontrado: {file_path}")
                return False
            
            # Verifica extensão
            if file_path.suffix.lower() != '.csv':
                logger.warning(f"Arquivo não é CSV: {file_path}")
                return False
            
            # Verifica se arquivo não está vazio
            if file_path.stat().st_size == 0:
                logger.warning(f"Arquivo CSV vazio: {file_path}")
                return False
            
            # Tenta ler primeira linha para validar formato
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                    if not header or len(header) == 0:
                        logger.warning(f"CSV sem cabeçalho: {file_path}")
                        return False
                except StopIteration:
                    logger.warning(f"CSV sem linhas: {file_path}")
                    return False
            
            logger.debug(f"CSV válido: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar CSV {file_path}: {e}")
            return False
    
    def move_to_processing(self, file_path: Path) -> Path:
        """Move arquivo da pasta data/ para processando/.
        
        Args:
            file_path: Caminho do arquivo na pasta data/
        
        Returns:
            Novo caminho do arquivo em processando/
        
        Raises:
            CSVFileManagerError: Se movimentação falhar
        """
        try:
            if not file_path.exists():
                raise CSVFileManagerError(f"Arquivo não encontrado: {file_path}")
            
            # Valida CSV antes de mover
            if not self.validate_csv(file_path):
                raise CSVFileManagerError(f"CSV inválido: {file_path}")
            
            # Define destino
            destination = self.processando_dir / file_path.name
            
            # Se já existe arquivo com mesmo nome, adiciona timestamp
            if destination.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = destination.stem
                suffix = destination.suffix
                destination = self.processando_dir / f"{stem}_{timestamp}{suffix}"
                logger.warning(f"Arquivo já existe, renomeando para: {destination.name}")
            
            # Move arquivo
            shutil.move(str(file_path), str(destination))
            logger.info(f"Arquivo movido para processamento: {file_path.name} -> {destination}")
            
            return destination
            
        except Exception as e:
            raise CSVFileManagerError(f"Erro ao mover arquivo para processamento: {e}")
    
    def move_to_processed(self, file_path: Path) -> Path:
        """Move arquivo da pasta processando/ para processado/.
        
        Args:
            file_path: Caminho do arquivo em processando/
        
        Returns:
            Novo caminho do arquivo em processado/
        
        Raises:
            CSVFileManagerError: Se movimentação falhar
        """
        try:
            if not file_path.exists():
                raise CSVFileManagerError(f"Arquivo não encontrado: {file_path}")
            
            # Define destino
            destination = self.processado_dir / file_path.name
            
            # Se já existe arquivo com mesmo nome, adiciona timestamp
            if destination.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                stem = destination.stem
                suffix = destination.suffix
                destination = self.processado_dir / f"{stem}_{timestamp}{suffix}"
                logger.warning(f"Arquivo já existe, renomeando para: {destination.name}")
            
            # Move arquivo
            shutil.move(str(file_path), str(destination))
            logger.info(f"Arquivo movido para processado: {file_path.name} -> {destination}")
            
            return destination
            
        except Exception as e:
            raise CSVFileManagerError(f"Erro ao mover arquivo para processado: {e}")
    
    def list_files_in_data(self) -> List[Path]:
        """Lista todos os arquivos CSV na pasta data/.
        
        Returns:
            Lista de caminhos de arquivos CSV
        """
        try:
            files = list(self.data_dir.glob("*.csv"))
            logger.debug(f"Encontrados {len(files)} arquivos CSV em data/")
            return files
        except Exception as e:
            logger.error(f"Erro ao listar arquivos em data/: {e}")
            return []
    
    def list_files_in_processing(self) -> List[Path]:
        """Lista todos os arquivos CSV na pasta processando/.
        
        Returns:
            Lista de caminhos de arquivos CSV
        """
        try:
            files = list(self.processando_dir.glob("*.csv"))
            logger.debug(f"Encontrados {len(files)} arquivos CSV em processando/")
            return files
        except Exception as e:
            logger.error(f"Erro ao listar arquivos em processando/: {e}")
            return []
    
    def list_files_in_processed(self) -> List[Path]:
        """Lista todos os arquivos CSV na pasta processado/.
        
        Returns:
            Lista de caminhos de arquivos CSV
        """
        try:
            files = list(self.processado_dir.glob("*.csv"))
            logger.debug(f"Encontrados {len(files)} arquivos CSV em processado/")
            return files
        except Exception as e:
            logger.error(f"Erro ao listar arquivos em processado/: {e}")
            return []
    
    def get_latest_processed_file(self) -> Optional[Path]:
        """Retorna o arquivo processado mais recente.
        
        Returns:
            Caminho do arquivo mais recente ou None se não houver arquivos
        """
        try:
            files = self.list_files_in_processed()
            if not files:
                return None
            
            # Ordena por data de modificação (mais recente primeiro)
            latest = max(files, key=lambda f: f.stat().st_mtime)
            logger.debug(f"Arquivo processado mais recente: {latest}")
            return latest
            
        except Exception as e:
            logger.error(f"Erro ao obter arquivo processado mais recente: {e}")
            return None
    
    def clean_old_processed_files(self, days_old: int = 30) -> int:
        """Remove arquivos processados mais antigos que X dias.
        
        Args:
            days_old: Número de dias para considerar arquivo antigo
        
        Returns:
            Número de arquivos removidos
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            files_removed = 0
            
            for file_path in self.list_files_in_processed():
                # Verifica data de modificação
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if modified_time < cutoff_date:
                    try:
                        file_path.unlink()
                        files_removed += 1
                        logger.info(f"Arquivo antigo removido: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Erro ao remover arquivo {file_path}: {e}")
            
            if files_removed > 0:
                logger.info(f"Limpeza concluída: {files_removed} arquivos removidos (>{days_old} dias)")
            else:
                logger.debug(f"Nenhum arquivo antigo encontrado (>{days_old} dias)")
            
            return files_removed
            
        except Exception as e:
            logger.error(f"Erro na limpeza de arquivos antigos: {e}")
            return 0
    
    def get_file_info(self, file_path: Path) -> dict:
        """Obtém informações detalhadas de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            Dicionário com informações do arquivo
        """
        try:
            if not file_path.exists():
                return {"error": "Arquivo não encontrado"}
            
            stat = file_path.stat()
            
            return {
                "name": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_valid_csv": self.validate_csv(file_path)
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações do arquivo {file_path}: {e}")
            return {"error": str(e)}


def create_csv_file_manager() -> CSVFileManager:
    """Factory function para criar gerenciador de arquivos CSV.
    
    Returns:
        Instância de CSVFileManager
    """
    return CSVFileManager()
