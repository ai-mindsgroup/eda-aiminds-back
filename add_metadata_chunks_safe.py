"""
Script genérico para adicionar chunks analíticos de qualquer CSV (um por vez, evita timeout).

Uso:
    python add_metadata_chunks_safe.py <nome_arquivo.csv>

Exemplo:
    python add_metadata_chunks_safe.py creditcard.csv
    python add_metadata_chunks_safe.py vendas.csv
"""
import sys
from pathlib import Path
from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import VectorStore
from src.settings import EDA_DATA_DIR_PROCESSADO
import pandas as pd
import time

# Validar argumentos CLI
if len(sys.argv) < 2:
    print("❌ Uso: python add_metadata_chunks_safe.py <nome_arquivo.csv>")
    print("\nExemplo:")
    print("  python add_metadata_chunks_safe.py creditcard.csv")
    sys.exit(1)

csv_filename = sys.argv[1]
csv_path = EDA_DATA_DIR_PROCESSADO / csv_filename

# Validar existência do arquivo
if not csv_path.exists():
    print(f"❌ Arquivo não encontrado: {csv_path}")
    print(f"\nVerifique se o arquivo está em: {EDA_DATA_DIR_PROCESSADO}")
    sys.exit(1)

print(f"🚀 Iniciando adição de chunks analíticos de: {csv_filename}")

# 1. Gerar chunks
agent = RAGAgent('rag_agent')
df = pd.read_csv(csv_path)
csv_text = df.to_csv(index=False)

# Gerar source_id baseado no nome do arquivo (sem extensão)
source_id = csv_filename.replace('.csv', '')
chunks = agent._generate_metadata_chunks(csv_text, source_id)
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
print(f"   Dataset: {csv_filename}")
print(f"   Source ID: {source_id}")
print(f"{'='*60}")
print(f"✅ CONCLUÍDO: {success_count}/{len(results)} chunks armazenados!")
print(f"{'='*60}")
