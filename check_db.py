"""
Script simples para testar conexão com Supabase/Postgres usando variáveis do .env
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv("configs/.env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("Testando conexão com o banco de dados...")
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    result = cur.fetchone()
    print(f"Conexão OK! Resultado: {result}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ ERRO: Falha na conexão com o banco: {e}")
    exit(1)
