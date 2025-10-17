import os
import pytest
from src.vectorstore.supabase_client import supabase
from src.embeddings.vector_store import VectorStore
from src.agent.data_ingestor import atomic_ingestion_and_query


def test_only_last_ingestion_remains():
    """Após duas ingestões sequenciais, a tabela embeddings deve conter apenas registros do último ingestion_id."""
    vector_store = VectorStore()

    csv_a = os.path.join('data', 'processando', 'creditcard.csv')
    results_a = atomic_ingestion_and_query(csv_a, supabase, vector_store)
    ingestion_id_a = results_a[0].metadata.get('ingestion_id') if results_a else None

    csv_b = os.path.join('data', 'processando', 'card_transdata.csv')
    results_b = atomic_ingestion_and_query(csv_b, supabase, vector_store)
    ingestion_id_b = results_b[0].metadata.get('ingestion_id') if results_b else None

    # Buscar todos os embeddings atualmente na tabela
    response = supabase.table('embeddings').select('id, metadata').execute()
    assert response.data is not None
    all_meta = [row.get('metadata', {}) for row in response.data]
    ingestion_ids = set(m.get('ingestion_id') for m in all_meta if m)

    # Deve existir apenas um ingestion_id e ser o ingestion_id_b
    assert len(ingestion_ids) == 1, f"Expected only one ingestion_id, found: {ingestion_ids}"
    assert ingestion_id_b in ingestion_ids
