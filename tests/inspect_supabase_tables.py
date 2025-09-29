"""
Script de inspeção e limpeza das tabelas do Supabase/PostgreSQL.

Este script consulta e exibe os dados das principais tabelas usadas pelo sistema multiagente:
- embeddings
- chunks
- metadata

Uso: 
- python tests/inspect_supabase_tables.py (apenas consulta)
- python tests/inspect_supabase_tables.py --delete-all (limpa todas as tabelas)

Obs: Este script é temporário e não faz parte dos testes automatizados. Remova após uso.
"""

# Adiciona o diretório raiz ao sys.path para importar src corretamente
import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def print_table(table_name, limit=10):
    print(f"\n--- {table_name.upper()} (até {limit} registros) ---")
    try:
        data = supabase.table(table_name).select("*").limit(limit).execute()
        rows = data.data
        if not rows:
            print("Nenhum registro encontrado.")
        else:
            for i, row in enumerate(rows, 1):
                print(f"[{i}] {row}")
    except Exception as e:
        print(f"Erro ao consultar {table_name}: {e}")

def delete_all_from_table(table_name):
    """Deleta todos os registros de uma tabela"""
    print(f"\n--- DELETANDO TODOS OS REGISTROS DE {table_name.upper()} ---")
    try:
        # Para deletar todos os registros, usamos uma condição sempre verdadeira
        # Por segurança, primeiro verificamos quantos registros existem
        count_data = supabase.table(table_name).select("id", count="exact").execute()
        total_records = count_data.count
        
        if total_records == 0:
            print(f"Tabela {table_name} já está vazia.")
            return
            
        print(f"Encontrados {total_records} registros em {table_name}. Deletando...")
        
        # Deleta todos os registros usando uma condição que sempre é verdadeira
        # Usamos neq (not equal) com um valor que não existe
        delete_result = supabase.table(table_name).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        print(f"✅ Tabela {table_name} limpa com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao deletar registros de {table_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inspeção e limpeza das tabelas Supabase')
    parser.add_argument('--delete-all', action='store_true', 
                       help='Deleta todos os registros das tabelas embeddings, chunks e metadata')
    
    args = parser.parse_args()
    
    if args.delete_all:
        print("🚨 ATENÇÃO: Esta operação irá deletar TODOS os registros das tabelas!")
        print("Tabelas que serão limpas: embeddings, chunks, metadata")
        
        # Confirma a operação
        confirm = input("Digite 'CONFIRMAR' para continuar: ")
        if confirm.upper() == 'CONFIRMAR':
            delete_all_from_table("embeddings")
            delete_all_from_table("chunks") 
            delete_all_from_table("metadata")
            print("\n✅ Limpeza concluída!")
        else:
            print("❌ Operação cancelada.")
    else:
        print_table("embeddings")
        print_table("chunks")
        print_table("metadata")
