#!/usr/bin/env python3
"""
Teste Rápido da API REST
=======================

Script para testar os endpoints principais da API.
Execute após iniciar o servidor.
"""

import asyncio
import json
import time
from pathlib import Path
import sys

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

import httpx


class APITester:
    """Testador da API REST."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_health_check(self):
        """Testa endpoints de saúde."""
        print("🏥 Testando Health Check...")
        
        try:
            # Teste básico
            response = await self.client.get(f"{self.base_url}/health/live")
            print(f"  Live: {response.status_code} - {response.json()}")
            
            # Teste completo
            response = await self.client.get(f"{self.base_url}/health/")
            if response.status_code == 200:
                print("  ✅ Health Check: OK")
            else:
                print(f"  ❌ Health Check: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_root_endpoint(self):
        """Testa endpoint raiz."""
        print("🏠 Testando endpoint raiz...")
        
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Root: {data['name']} v{data['version']}")
            else:
                print(f"  ❌ Root: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_csv_upload(self):
        """Testa upload de CSV."""
        print("📁 Testando upload de CSV...")
        
        try:
            # Criar CSV de teste
            csv_content = """id,amount,user_id,timestamp,category
1,150.50,user123,2023-01-01 10:00:00,food
2,75.25,user456,2023-01-01 10:01:00,transport
3,200.00,user789,2023-01-01 10:02:00,shopping
4,50.75,user123,2023-01-01 10:03:00,food
5,300.00,user456,2023-01-01 10:04:00,shopping"""
            
            files = {"file": ("test_data.csv", csv_content, "text/csv")}
            data = {
                "delimiter": ",",
                "encoding": "utf-8",
                "has_header": True,
                "preview_rows": 3
            }
            
            response = await self.client.post(
                f"{self.base_url}/csv/upload",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Upload: {result['filename']} - {result['rows_count']} linhas")
                return result['file_id']
            else:
                print(f"  ❌ Upload: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            return None
    
    async def test_csv_analysis(self, file_id: str):
        """Testa análise de CSV."""
        if not file_id:
            print("  ⏭️ Pulando análise - sem arquivo")
            return
        
        print("📊 Testando análise de CSV...")
        
        try:
            payload = {
                "file_id": file_id,
                "analysis_type": "statistical",
                "include_visualizations": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/csv/analyze",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Análise: {result['result']['analysis_type']} - {result['result']['processing_time_ms']}ms")
            else:
                print(f"  ❌ Análise: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_fraud_detection(self, file_id: str):
        """Testa detecção de fraudes."""
        if not file_id:
            print("  ⏭️ Pulando detecção - sem arquivo")
            return
        
        print("🔍 Testando detecção de fraudes...")
        
        try:
            payload = {
                "file_id": file_id,
                "amount_column": "amount",
                "user_column": "user_id",
                "timestamp_column": "timestamp",
                "threshold": 0.7
            }
            
            response = await self.client.post(
                f"{self.base_url}/csv/fraud-detection",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                fraud_count = result['result']['fraud_count']
                print(f"  ✅ Fraudes: {fraud_count} detectadas")
            else:
                print(f"  ❌ Detecção: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_rag_search(self):
        """Testa busca RAG."""
        print("🔍 Testando busca RAG...")
        
        try:
            payload = {
                "query": "Como detectar fraudes em cartão de crédito?",
                "query_type": "semantic_search",
                "max_results": 3,
                "similarity_threshold": 0.7
            }
            
            response = await self.client.post(
                f"{self.base_url}/rag/search",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                sources_count = len(result['sources'])
                print(f"  ✅ RAG: {sources_count} fontes encontradas")
            else:
                print(f"  ❌ RAG: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_chat(self):
        """Testa chat."""
        print("💬 Testando chat...")
        
        try:
            payload = {
                "message": "Olá! Como você pode me ajudar com análise de dados?",
                "session_id": "test_session_123",
                "include_memory": True,
                "temperature": 0.7
            }
            
            response = await self.client.post(
                f"{self.base_url}/rag/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Chat: Resposta recebida - {result['processing_time_ms']}ms")
            else:
                print(f"  ❌ Chat: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_auth(self):
        """Testa autenticação."""
        print("🔐 Testando autenticação...")
        
        try:
            # Criar API key
            payload = {
                "name": "Teste Key",
                "permissions": ["read", "write"]
            }
            
            response = await self.client.post(
                f"{self.base_url}/auth/api-key",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ API Key criada: {result['name']}")
                
                # Testar validação
                headers = {"Authorization": f"Bearer {result['api_key']}"}
                validate_response = await self.client.get(
                    f"{self.base_url}/auth/validate",
                    headers=headers
                )
                
                if validate_response.status_code == 200:
                    print("  ✅ Validação: OK")
                else:
                    print(f"  ❌ Validação: {validate_response.status_code}")
                    
            else:
                print(f"  ❌ Auth: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def test_system_stats(self):
        """Testa estatísticas do sistema."""
        print("📈 Testando estatísticas...")
        
        try:
            response = await self.client.get(f"{self.base_url}/analysis/stats")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Stats: {result['vectorstore_embeddings']} embeddings")
            else:
                print(f"  ❌ Stats: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    async def run_all_tests(self):
        """Executa todos os testes."""
        print("🚀 INICIANDO TESTES DA API")
        print("=" * 50)
        
        start_time = time.time()
        
        # Testes básicos
        await self.test_health_check()
        await self.test_root_endpoint()
        
        # Testes de CSV
        file_id = await self.test_csv_upload()
        await self.test_csv_analysis(file_id)
        await self.test_fraud_detection(file_id)
        
        # Testes de RAG e Chat
        await self.test_rag_search()
        await self.test_chat()
        
        # Testes de sistema
        await self.test_auth()
        await self.test_system_stats()
        
        total_time = time.time() - start_time
        
        print("=" * 50)
        print(f"🏁 TESTES CONCLUÍDOS em {total_time:.2f}s")
        print("\n📚 Documentação automática disponível em:")
        print(f"   • Swagger UI: {self.base_url}/docs")
        print(f"   • ReDoc: {self.base_url}/redoc")
        
        await self.client.aclose()


async def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testador da API EDA AI Minds")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="URL base da API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    print(f"🎯 Testando API em: {args.url}")
    print("💡 Certifique-se de que o servidor está rodando:")
    print("   python -m src.api.main")
    print()
    
    tester = APITester(args.url)
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro nos testes: {e}")


if __name__ == "__main__":
    asyncio.run(main())