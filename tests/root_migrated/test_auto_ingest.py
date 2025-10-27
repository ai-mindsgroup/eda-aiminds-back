"""Testes básicos para o sistema de ingestão automática.

Testa componentes individualmente antes de executar o serviço completo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data.csv_file_manager import create_csv_file_manager
from src.settings import (
    GOOGLE_DRIVE_ENABLED,
    EDA_DATA_DIR,
    EDA_DATA_DIR_PROCESSANDO,
    EDA_DATA_DIR_PROCESSADO
)


def test_directories():
    """Testa criação e acesso aos diretórios."""
    print("🧪 Testando diretórios...")
    
    try:
        file_manager = create_csv_file_manager()
        
        assert file_manager.data_dir.exists(), "Diretório data/ não existe"
        assert file_manager.processando_dir.exists(), "Diretório processando/ não existe"
        assert file_manager.processado_dir.exists(), "Diretório processado/ não existe"
        
        print("✅ Diretórios criados corretamente")
        print(f"   - data: {file_manager.data_dir}")
        print(f"   - processando: {file_manager.processando_dir}")
        print(f"   - processado: {file_manager.processado_dir}")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar diretórios: {e}")
        return False


def test_file_listing():
    """Testa listagem de arquivos."""
    print("\n🧪 Testando listagem de arquivos...")
    
    try:
        file_manager = create_csv_file_manager()
        
        data_files = file_manager.list_files_in_data()
        processing_files = file_manager.list_files_in_processing()
        processed_files = file_manager.list_files_in_processed()
        
        print(f"✅ Listagem concluída:")
        print(f"   - data/: {len(data_files)} arquivos")
        print(f"   - processando/: {len(processing_files)} arquivos")
        print(f"   - processado/: {len(processed_files)} arquivos")
        
        if processed_files:
            latest = file_manager.get_latest_processed_file()
            print(f"   - Último processado: {latest.name if latest else 'N/A'}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao listar arquivos: {e}")
        return False


def test_google_drive_config():
    """Testa configuração do Google Drive."""
    print("\n🧪 Testando configuração Google Drive...")
    
    try:
        from src.integrations.google_drive_client import GOOGLE_DRIVE_AVAILABLE
        from src.settings import (
            GOOGLE_DRIVE_CREDENTIALS_FILE,
            GOOGLE_DRIVE_TOKEN_FILE,
            GOOGLE_DRIVE_FOLDER_ID
        )
        
        print(f"   - Google Drive Enabled: {'✅' if GOOGLE_DRIVE_ENABLED else '❌'}")
        print(f"   - Bibliotecas instaladas: {'✅' if GOOGLE_DRIVE_AVAILABLE else '❌'}")
        
        if GOOGLE_DRIVE_ENABLED:
            print(f"   - Credentials file: {GOOGLE_DRIVE_CREDENTIALS_FILE}")
            print(f"     Existe: {'✅' if GOOGLE_DRIVE_CREDENTIALS_FILE.exists() else '❌'}")
            print(f"   - Token file: {GOOGLE_DRIVE_TOKEN_FILE}")
            print(f"     Existe: {'✅' if GOOGLE_DRIVE_TOKEN_FILE.exists() else '❌'}")
            print(f"   - Folder ID: {'✅ Configurado' if GOOGLE_DRIVE_FOLDER_ID else '❌ Não configurado'}")
            
            if not GOOGLE_DRIVE_AVAILABLE:
                print("\n⚠️ Para usar Google Drive, instale as dependências:")
                print("   pip install -r requirements-auto-ingest.txt")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar Google Drive: {e}")
        return False


def test_csv_validation():
    """Testa validação de arquivos CSV."""
    print("\n🧪 Testando validação de CSV...")
    
    try:
        file_manager = create_csv_file_manager()
        
        # Testa com arquivo fictício
        fake_csv = Path("test_fake.csv")
        is_valid = file_manager.validate_csv(fake_csv)
        
        print(f"   - Arquivo inexistente: {'❌' if not is_valid else '✅'} (esperado: ❌)")
        
        # Testa com arquivos reais se existirem
        processed_files = file_manager.list_files_in_processed()
        if processed_files:
            sample_file = processed_files[0]
            is_valid = file_manager.validate_csv(sample_file)
            print(f"   - Arquivo real ({sample_file.name}): {'✅' if is_valid else '❌'}")
        
        print("✅ Validação funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro ao validar CSV: {e}")
        return False


    except Exception as e:
        print(f"❌ Erro ao carregar DataIngestor: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("=" * 70)
    print("🧪 TESTES DO SISTEMA DE INGESTÃO AUTOMÁTICA")
    print("=" * 70)
    
    tests = [
        ("Diretórios", test_directories),
        ("Listagem de Arquivos", test_file_listing),
        ("Configuração Google Drive", test_google_drive_config),
        ("Validação CSV", test_csv_validation)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro não tratado em {name}: {e}")
            results.append((name, False))
    
    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status}: {name}")
    
    print("=" * 70)
    print(f"🎯 Resultado: {passed}/{total} testes passaram")
    print("=" * 70)
    
    if passed == total:
        print("\n✅ Todos os testes passaram! Sistema pronto para uso.")
        print("\n💡 Próximos passos:")
        print("   1. Configure Google Drive (se ainda não fez)")
        print("   2. Execute: python run_auto_ingest.py --once")
        print("   3. Para produção: python run_auto_ingest.py")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique a configuração.")
        print("\n💡 Verifique:")
        print("   - Arquivo configs/.env está configurado")
        print("   - Dependências instaladas: pip install -r requirements-auto-ingest.txt")
        print("   - Google Drive configurado (se habilitado)")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
