"""Script rápido para verificar source_id dos chunks ingeridos"""
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator

vs = VectorStore()
eg = EmbeddingGenerator()

# Gerar embedding dummy
emb_result = eg.generate_embedding("dataset metadata")
emb = emb_result.embedding

# Buscar chunks
results = vs.search_similar(query_embedding=emb, similarity_threshold=0.3, limit=20)

print(f"\nTotal de chunks encontrados: {len(results)}\n")

# Agrupar por source_id
source_ids = {}
for r in results:
    sid = r.metadata.get('source_id', 'unknown')
    chunk_type = r.metadata.get('chunk_type', 'unknown')
    
    if sid not in source_ids:
        source_ids[sid] = []
    source_ids[sid].append(chunk_type)

# Mostrar agrupamento
for sid, chunk_types in source_ids.items():
    print(f"source_id: {sid}")
    for ct in chunk_types:
        print(f"  - {ct}")
    print()
