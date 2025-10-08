"""Verifica schema da tabela embeddings"""
import psycopg
from src.settings import build_db_dsn

conn = psycopg.connect(build_db_dsn())
cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type, udt_name 
    FROM information_schema.columns 
    WHERE table_name = 'embeddings' 
    ORDER BY ordinal_position;
""")
rows = cur.fetchall()

print('SCHEMA DA TABELA embeddings:')
print('='*60)
for col, dtype, udt in rows:
    print(f'{col:20} | {dtype:20} | {udt}')

cur.close()
conn.close()
