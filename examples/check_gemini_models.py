#!/usr/bin/env python3
"""Script para listar modelos disponíveis do Google Gemini."""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.settings import GOOGLE_API_KEY

try:
    import google.generativeai as genai
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY não configurado")
        sys.exit(1)
    
    # Configurar API
    genai.configure(api_key=GOOGLE_API_KEY)
    
    print("🔍 MODELOS DISPONÍVEIS NO GOOGLE AI:")
    print("=" * 50)
    
    # Listar modelos
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Descrição: {model.display_name}")
            print(f"   Versão: {model.version}")
            print()
    
except ImportError:
    print("❌ google-generativeai não instalado")
    print("Execute: pip install google-generativeai")
except Exception as e:
    print(f"❌ Erro: {e}")