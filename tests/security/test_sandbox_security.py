"""
🔒 SPRINT 3 - TESTES AUTOMATIZADOS: Segurança (Blacklist/Whitelist)

Testes para validar que o sandbox bloqueia corretamente imports e funções
perigosas, e permite imports da whitelist.

Cobertura:
- Bloqueio de imports maliciosos (os, subprocess, sys, socket, etc)
- Bloqueio de funções perigosas (eval, exec, compile, open, etc)
- Permissão de imports whitelist
- Validação de mensagens de erro apropriadas

Autor: GitHub Copilot Sonnet 4.5
Data: 2025-10-17
Sprint: Sprint 3 - Testes Automatizados
"""

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: BLOQUEIO DE IMPORTS MALICIOSOS
# ═══════════════════════════════════════════════════════════════════════════

class TestBlockedImports:
    """Testes validando bloqueio de imports maliciosos."""
    
    @pytest.mark.security
    @pytest.mark.parametrize("blocked_module", [
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
    ])
    def test_blocked_import_should_fail(self, execute_sandbox_helper, assert_failure, blocked_module):
        """✅ Teste 39: Import bloqueado deve falhar."""
        code = f'''
import {blocked_module}
resultado = "não deveria chegar aqui"
'''
        result = execute_sandbox_helper(code)
        assert_failure(result, expected_error_type='ImportError')
        assert blocked_module.lower() in result['error'].lower() or 'import' in result['error'].lower()
    
    @pytest.mark.security
    def test_os_listdir_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 40: os.listdir() deve ser bloqueado."""
        code = '''
import os
resultado = os.listdir('/')
'''
        result = execute_sandbox_helper(code)
        assert_failure(result, expected_error_type='ImportError')
    
    @pytest.mark.security
    def test_subprocess_run_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 41: subprocess.run() deve ser bloqueado."""
        code = '''
import subprocess
resultado = subprocess.run(['ls'], capture_output=True)
'''
        result = execute_sandbox_helper(code)
        assert_failure(result, expected_error_type='ImportError')
    
    @pytest.mark.security
    def test_socket_connect_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 42: socket.connect() deve ser bloqueado."""
        code = '''
import socket
s = socket.socket()
resultado = s.connect(('google.com', 80))
'''
        result = execute_sandbox_helper(code)
        assert_failure(result, expected_error_type='ImportError')


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: BLOQUEIO DE FUNÇÕES PERIGOSAS
# ═══════════════════════════════════════════════════════════════════════════

class TestBlockedFunctions:
    """Testes validando bloqueio de funções perigosas."""
    
    @pytest.mark.security
    def test_eval_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 43: eval() deve ser bloqueada."""
        code = '''
resultado = eval('2 + 2')
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
        # eval pode resultar em NameError (não definida) ou RestrictedPython error
    
    @pytest.mark.security
    def test_exec_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 44: exec() deve ser bloqueada."""
        code = '''
exec('print("test")')
resultado = "não deveria executar"
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
    
    @pytest.mark.security
    def test_compile_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 45: compile() deve ser bloqueada."""
        code = '''
code_obj = compile('2 + 2', '<string>', 'eval')
resultado = eval(code_obj)
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
    
    @pytest.mark.security
    def test_open_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 46: open() deve ser bloqueada."""
        code = '''
with open('/etc/passwd', 'r') as f:
    resultado = f.read()
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
    
    @pytest.mark.security
    def test_globals_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 47: globals() deve ser bloqueada."""
        code = '''
g = globals()
resultado = g.keys()
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: WHITELIST FUNCIONANDO CORRETAMENTE
# ═══════════════════════════════════════════════════════════════════════════

class TestWhitelistPermissions:
    """Testes validando que whitelist permite imports corretos."""
    
    @pytest.mark.security
    def test_pandas_allowed(self, execute_sandbox_helper, assert_success):
        """✅ Teste 48: pandas deve ser permitido."""
        code = '''
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3]})
resultado = len(df)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=3)
    
    @pytest.mark.security
    def test_numpy_allowed(self, execute_sandbox_helper, assert_success):
        """✅ Teste 49: numpy deve ser permitido."""
        code = '''
import numpy as np
arr = np.array([1, 2, 3])
resultado = len(arr)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=3)
    
    @pytest.mark.security
    def test_math_allowed(self, execute_sandbox_helper, assert_success):
        """✅ Teste 50: math deve ser permitido."""
        code = '''
import math
resultado = math.sqrt(16)
'''
        result = execute_sandbox_helper(code)
        assert_success(result, expected_result=4.0)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: TENTATIVAS DE BYPASS
# ═══════════════════════════════════════════════════════════════════════════

class TestBypassAttempts:
    """Testes validando que tentativas de bypass não funcionam."""
    
    @pytest.mark.security
    def test_import_via_importlib_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 51: Import via __import__() deve ser controlado."""
        code = '''
os_module = __import__('os')
resultado = os_module.listdir('/')
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)
    
    @pytest.mark.security
    def test_access_builtins_blocked(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 52: Acesso a __builtins__ deve ser restrito."""
        code = '''
resultado = __builtins__['eval']('2 + 2')
'''
        result = execute_sandbox_helper(code)
        assert_failure(result)


"""
TOTAL DE TESTES NESTE MÓDULO: 14 testes

Distribuição:
- Bloqueio de Imports: 6 testes
- Bloqueio de Funções: 5 testes  
- Whitelist Permitida: 3 testes
- Tentativas de Bypass: 2 testes

Cobertura esperada: ~25% do sandbox.py (funções de segurança)
"""
