# Teste: Humanização, ordenação e análise adaptativa
import pytest
import pandas as pd
from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent

@pytest.fixture
def csv_dataset(tmp_path):
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [10, 20, 30],
        'C': [-5, 0, 5]
    })
    csv_path = tmp_path / 'test_dataset.csv'
    df.to_csv(csv_path, index=False)
    return str(csv_path), list(df.columns)

def test_humanizacao_e_ordenacao(csv_dataset):
    csv_path, colunas = csv_dataset
    agent = RAGDataAgent()
    pergunta = 'Qual o intervalo de cada variável?'
    resposta = agent._analisar_completo_csv(csv_path, pergunta)
    # Deve conter texto introdutório
    assert 'Análise completa do dataset' in resposta
    # Deve conter todas as colunas na ordem original
    for col in colunas:
        assert f'| {col} ' in resposta
    # Deve conter cabeçalho humanizado
    assert 'Mínimo' in resposta and 'Máximo' in resposta
    # Teste para média
    resposta_media = agent._analisar_completo_csv(csv_path, 'Qual a média das variáveis?')
    assert 'Média' in resposta_media
    # Teste para desvio padrão
    resposta_desvio = agent._analisar_completo_csv(csv_path, 'Desvio padrão das variáveis?')
    assert 'Desvio padrão' in resposta_desvio
    # Teste para estatísticas gerais
    resposta_geral = agent._analisar_completo_csv(csv_path, 'Me dê um resumo estatístico')
    assert 'Resumo estatístico' in resposta_geral
