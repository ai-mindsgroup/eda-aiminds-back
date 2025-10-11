#!/usr/bin/env python3
"""
Verificar Modelos Disponíveis - Google Gemini
=============================================

Script para listar modelos disponíveis na API do Google Gemini.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.settings import GOOGLE_API_KEY

def check_available_models():
    """Verifica modelos disponíveis no Google Gemini."""
    print("🔍 VERIFICANDO MODELOS GOOGLE GEMINI")
    print("=" * 40)
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY não configurado!")
        return
    
    try:
        import google.generativeai as genai
        
        # Configurar API
        genai.configure(api_key=GOOGLE_API_KEY)
        
        print("📋 Modelos disponíveis:")
        print("-" * 30)
        
        # Listar modelos
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"✅ {model.name}")
                print(f"   Descrição: {model.display_name}")
                print()
        
        print("💡 Testando modelo recomendado...")
        
        # Testar modelo mais comum
        test_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-pro",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]
        
        for model_name in test_models:
            try:
                print(f"\n🧪 Testando: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Diga apenas 'OK' se funcionou")
                print(f"✅ FUNCIONA: {model_name}")
                print(f"   Resposta: {response.text}")
                break
            except Exception as e:
                print(f"❌ FALHOU: {model_name} - {str(e)[:100]}")
        
    except ImportError:
        print("❌ Biblioteca google-generativeai não instalada")
        print("💡 Execute: pip install google-generativeai")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    check_available_models()