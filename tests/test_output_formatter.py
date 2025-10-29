"""
Teste unitário para o módulo output_formatter.py
"""
import pytest
import pandas as pd
from src.analysis.output_formatter import OutputFormatter

def test_format_output_markdown():
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    formatter = OutputFormatter()
    md = formatter.format_output(df, output_type='markdown')
    # Aceita qualquer tabela markdown válida contendo os dados esperados
    assert "|   A |   B |" in md
    assert "|  0 |   1 |   3 |" in md or "|  0 | 1 | 3 |" in md

def test_format_output_text():
    s = pd.Series([10, 20, 30], name="valores")
    formatter = OutputFormatter()
    txt = formatter.format_output(s, output_type='text')
    assert "valores" in txt
    assert "10" in txt

def test_format_output_plot():
    s = pd.Series([1, 2, 3])
    formatter = OutputFormatter()
    img_bytes = formatter.format_output(s, output_type='plot')
    assert isinstance(img_bytes, bytes)
    assert img_bytes[:8] == b'\x89PNG\r\n\x1a\n'  # PNG signature
