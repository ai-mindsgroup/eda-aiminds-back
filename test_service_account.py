"""Script de teste para Service Account do Google Drive.

Testa:
1. Autenticação com Service Account
2. Listagem de arquivos
3. Permissões de deleção

Execute: python test_service_account.py
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
        files = client.list_csv_files(only_new=False)
        
        if not files:
            print("   ℹ️ Nenhum arquivo CSV encontrado na pasta")
            print("   📝 Adicione arquivos CSV na pasta do Google Drive para testar")
        else:
            print(f"   ✅ Encontrados {len(files)} arquivo(s):")
            for i, file in enumerate(files, 1):
                print(f"      {i}. {file['name']} ({file['size_mb']:.2f} MB)")
                print(f"         ID: {file['id']}")
        
        # Testa permissões
        print("\n4️⃣ Verificando permissões...")
        if files:
            file_id = files[0]['id']
            file_name = files[0]['name']
            
            print(f"   📄 Testando permissões no arquivo: {file_name}")
            print(f"   ⚠️ ATENÇÃO: Este teste NÃO vai deletar o arquivo")
            print(f"   ℹ️ Apenas verifica se tem permissão")
            
            # Verifica metadados (isso indica se tem acesso)
            try:
                metadata = client.service.files().get(
                    fileId=file_id,
                    fields='id,name,permissions,capabilities'
                ).execute()
                
                can_delete = metadata.get('capabilities', {}).get('canDelete', False)
                
                if can_delete:
                    print(f"   ✅ Service Account TEM permissão para deletar arquivos!")
                    print(f"   🎉 Configuração está correta!")
                else:
                    print(f"   ❌ Service Account NÃO tem permissão para deletar")
                    print(f"   💡 Solução: Compartilhe a pasta com permissão 'Editor' ou 'Manager'")
                    
            except Exception as e:
                print(f"   ❌ Erro ao verificar permissões: {e}")
        
        print("\n" + "="*70)
        print("  ✅ TESTE CONCLUÍDO COM SUCESSO")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print("  ❌ ERRO NO TESTE")
        print("="*70)
        print(f"\nErro: {e}")
        print("\n💡 Verifique:")
        print("   1. Arquivo configs/google_drive_service_account.json existe")
        print("   2. GOOGLE_DRIVE_AUTH_MODE=service_account no .env")
        print("   3. Pasta do Drive compartilhada com Service Account")
        print("\n📖 Guia completo: docs/GOOGLE_DRIVE_SERVICE_ACCOUNT_SETUP.md\n")
        return False


if __name__ == "__main__":
    success = test_service_account()
    sys.exit(0 if success else 1)
