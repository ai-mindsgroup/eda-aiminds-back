"""
Debug profundo: Verificar embeddings e função RPC
"""
import psycopg
from src.settings import build_db_dsn
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import parse_embedding_from_api
import numpy as np
from numpy.linalg import norm

print("="*70)
print("🔍 DEBUG PROFUNDO: EMBEDDINGS E RPC")
print("="*70)

# Conectar via psycopg
conn = psycopg.connect(build_db_dsn())
cur = conn.cursor()

# 1. Buscar chunk metadata_distribution
print("\n1️⃣ Buscando chunk metadata_distribution...")
cur.execute("""
    SELECT id, chunk_text, embedding, metadata
    FROM embeddings
    WHERE metadata->>'chunk_type' = 'metadata_distribution'
    LIMIT 1
""")
row = cur.fetchone()

if not row:
    print("❌ Chunk não encontrado!")
    exit(1)

chunk_id, chunk_text, chunk_embedding_raw, chunk_metadata = row
print(f"   ✅ Chunk encontrado (ID: {chunk_id})")
print(f"   Metadata: {chunk_metadata}")
print(f"   Embedding type: {type(chunk_embedding_raw)}")

# Parse embedding
chunk_embedding = parse_embedding_from_api(str(chunk_embedding_raw))
print(f"   ✅ Embedding parseado: {len(chunk_embedding)} dimensões")
print(f"   Primeiros 5 valores: {chunk_embedding[:5]}")

# 2. Gerar embedding da pergunta
print("\n2️⃣ Gerando embedding da pergunta...")
pergunta = "Qual o intervalo de cada variável (mínimo, máximo)?"
gen = EmbeddingGenerator()
result = gen.generate_embedding(pergunta)
query_embedding = result.embedding

print(f"   ✅ Embedding gerado: {len(query_embedding)} dimensões")
print(f"   Primeiros 5 valores: {query_embedding[:5]}")

# 3. Calcular similaridade manualmente (cosseno)
print("\n3️⃣ Calculando similaridade cosseno...")
query_vec = np.array(query_embedding)
chunk_vec = np.array(chunk_embedding)

similarity_cosine = np.dot(query_vec, chunk_vec) / (norm(query_vec) * norm(chunk_vec))
print(f"   📊 Similaridade cosseno: {similarity_cosine:.6f}")

# 4. Calcular distância <=> (operador pgvector)
print("\n4️⃣ Calculando distância <=> (operador pgvector)...")
distance = np.linalg.norm(query_vec - chunk_vec)
similarity_pgvector = 1 - distance
print(f"   📊 Distância L2: {distance:.6f}")
print(f"   📊 Similaridade (1 - distância): {similarity_pgvector:.6f}")

# 5. Testar RPC function diretamente
print("\n5️⃣ Testando RPC function match_embeddings...")
query_embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

cur.execute("""
    SELECT * FROM match_embeddings(
        %s::vector(384),
        0.0,
        10
    )
""", (query_embedding_str,))

results = cur.fetchall()
print(f"   📊 Resultados encontrados: {len(results)}")
if results:
    for i, (id, text, metadata, sim) in enumerate(results, 1):
        print(f"      [{i}] Similaridade: {sim:.6f} - {metadata.get('chunk_type', 'N/A')}")
        print(f"          Preview: {text[:100]}...")

# 6. Buscar TODOS os embeddings e calcular similaridade
print("\n6️⃣ Buscando todos os embeddings e calculando similaridade...")
cur.execute("""
    SELECT id, metadata->>'chunk_type' as chunk_type, embedding
    FROM embeddings
    ORDER BY RANDOM()
    LIMIT 20
""")

results = []
for id, chunk_type, emb_raw in cur.fetchall():
    try:
        emb = parse_embedding_from_api(str(emb_raw))
        emb_vec = np.array(emb)
        sim = np.dot(query_vec, emb_vec) / (norm(query_vec) * norm(emb_vec))
        results.append((id, chunk_type, sim))
    except Exception as e:
        print(f"   ⚠️ Erro ao processar {id}: {e}")

results.sort(key=lambda x: x[2], reverse=True)
print(f"   Top 10 mais similares (amostra de 20):")
for i, (id, chunk_type, sim) in enumerate(results[:10], 1):
    print(f"      [{i}] {sim:.6f} - {chunk_type or 'transaction'}")

cur.close()
conn.close()

print("\n" + "="*70)
print("✅ DEBUG CONCLUÍDO")
print("="*70)
