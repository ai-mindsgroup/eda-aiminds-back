#!/usr/bin/env python3
"""
Teste Unitário da API - feature/refactore-langchain
==================================================

Teste usando TestClient do FastAPI para validar a API.
"""

from fastapi.testclient import TestClient
from api_simple import app
import json
from datetime import datetime

def test_basic_endpoints():
    """Testa endpoints básicos da API"""
    print("🧪 TESTE 2: Endpoints Básicos")
    print("=" * 40)
    
    client = TestClient(app)
    
    # Teste 1: Root endpoint
    print("\n1️⃣ Testando endpoint raiz (/)...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Título: {data['title']}")
    
    # Teste 2: Health check
    print("\n2️⃣ Testando health check...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print(f"   ✅ Status: {response.status_code}")
    print(f"   💚 Saúde: {data['status']}")
    
    # Teste 3: Endpoints list
    print("\n3️⃣ Testando lista de endpoints...")
    response = client.get("/endpoints")
    assert response.status_code == 200
    data = response.json()
    assert "available_endpoints" in data
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📋 Endpoints: {len(data['available_endpoints'])}")
    
    # Teste 4: API config
    print("\n4️⃣ Testando configuração da API...")
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    print(f"   ✅ Status: {response.status_code}")
    print(f"   ⚙️ Modo: {data['mode']}")
    
    # Teste 5: CSV files (vazio inicialmente)
    print("\n5️⃣ Testando lista de arquivos CSV...")
    response = client.get("/csv/files")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📁 Total arquivos: {data['total']}")
    
    # Teste 6: Dashboard metrics
    print("\n6️⃣ Testando métricas do dashboard...")
    response = client.get("/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Status dashboard: {data['status']}")
    
    print("\n🎉 TODOS OS ENDPOINTS BÁSICOS PASSARAM!")
    return True

def test_chat_functionality():
    """Testa funcionalidade de chat"""
    print("\n🧪 TESTE 3: Funcionalidade de Chat")
    print("=" * 40)
    
    client = TestClient(app)
    
    test_messages = [
        {"message": "olá", "expected_keywords": ["olá", "ajudar", "assistente"]},
        {"message": "help", "expected_keywords": ["funcionalidades", "upload", "análise"]},
        {"message": "como funciona", "expected_keywords": ["upload", "processamento", "insights"]},
        {"message": "status", "expected_keywords": ["status", "operacional", "funcionando"]},
        {"message": "csv", "expected_keywords": ["csv", "upload", "dados"]}
    ]
    
    for i, test in enumerate(test_messages, 1):
        print(f"\n{i}️⃣ Testando mensagem: '{test['message']}'...")
        
        response = client.post("/chat", json={
            "message": test["message"],
            "session_id": "test_session"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert "timestamp" in data
        
        response_text = data["response"].lower()
        found_keywords = [kw for kw in test["expected_keywords"] if kw in response_text]
        
        print(f"   ✅ Status: {response.status_code}")
        print(f"   💬 Resposta: {len(data['response'])} caracteres")
        print(f"   🔍 Keywords encontradas: {len(found_keywords)}/{len(test['expected_keywords'])}")
        
        # Verifica se pelo menos uma keyword foi encontrada
        assert len(found_keywords) > 0, f"Nenhuma keyword encontrada em: {response_text[:100]}"
    
    print("\n🎉 TODOS OS TESTES DE CHAT PASSARAM!")
    return True

def test_error_handling():
    """Testa tratamento de erros"""
    print("\n🧪 TESTE 4: Tratamento de Erros")
    print("=" * 40)
    
    client = TestClient(app)
    
    # Teste 1: Endpoint inexistente
    print("\n1️⃣ Testando endpoint inexistente...")
    response = client.get("/endpoint-que-nao-existe")
    assert response.status_code == 404
    print(f"   ✅ Status 404: {response.status_code}")
    
    # Teste 2: Chat sem dados
    print("\n2️⃣ Testando chat sem dados...")
    response = client.post("/chat", json={})
    assert response.status_code == 422  # Validation error
    print(f"   ✅ Status 422: {response.status_code}")
    
    print("\n🎉 TRATAMENTO DE ERROS OK!")
    return True

def main():
    """Executa todos os testes"""
    print("🚀 TESTES COMPLETOS DA API")
    print("🔧 Branch: feature/refactore-langchain")
    print("📅 Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    try:
        # Executa todos os testes
        test1 = test_basic_endpoints()
        test2 = test_chat_functionality() 
        test3 = test_error_handling()
        
        # Resultado final
        print("\n" + "=" * 50)
        print("🎯 RESULTADO FINAL")
        print("=" * 50)
        
        if test1 and test2 and test3:
            print("🎉 TODOS OS TESTES PASSARAM! ✅")
            print("🚀 API 100% FUNCIONAL na branch feature/refactore-langchain")
            print("\n📊 Resumo:")
            print("   ✅ Endpoints básicos: OK")
            print("   ✅ Funcionalidade chat: OK") 
            print("   ✅ Tratamento de erros: OK")
            print("   ✅ Validação de dados: OK")
            return True
        else:
            print("❌ ALGUNS TESTES FALHARAM")
            return False
            
    except Exception as e:
        print(f"❌ ERRO DURANTE OS TESTES: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)