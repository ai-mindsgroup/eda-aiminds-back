"""
Script para testar conexão com Supabase e realizar SELECT na tabela embeddings.
"""
from src.vectorstore.supabase_client import supabase
from src.settings import LOG_LEVEL
import logging

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("test_db")

try:
    logger.info("Testando conexão com Supabase...")
    # SELECT simples na tabela embeddings
    response = supabase.table("embeddings").select("*").limit(5).execute()
    logger.info(f"Resultado SELECT: {response.data}")
    print("Conexão OK. Exemplos da tabela embeddings:")
    for row in response.data:
        print(row)
except Exception as e:
    logger.error(f"Erro ao conectar ou consultar Supabase: {e}")
    print(f"Erro: {e}")
