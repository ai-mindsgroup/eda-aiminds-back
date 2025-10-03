#!/usr/bin/env python3
"""
Script para iniciar a API Simples
==================================
"""

import os
import sys

def main():
    """Iniciar API com uvicorn."""
    print("🚀 Iniciando API Simples - EDA AI Minds")
    print("=" * 50)
    print("📍 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("📋 ReDoc: http://localhost:8000/redoc")
    print("⏹️ Pressione Ctrl+C para parar")
    print()
    
    # Executar uvicorn via linha de comando
    os.system("uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    main()
