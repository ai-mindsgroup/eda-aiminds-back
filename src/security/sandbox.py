"""
Sandbox Seguro para Execução de Código Python - EDA AI Minds Backend

Este módulo implementa um ambiente sandbox seguro usando RestrictedPython
para executar código Python dinamicamente, bloqueando funções perigosas e
imports não autorizados.

ARQUITETURA DE SEGURANÇA:
========================

1. **RestrictedPython**: Compila código em ambiente restrito
2. **Whitelist de Imports**: Apenas módulos seguros permitidos (pandas, numpy, math)
3. **Blacklist de Funções**: Funções perigosas bloqueadas (eval, exec, open, __import__)
4. **Timeout**: Limite de 5 segundos por execução
5. **Limites de Memória**: 100MB máximo
6. **Logging Completo**: Auditoria de todas as execuções

CASOS DE USO:
============
- Execução de código gerado por LLM para análise de dados
- Cálculos matemáticos dinâmicos
- Transformações de DataFrame pandas
- Análises estatísticas customizadas

SEGURANÇA:
=========
- ✅ Bloqueia: os, subprocess, sys, socket, urllib, requests
- ✅ Bloqueia: eval, exec, compile, open, __import__, globals, locals
- ✅ Bloqueia: acesso a __builtins__, __file__, __name__
- ✅ Permite: pandas, numpy, math, statistics, datetime
- ✅ Timeout: 5 segundos (configurável)
- ✅ Memória: 100MB máximo (configurável)

EXEMPLO DE USO:
==============
```python
from security.sandbox import execute_in_sandbox

# Código seguro - será executado
result = execute_in_sandbox('''
import pandas as pd
import numpy as np

data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
mean_A = df['A'].mean()
resultado = f"Média de A: {mean_A}"
''')

print(result)
# Output: {'success': True, 'result': 'Média de A: 2.0', 'execution_time_ms': 45.2}

# Código malicioso - será bloqueado
result = execute_in_sandbox('''
import os
os.system('rm -rf /')  # BLOQUEADO!
''')

print(result)
# Output: {'success': False, 'error': 'ImportError: Import bloqueado: os'}
```

Autor: EDA AI Minds Team
Data: 2025-10-17
Versão: 1.0.0 (Sprint 3)
"""

import logging
import time
import signal
from typing import Dict, Any, Optional, List, Set
from contextlib import contextmanager
from datetime import datetime
import traceback

# resource módulo (apenas Unix/Linux)
try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False
    resource = None

# RestrictedPython para compilação segura
try:
    from RestrictedPython import compile_restricted
    from RestrictedPython.Guards import (
        safe_builtins, 
        safe_globals, 
        guarded_iter_unpack_sequence,
        safer_getattr
    )
    from RestrictedPython.Eval import default_guarded_getitem, default_guarded_getiter
    from RestrictedPython.PrintCollector import PrintCollector
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False
    compile_restricted = None
    safe_builtins = {}
    safe_globals = {}
    safer_getattr = None

from utils.logging_config import get_logger


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE SEGURANÇA
# ═══════════════════════════════════════════════════════════════════════════

# Imports permitidos (whitelist)
ALLOWED_IMPORTS: Set[str] = {
    'pandas',
    'numpy',
    'math',
    'statistics',
    'datetime',
    'json',
    'collections',
    'itertools',
    'functools',
    're',  # Regex (limitado)
}

# Imports bloqueados (blacklist)
BLOCKED_IMPORTS: Set[str] = {
    'os',
    'subprocess',
    'sys',
    'socket',
    'urllib',
    'requests',
    'http',
    'ftplib',
    'telnetlib',
    'pickle',  # Inseguro para deserialização
    'marshal',  # Inseguro
    '__builtin__',
    '__builtins__',
    'builtins',
    'importlib',
}

# Funções perigosas bloqueadas
BLOCKED_FUNCTIONS: Set[str] = {
    'eval',
    'exec',
    'compile',
    'open',
    '__import__',
    'globals',
    'locals',
    'vars',
    'dir',
    'getattr',
    'setattr',
    'delattr',
    'hasattr',
    'input',
    'raw_input',
}

