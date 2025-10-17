# Teste: Interpretação ampla e múltiplas métricas
import pytest
import pandas as pd
from src.agent.rag_data_agent import RAGDataAgent

@pytest.fixture
def csv_dataset(tmp_path):
    df = pd.DataFrame({
        'A': [1, 2, 3, 2],
        'B': [10, 20, 30, 20],
        'C': [-5, 0, 5, 0]
    })
    csv_path = tmp_path / 'test_dataset.csv'
    df.to_csv(csv_path, index=False)
    return str(csv_path), list(df.columns)

def test_tendencia_central_e_multiplas_metricas(csv_dataset):
    csv_path, colunas = csv_dataset
    agent = RAGDataAgent()
    pergunta = 'Quais as medidas de tendência central do dataset?'
    resposta = agent._analisar_completo_csv(csv_path, pergunta)
    # Deve conter média, mediana e moda
    assert 'Média' in resposta
    assert 'Mediana' in resposta
    assert 'Moda' in resposta
    # Deve conter todas as colunas
    for col in colunas:
        assert f'| {col} ' in resposta
    # Deve conter texto introdutório
    assert 'Análise completa do dataset' in resposta
    # Teste para pergunta ampla
    resposta_ampla = agent._analisar_completo_csv(csv_path, 'Me dê estatísticas gerais')
    assert 'Estatísticas gerais' in resposta_ampla or 'count' in resposta_ampla
