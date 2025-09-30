"""Script balanceado para ingestão eficiente e precisa do creditcard.csv.

ESTRATÉGIA BALANCEADA:
- Chunks médios (200-250 linhas) para boa granularidade
- Enriquecimento leve que preserva contexto semântico
- Batch sizes otimizados para estabilidade
- Processamento eficiente sem comprometer qualidade
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
    print("🚀 INGESTÃO BALANCEADA creditcard.csv (Velocidade + Precisão)")
    
    # Configurações balanceadas
    agent = RAGAgent(
        embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
        chunk_size=4096,  # Texto moderado
        chunk_overlap=200,  # Overlap suficiente para contexto
        csv_chunk_size_rows=250,  # Chunks médios (vs 20 muito pequeno, vs 1000 muito grande)
        csv_overlap_rows=25,  # 10% de overlap para contexto
    )
    
    print(f"✅ Configurações balanceadas:")
    print(f"   • Linhas por chunk: 250 (boa granularidade)")
    print(f"   • Overlap: 25 linhas (contexto preservado)")
    print(f"   • Enriquecimento: LEVE (sem pandas pesado)")
    print(f"   • Batch embeddings: 30 (estável)")
    print(f"   • Batch Supabase: 300 (otimizado)")
    
    # Calcular estimativa de chunks
    total_lines = 284807  # Total do creditcard.csv
    chunk_step = 250 - 25  # chunk_size - overlap
    estimated_chunks = (total_lines // chunk_step) + 1
    print(f"   • Chunks estimados: ~{estimated_chunks}")
    print(f"   • Tempo estimado: ~{estimated_chunks * 0.5 / 60:.1f} minutos")
    
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
        
        # Calcular eficiência
        chunks = metadata.get('chunks_created', 0)
        time_taken = metadata.get('processing_time', 1)
        if chunks and time_taken:
            speed = chunks / time_taken * 60  # chunks per minute
            print(f"   • Velocidade: {speed:.1f} chunks/minuto")
            
        # Taxa de sucesso
        generated = metadata.get('embeddings_generated', 0)
        stored = metadata.get('embeddings_stored', 0)
        if generated:
            success_rate = (stored / generated) * 100
            print(f"   • Taxa de sucesso: {success_rate:.1f}%")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())