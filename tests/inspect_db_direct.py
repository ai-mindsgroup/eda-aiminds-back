"""
Script de inspeção alternativo usando conexão direta ao PostgreSQL.

Este script conecta diretamente ao banco PostgreSQL para consultar as tabelas:
- embeddings
- chunks  
- metadata

Uso: python tests/inspect_db_direct.py

Obs: Este script é temporário para inspeção. Remova após uso.
"""

# Adiciona o diretório raiz ao sys.path para importar src corretamente
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from src.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def print_table_direct(table_name, limit=10):
    print(f"\n--- {table_name.upper()} (até {limit} registros) ---")
    try:
        # Conecta diretamente ao PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        
        # Primeiro verifica se a tabela existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print(f"Tabela '{table_name}' não existe.")
            return
        
        # Consulta os dados da tabela
        cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
        rows = cursor.fetchall()
        
        if not rows:
            print("Nenhum registro encontrado.")
        else:
            # Obtém nomes das colunas
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = [row[0] for row in cursor.fetchall()]
            
            print(f"Colunas: {', '.join(columns)}")
            
            for i, row in enumerate(rows, 1):
                print(f"[{i}] {dict(zip(columns, row))}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao consultar {table_name}: {e}")

def list_all_tables():
    print("\n--- TODAS AS TABELAS ---")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("Nenhuma tabela encontrada no schema public.")
        else:
            for table in tables:
                print(f"- {table[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro ao listar tabelas: {e}")

if __name__ == "__main__":
    list_all_tables()
    print_table_direct("embeddings")
    print_table_direct("chunks")
    print_table_direct("metadata")