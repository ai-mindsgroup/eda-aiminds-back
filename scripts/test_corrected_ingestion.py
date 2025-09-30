"""Teste de ingestão com dados corrigidos - subset do dataset."""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider

def test_corrected_ingestion():
    print("🧪 TESTE: Ingestão com dados corrigidos (subset 1000 linhas)")
    
    # Ler apenas 1000 linhas do CSV para teste rápido
    df = pd.read_csv("data/creditcard.csv", nrows=1000)
    
    # Converter para CSV string
    csv_content = df.to_csv(index=False)
    
    print(f"📊 Dataset carregado: {len(df)} linhas, {len(csv_content)} caracteres")
    
    # Configurar agente
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        chunk_size=2048,
        chunk_overlap=200,
        csv_chunk_size_rows=50,  # 50 linhas por chunk para teste
        csv_overlap_rows=5,
    )
    
    print(f"✅ Configurações:")
    print(f"   • Linhas por chunk: 50")
    print(f"   • Overlap: 5 linhas")
    print(f"   • Estimativa de chunks: ~{len(df) // 50}")
    
    result = agent.ingest_csv_data(
        csv_text=csv_content,
        source_id="creditcard_corrected_test"
    )
    
    print(f"✅ Resultado: {result['content']}")
    
    # Verificar qualidade dos dados
    from src.vectorstore.supabase_client import supabase
    
    sample = supabase.table('embeddings').select('chunk_text').eq('metadata->>source', 'creditcard_corrected_test').limit(1).execute()
    
    if sample.data:
        chunk_text = sample.data[0]['chunk_text']
        print(f"\n📋 VERIFICAÇÃO DO CHUNK:")
        print(f"   • Tamanho: {len(chunk_text)} caracteres")
        
        if 'DADOS ORIGINAIS' in chunk_text:
            print("   ✅ Seção de dados originais encontrada!")
            dados_section = chunk_text.split('=== DADOS ORIGINAIS ===')[1]
            lines = [line for line in dados_section.strip().split('\n') if line.strip() and ',' in line and not line.startswith('Time,')]
            print(f"   ✅ {len(lines)} linhas de dados CSV preservadas!")
        else:
            print("   ❌ Dados originais não encontrados!")
            
        print(f"\nPrimeiros 300 chars:")
        print(chunk_text[:300] + "...")

if __name__ == "__main__":
    test_corrected_ingestion()