"""
Rotas para Autenticação
======================

Endpoints para autenticação e autorização (estrutura básica).
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.schemas import APIKeyRequest, APIKeyResponse, BaseResponse
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Sistema simples de API keys (em produção usar JWT + banco)
_api_keys: dict[str, dict] = {}
security = HTTPBearer(auto_error=False)


@router.post(
    "/api-key",
    response_model=APIKeyResponse,
    summary="Criar API Key",
    description="Gera uma nova chave de API para acesso ao sistema",
)
async def create_api_key(request: APIKeyRequest):
    """
    Cria uma nova chave de API.
    
    **Funcionalidades:**
    - Gera chave única e segura
    - Define permissões específicas
    - Configura data de expiração opcional
    - Registra criação para auditoria
    
    **Permissões disponíveis:**
    - **read**: Leitura de dados e consultas
    - **write**: Upload e modificação de dados
    - **admin**: Acesso administrativo completo
    """
    try:
        # Gerar chave única
        api_key = f"eda_{uuid.uuid4().hex}"
        key_id = f"key_{uuid.uuid4().hex[:12]}"
        
        # Armazenar informações da chave
        key_info = {
            'key_id': key_id,
            'api_key': api_key,
            'name': request.name,
            'permissions': request.permissions,
            'created_at': datetime.now(),
            'expires_at': request.expires_at,
            'is_active': True,
            'usage_count': 0,
            'last_used': None,
        }
        
        _api_keys[api_key] = key_info
        
        logger.info(f"🔑 Nova API key criada: {key_id} ({request.name})")
        
        return APIKeyResponse(
            success=True,
            message=f"API key '{request.name}' criada com sucesso",
            key_id=key_id,
            api_key=api_key,
            name=request.name,
            permissions=request.permissions,
            created_at=key_info['created_at'],
            expires_at=request.expires_at,
        )
        
    except Exception as e:
        logger.error(f"❌ Erro criando API key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno criando API key"
        )


@router.get(
    "/api-keys",
    summary="Listar API Keys",
    description="Lista todas as chaves de API ativas",
)
async def list_api_keys():
    """
    Lista todas as chaves de API registradas.
    
    **Informações retornadas:**
    - ID e nome da chave
    - Permissões configuradas
    - Data de criação e expiração
    - Estatísticas de uso
    - Status (ativa/inativa)
    """
    try:
        keys_info = []
        
        for api_key, key_data in _api_keys.items():
            # Não expor a chave completa na listagem
            masked_key = f"{api_key[:8]}...{api_key[-4:]}"
            
            keys_info.append({
                'key_id': key_data['key_id'],
                'masked_key': masked_key,
                'name': key_data['name'],
                'permissions': key_data['permissions'],
                'created_at': key_data['created_at'],
                'expires_at': key_data['expires_at'],
                'is_active': key_data['is_active'],
                'usage_count': key_data['usage_count'],
                'last_used': key_data['last_used'],
            })
        
        return {
            'success': True,
            'message': f'{len(keys_info)} chave(s) encontrada(s)',
            'api_keys': keys_info,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro listando API keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno listando API keys"
        )


@router.delete(
    "/api-key/{key_id}",
    summary="Revogar API Key",
    description="Revoga uma chave de API específica",
)
async def revoke_api_key(key_id: str):
    """
    Revoga uma chave de API.
    
    A chave será desativada e não poderá mais ser usada para autenticação.
    """
    try:
        # Procurar chave pelo ID
        key_found = None
        for api_key, key_data in _api_keys.items():
            if key_data['key_id'] == key_id:
                key_found = api_key
                break
        
        if not key_found:
            raise HTTPException(
                status_code=404,
                detail="API key não encontrada"
            )
        
        # Marcar como inativa ao invés de deletar (para auditoria)
        _api_keys[key_found]['is_active'] = False
        _api_keys[key_found]['revoked_at'] = datetime.now()
        
        key_name = _api_keys[key_found]['name']
        
        logger.info(f"🔒 API key revogada: {key_id} ({key_name})")
        
        return {
            'success': True,
            'message': f"API key '{key_name}' revogada com sucesso",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro revogando API key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno revogando API key"
        )


@router.get(
    "/validate",
    summary="Validar autenticação",
    description="Valida se a autenticação atual é válida",
)
async def validate_auth(credentials: Optional[HTTPAuthorizationCredentials] = security):
    """
    Valida autenticação atual.
    
    Verifica se a API key fornecida é válida e retorna informações sobre ela.
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Token de autenticação não fornecido"
            )
        
        api_key = credentials.credentials
        
        # Validar API key
        key_info = validate_api_key(api_key)
        
        return {
            'success': True,
            'message': 'Autenticação válida',
            'key_info': {
                'key_id': key_info['key_id'],
                'name': key_info['name'],
                'permissions': key_info['permissions'],
                'expires_at': key_info['expires_at'],
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro validando autenticação: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno validando autenticação"
        )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def validate_api_key(api_key: str) -> dict:
    """
    Valida uma API key e retorna suas informações.
    
    Raises:
        HTTPException: Se a chave for inválida, expirada ou inativa
    """
    if not api_key or api_key not in _api_keys:
        raise HTTPException(
            status_code=401,
            detail="API key inválida"
        )
    
    key_info = _api_keys[api_key]
    
    # Verificar se a chave está ativa
    if not key_info['is_active']:
        raise HTTPException(
            status_code=401,
            detail="API key revogada"
        )
    
    # Verificar expiração
    if key_info['expires_at'] and datetime.now() > key_info['expires_at']:
        raise HTTPException(
            status_code=401,
            detail="API key expirada"
        )
    
    # Atualizar estatísticas de uso
    key_info['usage_count'] += 1
    key_info['last_used'] = datetime.now()
    
    return key_info


def check_permission(api_key: str, required_permission: str) -> bool:
    """
    Verifica se uma API key tem permissão específica.
    
    Args:
        api_key: Chave de API
        required_permission: Permissão necessária (read/write/admin)
        
    Returns:
        bool: True se tem permissão, False caso contrário
    """
    try:
        key_info = validate_api_key(api_key)
        
        # Admin tem todas as permissões
        if 'admin' in key_info['permissions']:
            return True
        
        # Verificar permissão específica
        return required_permission in key_info['permissions']
        
    except HTTPException:
        return False


# ============================================================================
# MIDDLEWARE DE AUTENTICAÇÃO (para uso em outras rotas)
# ============================================================================

def require_auth(required_permission: str = "read"):
    """
    Decorator para exigir autenticação em rotas.
    
    Usage:
        @require_auth("write")
        async def protected_route():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # TODO: Implementar middleware real de autenticação
            # Por enquanto, permitir acesso livre para desenvolvimento
            return await func(*args, **kwargs)
        return wrapper
    return decorator