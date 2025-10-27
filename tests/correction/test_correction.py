"""Teste da correção de enriquecimento - mini dataset para verificação."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider

def test_correction():
    print("🧪 TESTE: Verificando correção do enriquecimento")
    
    # Dados CSV de teste (10 linhas apenas)
    test_csv = """Time,V1,V2,V3,Amount,Class
0.0,-1.359807,-0.072781,2.536347,149.62,0
0.0,1.191857,0.266151,0.166480,2.69,0
1.0,-1.358354,-1.340163,1.773209,378.66,0
2.0,-0.966272,-0.185226,1.792993,123.50,0
2.0,-1.158233,0.877737,1.548718,69.99,0
3.0,0.061458,1.328243,-0.689281,3.67,0
4.0,-0.425966,0.960523,1.141109,4.99,0
5.0,1.229658,-0.644269,-2.261857,40.80,0
6.0,0.175806,-0.831213,-0.311166,93.20,0
7.0,-1.398473,-0.249091,0.771410,3.68,0"""
    
    print(f"📊 Dataset de teste: {test_csv.count(chr(10))} linhas")
    
    # Configurar agente com provider específico
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER
    )
    
    print("\n🔄 Processando ingestão...")
    
    try:
        result = agent.ingest_csv(
            csv_data=test_csv,
            source_id="test_correction",
            session_id="test_session"
        )
        
        print(f"\n✅ Ingestão concluída!")
        print(f"   Chunks gerados: {result.get('chunks_generated', 0)}")
        print(f"   Embeddings: {result.get('embeddings_created', 0)}")
        
        # Verificar metadados
        if 'metadata' in result:
            meta = result['metadata']
            print(f"\n📋 Metadados:")
            print(f"   Colunas: {meta.get('columns', [])}")
            print(f"   Linhas: {meta.get('rows', 0)}")
            print(f"   Tipos: {meta.get('dtypes', {})}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na ingestão: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correction()
    exit(0 if success else 1)