"""Cliente Google Drive para monitoramento e download de arquivos CSV.

Este módulo fornece:
- Autenticação OAuth2 com Google Drive API
- Listagem de arquivos em pasta específica
- Download de arquivos CSV
- Gerenciamento seguro de credenciais e tokens
"""
from __future__ import annotations

import io
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

from src.settings import (
    GOOGLE_DRIVE_CREDENTIALS_FILE,
    GOOGLE_DRIVE_TOKEN_FILE,
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_DRIVE_ENABLED,
    AUTO_INGEST_FILE_PATTERN
)

logger = logging.getLogger("eda.google_drive_client")

# Escopos necessários para ler arquivos do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveClientError(Exception):
    """Exceção base para erros do cliente Google Drive."""
    pass


class GoogleDriveClient:
    """Cliente para interagir com Google Drive API.
    
    Responsabilidades:
    - Autenticar via OAuth2
    - Listar arquivos CSV em pasta monitorada
    - Fazer download de arquivos
    - Gerenciar estado de sincronização
    """
    
    def __init__(
        self,
        credentials_file: Optional[Path] = None,
        token_file: Optional[Path] = None,
        folder_id: Optional[str] = None,
        file_pattern: Optional[str] = None
    ):
        """Inicializa o cliente Google Drive.
        
        Args:
            credentials_file: Caminho para o arquivo de credenciais OAuth2
            token_file: Caminho para armazenar token de autenticação
            folder_id: ID da pasta do Google Drive a monitorar
            file_pattern: Padrão regex para filtrar arquivos
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            raise GoogleDriveClientError(
                "Bibliotecas do Google Drive não instaladas. "
                "Execute: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        if not GOOGLE_DRIVE_ENABLED:
            logger.warning("Google Drive está desabilitado nas configurações (GOOGLE_DRIVE_ENABLED=false)")
        
        self.credentials_file = credentials_file or GOOGLE_DRIVE_CREDENTIALS_FILE
        self.token_file = token_file or GOOGLE_DRIVE_TOKEN_FILE
        self.folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID
        self.file_pattern = re.compile(file_pattern or AUTO_INGEST_FILE_PATTERN)
        
        self.service = None
        self._downloaded_files: set[str] = set()  # IDs de arquivos já processados
        
        logger.info(f"Google Drive Client inicializado (enabled={GOOGLE_DRIVE_ENABLED})")
        logger.info(f"  Credentials: {self.credentials_file}")
        logger.info(f"  Token: {self.token_file}")
        logger.info(f"  Folder ID: {self.folder_id}")
        logger.info(f"  File pattern: {self.file_pattern.pattern}")
    
    def authenticate(self) -> None:
        """Autentica com Google Drive API usando OAuth2.
        
        Processo:
        1. Verifica se existe token válido salvo
        2. Se token expirado, tenta renovar
        3. Se não tem token, inicia fluxo OAuth2
        4. Salva token para reutilização
        
        Raises:
            GoogleDriveClientError: Se autenticação falhar
        """
        creds = None
        
        # Verifica se já existe token salvo
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
                logger.info("Token de autenticação carregado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao carregar token: {e}")
        
        # Se não tem credenciais válidas, autentica
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Renovando token expirado...")
                    creds.refresh(Request())
                    logger.info("Token renovado com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao renovar token: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_file.exists():
                    raise GoogleDriveClientError(
                        f"Arquivo de credenciais não encontrado: {self.credentials_file}\n"
                        "Obtenha as credenciais em: https://console.cloud.google.com/apis/credentials"
                    )
                
                try:
                    logger.info("Iniciando fluxo de autenticação OAuth2...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Autenticação OAuth2 concluída com sucesso")
                except Exception as e:
                    raise GoogleDriveClientError(f"Erro na autenticação OAuth2: {e}")
            
            # Salva token para reutilização
            try:
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"Token salvo em: {self.token_file}")
            except Exception as e:
                logger.warning(f"Erro ao salvar token: {e}")
        
        # Cria serviço da API
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Serviço Google Drive API inicializado")
        except Exception as e:
            raise GoogleDriveClientError(f"Erro ao criar serviço Google Drive: {e}")
    
    def list_csv_files(self, only_new: bool = True) -> List[Dict[str, Any]]:
        """Lista arquivos CSV na pasta monitorada.
        
        Args:
            only_new: Se True, retorna apenas arquivos não processados
        
        Returns:
            Lista de dicionários com informações dos arquivos:
            {
                'id': str,
                'name': str,
                'mimeType': str,
                'size': int,
                'modifiedTime': str,
                'createdTime': str
            }
        
        Raises:
            GoogleDriveClientError: Se listagem falhar
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        if not self.folder_id:
            raise GoogleDriveClientError("GOOGLE_DRIVE_FOLDER_ID não configurado")
        
        try:
            # Query para buscar arquivos na pasta
            query = f"'{self.folder_id}' in parents and trashed=false"
            
            logger.info(f"Listando arquivos na pasta {self.folder_id}...")
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime, createdTime)",
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Encontrados {len(files)} arquivos totais")
            
            # Filtra por padrão CSV
            csv_files = []
            for file in files:
                if self.file_pattern.match(file['name']):
                    # Se only_new=True, ignora arquivos já processados
                    if only_new and file['id'] in self._downloaded_files:
                        logger.debug(f"Arquivo já processado: {file['name']}")
                        continue
                    csv_files.append(file)
            
            logger.info(f"Encontrados {len(csv_files)} arquivos CSV {'novos' if only_new else 'totais'}")
            
            return csv_files
            
        except HttpError as e:
            raise GoogleDriveClientError(f"Erro HTTP ao listar arquivos: {e}")
        except Exception as e:
            raise GoogleDriveClientError(f"Erro ao listar arquivos: {e}")
    
    def download_file(self, file_id: str, destination_path: Path) -> Path:
        """Faz download de um arquivo do Google Drive.
        
        Args:
            file_id: ID do arquivo no Google Drive
            destination_path: Caminho local onde salvar o arquivo
        
        Returns:
            Path do arquivo baixado
        
        Raises:
            GoogleDriveClientError: Se download falhar
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        try:
            # Obtém informações do arquivo
            file_metadata = self.service.files().get(fileId=file_id, fields='name,size').execute()
            file_name = file_metadata['name']
            file_size = int(file_metadata.get('size', 0))
            
            logger.info(f"Baixando arquivo: {file_name} ({file_size / 1024 / 1024:.2f} MB)")
            
            # Cria diretório se não existir
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Faz download
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}% completo")
            
            # Salva arquivo
            with open(destination_path, 'wb') as f:
                f.write(fh.getvalue())
            
            # Marca como baixado
            self._downloaded_files.add(file_id)
            
            logger.info(f"Arquivo salvo em: {destination_path}")
            return destination_path
            
        except HttpError as e:
            raise GoogleDriveClientError(f"Erro HTTP ao baixar arquivo: {e}")
        except Exception as e:
            raise GoogleDriveClientError(f"Erro ao baixar arquivo: {e}")
    
    def mark_as_downloaded(self, file_id: str) -> None:
        """Marca arquivo como já processado (sem baixar novamente).
        
        Args:
            file_id: ID do arquivo no Google Drive
        """
        self._downloaded_files.add(file_id)
        logger.debug(f"Arquivo {file_id} marcado como processado")
    
    def reset_download_history(self) -> None:
        """Limpa histórico de arquivos baixados (permite rebaixar todos)."""
        count = len(self._downloaded_files)
        self._downloaded_files.clear()
        logger.info(f"Histórico de downloads limpo ({count} arquivos)")
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Obtém informações detalhadas de um arquivo.
        
        Args:
            file_id: ID do arquivo no Google Drive
        
        Returns:
            Dicionário com informações do arquivo
        
        Raises:
            GoogleDriveClientError: Se consulta falhar
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime,parents'
            ).execute()
            
            return file_metadata
            
        except HttpError as e:
            raise GoogleDriveClientError(f"Erro HTTP ao obter informações do arquivo: {e}")
        except Exception as e:
            raise GoogleDriveClientError(f"Erro ao obter informações do arquivo: {e}")


def create_google_drive_client() -> GoogleDriveClient:
    """Factory function para criar e autenticar cliente Google Drive.
    
    Returns:
        Instância autenticada de GoogleDriveClient
    
    Raises:
        GoogleDriveClientError: Se criação ou autenticação falhar
    """
    try:
        client = GoogleDriveClient()
        client.authenticate()
        return client
    except Exception as e:
        logger.error(f"Erro ao criar cliente Google Drive: {e}")
        raise
