"""
Diagnóstico: Por que a busca vetorial não encontra chunks?
"""
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator
from src.vectorstore.supabase_client import supabase

print("="*70)
print("🔍 DIAGNÓSTICO: BUSCA VETORIAL")
print("="*70)

# 1. Verificar se chunks analíticos existem
print("\n1️⃣ Verificando chunks analíticos no banco...")
result = supabase.table('embeddings').select('*', count='exact').ilike('metadata->>chunk_type', 'metadata_%').execute()
print(f"   ✅ {result.count} chunks analíticos encontrados no banco\n")

# 2. Listar tipos de chunks analíticos
print("2️⃣ Tipos de chunks analíticos:")
for chunk_type in ['metadata_structure', 'metadata_distribution', 'metadata_central_tendency', 
                    'metadata_variability', 'metadata_outliers', 'metadata_correlation']:
    result = supabase.table('embeddings').select('id', count='exact').eq('metadata->>chunk_type', chunk_type).execute()
    print(f"   - {chunk_type}: {result.count} chunks")

# 3. Testar busca vetorial com diferentes thresholds
print("\n3️⃣ Testando busca vetorial com diferentes thresholds...")
pergunta = "Qual o intervalo de cada variável (mínimo, máximo)?"

gen = EmbeddingGenerator()
result = gen.generate_embedding(pergunta)
query_embedding = result.embedding

store = VectorStore()

for threshold in [0.0, 0.3, 0.5, 0.7, 0.9]:
    results = store.search_similar(
        query_embedding=query_embedding,
        similarity_threshold=threshold,
        limit=10
    )
    print(f"   Threshold {threshold}: {len(results)} resultados")
    if results:
        print(f"      Melhor match: {results[0].similarity_score:.3f} - {results[0].metadata.get('chunk_type', 'N/A')}")

# 4. Buscar TODOS os embeddings e calcular similaridade manualmente
print("\n4️⃣ Recuperando chunk metadata_distribution diretamente...")
result = supabase.table('embeddings').select('id, chunk_text, embedding, metadata').eq('metadata->>chunk_type', 'metadata_distribution').limit(1).execute()

if result.data:
    chunk = result.data[0]
    print(f"   ✅ Chunk encontrado (ID: {chunk['id']})")
    print(f"   Texto (preview): {chunk['chunk_text'][:200]}...")
    print(f"   Embedding type: {type(chunk['embedding'])}")
    print(f"   Embedding length: {len(str(chunk['embedding']))}")
    
    # Tentar parsear embedding
    from src.embeddings.vector_store import parse_embedding_from_api
    try:
        chunk_embedding = parse_embedding_from_api(chunk['embedding'])
        print(f"   ✅ Embedding parseado: {len(chunk_embedding)} dimensões")
        
        # Calcular similaridade manualmente (cosseno)
        import numpy as np
        from numpy.linalg import norm
        
        query_vec = np.array(query_embedding)
        chunk_vec = np.array(chunk_embedding)
        
        similarity = np.dot(query_vec, chunk_vec) / (norm(query_vec) * norm(chunk_vec))
        print(f"   📊 Similaridade cosseno manual: {similarity:.4f}")
        
    except Exception as e:
        print(f"   ❌ Erro ao parsear embedding: {e}")
else:
    print("   ❌ Chunk metadata_distribution NÃO encontrado!")

print("\n" + "="*70)
print("✅ DIAGNÓSTICO CONCLUÍDO")
print("="*70)
