"""Debug detalhado do enriquecimento de chunks."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.embeddings.chunker import TextChunker, ChunkStrategy
from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider

def debug_enrichment():
    print("🔍 DEBUG: Investigando enriquecimento de chunks")
    
    # Dados CSV de teste simples
    test_csv = """Time,V1,V2,V3,Amount,Class
0.0,-1.359807,-0.072781,2.536347,149.62,0
0.0,1.191857,0.266151,0.166480,2.69,0
1.0,-1.358354,-1.340163,1.773209,378.66,0"""

    print(f"Dados de entrada ({len(test_csv)} chars):")
    print(test_csv)
    print("\n" + "="*60)
    
    # 1. Testar chunking diretamente
    chunker = TextChunker(chunk_size=2048, overlap_size=200, csv_chunk_size_rows=2, csv_overlap_rows=0)
    raw_chunks = chunker.chunk_text(test_csv, "test_debug", ChunkStrategy.CSV_ROW)
    
    print(f"\n📊 CHUNKS CRIADOS: {len(raw_chunks)}")
    for i, chunk in enumerate(raw_chunks):
        print(f"\n--- CHUNK {i+1} ANTES DO ENRIQUECIMENTO ---")
        print(f"Conteúdo ({len(chunk.content)} chars):")
        print(chunk.content)
        print(f"Metadata: {chunk.metadata.__dict__}")
    
    # 2. Testar enriquecimento diretamente
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        chunk_size=2048,
        chunk_overlap=200,
        csv_chunk_size_rows=2,
        csv_overlap_rows=0,
    )
    
    enriched_chunks = agent._enrich_csv_chunks_light(raw_chunks)
    
    print(f"\n🔧 CHUNKS APÓS ENRIQUECIMENTO: {len(enriched_chunks)}")
    for i, chunk in enumerate(enriched_chunks):
        print(f"\n--- CHUNK {i+1} APÓS ENRIQUECIMENTO ---")
        print(f"Conteúdo ({len(chunk.content)} chars):")
        print(chunk.content)
        print(f"Metadata: {chunk.metadata.__dict__}")
        
        # Verificações
        if 'DADOS ORIGINAIS' in chunk.content:
            print("✅ Seção de dados originais encontrada!")
            dados_section = chunk.content.split('=== DADOS ORIGINAIS ===')[1]
            print(f"Dados originais ({len(dados_section)} chars):")
            print(dados_section[:200] + "..." if len(dados_section) > 200 else dados_section)
        else:
            print("❌ Seção de dados originais NÃO encontrada!")

if __name__ == "__main__":
    debug_enrichment()