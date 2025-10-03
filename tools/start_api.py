#!/usr/bin/env python3
"""
Inicializador da API EDA AI Minds
================================

Script para iniciar a API REST com configurações otimizadas.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    print("🔍 Verificando dependências...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pandas",
        "supabase",
        "python-dotenv"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package}")
    
    if missing:
        print(f"\n⚠️ Dependências ausentes: {', '.join(missing)}")
        print("💡 Instale com: pip install -r requirements.txt")
        return False
    
    print("✅ Todas as dependências estão instaladas\n")
    return True


def check_configuration():
    """Verifica configurações essenciais."""
    print("⚙️ Verificando configurações...")
    
    env_file = Path("configs/.env")
    if not env_file.exists():
        print("  ❌ Arquivo configs/.env não encontrado")
        print("  💡 Copie configs/.env.example para configs/.env")
        return False
    
    print("  ✅ Arquivo .env encontrado")
    
    # Verificar variáveis essenciais
    from src.settings import SUPABASE_URL, SUPABASE_KEY
    
    if not SUPABASE_URL:
        print("  ❌ SUPABASE_URL não configurado")
        return False
    
    if not SUPABASE_KEY:
        print("  ❌ SUPABASE_KEY não configurado") 
        return False
    
    print("  ✅ Configurações básicas OK\n")
    return True


def start_api_server(host="0.0.0.0", port=8000, reload=True):
    """Inicia o servidor da API."""
    print(f"🚀 Iniciando API em http://{host}:{port}")
    print("📚 Documentação disponível em:")
    print(f"   • Swagger UI: http://{host}:{port}/docs")
    print(f"   • ReDoc: http://{host}:{port}/redoc")
    print("\n⏹️ Pressione Ctrl+C para parar\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n⏹️ Servidor parado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")


def main():
    """Função principal."""
    print("🎯 EDA AI Minds - Inicializador da API")
    print("=" * 50)
    
    # Verificações
    if not check_dependencies():
        return 1
    
    if not check_configuration():
        return 1
    
    # Argumentos de linha de comando
    import argparse
    parser = argparse.ArgumentParser(description="Inicializar API EDA AI Minds")
    parser.add_argument("--host", default="0.0.0.0", help="Host do servidor")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor")
    parser.add_argument("--no-reload", action="store_true", help="Desabilitar reload automático")
    parser.add_argument("--test", action="store_true", help="Executar testes após iniciar")
    
    args = parser.parse_args()
    
    # Iniciar servidor
    if args.test:
        print("🧪 Modo de teste ativado - servidor será testado após inicialização")
        
        # Iniciar servidor em background
        import threading
        server_thread = threading.Thread(
            target=start_api_server,
            args=(args.host, args.port, not args.no_reload),
            daemon=True
        )
        server_thread.start()
        
        # Aguardar servidor inicializar
        time.sleep(3)
        
        # Executar testes
        print("\n🧪 Executando testes da API...")
        test_result = subprocess.run([
            sys.executable, "test_api.py", "--url", f"http://{args.host}:{args.port}"
        ])
        
        if test_result.returncode == 0:
            print("✅ Todos os testes passaram!")
        else:
            print("❌ Alguns testes falharam")
        
        # Manter servidor rodando
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\n⏹️ Servidor parado")
    else:
        start_api_server(args.host, args.port, not args.no_reload)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())