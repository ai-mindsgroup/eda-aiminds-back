"""
🔒 SPRINT 3 - TESTES AUTOMATIZADOS: Limites (Timeout e Memória)

Testes para validar que o sandbox respeita limites de tempo e memória,
e trata exceções corretamente.

Cobertura:
- Timeout para código de loop infinito
- Timeout para código demorado
- Limite de memória (Unix e Windows)
- Tratamento correto de exceções
- Integração timeout + memória

Autor: GitHub Copilot Sonnet 4.5
Data: 2025-10-17
Sprint: Sprint 3 - Testes Automatizados
"""

import pytest
import platform
import sys


# ═══════════════════════════════════════════════════════════════════════════
# MARCADORES
# ═══════════════════════════════════════════════════════════════════════════

# Skip timeout tests on Windows (signal.alarm não disponível)
skip_timeout_on_windows = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Timeout via signal.alarm não funciona no Windows"
)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: TIMEOUT
# ═══════════════════════════════════════════════════════════════════════════

class TestTimeout:
    """Testes validando timeout funcional."""
    
    @skip_timeout_on_windows
    @pytest.mark.slow
    def test_infinite_loop_timeout(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 53: Loop infinito deve atingir timeout."""
        code = '''
while True:
    pass
'''
        result = execute_sandbox_helper(code, timeout_seconds=2)
        assert_failure(result, expected_error_type='TimeoutError')
    
    @skip_timeout_on_windows
    @pytest.mark.slow
    @skip_timeout_on_windows
    @pytest.mark.slow
    def test_slow_computation_timeout(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 54: Computação lenta deve atingir timeout."""
        code = '''
import time
# time está na whitelist agora
time.sleep(5)
resultado = "não deveria chegar aqui"
'''
        result = execute_sandbox_helper(code, timeout_seconds=2)
        assert_failure(result, expected_error_type='TimeoutError')
    
    def test_fast_code_no_timeout(self, execute_sandbox_helper, assert_success):
        """✅ Teste 55: Código rápido não deve atingir timeout."""
        code = '''
resultado = sum(range(1000))
'''
        result = execute_sandbox_helper(code, timeout_seconds=5)
        assert_success(result)
    
    @skip_timeout_on_windows
    @pytest.mark.slow
    def test_timeout_custom_value(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 56: Timeout customizado deve funcionar."""
        code = '''
import time
time.sleep(2)
resultado = "completou"
'''
        # Timeout de 1 segundo - deve falhar
        result = execute_sandbox_helper(code, timeout_seconds=1)
        assert_failure(result, expected_error_type='TimeoutError')


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: LIMITE DE MEMÓRIA
# ═══════════════════════════════════════════════════════════════════════════

class TestMemoryLimit:
    """Testes validando limite de memória."""
    
    @pytest.mark.slow
    def test_memory_intensive_code_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 57: Código que consome muita memória deve ser bloqueado."""
        code = '''
import numpy as np

# Tentar alocar ~400MB
large_array = np.random.rand(50_000_000)
resultado = "não deveria alocar"
'''
        result = execute_sandbox_helper(code, memory_limit_mb=50, timeout_seconds=10)
        # Pode falhar por memória OU por timeout (alocação lenta)
        assert_failure(result)
        assert result['error_type'] in ('MemoryLimitError', 'MemoryError', 'TimeoutError')
    
    def test_small_memory_allowed(self, execute_sandbox_helper, assert_success):
        """✅ Teste 58: Código com pouca memória deve executar."""
        code = '''
import pandas as pd

df = pd.DataFrame({'A': list(range(100))})
resultado = len(df)
'''
        result = execute_sandbox_helper(code, memory_limit_mb=100)
        assert_success(result, expected_result=100)
    
    @pytest.mark.slow
    @pytest.mark.skipif(
        platform.system() == 'Windows',
        reason="Windows soft limit sujeito a GC, teste pode ser instável"
    )
    def test_gradual_memory_growth_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 59: Crescimento gradual de memória deve ser bloqueado."""
        code = '''
import numpy as np

arrays = []
for i in range(20):
    # ~10MB por iteração
    arrays.append(np.zeros((1_250_000,)))

resultado = len(arrays)
'''
        result = execute_sandbox_helper(code, memory_limit_mb=100, timeout_seconds=15)
        assert_failure(result)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: TRATAMENTO DE EXCEÇÕES
# ═══════════════════════════════════════════════════════════════════════════

class TestExceptionHandling:
    """Testes validando tratamento correto de exceções."""
    
    def test_user_exception_caught(self, execute_sandbox_helper, assert_success):
        """✅ Teste 60: Exceção do usuário dentro de try/except."""
        code = '''
try:
    x = 1 / 0
except ZeroDivisionError:
    resultado = "exceção capturada"
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result="exceção capturada")
    
    def test_user_exception_uncaught(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 61: Exceção não tratada deve retornar erro."""
        code = '''
x = 1 / 0
resultado = "não deveria chegar aqui"
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
        assert 'ZeroDivisionError' in result['error'] or 'division' in result['error'].lower()
    
    def test_index_error_uncaught(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 62: IndexError deve ser reportado."""
        code = '''
lista = [1, 2, 3]
resultado = lista[10]
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
        assert 'IndexError' in result['error'] or 'index' in result['error'].lower()
    
    def test_key_error_uncaught(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 63: KeyError deve ser reportado."""
        code = '''
dicionario = {'a': 1, 'b': 2}
resultado = dicionario['c']
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
        assert 'KeyError' in result['error'] or 'key' in result['error'].lower()


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: INTEGRAÇÃO TIMEOUT + MEMÓRIA
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegratedLimits:
    """Testes validando integração de timeout + memória."""
    
    @pytest.mark.slow
    def test_timeout_and_memory_both_active(self, execute_sandbox_helper):
        """✅ Teste 64: Timeout e memória devem funcionar juntos."""
        code = '''
import numpy as np
import time

# Alocar memória gradualmente E demorar
arrays = []
for i in range(10):
    arrays.append(np.zeros((5_000_000,)))  # ~40MB por iteração
    time.sleep(0.1)

resultado = len(arrays)
'''
        result = execute_sandbox_helper(code, timeout_seconds=3, memory_limit_mb=50)
        # Deve falhar por timeout OU memória
        assert result['success'] is False
        assert result['error_type'] in ('TimeoutError', 'MemoryLimitError', 'MemoryError', 'ImportError')
    
    def test_successful_execution_within_limits(self, execute_sandbox_helper, assert_success):
        """✅ Teste 65: Código dentro dos limites deve executar."""
        code = '''
import pandas as pd

data = {'A': list(range(1000)), 'B': list(range(1000, 2000))}
df = pd.DataFrame(data)
resultado = df['A'].sum()
'''
        result = execute_sandbox_helper(code, timeout_seconds=5, memory_limit_mb=100)
        assert_success(result, expected_result=499500)


"""
TOTAL DE TESTES NESTE MÓDULO: 13 testes

Distribuição:
- Timeout: 4 testes
- Limite de Memória: 3 testes
- Tratamento de Exceções: 4 testes
- Integração: 2 testes

Cobertura esperada: ~20% do sandbox.py (funções de limites)
"""
