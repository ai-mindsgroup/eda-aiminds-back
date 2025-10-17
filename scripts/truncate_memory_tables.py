import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv("configs/.env")
DB_HOST = os.getenv("DB_HOST")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")

conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    dbname=DB_NAME,
    port=5432
)

with conn:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE agent_sessions, agent_conversations, agent_context, agent_memory_embeddings RESTART IDENTITY CASCADE;")
        print("Tabelas de memória limpas com sucesso!")

conn.close()
