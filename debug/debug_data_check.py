#!/usr/bin/env python3
"""
Debug: Verificar dados carregados no banco após ingestão
"""
import sys
sys.path.append('src')

from src.vectorstore.supabase_client import supabase

def check_data():
    print("🔍 Verificando dados no banco...")
    
    # Contar embeddings
    try:
        response = supabase.table('embeddings').select('*', count='exact').execute()
        embeddings_count = response.count
        print(f"📊 Embeddings: {embeddings_count}")
        
        # Verificar alguns exemplos de tamanho dos chunks
        if embeddings_count > 0:
            sample_response = supabase.table('embeddings').select('chunk_text').limit(1).execute()
            
            print("\n📋 Verificação detalhada de 1 chunk:")
            for i, row in enumerate(sample_response.data):
                chunk_text = row['chunk_text']
                print(f"  Chunk {i+1}: {len(chunk_text)} caracteres")
                
                # Verificar se contém dados originais
                has_original = "=== DADOS ORIGINAIS ===" in chunk_text
                has_enriched = "Dataset de detecção de fraude" in chunk_text
                
                print(f"    ✓ Dados originais: {'Sim' if has_original else 'Não'}")
                print(f"    ✓ Enriquecimento: {'Sim' if has_enriched else 'Não'}")
                print(f"    📝 CONTEÚDO COMPLETO:")
                print("    " + "="*76)
                print("    " + chunk_text.replace('\n', '\n    '))
                print("    " + "="*76)
                print()
                
    except Exception as e:
        print(f"❌ Erro ao verificar embeddings: {e}")
    
    # Verificar tamanho do arquivo original
    import os
    csv_path = "data/creditcard.csv"
    if os.path.exists(csv_path):
        file_size = os.path.getsize(csv_path)
        print(f"📁 Arquivo CSV: {file_size:,} bytes")
        
        # Contar linhas
        with open(csv_path, 'r') as f:
            line_count = sum(1 for _ in f)
        print(f"📄 Linhas no CSV: {line_count:,}")
    
    print("\n✅ Verificação concluída!")

if __name__ == "__main__":
    check_data()