#!/usr/bin/env python3
"""
Teste rápido: Ingestão das primeiras 500 linhas para validar correção
"""
import sys
import pandas as pd
sys.path.append('src')

from src.agent.rag_agent import RAGAgent

def test_small_ingest():
    print("🧪 Teste rápido: Ingestão das primeiras 500 linhas")
    
    # Criar dataset de teste com 500 linhas
    print("📁 Lendo arquivo original...")
    df_full = pd.read_csv("data/creditcard.csv")
    
    # Pegar apenas as primeiras 500 linhas
    df_test = df_full.head(500)
    
    # Salvar arquivo de teste
    test_file = "data/creditcard_test_500.csv"
    df_test.to_csv(test_file, index=False)
    print(f"✅ Arquivo de teste criado: {test_file} ({len(df_test)} linhas)")
    
    # Executar ingestão
    print("\n🚀 Iniciando ingestão de teste...")
    agent = RAGAgent()
    
    result = agent.ingest_csv_file(
        file_path=test_file,
        source_id="creditcard_test_500"
    )
    
    print(f"\n📊 Resultado: {result.get('response', 'Sem resposta')}")
    
    return result

if __name__ == "__main__":
    test_small_ingest()