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
    from google.oauth2 import service_account
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
    GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE,
    GOOGLE_DRIVE_AUTH_MODE,
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_DRIVE_ENABLED,
    AUTO_INGEST_FILE_PATTERN
)

logger = logging.getLogger("eda.google_drive_client")

# Escopos necessários para ler E deletar arquivos do Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # Acesso a arquivos criados/abertos pelo app
    'https://www.googleapis.com/auth/drive'        # Acesso completo (necessário para delete)
]


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
        service_account_file: Optional[Path] = None,
        auth_mode: Optional[str] = None,
        folder_id: Optional[str] = None,
        file_pattern: Optional[str] = None
    ):
        """Inicializa o cliente Google Drive.
        
        Args:
            credentials_file: Caminho para o arquivo de credenciais OAuth2 (modo oauth)
            token_file: Caminho para armazenar token de autenticação (modo oauth)
            service_account_file: Caminho para credenciais Service Account (modo service_account)
            auth_mode: Modo de autenticação ("oauth" ou "service_account")
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
        
        self.auth_mode = auth_mode or GOOGLE_DRIVE_AUTH_MODE
        self.credentials_file = credentials_file or GOOGLE_DRIVE_CREDENTIALS_FILE
        self.token_file = token_file or GOOGLE_DRIVE_TOKEN_FILE
        self.service_account_file = service_account_file or GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE
        self.folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID
        self.file_pattern = re.compile(file_pattern or AUTO_INGEST_FILE_PATTERN)
        
        self.service = None
        self._downloaded_files: set[str] = set()  # IDs de arquivos já processados
        
        logger.info(f"Google Drive Client inicializado (enabled={GOOGLE_DRIVE_ENABLED})")
        logger.info(f"  Auth mode: {self.auth_mode}")
        if self.auth_mode == "service_account":
            logger.info(f"  Service Account: {self.service_account_file}")
        else:
            logger.info(f"  Credentials: {self.credentials_file}")
            logger.info(f"  Token: {self.token_file}")
        logger.info(f"  Folder ID: {self.folder_id}")
        logger.info(f"  File pattern: {self.file_pattern.pattern}")
    
    def authenticate(self) -> None:
        """Autentica com Google Drive API.
        
        Suporta dois modos:
        - OAuth2: Para aplicações que precisam acesso delegado do usuário
        - Service Account: Para aplicações server-side com acesso direto (RECOMENDADO)
        
        Service Account permite:
        - Acesso total sem interação do usuário
        - Deletar arquivos sem problemas de permissão
        - Compartilhar pasta uma vez e pronto
        
        Raises:
            GoogleDriveClientError: Se autenticação falhar
        """
        creds = None
        
        if self.auth_mode == "service_account":
            # ============================================================
            # MODO SERVICE ACCOUNT (Recomendado para automação)
            # ============================================================
            if not self.service_account_file.exists():
                raise GoogleDriveClientError(
                    f"Arquivo de Service Account não encontrado: {self.service_account_file}\n"
                    "Como criar:\n"
                    "1. Acesse: https://console.cloud.google.com/iam-admin/serviceaccounts\n"
                    "2. Crie Service Account\n"
                    "3. Baixe chave JSON\n"
                    "4. Compartilhe a pasta do Drive com o email do Service Account"
                )
            
            try:
                logger.info("Autenticando com Service Account...")
                creds = service_account.Credentials.from_service_account_file(
                    str(self.service_account_file),
                    scopes=SCOPES
                )
                logger.info("✅ Service Account autenticado com sucesso")
            except Exception as e:
                raise GoogleDriveClientError(f"Erro ao autenticar Service Account: {e}")
        
        else:
            # ============================================================
            # MODO OAUTH2 (Padrão, mas com limitações de permissão)
            # ============================================================
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
                        
                        # Detecta tipo de credencial (web ou installed)
                        import json
                        with open(self.credentials_file) as f:
                            creds_data = json.load(f)
                        
                        # Suporta tanto credenciais "web" quanto "installed"
                        if 'web' in creds_data:
                            logger.info("Detectado: credenciais tipo 'web' (aplicativo web)")
                            flow = InstalledAppFlow.from_client_secrets_file(
                                str(self.credentials_file), SCOPES
                            )
                            creds = flow.run_local_server(port=8080)
                        elif 'installed' in creds_data:
                            logger.info("Detectado: credenciais tipo 'installed' (aplicativo desktop)")
                            flow = InstalledAppFlow.from_client_secrets_file(
                                str(self.credentials_file), SCOPES
                            )
                            creds = flow.run_local_server(port=0)
                        else:
                            raise GoogleDriveClientError(
                                "Arquivo de credenciais inválido. Deve conter 'web' ou 'installed'."
                            )
                        
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
    
    def delete_file(self, file_id: str) -> None:
        """Deleta arquivo do Google Drive.
        
        ATENÇÃO: Esta operação é PERMANENTE! O arquivo será movido para lixeira.
        
        Args:
            file_id: ID do arquivo no Google Drive
        
        Raises:
            GoogleDriveClientError: Se deleção falhar
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        try:
            logger.info(f"🗑️ Deletando arquivo do Google Drive: {file_id}")
            
            # Tenta obter informações do arquivo antes de deletar (para logging)
            try:
                file_info = self.service.files().get(
                    fileId=file_id, 
                    fields='name,mimeType,size'
                ).execute()
                file_name = file_info.get('name', 'Desconhecido')
                logger.debug(f"   Arquivo a ser deletado: {file_name}")
            except Exception as info_error:
                logger.warning(f"   Não foi possível obter informações do arquivo: {info_error}")
                file_name = "Desconhecido"
            
            # Executa a deleção
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"✅ Arquivo '{file_name}' deletado com sucesso do Google Drive (ID: {file_id})")
            
            # Remove do histórico também
            if file_id in self._downloaded_files:
                self._downloaded_files.remove(file_id)
                logger.debug(f"   Arquivo removido do histórico de downloads")
                
        except HttpError as e:
            error_details = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            logger.error(f"❌ Erro HTTP ao deletar arquivo {file_id}: {error_details}")
            raise GoogleDriveClientError(f"Erro HTTP ao deletar arquivo: {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao deletar arquivo {file_id}: {e}")
            raise GoogleDriveClientError(f"Erro ao deletar arquivo: {e}")
    
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
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """Cria uma nova pasta no Google Drive.
        
        Args:
            folder_name: Nome da pasta a criar
            parent_folder_id: ID da pasta pai (None = raiz)
        
        Returns:
            ID da pasta criada
        
        Raises:
            GoogleDriveClientError: Se criação falhar
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"📁 Pasta criada: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except HttpError as e:
            raise GoogleDriveClientError(f"Erro HTTP ao criar pasta: {e}")
        except Exception as e:
            raise GoogleDriveClientError(f"Erro ao criar pasta: {e}")
    
    def find_folder_by_name(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """Busca pasta por nome.
        
        Args:
            folder_name: Nome da pasta a buscar
            parent_folder_id: ID da pasta pai (None = qualquer lugar)
        
        Returns:
            ID da pasta encontrada ou None
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"📁 Pasta encontrada: {folder_name} (ID: {folder_id})")
                return folder_id
            
            return None
            
        except HttpError as e:
            logger.error(f"Erro ao buscar pasta: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar pasta: {e}")
            return None
    
    def get_or_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """Obtém ID de pasta existente ou cria nova.
        
        Args:
            folder_name: Nome da pasta
            parent_folder_id: ID da pasta pai
        
        Returns:
            ID da pasta
        """
        # Tenta encontrar pasta existente
        folder_id = self.find_folder_by_name(folder_name, parent_folder_id)
        
        if folder_id:
            return folder_id
        
        # Se não encontrou, cria nova
        return self.create_folder(folder_name, parent_folder_id)
    
    def move_file(self, file_id: str, destination_folder_id: str) -> bool:
        """Move arquivo para outra pasta no Google Drive.
        
        Args:
            file_id: ID do arquivo a mover
            destination_folder_id: ID da pasta de destino
        
        Returns:
            True se movido com sucesso, False caso contrário
        
        Raises:
            GoogleDriveClientError: Se operação falhar
        """
        if not self.service:
            raise GoogleDriveClientError("Cliente não autenticado. Execute authenticate() primeiro.")
        
        try:
            # Obtém informações do arquivo (incluindo parents atuais)
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id,name,parents'
            ).execute()
            
            file_name = file_info.get('name', 'unknown')
            previous_parents = ','.join(file_info.get('parents', []))
            
            logger.info(f"📦 Movendo arquivo: {file_name} (ID: {file_id})")
            logger.debug(f"   De: {previous_parents} → Para: {destination_folder_id}")
            
            # Move arquivo (remove dos parents antigos e adiciona ao novo)
            self.service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields='id,name,parents'
            ).execute()
            
            logger.info(f"✅ Arquivo movido com sucesso: {file_name}")
            return True
            
        except HttpError as e:
            error_details = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
            logger.error(f"❌ Erro HTTP ao mover arquivo {file_id}: {error_details}")
            raise GoogleDriveClientError(f"Erro HTTP ao mover arquivo: {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao mover arquivo {file_id}: {e}")
            raise GoogleDriveClientError(f"Erro ao mover arquivo: {e}")


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
