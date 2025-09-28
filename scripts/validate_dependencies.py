"""Script para validar instalação de dependências.

Este script verifica se todas as dependências estão corretamente instaladas
e funcionais no ambiente atual.
"""
import sys
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def check_python_version() -> Tuple[bool, str]:
    """Verifica versão do Python."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (requer 3.10+)"


def check_package(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, str]:
    """Verifica se um pacote está instalado e importável."""
    try:
        if import_name:
            importlib.import_module(import_name)
        else:
            importlib.import_module(package_name)
        return True, f"✅ {package_name}"
    except ImportError:
        return False, f"❌ {package_name} - não instalado ou não importável"


def get_package_version(package_name: str) -> Optional[str]:
    """Obtém versão de um pacote instalado."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return None


def validate_dependencies():
    """Valida todas as dependências do projeto."""
    print("🔍 VALIDAÇÃO DE DEPENDÊNCIAS - EDA AI MINDS BACKEND")
    print("=" * 60)
    
    # Verificar versão Python
    python_ok, python_msg = check_python_version()
    print(f"\n📍 Versão Python: {python_msg}")
    
    if not python_ok:
        print("\n⚠️ AVISO: Python 3.10+ é requerido para algumas funcionalidades")
    
    print(f"\n🗂️ Verificando dependências core...")
    
    # Dependências core essenciais
    core_packages = [
        ("python-dotenv", "dotenv"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("psycopg", "psycopg"),
        ("coloredlogs", "coloredlogs"),
    ]
    
    core_results = []
    for package, import_name in core_packages:
        success, message = check_package(package, import_name)
        core_results.append((success, message))
        print(f"  {message}")
    
    print(f"\n🧠 Verificando dependências AI/ML...")
    
    # Dependências AI/ML
    ai_packages = [
        ("sentence-transformers", "sentence_transformers"),
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("scikit-learn", "sklearn"),
        ("scipy", "scipy"),
    ]
    
    ai_results = []
    for package, import_name in ai_packages:
        success, message = check_package(package, import_name)
        ai_results.append((success, message))
        print(f"  {message}")
    
    print(f"\n🔗 Verificando integrações LangChain...")
    
    # Dependências LangChain
    langchain_packages = [
        ("langchain", "langchain"),
        ("langchain-core", "langchain_core"),
        ("langchain-community", "langchain_community"),
        ("langchain-openai", "langchain_openai"),
        ("langchain-google-genai", "langchain_google_genai"),
    ]
    
    langchain_results = []
    for package, import_name in langchain_packages:
        success, message = check_package(package, import_name)
        langchain_results.append((success, message))
        print(f"  {message}")
    
    print(f"\n📊 Verificando dependências de visualização...")
    
    # Dependências de visualização
    viz_packages = [
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
    ]
    
    viz_results = []
    for package, import_name in viz_packages:
        success, message = check_package(package, import_name)
        viz_results.append((success, message))
        print(f"  {message}")
    
    print(f"\n🗄️ Verificando dependências de banco...")
    
    # Dependências de banco
    db_packages = [
        ("supabase", "supabase"),
        ("pgvector", "pgvector"),
        ("psycopg-binary", None),  # Não precisa importar
    ]
    
    db_results = []
    for package, import_name in db_packages:
        if import_name is None:
            # Para pacotes que não precisam ser importados
            version = get_package_version(package)
            if version:
                db_results.append((True, f"✅ {package} v{version}"))
                print(f"  ✅ {package} v{version}")
            else:
                db_results.append((False, f"❌ {package} - não encontrado"))
                print(f"  ❌ {package} - não encontrado")
        else:
            success, message = check_package(package, import_name)
            db_results.append((success, message))
            print(f"  {message}")
    
    # Estatísticas finais
    print(f"\n📈 RELATÓRIO DE VALIDAÇÃO")
    print("=" * 30)
    
    all_results = core_results + ai_results + langchain_results + viz_results + db_results
    total_packages = len(all_results)
    successful = sum(1 for success, _ in all_results if success)
    failed = total_packages - successful
    
    success_rate = (successful / total_packages) * 100
    
    print(f"Total de pacotes verificados: {total_packages}")
    print(f"✅ Instalados corretamente: {successful}")
    print(f"❌ Faltando ou com erro: {failed}")
    print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES:")
    if failed == 0:
        print("🎉 Todas as dependências estão funcionando perfeitamente!")
        print("   O sistema está pronto para uso completo.")
    elif failed <= 3:
        print("⚠️ Algumas dependências opcionais estão faltando.")
        print("   O sistema funcionará com funcionalidades limitadas.")
        print("   Execute: pip install -r requirements.txt")
    else:
        print("🚨 Muitas dependências estão faltando!")
        print("   Execute a instalação completa:")
        print("   pip install -r requirements.txt")
    
    # Verificações específicas do projeto
    print(f"\n🔧 VERIFICAÇÕES ESPECÍFICAS:")
    
    # Verificar se src/ existe
    src_path = Path("src")
    if src_path.exists():
        print("✅ Diretório src/ encontrado")
    else:
        print("❌ Diretório src/ não encontrado - execute no diretório raiz do projeto")
    
    # Verificar se configs/ existe  
    config_path = Path("configs")
    if config_path.exists():
        print("✅ Diretório configs/ encontrado")
        
        env_example = config_path / ".env.example"
        env_file = config_path / ".env"
        
        if env_example.exists():
            print("✅ Arquivo .env.example encontrado")
        else:
            print("❌ Arquivo .env.example não encontrado")
            
        if env_file.exists():
            print("✅ Arquivo .env configurado")
        else:
            print("⚠️ Arquivo .env não encontrado - copie de .env.example")
    else:
        print("❌ Diretório configs/ não encontrado")
    
    print(f"\n🚀 Para testar o sistema:")
    print("   python test_simple.py")
    print("   python demo_csv_agent.py")
    
    return success_rate >= 80.0


if __name__ == "__main__":
    try:
        success = validate_dependencies()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Validação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erro durante validação: {e}")
        sys.exit(1)