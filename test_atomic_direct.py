"""Teste direto do fluxo atomic_ingestion_and_query com RAGAgent."""
from src.vectorstore.supabase_client import supabase
from src.embeddings.vector_store import VectorStore
from src.agent.data_ingestor import atomic_ingestion_and_query

print("="*80)
print("TESTE: atomic_ingestion_and_query com RAGAgent")
print("="*80)

# Limpar embeddings primeiro
print("\n1. Limpando embeddings existentes...")
result = supabase.table('embeddings').select('id').execute()
for row in result.data:
    supabase.table('embeddings').delete().eq('id', row['id']).execute()
print(f"   ✅ {len(result.data)} embeddings deletados")

# Executar atomic_ingestion_and_query
print("\n2. Executando atomic_ingestion_and_query...")
csv_path = "data/processado/creditcard.csv"
vector_store = VectorStore()

results = atomic_ingestion_and_query(csv_path, supabase, vector_store)

print(f"   ✅ Retornou {len(results)} resultados")

# Verificar embeddings inseridos
print("\n3. Verificando embeddings na tabela...")
result = supabase.table('embeddings').select('id, metadata').execute()
total_embeddings = len(result.data)

print(f"   📊 Total de embeddings: {total_embeddings}")

# Contar chunks de metadata
metadata_chunks = [
    r for r in result.data 
    if r.get('metadata', {}).get('additional_info', {}).get('chunk_type', '').startswith('metadata_')
]

print(f"   📊 Chunks de metadata: {len(metadata_chunks)}")

# Listar tipos de chunks de metadata
chunk_types = set()
for r in metadata_chunks:
    chunk_type = r.get('metadata', {}).get('additional_info', {}).get('chunk_type', 'unknown')
    chunk_types.add(chunk_type)

print(f"\n4. Tipos de chunks de metadata encontrados:")
for ct in sorted(chunk_types):
    print(f"   - {ct}")

print("\n" + "="*80)
if len(metadata_chunks) == 6:
    print("✅ SUCESSO! 6 chunks de metadata gerados conforme esperado!")
else:
    print(f"❌ FALHA! Esperado 6 chunks de metadata, mas foram gerados {len(metadata_chunks)}")
print("="*80)
