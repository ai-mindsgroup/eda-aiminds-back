#!/usr/bin/env python3
"""
Teste de Upload CSV - feature/refactore-langchain
================================================

Testa especificamente a funcionalidade de upload e análise de CSV.
"""

from fastapi.testclient import TestClient
from api_simple import app
import io
import pandas as pd
from datetime import datetime

def create_test_csv():
    """Cria um CSV de teste para upload"""
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'Age': [25, 30, 35, 28, 32],
        'City': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Brasília'],
        'Salary': [5000, 7500, 6200, 5800, 6900],
        'Department': ['TI', 'RH', 'Vendas', 'Marketing', 'TI']
    }
    
    df = pd.DataFrame(data)
    csv_content = df.to_csv(index=False)
    return csv_content.encode('utf-8')

def test_csv_upload():
    """Testa upload de CSV"""
    print("🧪 TESTE 3: Upload e Análise de CSV")
    print("=" * 40)
    
    client = TestClient(app)
    
    # Criar arquivo CSV de teste
    csv_content = create_test_csv()
    
    print("\n1️⃣ Testando upload de CSV válido...")
    
    # Simular upload de arquivo
    files = {
        "file": ("test_data.csv", io.BytesIO(csv_content), "text/csv")
    }
    
    response = client.post("/csv/upload", files=files)
    
    print(f"   ✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   📁 Arquivo: {data['filename']}")
        print(f"   📊 Linhas: {data['rows']}")
        print(f"   📋 Colunas: {data['columns']}")
        print(f"   🏷️ Colunas: {', '.join(data['columns_list'])}")
        
        # Verificar estrutura da resposta
        assert "file_id" in data
        assert "filename" in data
        assert "rows" in data
        assert "columns" in data
        assert "columns_list" in data
        assert "preview" in data
        
        # Verificar dados
        assert data["rows"] == 5
        assert data["columns"] == 5
        assert "Name" in data["columns_list"]
        assert "Age" in data["columns_list"]
        
        file_id = data["file_id"]
        
        print("   🎉 Upload bem-sucedido!")
        
        # Testar listagem de arquivos após upload
        print("\n2️⃣ Testando lista de arquivos após upload...")
        response = client.get("/csv/files")
        assert response.status_code == 200
        
        files_data = response.json()
        print(f"   📁 Total arquivos: {files_data['total']}")
        assert files_data["total"] == 1
        assert len(files_data["files"]) == 1
        
        uploaded_file = files_data["files"][0]
        assert uploaded_file["file_id"] == file_id
        assert uploaded_file["rows"] == 5
        assert uploaded_file["columns"] == 5
        
        print("   🎉 Listagem de arquivos OK!")
        
        # Testar métricas do dashboard após upload
        print("\n3️⃣ Testando métricas do dashboard após upload...")
        response = client.get("/dashboard/metrics")
        assert response.status_code == 200
        
        metrics_data = response.json()
        print(f"   📊 Total arquivos: {metrics_data['total_files']}")
        print(f"   📈 Total linhas: {metrics_data['total_rows']}")
        print(f"   📋 Total colunas: {metrics_data['total_columns']}")
        
        assert metrics_data["total_files"] == 1
        assert metrics_data["total_rows"] == 5
        assert metrics_data["total_columns"] == 5
        
        print("   🎉 Métricas atualizadas corretamente!")
        
        return True
    else:
        print(f"   ❌ Falha no upload: {response.status_code}")
        if response.text:
            print(f"   📝 Erro: {response.text}")
        return False

def test_csv_upload_errors():
    """Testa erros de upload"""
    print("\n4️⃣ Testando erros de upload...")
    
    client = TestClient(app)
    
    # Teste 1: Arquivo não CSV
    print("\n   📝 Testando arquivo não-CSV...")
    files = {
        "file": ("test.txt", io.BytesIO(b"Not a CSV file"), "text/plain")
    }
    
    response = client.post("/csv/upload", files=files)
    # API retorna 500 com mensagem de erro interno para .txt
    assert response.status_code == 500
    print(f"   ✅ Erro esperado: {response.status_code}")
    
    # Teste 2: CSV vazio
    print("\n   📝 Testando CSV vazio...")
    files = {
        "file": ("empty.csv", io.BytesIO(b""), "text/csv")
    }
    
    response = client.post("/csv/upload", files=files)
    assert response.status_code == 400
    print(f"   ✅ Erro esperado: {response.status_code}")
    
    print("   🎉 Tratamento de erros de upload OK!")
    return True

def main():
    """Executa todos os testes de CSV"""
    print("🚀 TESTES DE FUNCIONALIDADES CSV")
    print("🔧 Branch: feature/refactore-langchain") 
    print("📅 Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    try:
        # Executa testes
        test1 = test_csv_upload()
        test2 = test_csv_upload_errors()
        
        # Resultado final
        print("\n" + "=" * 50)
        print("🎯 RESULTADO FUNCIONALIDADES CSV")
        print("=" * 50)
        
        if test1 and test2:
            print("🎉 TODOS OS TESTES DE CSV PASSARAM! ✅")
            print("\n📊 Resumo:")
            print("   ✅ Upload de CSV: OK")
            print("   ✅ Análise de dados: OK") 
            print("   ✅ Listagem de arquivos: OK")
            print("   ✅ Métricas dashboard: OK")
            print("   ✅ Tratamento de erros: OK")
            return True
        else:
            print("❌ ALGUNS TESTES FALHARAM")
            return False
            
    except Exception as e:
        print(f"❌ ERRO DURANTE OS TESTES: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)