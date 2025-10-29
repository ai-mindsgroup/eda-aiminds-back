"""
Teste unitário para o módulo code_generator.py
"""
import pytest
from src.analysis.code_generator import CodeGenerator

def test_generate_code_frequencia_coluna():
    generator = CodeGenerator()
    intent = {"tipo": "frequencia_coluna", "coluna": "idade"}
    context = {"nome_arquivo": "dados.csv"}
    codigo = generator.generate_code(intent, context)
    assert "value_counts" in codigo
    assert "idade" in codigo
    assert "dados.csv" in codigo

def test_generate_code_histograma_coluna():
    generator = CodeGenerator()
    intent = {"tipo": "histograma_coluna", "coluna": "salario"}
    context = {"nome_arquivo": "dados.csv"}
    codigo = generator.generate_code(intent, context)
    assert "plt.show()" in codigo
    assert "salario" in codigo
    assert "dados.csv" in codigo

def test_generate_code_tipo_nao_suportado():
    generator = CodeGenerator()
    intent = {"tipo": "analise_inexistente", "coluna": "x"}
    context = {"nome_arquivo": "dados.csv"}
    codigo = generator.generate_code(intent, context)
    assert "não suportado" in codigo
