"""Teste da correção de enriquecimento - mini dataset para verificação."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
1.0,-0.966272,-0.185226,1.792993,123.50,0
2.0,-1.158233,0.877737,1.548718,69.99,0
2.0,0.635273,-0.221929,0.492199,3.67,0
3.0,-0.893286,-0.208038,1.416432,4.99,0
3.0,-0.083711,-0.208254,-0.559825,40.80,0
4.0,1.249999,-0.208038,0.253844,93.20,0
4.0,-0.647729,0.133558,-0.496192,3.68,0"""

    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        chunk_size=2048,
        chunk_overlap=200,
        csv_chunk_size_rows=5,  # Apenas 5 linhas por chunk para teste
        csv_overlap_rows=1,
    )
    
    result = agent.ingest_csv_data(
        csv_text=test_csv,
        source_id="test_correction"
    )
    
    print(f"✅ Resultado: {result['content']}")
    
    # Verificar o conteúdo dos chunks gerados
    from src.vectorstore.supabase_client import supabase
    
    test_embeddings = supabase.table('embeddings').select('chunk_text').eq('metadata->>source', 'test_correction').execute()
    
    for i, emb in enumerate(test_embeddings.data):
        chunk_text = emb['chunk_text']
        print(f"\n=== CHUNK {i+1} ===")
        print(f"Tamanho: {len(chunk_text)} caracteres")
        
        if 'DADOS ORIGINAIS' in chunk_text:
            print("✅ Seção de dados originais encontrada!")
            dados_section = chunk_text.split('=== DADOS ORIGINAIS ===')[1]
            lines = [line for line in dados_section.strip().split('\n') if line.strip() and ',' in line]
            print(f"✅ {len(lines)} linhas CSV preservadas!")
        else:
            print("❌ Dados originais não encontrados!")
            
        print("Primeiros 200 chars:")
        print(chunk_text[:200])

if __name__ == "__main__":
    test_correction()