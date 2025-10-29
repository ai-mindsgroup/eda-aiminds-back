"""
Teste unitário para o módulo code_executor.py
"""
import pytest
import pandas as pd
from src.analysis.code_executor import CodeExecutor

def test_execute_code_sucesso():
    df = pd.DataFrame({"idade": [10, 20, 30]})
    code = "resultado = df['idade'].sum()"
    executor = CodeExecutor()
    res = executor.execute_code(code, {"df": df})
    assert res["success"]
    assert res["result"] == 60

def test_execute_code_erro():
    code = "resultado = 1/0"  # Vai gerar ZeroDivisionError
    executor = CodeExecutor()
    res = executor.execute_code(code)
    assert not res["success"]
    assert "ZeroDivisionError" in res["traceback"]

def test_execute_code_sem_resultado():
    code = "x = 123"  # Não define 'resultado'
    executor = CodeExecutor()
    res = executor.execute_code(code)
    assert res["success"]
    assert res["result"] is None
