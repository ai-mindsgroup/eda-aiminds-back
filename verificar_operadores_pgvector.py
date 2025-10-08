"""
Verificar operadores pgvector e calcular distância
"""
import psycopg
from src.settings import build_db_dsn
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import parse_embedding_from_api

# Conectar
conn = psycopg.connect(build_db_dsn())
cur = conn.cursor()

# 1. Verificar operadores disponíveis
print("1️⃣ Operadores pgvector disponíveis:")
cur.execute("""
    SELECT oprname, oprleft::regtype, oprright::regtype, oprresult::regtype
    FROM pg_operator 
    WHERE oprname IN ('<->', '<=>', '<#>', '<>')
    ORDER BY oprname
""")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]} / {row[2]} → {row[3]}")

# 2. Buscar chunk e calcular distâncias
print("\n2️⃣ Buscando chunk metadata_distribution...")
cur.execute("""
    SELECT id, embedding
    FROM embeddings
    WHERE metadata->>'chunk_type' = 'metadata_distribution'
    LIMIT 1
""")
row = cur.fetchone()
chunk_id, chunk_emb_raw = row
chunk_emb = parse_embedding_from_api(str(chunk_emb_raw))

# 3. Gerar embedding da pergunta
print("3️⃣ Gerando embedding da pergunta...")
gen = EmbeddingGenerator()
result = gen.generate_embedding("Qual o intervalo de cada variável (mínimo, máximo)?")
query_emb = result.embedding
query_emb_str = '[' + ','.join(str(x) for x in query_emb) + ']'

# 4. Testar operadores
print("\n4️⃣ Testando operadores:")
for op in ['<->', '<=>', '<#>']:
    try:
        cur.execute(f"""
            SELECT %s::vector(384) {op} embedding AS distance
            FROM embeddings
            WHERE id = %s
        """, (query_emb_str, chunk_id))
        distance = cur.fetchone()[0]
        print(f"   {op}: {distance:.6f}")
    except Exception as e:
        print(f"   {op}: ERRO - {e}")

# 5. Testar RPC com threshold negativo
print("\n5️⃣ Testando RPC com threshold negativo...")
for threshold in [-1.0, -0.5, 0.0, 0.5]:
    cur.execute("""
        SELECT COUNT(*)
        FROM match_embeddings(%s::vector(384), %s, 10)
    """, (query_emb_str, threshold))
    count = cur.fetchone()[0]
    print(f"   Threshold {threshold}: {count} resultados")

cur.close()
conn.close()
print("\n✅ Concluído")
