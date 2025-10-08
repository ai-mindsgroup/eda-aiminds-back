"""Verificar chunks armazenados."""
from src.vectorstore.supabase_client import supabase

# Verificar chunks de metadados
result = supabase.table('embeddings').select('id, chunk_text, metadata').eq('metadata->>source', 'creditcard_full').eq('metadata->>chunk_type', 'metadata_types').limit(1).execute()

print(f'Total de chunks metadata_types: {len(result.data)}')

if result.data:
    chunk = result.data[0]
    print(f'\n✅ Chunk encontrado!')
    print(f'ID: {chunk.get("id")}')
    print(f'Metadata: {chunk.get("metadata")}')
    print(f'Conteúdo (primeiros 300 chars): {chunk.get("chunk_text", "")[:300]}...')
else:
    print('\n❌ Nenhum chunk encontrado!')
    
# Verificar total de chunks creditcard
total_result = supabase.table('embeddings').select('count').eq('metadata->>source', 'creditcard_full').execute()
print(f'\nTotal de chunks creditcard_full: {total_result.data}')
