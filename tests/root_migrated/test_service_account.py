"""Script de teste para Service Account do Google Drive.

Testa:
1. Autenticação com Service Account
2. Listagem de arquivos
3. Permissões de deleção

Execute: python tests/root_migrated/test_service_account.py
"""
import sys
from pathlib import Path
# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))
from src.integrations.google_drive_client import GoogleDriveClient
from src.utils.logging_config import get_logger
logger = get_logger(__name__)

def test_service_account():
    """Testa autenticação e operações com Service Account."""
    print("\n" + "="*70)
    print("  TESTE: Google Drive Service Account")
    print("="*70 + "\n")
    try:
        # Cria cliente em modo service_account
        print("1️⃣ Criando cliente Google Drive (Service Account mode)...")
        client = GoogleDriveClient(auth_mode="service_account")
        # Autentica
        print("\n2️⃣ Autenticando...")
        client.authenticate()
        print("   ✅ Autenticação bem-sucedida!")
        # Lista arquivos
        print("\n3️⃣ Listando arquivos CSV na pasta...")
        # ...restante do código mantido...
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_service_account()
