"""
🔒 SPRINT 3 - TESTES AUTOMATIZADOS: Fixtures e Configurações Globais

Este módulo fornece fixtures pytest reutilizáveis para todos os testes
da sandbox segura, incluindo:

- Fixtures de código válido/inválido
- Fixtures de DataFrames de teste
- Configurações de timeout e memória
- Mocks de dependências externas
- Parametrizações comuns

Autor: GitHub Copilot Sonnet 4.5
Data: 2025-10-17
Sprint: Sprint 3 - Testes Automatizados
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.security.sandbox import (
    execute_in_sandbox,
    ALLOWED_IMPORTS,
    BLOCKED_IMPORTS,
    DEFAULT_MEMORY_LIMIT_MB
)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES GLOBAIS
# ═══════════════════════════════════════════════════════════════════════════

# Timeout padrão para testes (mais longo que produção para não causar falsos positivos)
DEFAULT_TEST_TIMEOUT = 10

# Memory limit padrão para testes
DEFAULT_TEST_MEMORY = 200  # MB (mais generoso para testes)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES: CÓDIGO DE TESTE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def simple_valid_code():
    """Código Python simples e válido."""
    return """
resultado = 2 + 2
"""


@pytest.fixture
def complex_valid_code():
    """Código Python complexo mas válido com pandas."""
    return """
import pandas as pd
import numpy as np

# Criar DataFrame
data = {
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50],
    'C': [100, 200, 300, 400, 500]
}
df = pd.DataFrame(data)

# Operações estatísticas
mean_A = df['A'].mean()
sum_B = df['B'].sum()
max_C = df['C'].max()

# Resultado complexo
resultado = {
    'mean_A': mean_A,
    'sum_B': sum_B,
    'max_C': max_C,
    'shape': df.shape,
    'columns': list(df.columns)
}
"""


@pytest.fixture
def malicious_import_os():
    """Código malicioso tentando importar 'os' (bloqueado)."""
    return """
import os
resultado = os.listdir('/')
"""


@pytest.fixture
def malicious_import_subprocess():
    """Código malicioso tentando importar 'subprocess' (bloqueado)."""
    return """
import subprocess
resultado = subprocess.run(['ls', '-la'], capture_output=True)
"""


@pytest.fixture
def malicious_eval():
    """Código malicioso tentando usar eval() (bloqueado)."""
    return """
resultado = eval('2 + 2')
"""


@pytest.fixture
def malicious_exec():
    """Código malicioso tentando usar exec() (bloqueado)."""
    return """
exec('print("malicious")')
resultado = "executed"
"""


@pytest.fixture
def timeout_code():
    """Código que causa timeout (loop infinito)."""
    return """
# Loop infinito - deve ser interrompido por timeout
while True:
    pass
"""


@pytest.fixture
def syntax_error_code():
    """Código com erro de sintaxe."""
    return """
