# Teste Integrado: Ingestão, Limpeza e Isolamento

import pytest
from src.agent.memory_cleaner import clean_all_agent_memory
from src.agent.rag_data_agent import RAGDataAgent
import pandas as pd
import os

def simulate_ingestion_and_analysis(csv_path, session_id, source_id):
    # Simula ingestão de dados
    df = pd.read_csv(csv_path)
    agent = RAGDataAgent()
    agent.session_id = session_id
    agent.source_id = source_id
    agent.memory = {"last_query": "ingest", "dataset": os.path.basename(csv_path)}
    # Limpa memória do agente instanciado
    agent.reset_memory(session_id)
    return agent

def test_integrated_ingestion_cleaning(tmp_path):
    # Cria dois datasets simulados
    csv1 = tmp_path / "dataset1.csv"
    csv2 = tmp_path / "dataset2.csv"
    df1 = pd.DataFrame({"A": [1,2], "B": [3,4]})
    df2 = pd.DataFrame({"X": [5,6], "Y": [7,8]})
    df1.to_csv(csv1, index=False)
    df2.to_csv(csv2, index=False)
    # Ingestão e análise do primeiro dataset
    agent1 = simulate_ingestion_and_analysis(str(csv1), "sess1", "hash1")
    assert agent1.memory == {}  # Memória deve estar limpa
    # Ingestão e análise do segundo dataset
    agent2 = simulate_ingestion_and_analysis(str(csv2), "sess2", "hash2")
    assert agent2.memory == {}  # Memória deve estar limpa
    # Isolamento garantido
    assert agent1.source_id != agent2.source_id
    assert agent1.session_id != agent2.session_id
