# Teste: Intervalo de todas as variáveis
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
    return str(csv_path)

def test_intervalo_todas_colunas(csv_dataset):
    agent = RAGDataAgent()
    pergunta = 'Qual o intervalo de cada variável?'
    resposta = agent._analisar_completo_csv(csv_dataset, pergunta)
    # Deve conter todas as colunas
    assert '| A ' in resposta
    assert '| B ' in resposta
    assert '| C ' in resposta
    assert 'Mínimo' in resposta and 'Máximo' in resposta
    # Deve ser Markdown
    assert resposta.startswith('|')
