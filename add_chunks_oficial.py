"""
Script simplificado: usa o método OFICIAL store_embeddings
que já sabe lidar com result.chunk_content corretamente
"""
from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import VectorStore
import pandas as pd

print("🚀 Adicionando 6 chunks analíticos...")

# 1. Gerar chunks
agent = RAGAgent('rag_agent')
df = pd.read_csv('data/creditcard.csv')
csv_text = df.to_csv(index=False)
chunks = agent._generate_metadata_chunks(csv_text, 'creditcard_full')
print(f"✅ {len(chunks)} chunks gerados")

# 2. Gerar embeddings
gen = EmbeddingGenerator()
results = gen.generate_embeddings_batch(chunks)
print(f"✅ {len(results)} embeddings gerados")

# 3. Armazenar usando o método OFICIAL (que já faz certo!)
store = VectorStore()

# Vamos tentar inserir UM POR VEZ para evitar timeout
success = 0
for i, result in enumerate(results, 1):
    try:
        print(f"\n[{i}/{len(results)}] Armazenando: {result.chunk_metadata.get('chunk_type')}")
        store.store_embeddings([result])  # Lista com 1 elemento
        success += 1
        print(f"  ✅ Sucesso!")
    except Exception as e:
        print(f"  ❌ Erro: {str(e)[:100]}")

print(f"\n{'='*60}")
print(f"✅ CONCLUÍDO: {success}/{len(results)} chunks!")
print(f"{'='*60}")
