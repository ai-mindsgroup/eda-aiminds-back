"""Script para limpar tabela embeddings de forma simples."""
from src.vectorstore.supabase_client import supabase

# Pegar todos os IDs
result = supabase.table('embeddings').select('id').execute()
ids = [row['id'] for row in result.data]

print(f"Total de embeddings: {len(ids)}")

if ids:
    print("Deletando embeddings...")
    for id in ids:
        try:
            supabase.table('embeddings').delete().eq('id', id).execute()
        except Exception as e:
            print(f"Erro ao deletar {id}: {e}")
    
    print("✅ Tabela limpa!")
else:
    print("Tabela já está vazia")

# Verificar
result = supabase.table('embeddings').select('id').execute()
print(f"Embeddings restantes: {len(result.data)}")
