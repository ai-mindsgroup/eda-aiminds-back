#!/usr/bin/env python3
"""
Verificação de API Key do Grok
==============================

Este script verifica se a API key está sendo lida corretamente do arquivo .env.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def verify_env_loading():
    """Verifica se o arquivo .env está sendo carregado corretamente."""
    print("🧪 VERIFICAÇÃO DO CARREGAMENTO DO .ENV")
    print("=" * 50)
    
    # Verificar se o arquivo .env existe
    env_path = Path(root_dir) / "configs" / ".env"
    print(f"📁 Caminho do .env: {env_path}")
    print(f"📄 Arquivo existe: {'✅ Sim' if env_path.exists() else '❌ Não'}")
    
    if env_path.exists():
        print("\n📝 Conteúdo do arquivo .env:")
        try:
            with open(env_path, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                for line in lines:
                    if 'GROK_API_KEY' in line:
                        key_part = line.split('=')[1] if '=' in line else 'N/A'
                        print(f"   GROK_API_KEY={key_part[:15]}... (mostrando apenas primeiros 15 chars)")
                    elif line.strip() and not line.startswith('#'):
                        var_name = line.split('=')[0]
                        print(f"   {var_name}=...")
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
    
    # Verificar se a variável está sendo carregada via settings
    print("\n🔧 Carregamento via src.settings:")
    try:
        from src.settings import GROK_API_KEY
        if GROK_API_KEY:
            print(f"   ✅ GROK_API_KEY carregado: {GROK_API_KEY[:15]}...")
            print(f"   📏 Comprimento: {len(GROK_API_KEY)} caracteres")
            print(f"   🔤 Prefixo: {GROK_API_KEY[:4]}")
            return GROK_API_KEY
        else:
            print("   ❌ GROK_API_KEY está vazio ou None")
            return None
    except Exception as e:
        print(f"   ❌ Erro ao importar: {e}")
        return None

def test_api_key_format(api_key):
    """Testa se a API key tem o formato esperado."""
    print("\n🔍 VERIFICAÇÃO DO FORMATO DA API KEY")
    print("=" * 40)
    
    if not api_key:
        print("❌ API key não disponível para teste")
        return False
    
    # Verificar formato esperado para chaves xAI (ambos os formatos)
    valid_prefixes = ["gsk_", "xai-"]
    current_prefix = api_key[:4]
    print(f"🔤 Prefixos válidos: {', '.join(valid_prefixes)}")
    print(f"🔤 Prefixo atual: {current_prefix}")
    
    if any(api_key.startswith(prefix) for prefix in valid_prefixes):
        print("✅ Prefixo correto")
    else:
        print("❌ Prefixo incorreto")
        return False
    
    # Verificar comprimento (chaves xAI geralmente têm ~64 caracteres)
    length = len(api_key)
    print(f"📏 Comprimento: {length} caracteres")
    
    if 50 <= length <= 80:  # Range esperado
        print("✅ Comprimento adequado")
    else:
        print("⚠️ Comprimento suspeito")
    
    # Verificar se contém apenas caracteres válidos (ambos os formatos)
    import re
    valid_patterns = [
        r'^gsk_[A-Za-z0-9]+$',  # Formato antigo
        r'^xai-[A-Za-z0-9]+$'   # Formato novo
    ]
    
    if any(re.match(pattern, api_key) for pattern in valid_patterns):
        print("✅ Caracteres válidos")
        return True
    else:
        print("❌ Caracteres inválidos encontrados")
        return False

def make_simple_request(api_key):
    """Faz uma requisição simples para testar a API key."""
    print("\n🚀 TESTE DE REQUISIÇÃO SIMPLES")
    print("=" * 35)
    
    if not api_key:
        print("❌ Sem API key para testar")
        return False
    
    import requests
    import json
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Requisição mínima para testar autenticação
    payload = {
        "messages": [
            {"role": "user", "content": "Hi"}
        ],
        "model": "grok-3-mini",
        "max_tokens": 10
    }
    
    try:
        print("📡 Enviando requisição de teste...")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key válida! Funcionando corretamente")
            return True
        elif response.status_code == 403:
            try:
                error_data = response.json()
                if "credits" in error_data.get("error", "").lower():
                    print("✅ API key válida! ⚠️ Sem créditos na conta")
                    print(f"💳 Adicione créditos em: https://console.x.ai")
                    return "credits_needed"
            except:
                pass
            print(f"❌ Erro 403: Sem permissão")
            return False
        else:
            print(f"❌ Erro: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Detalhes: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📝 Texto: {response.text}")
            return False
    
    except Exception as e:
        print(f"💥 Exceção: {e}")
        return False

def main():
    """Executa todas as verificações."""
    print("🔍 DIAGNÓSTICO COMPLETO DA API KEY DO GROK")
    print("=" * 60)
    
    # 1. Verificar carregamento do .env
    api_key = verify_env_loading()
    
    # 2. Verificar formato da API key
    format_ok = test_api_key_format(api_key)
    
    # 3. Testar requisição real
    if format_ok:
        request_ok = make_simple_request(api_key)
    else:
        request_ok = False
    
    # Resultado final
    print("\n🏁 RESULTADO DO DIAGNÓSTICO")
    print("=" * 35)
    
    if api_key:
        print("✅ API key carregada do .env")
    else:
        print("❌ Problema no carregamento da API key")
    
    if format_ok:
        print("✅ Formato da API key válido")
    else:
        print("❌ Formato da API key inválido")
    
    if request_ok == True:
        print("✅ API key funcionando na xAI!")
        print("\n🎉 TUDO OK! Pode usar o GrokLLMAgent")
    elif request_ok == "credits_needed":
        print("✅ API key válida na xAI!")
        print("💳 Precisa adicionar créditos à conta")
        print("\n🔧 PRÓXIMO PASSO:")
        print("   1. Acesse https://console.x.ai")
        print("   2. Adicione créditos à sua conta")
        print("   3. Depois pode usar o GrokLLMAgent normalmente!")
    else:
        print("❌ API key não autorizada na xAI")
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("   1. Verifique se a API key não expirou")
        print("   2. Gere uma nova API key em https://console.x.ai")
        print("   3. Atualize o arquivo configs/.env")

if __name__ == "__main__":
    main()