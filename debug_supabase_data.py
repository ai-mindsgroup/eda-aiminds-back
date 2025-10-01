#!/usr/bin/env python3
"""Debug: Verificar dados disponíveis no Supabase"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.vectorstore.supabase_client import supabase

def check_supabase_data():
    """Verificar que dados estão disponíveis no Supabase"""
    
    print("🔍 Verificando dados no Supabase...")
    
    # 1. Verificar tabela embeddings
    print("\n📊 Tabela embeddings:")
    try:
        embeddings_result = supabase.table('embeddings').select('id, chunk_text').limit(3).execute()
        print(f"   - Total de embeddings encontrados: {len(embeddings_result.data)}")
        for i, emb in enumerate(embeddings_result.data[:2]):
            chunk_preview = emb.get('chunk_text', '')[:100] + '...' if emb.get('chunk_text') else 'N/A'
            print(f"   - Embedding {i+1}: ID={emb.get('id')}, Chunk='{chunk_preview}'")
    except Exception as e:
        print(f"   ❌ Erro ao acessar embeddings: {str(e)}")
    
    # 2. Verificar tabela chunks
    print("\n📋 Tabela chunks:")
    try:
        chunks_result = supabase.table('chunks').select('id, content, metadata').limit(3).execute()
        print(f"   - Total de chunks encontrados: {len(chunks_result.data)}")
        for i, chunk in enumerate(chunks_result.data[:2]):
            content_preview = chunk.get('content', '')[:100] + '...' if chunk.get('content') else 'N/A'
            metadata = chunk.get('metadata', {})
            print(f"   - Chunk {i+1}: ID={chunk.get('id')}")
            print(f"     Content: '{content_preview}'")
            print(f"     Metadata: {metadata}")
    except Exception as e:
        print(f"   ❌ Erro ao acessar chunks: {str(e)}")
    
    # 3. Verificar tabela metadata
    print("\n🗂️ Tabela metadata:")
    try:
        metadata_result = supabase.table('metadata').select('*').limit(5).execute()
        print(f"   - Total de metadados encontrados: {len(metadata_result.data)}")
        for i, meta in enumerate(metadata_result.data[:3]):
            print(f"   - Metadata {i+1}: {meta}")
    except Exception as e:
        print(f"   ❌ Erro ao acessar metadata: {str(e)}")

if __name__ == "__main__":
    check_supabase_data()