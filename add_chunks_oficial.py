"""
Script genérico para adicionar chunks analíticos de qualquer CSV.

Uso:
    python add_chunks_oficial.py <nome_arquivo.csv>

Exemplo:
    python add_chunks_oficial.py creditcard.csv
    python add_chunks_oficial.py vendas.csv
"""
import sys
from pathlib import Path
from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.vector_store import VectorStore
from src.settings import EDA_DATA_DIR_PROCESSADO
import pandas as pd

# Validar argumentos CLI
if len(sys.argv) < 2:
    print("❌ Uso: python add_chunks_oficial.py <nome_arquivo.csv>")
    print("\nExemplo:")
    print("  python add_chunks_oficial.py creditcard.csv")
    sys.exit(1)

csv_filename = sys.argv[1]
csv_path = EDA_DATA_DIR_PROCESSADO / csv_filename

# Validar existência do arquivo
if not csv_path.exists():
    print(f"❌ Arquivo não encontrado: {csv_path}")
    print(f"\nVerifique se o arquivo está em: {EDA_DATA_DIR_PROCESSADO}")
    sys.exit(1)

print(f"🚀 Adicionando chunks analíticos de: {csv_filename}")

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
print(f"✅ CONCLUÍDO: {success}/{len(results)} chunks armazenados!")
print(f"   Dataset: {csv_filename}")
print(f"   Source ID: {source_id}")
print(f"{'='*60}")
