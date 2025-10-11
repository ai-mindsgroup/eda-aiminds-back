#!/usr/bin/env python3
"""
Teste Completo da API - feature/refactore-langchain
==================================================

Script para testar todos os aspectos da API migrada.
"""

import requests
import json
import time
import os
import sys
from datetime import datetime

def test_api_endpoints():
    """Testa todos os endpoints da API"""
    base_url = "http://localhost:8000"
    
    print("🧪 TESTE 2: Testando Endpoints da API")
    print("=" * 50)
    
    # Lista de endpoints para testar
    endpoints = [
        {
            "method": "GET",
            "url": "/",
            "name": "Root - Informações da API",
            "expected_status": 200
        },
        {
            "method": "GET", 
            "url": "/health",
            "name": "Health Check",
            "expected_status": 200
        },
        {
            "method": "GET",
            "url": "/endpoints", 
            "name": "Lista de Endpoints",
            "expected_status": 200
        },
        {
            "method": "GET",
            "url": "/api/config",
            "name": "Configuração da API", 
            "expected_status": 200
        },
        {
            "method": "GET",
            "url": "/csv/files",
            "name": "Lista de arquivos CSV",
            "expected_status": 200
        },
        {
            "method": "GET",
            "url": "/dashboard/metrics",
            "name": "Métricas do Dashboard",
            "expected_status": 200
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            print(f"\n🔍 Testando: {endpoint['name']}")
            
            if endpoint["method"] == "GET":
                response = requests.get(f"{base_url}{endpoint['url']}", timeout=5)
            elif endpoint["method"] == "POST":
                response = requests.post(f"{base_url}{endpoint['url']}", timeout=5)
            
            status_ok = response.status_code == endpoint["expected_status"]
            
            result = {
                "endpoint": endpoint["url"],
                "name": endpoint["name"], 
                "status_code": response.status_code,
                "expected": endpoint["expected_status"],
                "success": status_ok,
                "response_size": len(response.text) if response.text else 0
            }
            
            if status_ok:
                print(f"   ✅ Status: {response.status_code} - OK")
                if response.text:
                    try:
                        data = response.json()
                        print(f"   📊 Dados: {len(str(data))} caracteres")
                        if 'status' in data:
                            print(f"   🎯 Status interno: {data['status']}")
                    except:
                        print(f"   📝 Resposta: {len(response.text)} caracteres")
            else:
                print(f"   ❌ Status: {response.status_code} (esperado: {endpoint['expected_status']})")
                
            results.append(result)
            
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Erro: API não está rodando em {base_url}")
            result = {
                "endpoint": endpoint["url"],
                "name": endpoint["name"],
                "status_code": "CONNECTION_ERROR", 
                "expected": endpoint["expected_status"],
                "success": False,
                "error": "API não está rodando"
            }
            results.append(result)
            break
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            result = {
                "endpoint": endpoint["url"],
                "name": endpoint["name"],
                "status_code": "ERROR",
                "expected": endpoint["expected_status"], 
                "success": False,
                "error": str(e)
            }
            results.append(result)
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES DE ENDPOINTS")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    print(f"✅ Sucessos: {success_count}/{total_count}")
    print(f"❌ Falhas: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 TODOS OS ENDPOINTS PASSARAM!")
        return True
    else:
        print("⚠️  ALGUNS ENDPOINTS FALHARAM")
        for result in results:
            if not result["success"]:
                print(f"   ❌ {result['name']}: {result.get('error', 'Status incorreto')}")
        return False

def test_chat_endpoint():
    """Testa especificamente o endpoint de chat"""
    print("\n🧪 TESTE 3: Testando Chat Endpoint")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Mensagens de teste
    test_messages = [
        "olá",
        "help", 
        "como funciona",
        "status",
        "obrigado"
    ]
    
    results = []
    
    for message in test_messages:
        try:
            print(f"\n💬 Testando mensagem: '{message}'")
            
            payload = {
                "message": message,
                "session_id": "test_session"
            }
            
            response = requests.post(
                f"{base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                print(f"   ✅ Resposta recebida: {len(response_text)} caracteres")
                print(f"   📝 Preview: {response_text[:100]}...")
                
                results.append({
                    "message": message,
                    "success": True,
                    "response_length": len(response_text)
                })
            else:
                print(f"   ❌ Erro: Status {response.status_code}")
                results.append({
                    "message": message, 
                    "success": False,
                    "error": f"Status {response.status_code}"
                })
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            results.append({
                "message": message,
                "success": False, 
                "error": str(e)
            })
    
    # Resumo do chat
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    print(f"\n📊 Resumo Chat: {success_count}/{total_count} mensagens OK")
    
    return success_count == total_count

def main():
    """Função principal de testes"""
    print("🚀 INICIANDO TESTES COMPLETOS DA API")
    print("🔧 Branch: feature/refactore-langchain")
    print("📅 Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # Verificar se a API está rodando
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code == 200:
            print("✅ API está rodando e respondendo!")
            
            # Executar testes
            endpoint_results = test_api_endpoints()
            chat_results = test_chat_endpoint()
            
            # Resultado final
            print("\n" + "=" * 60)
            print("🎯 RESULTADO FINAL DOS TESTES")
            print("=" * 60)
            
            if endpoint_results and chat_results:
                print("🎉 TODOS OS TESTES PASSARAM! ✅")
                print("🚀 A API está 100% funcional na branch feature/refactore-langchain")
                return True
            else:
                print("⚠️  ALGUNS TESTES FALHARAM ❌")
                return False
                
        else:
            print("❌ API não está respondendo corretamente")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API não está rodando em http://localhost:8000")
        print("💡 Execute: python api_simple.py")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)