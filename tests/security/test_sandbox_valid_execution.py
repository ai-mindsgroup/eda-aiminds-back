"""
🔒 SPRINT 3 - TESTES AUTOMATIZADOS: Execução Válida de Código

Testes para validar que o sandbox executa corretamente código Python válido,
desde operações simples até manipulações complexas com pandas/numpy.

Cobertura:
- Operações matemáticas básicas
- Operações com strings
- Operações com listas/dicionários
- Manipulação de DataFrames com pandas
- Operações estatísticas com numpy
- Código multi-linha complexo
- Imports permitidos da whitelist

Autor: GitHub Copilot Sonnet 4.5
Data: 2025-10-17
Sprint: Sprint 3 - Testes Automatizados
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

# Fixtures importadas automaticamente do conftest.py


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: OPERAÇÕES SIMPLES
# ═══════════════════════════════════════════════════════════════════════════

class TestSimpleOperations:
    """Testes de operações simples e básicas."""
    
    def test_simple_addition(self, execute_sandbox_helper, assert_success):
        """✅ Teste 1: Operação aritmética simples (adição)."""
        code = "resultado = 2 + 2"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=4)
    
    def test_simple_multiplication(self, execute_sandbox_helper, assert_success):
        """✅ Teste 2: Operação aritmética simples (multiplicação)."""
        code = "resultado = 10 * 5"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=50)
    
    def test_simple_division(self, execute_sandbox_helper, assert_success):
        """✅ Teste 3: Operação aritmética simples (divisão)."""
        code = "resultado = 100 / 4"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=25.0)
    
    def test_simple_power(self, execute_sandbox_helper, assert_success):
        """✅ Teste 4: Operação aritmética simples (potência)."""
        code = "resultado = 2 ** 8"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=256)
    
    def test_simple_modulo(self, execute_sandbox_helper, assert_success):
        """✅ Teste 5: Operação aritmética simples (módulo)."""
        code = "resultado = 15 % 4"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=3)
    
    @pytest.mark.parametrize("expression,expected", [
        ("2 + 2", 4),
        ("10 * 5", 50),
        ("100 / 4", 25.0),
        ("2 ** 8", 256),
        ("15 % 4", 3),
        ("abs(-42)", 42),
        ("min(1, 2, 3)", 1),
        ("max(10, 20, 30)", 30),
        ("len([1, 2, 3, 4, 5])", 5)
    ])
    def test_parametrized_math_operations(self, execute_sandbox_helper, assert_success, expression, expected):
        """✅ Teste 6: Operações matemáticas parametrizadas."""
        code = f"resultado = {expression}"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=expected)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: OPERAÇÕES COM STRINGS
# ═══════════════════════════════════════════════════════════════════════════

class TestStringOperations:
    """Testes de operações com strings."""
    
    def test_string_concatenation(self, execute_sandbox_helper, assert_success):
        """✅ Teste 7: Concatenação de strings."""
        code = 'resultado = "hello " + "world"'
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result="hello world")
    
    def test_string_upper(self, execute_sandbox_helper, assert_success):
        """✅ Teste 8: String upper()."""
        code = 'resultado = "test".upper()'
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result="TEST")
    
    def test_string_length(self, execute_sandbox_helper, assert_success):
        """✅ Teste 9: Comprimento de string."""
        code = 'resultado = len("python")'
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=6)
    
    def test_string_split(self, execute_sandbox_helper, assert_success):
        """✅ Teste 10: String split()."""
        code = 'resultado = "a,b,c".split(",")'
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=['a', 'b', 'c'])
    
    def test_string_formatting(self, execute_sandbox_helper, assert_success):
        """✅ Teste 11: String formatting (f-strings)."""
        code = '''
name = "Python"
version = 3.12
resultado = f"{name} {version}"
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result="Python 3.12")


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: ESTRUTURAS DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

class TestDataStructures:
    """Testes com listas, dicionários, tuplas e sets."""
    
    def test_list_comprehension(self, execute_sandbox_helper, assert_success):
        """✅ Teste 12: List comprehension."""
        code = "resultado = [x * 2 for x in range(5)]"
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=[0, 2, 4, 6, 8])
    
    def test_dictionary_creation(self, execute_sandbox_helper, assert_success):
        """✅ Teste 13: Criação de dicionário."""
        code = '''
resultado = {
    'name': 'Alice',
    'age': 30,
    'city': 'NYC'
}
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result={'name': 'Alice', 'age': 30, 'city': 'NYC'})
    
    def test_list_operations(self, execute_sandbox_helper, assert_success):
        """✅ Teste 14: Operações com listas."""
        code = '''
lista = [1, 2, 3, 4, 5]
lista.append(6)
lista.extend([7, 8])
resultado = lista
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=[1, 2, 3, 4, 5, 6, 7, 8])
    
    def test_tuple_unpacking(self, execute_sandbox_helper, assert_success):
        """✅ Teste 15: Tuple unpacking."""
        code = '''
a, b, c = (10, 20, 30)
resultado = a + b + c
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=60)
    
    def test_set_operations(self, execute_sandbox_helper, assert_success):
        """✅ Teste 16: Operações com sets."""
        code = '''
set1 = {1, 2, 3, 4}
set2 = {3, 4, 5, 6}
resultado = sorted(list(set1.intersection(set2)))
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=[3, 4])


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: PANDAS (OPERAÇÕES COMPLEXAS)
# ═══════════════════════════════════════════════════════════════════════════

class TestPandasOperations:
    """Testes de operações complexas com pandas."""
    
    def test_pandas_dataframe_creation(self, execute_sandbox_helper, assert_success):
        """✅ Teste 17: Criação de DataFrame pandas."""
        code = '''
import pandas as pd

data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
resultado = df.shape
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=(3, 2))
    
    def test_pandas_dataframe_mean(self, execute_sandbox_helper, assert_success):
        """✅ Teste 18: Cálculo de média com pandas."""
        code = '''
import pandas as pd

df = pd.DataFrame({'A': [1, 2, 3, 4, 5]})
resultado = float(df['A'].mean())
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=3.0)
    
    def test_pandas_dataframe_filtering(self, execute_sandbox_helper, assert_success):
        """✅ Teste 19: Filtragem de DataFrame."""
        code = '''
import pandas as pd

df = pd.DataFrame({'A': [1, 2, 3, 4, 5], 'B': [10, 20, 30, 40, 50]})
filtered = df[df['A'] > 3]
resultado = len(filtered)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=2)
    
    def test_pandas_groupby(self, execute_sandbox_helper, assert_success):
        """✅ Teste 20: GroupBy com pandas."""
        code = '''
import pandas as pd

df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B', 'A'],
    'value': [10, 20, 30, 40, 50]
})
grouped = df.groupby('category')['value'].sum()
resultado = dict(grouped)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result={'A': 90, 'B': 60})
    
    def test_pandas_merge(self, execute_sandbox_helper, assert_success):
        """✅ Teste 21: Merge de DataFrames."""
        code = '''
import pandas as pd

df1 = pd.DataFrame({'key': ['A', 'B', 'C'], 'value1': [1, 2, 3]})
df2 = pd.DataFrame({'key': ['A', 'B', 'D'], 'value2': [10, 20, 30]})
merged = pd.merge(df1, df2, on='key', how='inner')
resultado = len(merged)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=2)
    
    def test_pandas_with_custom_dataframe(self, execute_sandbox_helper, assert_success, small_dataframe):
        """✅ Teste 22: Uso de DataFrame customizado (via custom_globals)."""
        code = '''
# df é injetado via custom_globals
resultado = df['A'].sum()
'''
        result = execute_sandbox_helper(
            code,
            custom_globals={'df': small_dataframe}
        )
        assert_success(result, expected_result=45)  # 0+1+2+...+9 = 45


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: NUMPY (OPERAÇÕES ESTATÍSTICAS)
# ═══════════════════════════════════════════════════════════════════════════

class TestNumpyOperations:
    """Testes de operações estatísticas com numpy."""
    
    def test_numpy_array_creation(self, execute_sandbox_helper, assert_success):
        """✅ Teste 23: Criação de array numpy."""
        code = '''
import numpy as np

arr = np.array([1, 2, 3, 4, 5])
resultado = arr.shape[0]
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=5)
    
    def test_numpy_mean(self, execute_sandbox_helper, assert_success):
        """✅ Teste 24: Cálculo de média com numpy."""
        code = '''
import numpy as np

arr = np.array([10, 20, 30, 40, 50])
resultado = float(np.mean(arr))
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=30.0)
    
    def test_numpy_std(self, execute_sandbox_helper, assert_success):
        """✅ Teste 25: Desvio padrão com numpy."""
        code = '''
import numpy as np

arr = np.array([2, 4, 6, 8, 10])
resultado = round(float(np.std(arr)), 2)
'''
        result = execute_sandbox_helper(code)
        # std([2, 4, 6, 8, 10]) ≈ 2.83
        assert result['success'] is True
        assert 2.8 <= result['result'] <= 2.9
    
    def test_numpy_matrix_operations(self, execute_sandbox_helper, assert_success):
        """✅ Teste 26: Operações com matrizes numpy."""
        code = '''
import numpy as np

matrix1 = np.array([[1, 2], [3, 4]])
matrix2 = np.array([[5, 6], [7, 8]])
resultado = (matrix1 + matrix2).tolist()
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=[[6, 8], [10, 12]])
    
    def test_numpy_random(self, execute_sandbox_helper, assert_success):
        """✅ Teste 27: Geração de números aleatórios com numpy."""
        code = '''
import numpy as np

np.random.seed(42)  # Seed para reproducibilidade
arr = np.random.rand(5)
resultado = len(arr)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=5)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: CÓDIGO MULTI-LINHA COMPLEXO
# ═══════════════════════════════════════════════════════════════════════════

class TestComplexCode:
    """Testes com código multi-linha e complexo."""
    
    def test_complex_statistical_analysis(self, execute_sandbox_helper, assert_success):
        """✅ Teste 28: Análise estatística complexa."""
        code = '''
import pandas as pd
import numpy as np

# Criar dados
data = {
    'values': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
}
df = pd.DataFrame(data)

# Análise estatística completa
stats = {
    'mean': float(df['values'].mean()),
    'median': float(df['values'].median()),
    'std': float(df['values'].std()),
    'min': int(df['values'].min()),
    'max': int(df['values'].max()),
    'count': int(len(df))
}

resultado = stats
'''
        result = execute_sandbox_helper(code)
        assert result['success'] is True
        assert result['result']['mean'] == 55.0
        assert result['result']['median'] == 55.0
        assert result['result']['min'] == 10
        assert result['result']['max'] == 100
        assert result['result']['count'] == 10
    
    def test_complex_data_transformation(self, execute_sandbox_helper, assert_success):
        """✅ Teste 29: Transformação complexa de dados."""
        code = '''
import pandas as pd

# Criar DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, 30, 35, 40],
    'salary': [50000, 60000, 70000, 80000]
})

# Transformações
df['age_group'] = df['age'].apply(lambda x: 'young' if x < 30 else 'senior')
df['salary_k'] = df['salary'] / 1000

# Estatísticas por grupo
stats_by_group = df.groupby('age_group').agg({
    'salary': 'mean',
    'age': 'mean'
}).to_dict()

resultado = {
    'total_rows': len(df),
    'avg_salary': float(df['salary'].mean()),
    'groups': stats_by_group
}
'''
        result = execute_sandbox_helper(code)
        assert result['success'] is True
        assert result['result']['total_rows'] == 4
        assert result['result']['avg_salary'] == 65000.0
    
    def test_complex_multi_step_computation(self, execute_sandbox_helper, assert_success):
        """✅ Teste 30: Computação multi-etapas."""
        code = '''
import pandas as pd
import numpy as np

# Etapa 1: Gerar dados sintéticos
np.random.seed(42)
data = {
    'feature1': np.random.randn(100),
    'feature2': np.random.randn(100)
}
df = pd.DataFrame(data)

# Etapa 2: Normalização Z-score
df['feature1_norm'] = (df['feature1'] - df['feature1'].mean()) / df['feature1'].std()
df['feature2_norm'] = (df['feature2'] - df['feature2'].mean()) / df['feature2'].std()

# Etapa 3: Computar correlação
correlation = df[['feature1_norm', 'feature2_norm']].corr().iloc[0, 1]

# Etapa 4: Resultado final
resultado = {
    'rows': len(df),
    'features': list(df.columns),
    'correlation': round(float(correlation), 4),
    'mean_feature1_norm': round(float(df['feature1_norm'].mean()), 10)  # Deve ser ~0
}
'''
        result = execute_sandbox_helper(code)
        assert result['success'] is True
        assert result['result']['rows'] == 100
        assert len(result['result']['features']) == 4
        # Média normalizada deve ser muito próxima de 0
        assert abs(result['result']['mean_feature1_norm']) < 1e-10


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: IMPORTS PERMITIDOS (WHITELIST)
# ═══════════════════════════════════════════════════════════════════════════

class TestAllowedImports:
    """Testes validando que todos imports da whitelist funcionam."""
    
    @pytest.mark.parametrize("module_name", [
        'pandas',
        'numpy',
        'math',
        'statistics',
        'datetime',
        'time',
        'json',
        'collections',
        'itertools',
        'functools',
        're'
    ])
    def test_allowed_import(self, execute_sandbox_helper, assert_success, module_name):
        """✅ Teste 31: Import permitido deve funcionar."""
        code = f'''
import {module_name}
resultado = "{module_name} importado com sucesso"
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=f"{module_name} importado com sucesso")
    
    def test_math_module_usage(self, execute_sandbox_helper, assert_success):
        """✅ Teste 32: Uso do módulo math."""
        code = '''
import math

resultado = {
    'pi': round(math.pi, 2),
    'sqrt_16': math.sqrt(16),
    'ceil_4_3': math.ceil(4.3)
}
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result={'pi': 3.14, 'sqrt_16': 4.0, 'ceil_4_3': 5})
    
    def test_datetime_module_usage(self, execute_sandbox_helper, assert_success):
        """✅ Teste 33: Uso do módulo datetime."""
        code = '''
import datetime

now = datetime.datetime(2025, 10, 17, 12, 0, 0)
resultado = now.strftime("%Y-%m-%d")
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result="2025-10-17")
    
    def test_json_module_usage(self, execute_sandbox_helper, assert_success):
        """✅ Teste 34: Uso do módulo json."""
        code = '''
import json

data = {'name': 'test', 'value': 42}
json_str = json.dumps(data)
parsed = json.loads(json_str)
resultado = parsed
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result={'name': 'test', 'value': 42})


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: FUNÇÕES E CLASSES
# ═══════════════════════════════════════════════════════════════════════════

class TestFunctionsAndClasses:
    """Testes com definição de funções e classes."""
    
    def test_function_definition(self, execute_sandbox_helper, assert_success):
        """✅ Teste 35: Definição e uso de função."""
        code = '''
def soma(a, b):
    return a + b

resultado = soma(10, 20)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=30)
    
    def test_lambda_function(self, execute_sandbox_helper, assert_success):
        """✅ Teste 36: Uso de função lambda."""
        code = '''
square = lambda x: x ** 2
resultado = square(5)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=25)
    
    def test_class_definition(self, execute_sandbox_helper, assert_success):
        """✅ Teste 37: Definição e uso de classe."""
        code = '''
class Calculator:
    def __init__(self, value):
        self.value = value
    
    def add(self, x):
        return self.value + x

calc = Calculator(10)
resultado = calc.add(5)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=15)
    
    def test_recursive_function(self, execute_sandbox_helper, assert_success):
        """✅ Teste 38: Função recursiva (fatorial)."""
        code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

resultado = factorial(5)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=120)


# ═══════════════════════════════════════════════════════════════════════════
# SUMÁRIO DOS TESTES
# ═══════════════════════════════════════════════════════════════════════════

"""
TOTAL DE TESTES NESTE MÓDULO: 38 testes

Distribuição:
- Operações Simples: 6 testes
- Operações com Strings: 5 testes
- Estruturas de Dados: 5 testes
- Pandas (Complexo): 6 testes
- Numpy (Estatístico): 5 testes
- Código Complexo: 3 testes
- Imports Permitidos: 4 testes
- Funções e Classes: 4 testes

Cobertura esperada: ~40% do sandbox.py (funções de execução válida)
"""
