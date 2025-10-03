#!/usr/bin/env python3
"""
Verificação Rápida de Dependências
=================================

Verifica se a API pode ser iniciada com as dependências atuais.
"""

import sys
import importlib
from pathlib import Path


def check_critical_imports():
    """Verifica importações críticas da API."""
    print("🔍 Verificando importações críticas...")
    
    critical_imports = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("httpx", "HTTP client para testes"),
        ("pandas", "Data manipulation"),
        ("python-multipart", "File upload support")
    ]
    
    missing = []
    
    for module_name, description in critical_imports:
        try:
            import_name = module_name.replace("-", "_")
            module = importlib.import_module(import_name)
            version = getattr(module, "__version__", "unknown")
            print(f"  ✅ {module_name}: {version}")
        except ImportError as e:
            print(f"  ❌ {module_name}: AUSENTE")
            missing.append(module_name)
    
    return missing


def check_api_structure():
    """Verifica se a estrutura da API está presente."""
    print(f"\n📁 Verificando estrutura da API...")
    
    required_files = [
        "src/api/main.py",
        "src/api/schemas.py", 
        "src/api/routes/__init__.py",
        "src/api/routes/health.py",
        "src/api/routes/csv.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}: AUSENTE")
            missing_files.append(file_path)
    
    return missing_files


def test_basic_imports():
    """Testa importações básicas da API."""
    print(f"\n🧪 Testando importações básicas...")
    
    try:
        # Testar FastAPI
        from fastapi import FastAPI
        print("  ✅ FastAPI pode ser importado")
        
        # Testar Pydantic
        from pydantic import BaseModel
        print("  ✅ Pydantic pode ser importado")
        
        # Testar uvicorn
        import uvicorn
        print("  ✅ Uvicorn pode ser importado")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Erro importando: {e}")
        return False


def main():
    """Função principal."""
    print("🚀 Verificação Rápida - API REST")
    print("=" * 50)
    
    # Verificar dependências críticas
    missing_deps = check_critical_imports()
    
    # Verificar estrutura
    missing_files = check_api_structure()
    
    # Testar importações básicas
    can_import = test_basic_imports()
    
    # Resumo
    print(f"\n📊 Resumo:")
    print(f"  Dependências ausentes: {len(missing_deps)}")
    print(f"  Arquivos ausentes: {len(missing_files)}")
    print(f"  Importações funcionais: {'✅' if can_import else '❌'}")
    
    if missing_deps:
        print(f"\n⚠️ Instale dependências ausentes:")
        print(f"   pip install {' '.join(missing_deps)}")
    
    if missing_files:
        print(f"\n⚠️ Arquivos ausentes:")
        for file in missing_files:
            print(f"   {file}")
    
    # Status final
    if not missing_deps and not missing_files and can_import:
        print(f"\n🎉 API pronta para ser executada!")
        print(f"   Execute: python start_api.py")
        return 0
    else:
        print(f"\n⚠️ Resolva os problemas antes de executar a API.")
        return 1


if __name__ == "__main__":
    sys.exit(main())