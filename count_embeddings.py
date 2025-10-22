"""
Script para contar registros na tabela embeddings do Supabase.
"""
from src.vectorstore.supabase_client import supabase
from src.settings import LOG_LEVEL
import logging

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("count_embeddings")

try:
    logger.info("Contando registros na tabela embeddings...")
    response = supabase.table("embeddings").select("id", count="exact").execute()
    total = response.count
    print(f"Total de registros na tabela embeddings: {total}")
except Exception as e:
    logger.error(f"Erro ao contar registros: {e}")
    print(f"Erro: {e}")
