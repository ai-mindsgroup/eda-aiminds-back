import psycopg
from dotenv import load_dotenv
import os

load_dotenv('configs/.env')

conn_str = f"host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} sslmode=require"
conn = psycopg.connect(conn_str)
cur = conn.cursor()
cur.execute('SELECT chunk_text FROM embeddings LIMIT 1')
chunk = cur.fetchone()[0]
print("="*80)
print("EXEMPLO DE CHUNK_TEXT:")
print("="*80)
print(chunk[:2000])
print("\n...")
conn.close()
