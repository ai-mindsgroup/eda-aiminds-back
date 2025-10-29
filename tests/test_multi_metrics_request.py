import json
import pandas as pd
from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent


class DummyLLM:
    def __init__(self, response_content):
        self.response = response_content

    def invoke(self, prompt):
        class Resp:
            def __init__(self, content):
                self.content = content
        return Resp(self.response)


def test_agent_includes_variance_and_std():
    # DataFrame de teste simples
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [2, 2, 2, 2, 2]
    })

    # Simular LLM que retorna apenas uma instrução (desvio padrão)
    llm_response = json.dumps([
        {'acao': 'desvio padrão', 'colunas': ['A','B'], 'params': {}, 'justificativa': 'Solicitado.'}
    ])

    agent = RAGDataAgent()
    agent.llm = DummyLLM(llm_response)

    # Chamar o interpretador - ele deve adicionar 'variância' via pós-processamento
    instrucoes = agent._interpretar_pergunta_llm("Qual a variabilidade dos dados (desvio padrão, variância)?", df)

    acoes = [i['acao'].lower() for i in instrucoes if isinstance(i, dict)]
    assert 'desvio padrão' in acoes or 'desvio padrao' in acoes
    assert 'variância' in acoes or 'variancia' in acoes or 'variance' in acoes

    # Executar instruções e verificar resultados
    resultados = {i['acao']: agent._executar_instrucao(df, i) for i in instrucoes}

    assert 'Desvio padrão' in ''.join(resultados.get('desvio padrão').columns)
    assert 'Variância' in ''.join(resultados.get('variância').columns) or resultados.get('variancia') is not None