def foo(
    # Falta fechar parêntese
resultado = 42
"""


@pytest.fixture
def memory_intensive_code():
    """Código que consome muita memória."""
    return """
import numpy as np

# Alocar array grande (~400MB)
# 50 milhões de floats x 8 bytes = 400MB
large_array = np.random.rand(50_000_000)
resultado = f"Array shape: {large_array.shape}"
"""


@pytest.fixture
def empty_code():
    """Código vazio."""
    return ""


@pytest.fixture
def code_without_result():
    """Código válido mas sem variável 'resultado'."""
    return """
x = 10
y = 20
z = x + y
"""


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES: DATAFRAMES DE TESTE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def small_dataframe():
    """DataFrame pequeno para testes (~1KB)."""
    data = {
        'A': list(range(10)),
        'B': list(range(10, 20)),
        'C': list(range(20, 30))
    }
    return pd.DataFrame(data)


@pytest.fixture
def medium_dataframe():
    """DataFrame médio para testes (~1MB)."""
    data = {
        f'col_{i}': list(range(10000))
        for i in range(10)
    }
    return pd.DataFrame(data)


@pytest.fixture
def large_dataframe():
    """DataFrame grande para testes (~10MB)."""
    data = {
        f'col_{i}': list(range(100000))
        for i in range(10)
    }
    return pd.DataFrame(data)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES: CONFIGURAÇÕES DE EXECUÇÃO
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def default_execution_config():
    """Configuração padrão de execução."""
    return {
        'timeout_seconds': DEFAULT_TEST_TIMEOUT,
        'memory_limit_mb': DEFAULT_TEST_MEMORY,
        'allowed_imports': None,  # Usar padrão
        'return_variable': 'resultado',
        'custom_globals': None
    }


@pytest.fixture
def strict_execution_config():
    """Configuração estrita (timeout curto, memória baixa)."""
    return {
        'timeout_seconds': 2,
        'memory_limit_mb': 50,
        'allowed_imports': ['pandas', 'numpy'],
        'return_variable': 'resultado',
        'custom_globals': None
    }


@pytest.fixture
def relaxed_execution_config():
    """Configuração relaxada (timeout longo, memória alta)."""
    return {
        'timeout_seconds': 30,
        'memory_limit_mb': 500,
        'allowed_imports': None,
        'return_variable': 'resultado',
        'custom_globals': None
    }


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES: MOCKS E PATCHES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_logger():
    """Mock do logger para capturar logs."""
    with patch('src.security.sandbox.get_logger') as mock_log:
        logger_instance = Mock()
        mock_log.return_value = logger_instance
        yield logger_instance


@pytest.fixture
def mock_psutil():
    """Mock do psutil para simular diferentes cenários de memória."""
    with patch('src.security.sandbox.psutil') as mock_ps:
        # Configurar mock padrão
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 50 * 1024 * 1024  # 50MB
        mock_ps.Process.return_value = mock_process
        yield mock_ps


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES: HELPERS E UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def execute_sandbox_helper(default_execution_config):
    """
    Helper function para executar sandbox com configurações padrão.
    
    Usage:
        result = execute_sandbox_helper(code='resultado = 42')
    """
    def _execute(code: str, **kwargs) -> Dict[str, Any]:
        """
        Executa código no sandbox com configurações mescladas.
        
        Args:
            code: Código Python a executar
            **kwargs: Sobrescrever configurações padrão
            
        Returns:
            Dict com resultado da execução
        """
        config = {**default_execution_config, **kwargs}
        return execute_in_sandbox(code=code, **config)
    
    return _execute


@pytest.fixture
def assert_success():
    """Helper para validar execução bem-sucedida."""
    def _assert(result: Dict[str, Any], expected_result: Any = None):
        """
        Valida que execução foi bem-sucedida.
        
        Args:
            result: Resultado do execute_in_sandbox
            expected_result: Resultado esperado (opcional)
        """
        assert result['success'] is True, f"Execução falhou: {result.get('error')}"
        assert 'result' in result
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] > 0
        
        if expected_result is not None:
            assert result['result'] == expected_result
    
    return _assert


@pytest.fixture
def assert_failure():
    """Helper para validar falha esperada."""
    def _assert(result: Dict[str, Any], expected_error_type: str = None):
        """
        Valida que execução falhou conforme esperado.
        
        Args:
            result: Resultado do execute_in_sandbox
            expected_error_type: Tipo de erro esperado (opcional)
        """
        assert result['success'] is False, "Execução deveria ter falhado"
        assert 'error' in result
        assert 'error_type' in result
        
        if expected_error_type:
            assert result['error_type'] == expected_error_type, \
                f"Erro esperado: {expected_error_type}, obtido: {result['error_type']}"
    
    return _assert


# ═══════════════════════════════════════════════════════════════════════════
# PARAMETRIZAÇÃO: CASOS DE TESTE COMUNS
# ═══════════════════════════════════════════════════════════════════════════

# Lista de imports permitidos para testes parametrizados
VALID_IMPORTS = [
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
]

# Lista de imports bloqueados para testes parametrizados
BLOCKED_IMPORTS_LIST = [
    'os',
    'subprocess',
    'sys',
    'socket',
    'urllib',
    'requests',
    'http',
    'pickle',
    '__builtin__',
    'importlib'
]

# Casos de teste parametrizados para operações matemáticas simples
SIMPLE_MATH_CASES = [
    ('2 + 2', 4),
    ('10 * 5', 50),
    ('100 / 4', 25.0),
    ('2 ** 8', 256),
    ('15 % 4', 3)
]

# Casos de teste parametrizados para operações com strings
STRING_CASES = [
    ('"hello " + "world"', 'hello world'),
    ('"test".upper()', 'TEST'),
    ('len("python")', 6),
    ('"a,b,c".split(",")', ['a', 'b', 'c'])
]


# ═══════════════════════════════════════════════════════════════════════════
# PYTEST HOOKS E CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Configure pytest com markers customizados."""
    config.addinivalue_line(
        "markers", "slow: marca testes lentos (executados apenas com --run-slow)"
    )
    config.addinivalue_line(
        "markers", "security: marca testes de segurança"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "load: marca testes de carga/performance"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica coleção de testes baseado em markers."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Adiciona opções customizadas ao pytest."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-load",
        action="store_true",
        default=False,
        help="run load/stress tests"
    )


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES DE SESSÃO (EXECUTAM UMA VEZ)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_session_info():
    """Informações da sessão de testes."""
    import platform
    
    return {
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'architecture': platform.machine(),
        'processor': platform.processor()
    }


@pytest.fixture(scope="session", autouse=True)
def print_test_session_header(test_session_info):
    """Imprime header da sessão de testes."""
    print("\n" + "=" * 80)
    print("🔒 SPRINT 3 - TESTES AUTOMATIZADOS: SANDBOX SEGURA")
    print("=" * 80)
    print(f"Platform: {test_session_info['platform']}")
    print(f"Python: {test_session_info['python_version']}")
    print(f"Architecture: {test_session_info['architecture']}")
    print("=" * 80 + "\n")
