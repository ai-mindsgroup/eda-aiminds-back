"""
Script para adicionar os 6 chunks analíticos um por vez (evita timeout)
"""
from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import VectorStore
import pandas as pd
import time

print("🚀 Iniciando adição de chunks analíticos...")

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

# 3. Armazenar UM POR VEZ (evita timeout)
store = VectorStore()
success_count = 0

for i, result in enumerate(results, 1):
    try:
        print(f"\n[{i}/{len(results)}] Armazenando chunk: {result.chunk_metadata.get('chunk_type', 'UNKNOWN')}")
        
        # Preparar payload individual
        payload = {
            'chunk_text': result.chunk_content,  # É chunk_content, não chunk_text!
            'embedding': result.embedding,
            'metadata': {
                **result.chunk_metadata,
                'stored_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # Inserir um por vez
        response = store.supabase.table('embeddings').insert(payload).execute()
        success_count += 1
        print(f"  ✅ Armazenado com sucesso (ID: {response.data[0]['id'][:8]}...)")
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")

print(f"\n{'='*60}")
print(f"✅ CONCLUÍDO: {success_count}/{len(results)} chunks armazenados!")
print(f"{'='*60}")
