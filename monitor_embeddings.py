"""
Script de Monitoramento: Acompanha inserções na tabela embeddings em tempo real.
Execute este script ANTES de rodar run_auto_ingest.py --once
"""
import time
from src.vectorstore.supabase_client import supabase

print("\n" + "="*80)
print("📊 MONITORAMENTO DE EMBEDDINGS - AGUARDANDO INGESTÃO")
print("="*80)

# Limpar tabela primeiro
print("\n🧹 Limpando embeddings existentes...")
result = supabase.table('embeddings').select('id').execute()
initial_count = len(result.data)

if initial_count > 0:
    for row in result.data:
        supabase.table('embeddings').delete().eq('id', row['id']).execute()
    print(f"   ✅ {initial_count} embeddings deletados")
else:
    print("   ✅ Tabela já está vazia")

print("\n⏳ Aguardando ingestão... (Ctrl+C para cancelar)")
print("   Execute: python run_auto_ingest.py --once\n")

last_count = 0
start_time = time.time()

try:
    while True:
        result = supabase.table('embeddings').select('id, metadata').execute()
        current_count = len(result.data)
        
        if current_count != last_count:
            elapsed = time.time() - start_time
            
            # Contar metadata chunks
            metadata_chunks = sum(
                1 for r in result.data 
                if r.get('metadata', {}).get('additional_info', {}).get('chunk_type', '').startswith('metadata_')
            )
            
            # Contar data chunks
            data_chunks = current_count - metadata_chunks
            
            print(f"[{elapsed:6.1f}s] 📊 Total: {current_count:3d} embeddings | " + 
                  f"Metadata: {metadata_chunks:2d} | Dados: {data_chunks:3d}")
            
            # Se chegou a 6+ embeddings de metadata, mostrar detalhes
            if metadata_chunks >= 6 and last_count < current_count:
                print("\n   🎯 Chunks de Metadata Detectados:")
                for r in result.data:
                    chunk_type = r.get('metadata', {}).get('additional_info', {}).get('chunk_type', '')
                    if chunk_type.startswith('metadata_'):
                        topic = r.get('metadata', {}).get('additional_info', {}).get('topic', 'N/A')
                        print(f"      ✅ {chunk_type} - {topic}")
                print()
            
            last_count = current_count
            
            # Se estabilizou (sem mudança por 5 segundos), assumir que terminou
            if current_count > 0:
                time.sleep(5)
                result_check = supabase.table('embeddings').select('id').execute()
                if len(result_check.data) == current_count:
                    print("\n" + "="*80)
                    print("✅ INGESTÃO CONCLUÍDA!")
                    print("="*80)
                    print(f"   📊 Total de embeddings: {current_count}")
                    print(f"   📊 Chunks de metadata: {metadata_chunks}")
                    print(f"   📊 Chunks de dados: {data_chunks}")
                    
                    if metadata_chunks == 6:
                        print("\n   🎉 SUCESSO! 6 chunks de metadata conforme esperado!")
                    else:
                        print(f"\n   ⚠️  Esperado 6 chunks de metadata, mas foram gerados {metadata_chunks}")
                    
                    print("="*80 + "\n")
                    break
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\n⏹️  Monitoramento cancelado pelo usuário")
    print(f"   Embeddings finais: {last_count}\n")