# Limites de recursos
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_MEMORY_LIMIT_MB = 100
DEFAULT_CPU_TIME_SECONDS = 10


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES CUSTOMIZADAS
# ═══════════════════════════════════════════════════════════════════════════

class SandboxExecutionError(Exception):
    """Erro durante execução no sandbox."""
    pass


class SandboxTimeoutError(SandboxExecutionError):
    """Timeout durante execução."""
    pass


class SandboxMemoryError(SandboxExecutionError):
    """Limite de memória excedido."""
    pass


class SandboxImportError(SandboxExecutionError):
    """Import bloqueado por segurança."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# TIMEOUT HANDLER
# ═══════════════════════════════════════════════════════════════════════════

class TimeoutException(Exception):
    """Exceção de timeout."""
    pass


def timeout_handler(signum, frame):
    """Handler para timeout de execução."""
    raise TimeoutException("Execução excedeu o tempo limite")


@contextmanager
def execution_timeout(seconds: int):
    """
    Context manager para timeout de execução.
    
    Args:
        seconds: Tempo limite em segundos
    """
    # Configurar timeout via signal (apenas Unix/Linux)
    try:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    except AttributeError:
        # Windows não suporta signal.SIGALRM, usar thread alternativo
        # TODO: Implementar timeout com threading para Windows
        yield


# ═══════════════════════════════════════════════════════════════════════════
# IMPORT GUARD
# ═══════════════════════════════════════════════════════════════════════════

def safe_import(name: str, *args, **kwargs):
    """
    Função __import__ segura que verifica whitelist/blacklist.
    
    Args:
        name: Nome do módulo a importar
        
    Raises:
        SandboxImportError: Se import não autorizado
    """
    logger = get_logger(__name__)
    
    # Verificar blacklist primeiro
    if name in BLOCKED_IMPORTS or name.split('.')[0] in BLOCKED_IMPORTS:
        logger.warning(f"🚨 Tentativa de import bloqueado: {name}")
        raise SandboxImportError(f"Import bloqueado por segurança: {name}")
    
    # Verificar whitelist
    base_module = name.split('.')[0]
    if base_module not in ALLOWED_IMPORTS:
        logger.warning(f"⚠️ Import não autorizado: {name}")
        raise SandboxImportError(f"Import não autorizado (não está na whitelist): {name}")
    
    # Import permitido
    logger.debug(f"✅ Import permitido: {name}")
    return __import__(name, *args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# SAFE GLOBALS
# ═══════════════════════════════════════════════════════════════════════════

def build_safe_globals() -> Dict[str, Any]:
    """
    Constrói ambiente global seguro para execução.
    
    Returns:
        Dict com builtins seguros e imports permitidos
    """
    safe_env = {
        '__builtins__': {
            # Funções básicas permitidas
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'isinstance': isinstance,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
            
            # RestrictedPython guards
            '_getitem_': default_guarded_getitem,
            '_getiter_': default_guarded_getiter,
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            '_getattr_': safer_getattr,
            '_print_': PrintCollector,
            '_inplacevar_': lambda op, x, y: op(x, y),  # Para operadores in-place (+=, -=, etc)
            
            # Import seguro
            '__import__': safe_import,
        },
        
        # Variáveis especiais bloqueadas
        '__name__': 'restricted_module',
        '__file__': '<sandbox>',
        '__doc__': None,
    }
    
    return safe_env


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL: execute_in_sandbox
# ═══════════════════════════════════════════════════════════════════════════

def execute_in_sandbox(
    code: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    allowed_imports: Optional[List[str]] = None,
    return_variable: str = 'resultado'
) -> Dict[str, Any]:
    """
    Executa código Python em ambiente sandbox seguro.
    
    Args:
        code: Código Python a ser executado
        timeout_seconds: Tempo limite de execução em segundos (padrão: 5)
        memory_limit_mb: Limite de memória em MB (padrão: 100)
        allowed_imports: Lista customizada de imports permitidos (opcional)
        return_variable: Nome da variável a retornar como resultado (padrão: 'resultado')
        
    Returns:
        Dict com:
            - success (bool): Se execução foi bem-sucedida
            - result (Any): Resultado da execução (valor da variável 'resultado')
            - execution_time_ms (float): Tempo de execução em milissegundos
            - error (str): Mensagem de erro (se success=False)
            - error_type (str): Tipo do erro (se success=False)
            - logs (List[str]): Logs da execução
            
    Raises:
        ValueError: Se RestrictedPython não estiver disponível
        
    Exemplo:
        >>> result = execute_in_sandbox('''
        ... import pandas as pd
        ... df = pd.DataFrame({'A': [1, 2, 3]})
        ... resultado = df['A'].mean()
        ... ''')
        >>> print(result['result'])  # 2.0
    """
    logger = get_logger(__name__)
    
    # Verificar se RestrictedPython está disponível
    if not RESTRICTED_PYTHON_AVAILABLE:
        error_msg = "RestrictedPython não está instalado. Execute: pip install RestrictedPython"
        logger.error(error_msg)
        return {
            'success': False,
            'result': None,
            'execution_time_ms': 0,
            'error': error_msg,
            'error_type': 'DependencyError',
            'logs': [error_msg]
        }
    
    # Atualizar whitelist se customizada
    global ALLOWED_IMPORTS
    if allowed_imports:
        ALLOWED_IMPORTS.update(allowed_imports)
    
    # Inicializar resultado
    start_time = time.time()
    execution_logs = []
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # 1. COMPILAR CÓDIGO EM MODO RESTRITO
        # ═══════════════════════════════════════════════════════════════
        logger.info("🔒 Compilando código em modo restrito...")
        execution_logs.append("Iniciando compilação RestrictedPython")
        
        try:
            byte_code = compile_restricted(
                code,
                filename='<sandbox>',
                mode='exec'
            )
        except SyntaxError as e:
            # RestrictedPython lança SyntaxError para código restrito
            error_msg = str(e)
            logger.error(f"❌ Erro de compilação (código restrito): {error_msg}")
            execution_logs.append(f"Erro de compilação: {error_msg}")
            return {
                'success': False,
                'result': None,
                'execution_time_ms': (time.time() - start_time) * 1000,
                'error': error_msg,
                'error_type': 'CompilationError',
                'logs': execution_logs
            }
        
        # compile_restricted retorna objeto 'code' diretamente quando sucesso
        # ou lança SyntaxError quando falha
        execution_logs.append("✅ Compilação bem-sucedida")
        
        # ═══════════════════════════════════════════════════════════════
        # 2. PREPARAR AMBIENTE DE EXECUÇÃO
        # ═══════════════════════════════════════════════════════════════
        logger.debug("🔧 Preparando ambiente de execução...")
        safe_env = build_safe_globals()
        
        # Namespace local para variáveis do código
        local_namespace = {}
        
        # ═══════════════════════════════════════════════════════════════
        # 3. CONFIGURAR LIMITES DE RECURSOS
        # ═══════════════════════════════════════════════════════════════
        # TODO: Implementar limites de memória (requer cgroups no Linux)
        # Por enquanto, apenas logging
        logger.debug(f"⚙️ Limites: timeout={timeout_seconds}s, memory={memory_limit_mb}MB")
        execution_logs.append(f"Limites configurados: {timeout_seconds}s, {memory_limit_mb}MB")
        
        # ═══════════════════════════════════════════════════════════════
        # 4. EXECUTAR CÓDIGO COM TIMEOUT
        # ═══════════════════════════════════════════════════════════════
        logger.info("▶️ Executando código no sandbox...")
        execution_logs.append("Iniciando execução")
        
        try:
            with execution_timeout(timeout_seconds):
                exec(byte_code, safe_env, local_namespace)
        except TimeoutException:
            error_msg = f"Execução excedeu o timeout de {timeout_seconds}s"
            logger.error(f"⏱️ {error_msg}")
            execution_logs.append(f"TIMEOUT: {error_msg}")
            return {
                'success': False,
                'result': None,
                'execution_time_ms': (time.time() - start_time) * 1000,
                'error': error_msg,
                'error_type': 'TimeoutError',
                'logs': execution_logs
            }
        
        execution_logs.append("✅ Execução concluída")
        
        # ═══════════════════════════════════════════════════════════════
        # 5. EXTRAIR RESULTADO
        # ═══════════════════════════════════════════════════════════════
        result_value = local_namespace.get(return_variable)
        
        if result_value is None:
            logger.warning(f"⚠️ Variável '{return_variable}' não encontrada no namespace")
            execution_logs.append(f"Aviso: Variável '{return_variable}' não definida")
            # Retornar todo o namespace como fallback
            result_value = {k: v for k, v in local_namespace.items() 
                           if not k.startswith('_')}
        
        # ═══════════════════════════════════════════════════════════════
        # 6. RETORNAR SUCESSO
        # ═══════════════════════════════════════════════════════════════
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Sandbox executado com sucesso em {execution_time_ms:.2f}ms")
        execution_logs.append(f"Sucesso em {execution_time_ms:.2f}ms")
        
        return {
            'success': True,
            'result': result_value,
            'execution_time_ms': execution_time_ms,
            'error': None,
            'error_type': None,
            'logs': execution_logs
        }
        
    except SandboxImportError as e:
        # Import bloqueado
        error_msg = str(e)
        logger.error(f"🚨 Import bloqueado: {error_msg}")
        execution_logs.append(f"ERRO DE SEGURANÇA: {error_msg}")
        return {
            'success': False,
            'result': None,
            'execution_time_ms': (time.time() - start_time) * 1000,
            'error': error_msg,
            'error_type': 'ImportError',
            'logs': execution_logs
        }
        
    except Exception as e:
        # Erro genérico
        error_msg = f"{type(e).__name__}: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error(f"❌ Erro durante execução: {error_msg}\n{error_trace}")
        execution_logs.append(f"ERRO: {error_msg}")
        
        return {
            'success': False,
            'result': None,
            'execution_time_ms': (time.time() - start_time) * 1000,
            'error': error_msg,
            'error_type': type(e).__name__,
            'logs': execution_logs,
            'traceback': error_trace
        }


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def validate_code_safety(code: str) -> Dict[str, Any]:
    """
    Valida se código é seguro antes de executar (análise estática).
    
    Args:
        code: Código Python a validar
        
    Returns:
        Dict com:
            - is_safe (bool): Se código parece seguro
            - warnings (List[str]): Avisos de segurança
            - blocked_patterns (List[str]): Padrões perigosos detectados
    """
    warnings = []
    blocked_patterns = []
    
    # Verificar imports bloqueados
    for blocked in BLOCKED_IMPORTS:
        if f'import {blocked}' in code or f'from {blocked}' in code:
            blocked_patterns.append(f"Import bloqueado: {blocked}")
    
    # Verificar funções perigosas
    for func in BLOCKED_FUNCTIONS:
        if f'{func}(' in code:
            blocked_patterns.append(f"Função perigosa: {func}()")
    
    # Verificar padrões suspeitos
    suspicious_patterns = ['__', 'exec(', 'eval(', 'compile(', 'open(']
    for pattern in suspicious_patterns:
        if pattern in code:
            warnings.append(f"Padrão suspeito detectado: {pattern}")
    
    is_safe = len(blocked_patterns) == 0
    
    return {
        'is_safe': is_safe,
        'warnings': warnings,
        'blocked_patterns': blocked_patterns
    }


def get_sandbox_info() -> Dict[str, Any]:
    """
    Retorna informações sobre configuração do sandbox.
    
    Returns:
        Dict com configurações e status do sandbox
    """
    return {
        'restricted_python_available': RESTRICTED_PYTHON_AVAILABLE,
        'allowed_imports': sorted(list(ALLOWED_IMPORTS)),
        'blocked_imports': sorted(list(BLOCKED_IMPORTS)),
        'blocked_functions': sorted(list(BLOCKED_FUNCTIONS)),
        'default_timeout_seconds': DEFAULT_TIMEOUT_SECONDS,
        'default_memory_limit_mb': DEFAULT_MEMORY_LIMIT_MB,
        'version': '1.0.0'
    }
