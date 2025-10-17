import os
from supabase import create_client
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv("configs/.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tables = [
    "agent_sessions",
    "agent_conversations",
    "agent_context",
    "agent_memory_embeddings"
]

for table in tables:
    print(f"Limpando tabela: {table}")
    res = supabase.table(table).delete().gt("id", "").execute()
    print(f"Status: {res}")

print("Todas as tabelas de memória foram limpas com sucesso.")
