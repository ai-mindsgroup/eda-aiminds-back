#!/usr/bin/env python3
"""
Debug da API do Grok
====================

Este script testa diretamente a API do Grok para identificar problemas.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import requests
import json

def test_grok_api():
    """Testa a API do Grok diretamente."""
    from src.settings import GROK_API_KEY
    
    if not GROK_API_KEY:
        print("❌ GROK_API_KEY não configurado")
        return
    
    print(f"🔑 Usando API Key: {GROK_API_KEY[:10]}...")
    
    # Testar diferentes endpoints e modelos da documentação oficial
    test_configs = [
        {
            "url": "https://api.x.ai/v1/chat/completions",
            "model": "grok-3-mini"
        },
        {
            "url": "https://api.x.ai/v1/chat/completions", 
            "model": "grok-3"
        },
        {
            "url": "https://api.x.ai/v1/chat/completions",
            "model": "grok-4"
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Teste {i}: {config['model']}")
        print(f"   URL: {config['url']}")
        
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": "Hello, respond with 'API working' in Portuguese"}
            ],
            "model": config['model'],
            "temperature": 0.3,
            "max_tokens": 50
        }
        
        try:
            print(f"   📡 Enviando requisição...")
            response = requests.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"   ✅ Sucesso! Resposta: {content}")
                return True
            else:
                print(f"   ❌ Erro: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 Detalhes: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   📝 Texto: {response.text}")
                    
        except Exception as e:
            print(f"   💥 Exceção: {e}")
    
    return False

def list_available_models():
    """Tenta listar modelos disponíveis."""
    from src.settings import GROK_API_KEY
    
    print("\n🔍 Tentando listar modelos disponíveis...")
    
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.x.ai/v1/models",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("📋 Modelos disponíveis:")
            for model in data.get("data", []):
                print(f"   - {model.get('id', 'N/A')}")
        else:
            print(f"❌ Erro ao listar modelos: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Detalhes: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Texto: {response.text}")
                
    except Exception as e:
        print(f"💥 Exceção ao listar modelos: {e}")

def main():
    print("🚀 DEBUG DA API DO GROK")
    print("=" * 40)
    
    # Testar modelos
    success = test_grok_api()
    
    # Listar modelos disponíveis
    list_available_models()
    
    if success:
        print("\n✅ API funcionando! Pode usar o GrokLLMAgent.")
    else:
        print("\n❌ API com problemas. Verifique configuração.")

if __name__ == "__main__":
    main()