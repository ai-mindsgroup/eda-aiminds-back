"""Teste de ingestão com dados corrigidos - subset do dataset."""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider

def test_corrected_ingestion():
    print("🧪 TESTE: Ingestão com dados corrigidos (subset 1000 linhas)")
    
    # Ler apenas 1000 linhas do CSV para teste rápido
    df = pd.read_csv("data/creditcard.csv", nrows=1000)
    
    # Converter para CSV string
    csv_data = df.to_csv(index=False)
    
    print(f"📊 Dataset: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Criar agente
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER
    )
    
    print("\n🔄 Processando ingestão...")
    
    try:
        result = agent.ingest_csv(
            csv_data=csv_data,
            source_id="creditcard_corrected",
            session_id="test_session"
        )
        
        print(f"\n✅ Ingestão concluída!")
        print(f"   Chunks gerados: {result.get('chunks_generated', 0)}")
        print(f"   Embeddings: {result.get('embeddings_created', 0)}")
        
        # Verificar metadados
        if 'metadata' in result:
            meta = result['metadata']
            print(f"\n📋 Metadados:")
            print(f"   Colunas: {len(meta.get('columns', []))}")
            print(f"   Linhas: {meta.get('rows', 0)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na ingestão: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_corrected_ingestion()
    exit(0 if success else 1)
