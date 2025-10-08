"""Verificar se chunks analíticos foram armazenados corretamente."""
from src.vectorstore.supabase_client import supabase

print("=" * 60)
print("🔍 VERIFICAÇÃO DE CHUNKS ANALÍTICOS")
print("=" * 60)

# 1. Contar total de embeddings
total_result = supabase.table('embeddings')\
    .select('id', count='exact')\
    .eq('metadata->>source', 'creditcard_full')\
    .execute()

total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
print(f"\n📊 Total de chunks para 'creditcard_full': {total_count}")

# 2. Buscar chunks analíticos específicos
chunk_types = [
    'metadata_types',
    'metadata_distribution',
    'metadata_central_variability',
    'metadata_frequency_outliers',
    'metadata_correlations',
    'metadata_patterns_clusters'
]

print("\n🔎 Buscando chunks analíticos por tipo:\n")
found_chunks = {}

for chunk_type in chunk_types:
    result = supabase.table('embeddings')\
        .select('chunk_text, metadata')\
        .eq('metadata->>source', 'creditcard_full')\
        .eq('metadata->>chunk_type', chunk_type)\
        .limit(1)\
        .execute()
    
    if result.data:
        found_chunks[chunk_type] = result.data[0]
        print(f"✅ {chunk_type}")
        print(f"   Preview: {result.data[0]['chunk_text'][:100]}...")
    else:
        print(f"❌ {chunk_type} - NÃO ENCONTRADO")

print("\n" + "=" * 60)
print(f"📈 RESUMO:")
print(f"   Chunks esperados: 17.801 (dados) + 6 (analíticos) = 17.807")
print(f"   Chunks encontrados: {total_count}")
print(f"   Chunks analíticos encontrados: {len(found_chunks)}/6")
print("=" * 60)

if len(found_chunks) == 6:
    print("\n✅ SUCESSO! Todos os chunks analíticos foram armazenados!")
elif len(found_chunks) == 0:
    print("\n❌ ERRO! Nenhum chunk analítico foi armazenado!")
    print("   Possível causa: Falha no script add_metadata_chunks.py")
else:
    print(f"\n⚠️ PARCIAL! Apenas {len(found_chunks)}/6 chunks foram armazenados")
