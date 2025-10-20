"""Verifica tabelas existentes no novo projeto Supabase"""
import psycopg
from dotenv import load_dotenv
import os

load_dotenv("configs/.env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print(f"\nConectando ao novo projeto: {DB_USER.split('.')[1] if '.' in DB_USER else DB_USER}")
print(f"Host: {DB_HOST}\n")

try:
    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    
    print("=" * 60)
    print("TABELAS NO SCHEMA PUBLIC")
    print("=" * 60)
    
    if tables:
        for i, (table,) in enumerate(tables, 1):
            print(f"{i}. {table}")
        print(f"\nTotal: {len(tables)} tabela(s) encontrada(s)")
    else:
        print("✅ Nenhuma tabela encontrada - banco limpo/vazio")
    
    print("=" * 60)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    exit(1)
