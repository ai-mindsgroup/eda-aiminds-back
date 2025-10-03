#!/usr/bin/env python3
"""
Verificador de Dependências da API
=================================

Script para verificar se todas as dependências necessárias estão instaladas.
"""

import sys
import importlib
from typing import List, Tuple


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Verifica se um pacote está instalado.
    
    Args:
        package_name: Nome do pacote no pip
        import_name: Nome para import (se diferente do package_name)
    
    Returns:
        Tuple[bool, str]: (está_instalado, versão_ou_erro)
    """
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, version
    except ImportError as e:
        return False, str(e)


def main():
    """Verifica todas as dependências da API."""
    print("🔍 Verificando Dependências da API REST")
    print("=" * 50)
    
    # Dependências essenciais da API
    api_dependencies = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("python-multipart", "multipart"),
        ("pydantic", "pydantic"),
        ("pydantic-settings", "pydantic_settings"),
        ("httpx", "httpx"),
        ("slowapi", "slowapi"),
        ("python-jose", "jose"),
        ("psutil", "psutil"),
        ("python-dotenv", "dotenv"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("supabase", "supabase"),
        ("pytest", "pytest"),
    ]
    
    # Dependências do sistema multiagente
    multiagent_dependencies = [
        ("langchain", "langchain"),
        ("langchain-core", "langchain_core"),
        ("langchain-google-genai", "langchain_google_genai"),
        ("openai", "openai"),
        ("groq", "groq"),
        ("sentence-transformers", "sentence_transformers"),
        ("scikit-learn", "sklearn"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
    ]
    
    # Verificar dependências da API
    print("📋 Dependências da API:")
    api_missing = []
    for package, import_name in api_dependencies:
        installed, version = check_package(package, import_name)
        if installed:
            print(f"  ✅ {package}: {version}")
        else:
            print(f"  ❌ {package}: NÃO INSTALADO")
            api_missing.append(package)
    
    # Verificar dependências do sistema multiagente
    print(f"\n🤖 Dependências do Sistema Multiagente:")
    multiagent_missing = []
    for package, import_name in multiagent_dependencies:
        installed, version = check_package(package, import_name)
        if installed:
            print(f"  ✅ {package}: {version}")
        else:
            print(f"  ❌ {package}: NÃO INSTALADO")
            multiagent_missing.append(package)
    
    # Resumo
    print(f"\n📊 Resumo:")
    print(f"  API essencial: {len(api_dependencies) - len(api_missing)}/{len(api_dependencies)} instaladas")
    print(f"  Sistema multiagente: {len(multiagent_dependencies) - len(multiagent_missing)}/{len(multiagent_dependencies)} instaladas")
    
    # Comandos de instalação
    if api_missing:
        print(f"\n⚠️ Dependências da API ausentes:")
        print(f"   pip install {' '.join(api_missing)}")
    
    if multiagent_missing:
        print(f"\n⚠️ Dependências do sistema multiagente ausentes:")
        print(f"   pip install {' '.join(multiagent_missing)}")
    
    # Verificações específicas
    print(f"\n🔧 Verificações Específicas:")
    
    # Verificar se pode importar a aplicação
    try:
        from src.api.main import app
        print("  ✅ Aplicação FastAPI pode ser importada")
    except ImportError as e:
        print(f"  ❌ Erro importando aplicação: {e}")
    
    # Verificar configurações
    try:
        from src.settings import SUPABASE_URL, SUPABASE_KEY
        print(f"  ✅ Configurações carregadas")
        print(f"    SUPABASE_URL: {'✅ Configurado' if SUPABASE_URL else '❌ Ausente'}")
        print(f"    SUPABASE_KEY: {'✅ Configurado' if SUPABASE_KEY else '❌ Ausente'}")
    except ImportError as e:
        print(f"  ❌ Erro carregando configurações: {e}")
    
    # Verificar banco vetorial
    try:
        from src.vectorstore.supabase_client import supabase
        print("  ✅ Cliente Supabase pode ser inicializado")
    except ImportError as e:
        print(f"  ❌ Erro inicializando Supabase: {e}")
    
    # Comandos úteis
    print(f"\n💡 Comandos Úteis:")
    print(f"   # Instalar todas as dependências:")
    print(f"   pip install -r requirements.txt")
    print(f"   ")
    print(f"   # Instalar apenas dependências da API:")
    print(f"   pip install -r requirements-api.txt")
    print(f"   ")
    print(f"   # Iniciar API:")
    print(f"   python start_api.py")
    print(f"   ")
    print(f"   # Testar API:")
    print(f"   python test_api.py")
    
    # Status final
    if not api_missing:
        print(f"\n🎉 Todas as dependências da API estão instaladas!")
        print(f"   A API está pronta para ser executada.")
        return 0
    else:
        print(f"\n⚠️ Algumas dependências estão ausentes.")
        print(f"   Instale as dependências antes de executar a API.")
        return 1


if __name__ == "__main__":
    sys.exit(main())