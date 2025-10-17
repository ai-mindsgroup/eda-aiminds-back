import sys
sys.path.insert(0, ".")
import os
import pytest
from src.vectorstore.supabase_client import supabase
from src.embeddings.vector_store import VectorStore
from src.agent.data_ingestor import atomic_ingestion_and_query

def test_ingestion_isolation_creditcard():
    """
    Testa ingestão e consulta isolada para creditcard.csv
    """
    csv_path = os.path.join('data', 'processando', 'creditcard.csv')
    vector_store = VectorStore()
    results = atomic_ingestion_and_query(csv_path, supabase, vector_store)
    assert len(results) > 0, "Deve retornar embeddings para creditcard.csv"
    for r in results:
        assert r.metadata.get('source') == csv_path


def test_ingestion_isolation_cardtransdata():
    """
    Testa ingestão e consulta isolada para card_transdata.csv
    """
    csv_path = os.path.join('data', 'processando', 'card_transdata.csv')
    vector_store = VectorStore()
    results = atomic_ingestion_and_query(csv_path, supabase, vector_store)
    assert len(results) > 0, "Deve retornar embeddings para card_transdata.csv"
    for r in results:
        assert r.metadata.get('source') == csv_path


def test_switch_between_files():
    """
    Testa ingestão sequencial de dois arquivos e garante isolamento dos embeddings.
    """
    vector_store = VectorStore()
    # Ingest creditcard.csv
    csv_a = os.path.join('data', 'processando', 'creditcard.csv')
    results_a = atomic_ingestion_and_query(csv_a, supabase, vector_store)
    ingestion_id_a = results_a[0].metadata.get('ingestion_id') if results_a else None
    # Ingest card_transdata.csv
    csv_b = os.path.join('data', 'processando', 'card_transdata.csv')
    results_b = atomic_ingestion_and_query(csv_b, supabase, vector_store)
    ingestion_id_b = results_b[0].metadata.get('ingestion_id') if results_b else None
    # Consulta isolada para cada ingestion_id
    filtered_a = vector_store.search_similar([0.0]*384, similarity_threshold=0.0, limit=1000, filters={'ingestion_id': ingestion_id_a})
    filtered_b = vector_store.search_similar([0.0]*384, similarity_threshold=0.0, limit=1000, filters={'ingestion_id': ingestion_id_b})
    # Novo comportamento: após a segunda ingestão a tabela deve conter apenas registros da última ingestão
    assert len(filtered_a) == 0, "Ingestão anterior deve ter sido removida"
    assert len(filtered_b) > 0, "A última ingestão deve retornar embeddings"
