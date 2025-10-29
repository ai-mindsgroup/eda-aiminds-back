import pytest
import pandas as pd
import sys
import os

# Ajusta caminho para importar o pacote src durante os testes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent


def make_df_temporal(cols, values):
    return pd.DataFrame({col: val for col, val in zip(cols, values)})


def test_detect_no_temporal():
    df = make_df_temporal(['A', 'B'], [[1, 2, 3], [4, 5, 6]])
    df.to_csv('temp_none.csv', index=False)
    agent = RAGDataAgent()
    result = agent._analisar_completo_csv('temp_none.csv', 'média', override_temporal_col=None)
    assert isinstance(result, str)
    assert 'Resumo' in result or 'Média' in result or 'estatístico' in result


def test_detect_single_temporal():
    df = make_df_temporal(['data'], [pd.date_range('2020-01-01', periods=3)])
    df.to_csv('temp_single.csv', index=False)
    agent = RAGDataAgent()
    result = agent._analisar_completo_csv('temp_single.csv', 'análise temporal')
    assert isinstance(result, str)
    assert 'temporal' in result.lower() or 'dimensão temporal' in result


def test_detect_multiple_temporal():
    df = make_df_temporal(
        ['data', 'timestamp'],
        [pd.date_range('2020-01-01', periods=3), pd.date_range('2021-01-01', periods=3)],
    )
    df.to_csv('temp_multi.csv', index=False)
    agent = RAGDataAgent()
    result = agent._analisar_completo_csv('temp_multi.csv', 'análise temporal')
    assert isinstance(result, str)
    # espera ao menos duas menções à dimensão temporal
    assert result.lower().count('temporal') >= 2


def test_override_manual():
    df = make_df_temporal(
        ['A', 'B', 'tempo'],
        [[1, 2, 3], [4, 5, 6], pd.date_range('2022-01-01', periods=3)],
    )
    df.to_csv('temp_override.csv', index=False)
    agent = RAGDataAgent()
    result = agent._analisar_completo_csv('temp_override.csv', 'análise temporal', override_temporal_col='tempo')
    assert isinstance(result, str)
    assert 'tempo' in result.lower() or 'temporal' in result.lower()


def test_invalid_temporal():
    df = make_df_temporal(['bad_date'], [['foo', 'bar', 'baz']])
    df.to_csv('temp_invalid.csv', index=False)
    agent = RAGDataAgent()
    result = agent._analisar_completo_csv('temp_invalid.csv', 'análise temporal')
    # Deve retornar análise estatística geral (sem colunas temporais detectadas)
    assert isinstance(result, str)
    assert 'Resumo' in result or 'Média' in result or 'estatísticas' in result
