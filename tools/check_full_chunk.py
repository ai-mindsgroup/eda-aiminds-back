#!/usr/bin/env python3
"""
Debug: Ver chunk completo no banco
"""
import sys
sys.path.append('src')

from src.vectorstore.supabase_client import supabase

def check_full_chunk():
    print("🔍 Verificando chunk completo no banco...")
    
    try:
        # Buscar um chunk específico
        response = supabase.table('embeddings').select('chunk_text').limit(1).execute()
        
        if response.data:
            chunk_text = response.data[0]['chunk_text']
            print(f"📊 Tamanho real do chunk: {len(chunk_text)} caracteres")
            print(f"📋 Contém 'DADOS ORIGINAIS': {'=== DADOS ORIGINAIS ===' in chunk_text}")
            print("\n📄 CHUNK COMPLETO DO BANCO:")
            print("=" * 80)
            print(chunk_text)
            print("=" * 80)
        else:
            print("❌ Nenhum chunk encontrado!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    check_full_chunk()