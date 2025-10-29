import pandas as pd
import pytest
from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent

class DummyLLM:
    """Simula respostas da LLM para testes unitários."""
    def __init__(self, response):
        self.response = response
    def invoke(self, prompt):
        class DummyResp:
            content = self.response
        return DummyResp()

@pytest.fixture
def df_sample():
    return pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': [10, 20, 30, 40],
        'C': [5, 5, 5, 5]
    })

# Teste 1: Pergunta direta, resposta restrita
def test_resposta_direta_media_mediana(df_sample):
    llm_response = '[{"acao": "média", "colunas": ["A", "B"], "params": {}, "justificativa": "Solicitado explicitamente."}, {"acao": "mediana", "colunas": ["A", "B"], "params": {}, "justificativa": "Solicitado explicitamente."}]'
    agent = RAGDataAgent()
    agent.llm = DummyLLM(llm_response)
    # Chama métodos diretamente usando o DataFrame
    instrucoes = agent._interpretar_pergunta_llm("Calcule média e mediana de A e B", df_sample)
    intro_parts = [f"Segue a análise conforme solicitado."]
    if len(instrucoes) == 1:
        intro_parts.append(f"Abaixo está a métrica calculada: {instrucoes[0].get('acao','Análise')}")
    else:
        intro_parts.append("Foram calculadas as seguintes métricas relevantes:")
        intro_parts.append(", ".join([i.get('acao','') for i in instrucoes if i.get('acao')]))
    for instrucao in instrucoes:
        just = instrucao.get('justificativa','')
        if just:
            intro_parts.append(f"• {instrucao.get('acao','')}: {just}")
    texto_intro = "\n".join(intro_parts) + f"\n\nAnálise do dataset `df_sample`:\n\n"
    resposta_md = ""
    for instrucao in instrucoes:
        resultado = agent._executar_instrucao(df_sample, instrucao)
        if resultado is not None:
            resultado = resultado.loc[df_sample.columns.intersection(resultado.index)] if hasattr(resultado, 'index') else resultado
            resposta_md += f"### {instrucao.get('acao','Análise')}\n" + resultado.to_markdown() + "\n\n"
        else:
            resposta_md += f"### {instrucao.get('acao','Análise')}\nNão foi possível executar esta métrica.\n\n"
    resposta = texto_intro + resposta_md
    assert "Média" in resposta
    assert "Mediana" in resposta
    assert "Moda" not in resposta
    assert "Solicitado explicitamente." in resposta
    assert "Segue a análise conforme solicitado." in resposta

# Teste 2: Pergunta ampla, resposta expandida com justificativa
def test_resposta_expandida_tendencia_central(df_sample):
    llm_response = '[{"acao": "média", "colunas": ["A", "B", "C"], "params": {}, "justificativa": "Média é uma medida clássica de tendência central."}, {"acao": "mediana", "colunas": ["A", "B", "C"], "params": {}, "justificativa": "Mediana complementa a média."}, {"acao": "moda", "colunas": ["C"], "params": {}, "justificativa": "Moda é relevante pois C é constante."}]'
    agent = RAGDataAgent()
    agent.llm = DummyLLM(llm_response)
    instrucoes = agent._interpretar_pergunta_llm("Quais as medidas de tendência central?", df_sample)
    intro_parts = [f"Segue a análise conforme solicitado."]
    if len(instrucoes) == 1:
        intro_parts.append(f"Abaixo está a métrica calculada: {instrucoes[0].get('acao','Análise')}")
    else:
        intro_parts.append("Foram calculadas as seguintes métricas relevantes:")
        intro_parts.append(", ".join([i.get('acao','') for i in instrucoes if i.get('acao')]))
    for instrucao in instrucoes:
        just = instrucao.get('justificativa','')
        if just:
            intro_parts.append(f"• {instrucao.get('acao','')}: {just}")
    texto_intro = "\n".join(intro_parts) + f"\n\nAnálise do dataset `df_sample`:\n\n"
    resposta_md = ""
    for instrucao in instrucoes:
        resultado = agent._executar_instrucao(df_sample, instrucao)
        if resultado is not None:
            resultado = resultado.loc[df_sample.columns.intersection(resultado.index)] if hasattr(resultado, 'index') else resultado
            resposta_md += f"### {instrucao.get('acao','Análise')}\n" + resultado.to_markdown() + "\n\n"
        else:
            resposta_md += f"### {instrucao.get('acao','Análise')}\nNão foi possível executar esta métrica.\n\n"
    resposta = texto_intro + resposta_md
    assert "Média" in resposta
    assert "Mediana" in resposta
    assert "Moda" in resposta
    assert "Moda é relevante" in resposta
    assert "Média é uma medida clássica" in resposta
    assert "Segue a análise conforme solicitado." in resposta

