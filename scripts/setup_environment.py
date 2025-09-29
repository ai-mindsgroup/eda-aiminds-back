"""Script de Setup Completo - EDA AI Minds Backend
===============================================

Este script automatiza a instalação completa do ambiente de desenvolvimento.
Execute este script para configurar tudo de uma vez.
"""

import sys
import os
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Executa um comando e retorna sucesso/falha."""
    print(f"\n📋 {description}")
    print(f"Executando: {command}")
    
    try:
        result = subprocess.run(
            command.split(),
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def check_python_version():
    """Verifica se Python está na versão adequada."""
    version = sys.version_info
    print(f"🐍 Python detectado: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 10:
        print("✅ Versão do Python adequada")
        return True
    else:
        print("❌ Python 3.10+ é necessário")
        return False


def check_virtual_env():
    """Verifica se está em ambiente virtual."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Ambiente virtual detectado")
        return True
    else:
        print("⚠️ Não está em ambiente virtual")
        print("   Recomenda-se usar ambiente virtual:")
        print("   python -m venv .venv")
        print("   .venv\\Scripts\\Activate.ps1  # Windows PowerShell")
        return False


def setup_environment():
    """Configura o ambiente completo."""
    print("🚀 SETUP COMPLETO - EDA AI MINDS BACKEND")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        return False
    
    # Verificar ambiente virtual
    check_virtual_env()
    
    # Atualizar pip
    success = run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Atualizando pip para versão mais recente"
    )
    
    if not success:
        print("⚠️ Falha ao atualizar pip, continuando...")
    
    # Instalar dependências principais
    success = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Instalando todas as dependências do requirements.txt"
    )
    
    if not success:
        print("❌ Falha na instalação das dependências principais")
        return False
    
    # Verificar se configs existe
    configs_dir = Path("configs")
    if not configs_dir.exists():
        print("⚠️ Diretório configs/ não encontrado")
        return False
    
    # Verificar arquivos de configuração
    env_example = configs_dir / ".env.example"
    env_file = configs_dir / ".env"
    
    if env_example.exists() and not env_file.exists():
        print(f"\n📋 Copiando .env.example para .env")
        try:
            import shutil
            shutil.copy2(env_example, env_file)
            print("✅ Arquivo .env criado")
            print("⚠️ IMPORTANTE: Configure suas chaves de API em configs/.env")
        except Exception as e:
            print(f"❌ Erro ao copiar .env: {e}")
    
    # Executar migrations do banco de dados (se configurado)
    print(f"\n📋 Verificando configuração do banco de dados...")
    
    if env_file.exists():
        print("📋 Executando migrations do banco de dados")
        try:
            # Tentar importar e executar migrations
            migrations_result = run_command(
                f"{sys.executable} scripts/run_migrations.py",
                "Aplicando migrations do banco de dados"
            )
            
            if migrations_result:
                print("✅ Migrations aplicadas com sucesso")
            else:
                print("⚠️ Falha nas migrations - verifique configuração do banco")
                print("   Você pode executar manualmente: python scripts/run_migrations.py")
                
        except Exception as e:
            print(f"⚠️ Erro ao executar migrations: {e}")
            print("   Configure o banco em configs/.env e execute:")
            print("   python scripts/run_migrations.py")
    else:
        print("⚠️ Arquivo .env não encontrado - pule as migrations por enquanto")
        print("   Configure .env e depois execute: python scripts/run_migrations.py")
    
    # Executar validação de dependências
    print(f"\n📋 Executando validação de dependências")
    try:
        import scripts.validate_dependencies as validator
        success_rate = validator.validate_dependencies()
        if success_rate >= 80.0:
            print(f"\n🎉 SETUP COMPLETO COM SUCESSO!")
        else:
            print(f"\n⚠️ Setup parcialmente concluído")
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
    
    # Instruções finais
    print(f"\n" + "=" * 50)
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Configure suas chaves de API em configs/.env")
    print("2. Verifique se as migrations foram aplicadas")
    print("3. Execute: python scripts/validate_dependencies.py")
    print("4. Teste o sistema: python examples/teste_groq_completo.py")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    try:
        success = setup_environment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erro durante setup: {e}")
        sys.exit(1)