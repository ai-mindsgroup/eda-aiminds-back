"""Script para limpar tabela embeddings de forma eficiente."""
from src.vectorstore.supabase_client import supabase
import time

print("🗑️ Limpando tabela embeddings...")

try:
    # Deletar em pequenos lotes para evitar timeout
    batch_size = 50
    total_deleted = 0
    
    while True:
        # Buscar IDs em lote pequeno
        result = supabase.table('embeddings').select('id').limit(batch_size).execute()
        
        if not result.data:
            break
        
        ids_to_delete = [row['id'] for row in result.data]
        
        # Deletar por ID específico
        for row_id in ids_to_delete:
            try:
                supabase.table('embeddings').delete().eq('id', row_id).execute()
                total_deleted += 1
                if total_deleted % 10 == 0:
                    print(f"  Deletados {total_deleted}...")
            except Exception as e:
                print(f"  Erro ao deletar {row_id}: {e}")
                time.sleep(0.1)
    
    print(f"✅ Total deletado: {total_deleted} embeddings")
    
    # Verificar
    final_count = supabase.table('embeddings').select('id', count='exact').execute()
    print(f"📊 Embeddings restantes: {final_count.count}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
