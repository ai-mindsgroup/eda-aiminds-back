import psycopg
from src import settings

try:
    with psycopg.connect(settings.build_db_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            print('Conexão OK')
except Exception as e:
    print('Falhou:', e)
