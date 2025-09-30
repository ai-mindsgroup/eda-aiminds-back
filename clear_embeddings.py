#!/usr/bin/env python3
"""
Limpa embeddings do banco para reingestão corrigida
"""
import sys
sys.path.append('src')

from src.vectorstore.supabase_client import supabase

def clear_embeddings():
    print("🗑️ Limpando embeddings antigos...")
    
    try:
        # Deletar todos os embeddings usando método mais simples
        response = supabase.table('embeddings').delete().gte('created_at', '2000-01-01').execute()
        
        # Verificar contagem após limpeza
        count_response = supabase.table('embeddings').select('*', count='exact').execute()
        remaining_count = count_response.count
        
        print(f"✅ Embeddings removidos! Restantes: {remaining_count}")
        
    except Exception as e:
        print(f"❌ Erro ao limpar embeddings: {e}")

if __name__ == "__main__":
    clear_embeddings()