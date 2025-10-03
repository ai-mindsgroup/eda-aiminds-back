#!/usr/bin/env python3
"""
Teste Rápido da API - Upload CSV
=================================

Script para validar que o upload está funcionando.
"""

import requests
import json
from pathlib import Path

# Configuração
API_URL = "http://localhost:8000"
CSV_FILE = "data/creditcard_test_500.csv"

def test_health():
    """Testar health check."""
    print("🔍 Testando health check...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API está saudável: {data['status']}")
            print(f"   Versão: {data['version']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def test_upload():
    """Testar upload de CSV."""
    print(f"\n📤 Testando upload de CSV...")
    
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"❌ Arquivo não encontrado: {CSV_FILE}")
        return False
    
    try:
        with open(csv_path, 'rb') as f:
            files = {'file': (csv_path.name, f, 'text/csv')}
            response = requests.post(f"{API_URL}/csv/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload bem-sucedido!")
            print(f"   File ID: {data['file_id']}")
            print(f"   Filename: {data['filename']}")
            print(f"   Linhas: {data['rows']}")
            print(f"   Colunas: {data['columns']}")
            print(f"   Mensagem: {data['message']}")
            print(f"   Colunas: {', '.join(data['columns_list'][:5])}...")
            print(f"   Preview: {data['preview']['total_preview_rows']} linhas")
            return True
        else:
            print(f"❌ Upload falhou: {response.status_code}")
            print(f"   Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        return False

def test_list_files():
    """Testar listagem de arquivos."""
    print(f"\n📋 Testando listagem de arquivos...")
    try:
        response = requests.get(f"{API_URL}/csv/files")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de arquivos: {data['total']}")
            for file_info in data['files']:
                print(f"   - {file_info['filename']}: {file_info['rows']} linhas, {file_info['columns']} colunas")
            return True
        else:
            print(f"❌ Listagem falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na listagem: {e}")
        return False

def test_metrics():
    """Testar métricas do dashboard."""
    print(f"\n📊 Testando métricas do dashboard...")
    try:
        response = requests.get(f"{API_URL}/dashboard/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Métricas obtidas:")
            print(f"   Total de arquivos: {data['total_files']}")
            print(f"   Total de linhas: {data['total_rows']}")
            print(f"   Total de colunas: {data['total_columns']}")
            print(f"   Status: {data['status']}")
            return True
        else:
            print(f"❌ Métricas falharam: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro nas métricas: {e}")
        return False

def main():
    """Executar todos os testes."""
    print("=" * 60)
    print("🧪 TESTE RÁPIDO - API UPLOAD CSV")
    print("=" * 60)
    
    results = []
    
    # Teste 1: Health Check
    results.append(("Health Check", test_health()))
    
    # Teste 2: Upload CSV
    results.append(("Upload CSV", test_upload()))
    
    # Teste 3: Listar Arquivos
    results.append(("Listar Arquivos", test_list_files()))
    
    # Teste 4: Métricas
    results.append(("Métricas", test_metrics()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:20s} {status}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! API ESTÁ FUNCIONANDO PERFEITAMENTE!")
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam. Verifique a API.")

if __name__ == "__main__":
    main()
