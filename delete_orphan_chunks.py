"""
Script cirúrgico para deletar APENAS os 12 chunks analíticos órfãos
(aqueles com chunk_type=NULL mas texto de análise)
"""
from src.vectorstore.supabase_client import supabase

print("🔍 Buscando chunks analíticos órfãos...")

# Estratégia: Buscar pelos últimos 50 chunks e filtrar os órfãos
# (os 12 órfãos devem estar entre os mais recentes)
result = supabase.table('embeddings')\
    .select('id, chunk_text, metadata, created_at')\
    .eq('metadata->>source', 'creditcard_full')\
    .order('created_at', desc=True)\
    .limit(50)\
    .execute()

# Filtrar apenas os órfãos (chunk_type NULL) que são analíticos
orphan_chunks = []
for row in result.data:
    metadata = row.get('metadata', {})
    chunk_type = metadata.get('chunk_type')
    chunk_text = row.get('chunk_text', '')
    
    # Se chunk_type é None/null E o texto contém "ANÁLISE"
    if (not chunk_type or chunk_type == 'null' or chunk_type == 'NONE') and 'ANÁLISE' in chunk_text:
        orphan_chunks.append({
            'id': row['id'],
            'preview': chunk_text[:80]
        })

print(f"\n📋 Encontrados {len(orphan_chunks)} chunks órfãos:")
for i, chunk in enumerate(orphan_chunks, 1):
    print(f"  {i}. ID={chunk['id']}: {chunk['preview']}...")

if orphan_chunks:
    print(f"\n⚠️  Atenção: Vou deletar {len(orphan_chunks)} chunks órfãos")
    confirm = input("Digite 'SIM' para confirmar: ")
    
    if confirm.strip().upper() == 'SIM':
        deleted_count = 0
        for chunk in orphan_chunks:
            try:
                supabase.table('embeddings').delete().eq('id', chunk['id']).execute()
                deleted_count += 1
                print(f"  ✅ Deletado ID {chunk['id']}")
            except Exception as e:
                print(f"  ❌ Erro ao deletar ID {chunk['id']}: {e}")
        
        print(f"\n✅ {deleted_count}/{len(orphan_chunks)} chunks órfãos removidos com sucesso!")
    else:
        print("\n❌ Operação cancelada pelo usuário")
else:
    print("\n✅ Nenhum chunk órfão encontrado!")
