#!/usr/bin/env python3
"""
Debug: Verificar o que está acontecendo com o enriquecimento
"""
import sys
sys.path.append('src')

from src.agent.rag_agent import RAGAgent
from src.embeddings.chunker import TextChunk, ChunkMetadata, ChunkStrategy

def debug_enrichment():
    print("🔍 Debug do processo de enriquecimento...")
    
    # Criar um chunk de teste
    test_content = """Time,V1,V2,V3,V4,V5,V6,V7,V8,V9,V10,V11,V12,V13,V14,V15,V16,V17,V18,V19,V20,V21,V22,V23,V24,V25,V26,V27,V28,Amount,Class
0.0,-1.359807134,-0.072781173,2.536346738,1.378155224,-0.338320769,0.462387778,0.239598554,0.098697901,0.363786969,0.090794172,-0.551599533,-0.617800856,-0.991389847,-0.311169354,1.468176972,-0.470400525,0.207971242,0.025790577,0.403992960,0.251412098,-0.018306778,0.277837576,-0.110473910,0.066928075,0.128539358,-0.189114844,0.133558377,-0.021053053,149.62,0
284.015445,-1.359807134,-0.072781173,2.536346738,1.378155224,-0.338320769,0.462387778,0.239598554,0.098697901,0.363786969,0.090794172,-0.551599533,-0.617800856,-0.991389847,-0.311169354,1.468176972,-0.470400525,0.207971242,0.025790577,0.403992960,0.251412098,-0.018306778,0.277837576,-0.110473910,0.066928075,0.128539358,-0.189114844,0.133558377,-0.021053053,2.69,0"""
    
    metadata = ChunkMetadata(
        source="test_debug",
        chunk_index=1,
        strategy=ChunkStrategy.CSV_ROW,
        char_count=len(test_content),
        word_count=len(test_content.split()),
        start_position=0,
        end_position=len(test_content),
        additional_info={"start_row": 1, "end_row": 3}
    )
    
    test_chunk = TextChunk(content=test_content, metadata=metadata)
    
    print(f"📝 Chunk original tem {len(test_content)} caracteres")
    print(f"🔗 Primeiros 200 chars: {test_content[:200]}...")
    
    # Testar o enriquecimento
    agent = RAGAgent()
    enriched_chunks = agent._enrich_csv_chunks_light([test_chunk])
    
    if enriched_chunks:
        enriched = enriched_chunks[0]
        print(f"\n✨ Chunk enriquecido tem {len(enriched.content)} caracteres")
        print(f"📋 Contém 'DADOS ORIGINAIS': {'=== DADOS ORIGINAIS ===' in enriched.content}")
        print(f"📋 Contém dados do CSV: {test_content[:50] in enriched.content}")
        print(f"\n📄 Conteúdo completo do chunk enriquecido:")
        print("=" * 80)
        print(enriched.content)
        print("=" * 80)
    else:
        print("❌ Nenhum chunk enriquecido retornado!")

if __name__ == "__main__":
    debug_enrichment()