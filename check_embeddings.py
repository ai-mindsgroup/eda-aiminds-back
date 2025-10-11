from src.vectorstore.supabase_client import supabase

result = supabase.table('embeddings').select('id, chunk_text').limit(3).execute()
print(f'Total de embeddings: {len(result.data)}')
for i, emb in enumerate(result.data):
    chunk_preview = emb["chunk_text"][:100] + "..." if len(emb["chunk_text"]) > 100 else emb["chunk_text"]
    print(f'  {i+1}. {chunk_preview}')