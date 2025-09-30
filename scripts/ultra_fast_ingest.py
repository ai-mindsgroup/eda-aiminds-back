"""Script de ingestão balanceado - performance + qualidade.

ESTRATÉGIA BALANCEADA:
- Chunks médios (250 linhas) para boa granularidade
- Enriquecimento leve preservando contexto
- Processamento assíncrono (4 workers paralelos)
- Qualidade preservada com velocidade otimizada

ESTIMATIVA: ~2-4 horas (vs 12h anterior)
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider

def main() -> int:
    print("🚀 INGESTÃO BALANCEADA creditcard.csv (Performance + Qualidade)")
    
    # Configurações balanceadas
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        chunk_size=2048,  # Chunks textuais médios
        chunk_overlap=200,  # Overlap adequado
        csv_chunk_size_rows=250,  # 250 linhas por chunk (balanceado)
        csv_overlap_rows=25,  # 10% de overlap
    )
    
    print(f"✅ Configurações balanceadas:")
    print(f"   • Linhas por chunk: 250 (qualidade + performance)")
    print(f"   • Overlap: 25 linhas (10% - preserva contexto)")
    print(f"   • Enriquecimento: LEVE (contexto essencial)")
    print(f"   • Processamento: ASSÍNCRONO (4 workers)")
    print(f"   • Batch embeddings: 100")
    print(f"   • Batch Supabase: 1000")
    
    result = agent.ingest_csv_file(
        file_path="data/creditcard.csv",
        source_id="creditcard_balanced_v1",
        encoding="utf-8",
        errors="ignore",
    )

    content = result.get("content", "")
    metadata = result.get("metadata", {})

    if metadata.get("error"):
        print("❌ Falha na ingestão:")
        print(f"   • {content}")
        return 1

    print("✅ Ingestão balanceada concluída!")
    print(content)
    
    if metadata:
        print("\n📊 Estatísticas:")
        print(f"   • Chunks: {metadata.get('chunks_created')}")
        print(f"   • Embeddings: {metadata.get('embeddings_generated')}")
        print(f"   • Armazenados: {metadata.get('embeddings_stored')}")
        print(f"   • Tempo: {metadata.get('processing_time', 0):.1f}s")
        
        # Calcular velocidade e projeção
        chunks = metadata.get('chunks_created', 0)
        time_taken = metadata.get('processing_time', 1)
        if chunks and time_taken:
            speed = chunks / time_taken
            print(f"   • Velocidade: {speed:.1f} chunks/segundo")
            
            # Estimar total com 285k linhas / 250 por chunk = ~1140 chunks
            total_chunks_estimated = 285000 // 250
            if speed > 0:
                total_time_estimated = total_chunks_estimated / speed
                hours = total_time_estimated / 3600
                print(f"   • Estimativa total: {hours:.1f} horas para dataset completo")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())