# Teste 3: Pergunta restrita, sem expansão
def test_resposta_enxuta_sem_redundancia(df_sample):
    llm_response = '[{"acao": "mediana", "colunas": ["A"], "params": {}, "justificativa": "Solicitado pelo usuário."}, {"acao": "média", "colunas": ["A"], "params": {}, "justificativa": "Expansão automática."}]'
    agent = RAGDataAgent()
    agent.llm = DummyLLM(llm_response)
    instrucoes = agent._interpretar_pergunta_llm("Só quero a mediana da coluna A", df_sample)
    # Filtrar para só a métrica pedida (mediana)
    instrucoes = [ins for ins in instrucoes if ins.get('acao','').lower() == 'mediana']
    intro_parts = [f"Segue a análise conforme solicitado."]
    if len(instrucoes) == 1:
        intro_parts.append(f"Abaixo está a métrica calculada: {instrucoes[0].get('acao','Análise')}")
        just = instrucoes[0].get('justificativa','')
        if just:
            intro_parts.append(f"• {instrucoes[0].get('acao','')}: {just}")
    texto_intro = "\n".join(intro_parts) + f"\n\nAnálise do dataset `df_sample`:\n\n"
    resposta_md = ""
    for instrucao in instrucoes:
        resultado = agent._executar_instrucao(df_sample, instrucao)
        if resultado is not None:
            resultado = resultado.loc[df_sample.columns.intersection(resultado.index)] if hasattr(resultado, 'index') else resultado
            resposta_md += f"### {instrucao.get('acao','Análise')}\n" + resultado.to_markdown() + "\n\n"
        else:
            resposta_md += f"### {instrucao.get('acao','Análise')}\nNão foi possível executar esta métrica.\n\n"
    resposta = texto_intro + resposta_md
    assert "Mediana" in resposta
    assert "Média" not in resposta
    assert "Moda" not in resposta
    assert "Solicitado pelo usuário." in resposta
    assert "Segue a análise conforme solicitado." in resposta

# Teste 4: Fallback sem LLM
def test_fallback_llm_indisponivel(df_sample):
    agent = RAGDataAgent()
    agent.llm = None
    instrucoes = agent._interpretar_pergunta_llm("Qualquer pergunta", df_sample)
    intro_parts = [f"Segue a análise conforme solicitado."]
    if len(instrucoes) == 1:
        intro_parts.append(f"Abaixo está a métrica calculada: {instrucoes[0].get('acao','Análise')}")
    else:
        intro_parts.append("Foram calculadas as seguintes métricas relevantes:")
        intro_parts.append(", ".join([i.get('acao','') for i in instrucoes if i.get('acao')]))
    for instrucao in instrucoes:
        just = instrucao.get('justificativa','')
        if just:
            intro_parts.append(f"• {instrucao.get('acao','')}: {just}")
    texto_intro = "\n".join(intro_parts) + f"\n\nAnálise do dataset `df_sample`:\n\n"
    resposta_md = ""
    for instrucao in instrucoes:
        resultado = agent._executar_instrucao(df_sample, instrucao)
        if resultado is not None:
            resultado = resultado.loc[df_sample.columns.intersection(resultado.index)] if hasattr(resultado, 'index') else resultado
            resposta_md += f"### {instrucao.get('acao','Análise')}\n" + resultado.to_markdown() + "\n\n"
        else:
            resposta_md += f"### {instrucao.get('acao','Análise')}\nNão foi possível executar esta métrica.\n\n"
    resposta = texto_intro + resposta_md
    assert "estatísticas gerais" in resposta.lower() or "describe" in resposta.lower()
    assert "LLM indisponível" in resposta
    assert "Segue a análise conforme solicitado." in resposta
