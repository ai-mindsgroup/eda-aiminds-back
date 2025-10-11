#!/usr/bin/env python3
"""
Debug do comportamento de upload para corrigir testes
"""

from fastapi.testclient import TestClient
from api_simple import app
import io

def debug_upload_errors():
    """Debug dos erros de upload"""
    client = TestClient(app)
    
    print("🔍 DEBUG: Testando comportamento de upload com erros")
    
    # Teste arquivo não CSV
    files = {
        "file": ("test.txt", io.BytesIO(b"Not a CSV file"), "text/plain")
    }
    
    response = client.post("/csv/upload", files=files)
    print(f"Arquivo .txt - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Resposta: {response.text[:200]}")
    
    # Teste CSV vazio  
    files = {
        "file": ("empty.csv", io.BytesIO(b""), "text/csv")
    }
    
    response = client.post("/csv/upload", files=files)
    print(f"CSV vazio - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Resposta: {response.text[:200]}")

if __name__ == "__main__":
    debug_upload_errors()