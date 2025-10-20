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
from src.security.sandbox import execute_in_sandbox

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

# psutil para monitoramento de memória (fallback Windows)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

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

from src.utils.logging_config import get_logger

# Sistema de monitoramento
try:
    from src.monitoring.sandbox_monitor import SandboxMonitor, ExecutionStatus
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    SandboxMonitor = None
    ExecutionStatus = None


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
    'time',  # Para sleep e medições de tempo
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
# LIMITE DE MEMÓRIA
# ═══════════════════════════════════════════════════════════════════════════

class MemoryLimitExceeded(Exception):
    """Exceção levantada quando limite de memória é excedido."""
    pass


def set_memory_limit_unix(megabytes: int) -> bool:
    """
    Define limite de memória para o processo atual (Unix/Linux apenas).
    
    Args:
        megabytes: Limite de memória em MB
        
    Returns:
        True se limite foi aplicado, False caso contrário
        
    Raises:
        MemoryLimitExceeded: Se já excedeu o limite antes de configurar
    """
    if not RESOURCE_AVAILABLE:
        return False
    
    logger = get_logger(__name__)
    
    try:
        # Converter MB para bytes
        max_bytes = megabytes * 1024 * 1024
        
        # Definir limite de memória virtual (RLIMIT_AS)
        # Usa soft limit para permitir ajustes dinâmicos
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
        
        logger.debug(f"✅ Limite de memória configurado: {megabytes}MB (Unix/Linux)")
        return True
        
    except ValueError as e:
        logger.error(f"❌ Erro ao configurar limite de memória: {e}")
        return False
    except OSError as e:
        logger.error(f"❌ OSError ao configurar limite de memória: {e}")
        return False


def get_memory_usage_mb() -> float:
    """
    Obtém uso atual de memória do processo em MB.
    
    Returns:
        Uso de memória em MB, ou -1 se não disponível
    """
    logger = get_logger(__name__)
    
    # Tentar psutil primeiro (cross-platform)
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            # rss = Resident Set Size (memória física usada)
            return memory_info.rss / (1024 * 1024)
        except Exception as e:
            logger.debug(f"Erro ao obter memória via psutil: {e}")
    
    # Fallback: resource (Unix/Linux)
    if RESOURCE_AVAILABLE:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss em KB no Linux, bytes no macOS
            import platform
            if platform.system() == 'Darwin':  # macOS
                return usage.ru_maxrss / (1024 * 1024)
            else:  # Linux
                return usage.ru_maxrss / 1024
        except Exception as e:
            logger.debug(f"Erro ao obter memória via resource: {e}")
    
    return -1


@contextmanager
def memory_limit_context(megabytes: int, platform_name: str = None):
    """
    Context manager para aplicar limite de memória.
    
    ESTRATÉGIA:
    - Unix/Linux: resource.setrlimit() (hard limit pelo kernel)
    - Windows: Monitoramento via psutil + exceção manual (soft limit)
    
    Args:
        megabytes: Limite de memória em MB
        platform_name: Nome da plataforma (auto-detectado se None)
        
    Yields:
        None
        
    Raises:
        MemoryLimitExceeded: Se limite de memória for excedido
    """
    logger = get_logger(__name__)
    
    # Detectar plataforma
    if platform_name is None:
        import platform
        platform_name = platform.system()
    
    # Variáveis de controle
    original_limit = None
    monitoring_active = False
    
    try:
        # ═══════════════════════════════════════════════════════════
        # UNIX/LINUX: Hard limit via resource.setrlimit()
        # ═══════════════════════════════════════════════════════════
        if platform_name in ('Linux', 'Darwin') and RESOURCE_AVAILABLE:
            try:
                # Salvar limite original
                original_limit = resource.getrlimit(resource.RLIMIT_AS)
                
                # Aplicar novo limite
                success = set_memory_limit_unix(megabytes)
                
                if success:
                    logger.info(f"🔒 Limite de memória HARD aplicado: {megabytes}MB (Unix/Linux)")
                else:
                    logger.warning(f"⚠️ Não foi possível aplicar limite hard, usando monitoramento")
                    monitoring_active = True
            except Exception as e:
                logger.warning(f"⚠️ Erro ao configurar limite Unix: {e}, usando monitoramento")
                monitoring_active = True
        
        # ═══════════════════════════════════════════════════════════
        # WINDOWS: Soft limit via monitoramento psutil
        # ═══════════════════════════════════════════════════════════
        else:
            logger.info(f"🔒 Limite de memória SOFT via monitoramento: {megabytes}MB (Windows/Fallback)")
            monitoring_active = True
        
        # Executar código protegido
        yield
        
    finally:
        # Restaurar limite original (Unix/Linux)
        if original_limit is not None and RESOURCE_AVAILABLE:
            try:
                resource.setrlimit(resource.RLIMIT_AS, original_limit)
                logger.debug("✅ Limite de memória original restaurado")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao restaurar limite: {e}")


def check_memory_limit(megabytes: int, memory_before: float = 0):
    """
    Verifica se uso atual de memória excede o limite (para fallback Windows).
    
    Estratégia:
    - Se memory_before fornecido: verifica DELTA de memória (alocação do código)
    - Se memory_before não fornecido: verifica memória TOTAL do processo
    
    Args:
        megabytes: Limite de memória em MB
        memory_before: Memória antes da execução (MB), para calcular delta
        
    Raises:
        MemoryLimitExceeded: Se memória exceder limite
    """
    current_mb = get_memory_usage_mb()
    logger = get_logger(__name__)
    
    if current_mb <= 0:
        return  # Não conseguiu medir memória
    
    # Estratégia 1: Verificar DELTA de memória (mais justo)
    if memory_before > 0:
        delta_mb = current_mb - memory_before
        
        if delta_mb > megabytes:
            logger.error(f"❌ Delta de memória excedido: {delta_mb:.2f}MB > {megabytes}MB")
            raise MemoryLimitExceeded(
                f"Código alocou {delta_mb:.2f}MB de memória, limite é {megabytes}MB"
            )
    
    # Estratégia 2: Verificar memória TOTAL do processo (fallback conservador)
    else:
        if current_mb > megabytes:
            logger.error(f"❌ Memória total excedida: {current_mb:.2f}MB > {megabytes}MB")
            raise MemoryLimitExceeded(
                f"Processo excedeu limite de memória: {current_mb:.2f}MB > {megabytes}MB"
            )


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
            '_write_': lambda x: x,  # Para operações de escrita (necessário para RestrictedPython)
            
            # Import seguro
            '__import__': safe_import,
        },
        
        # Variáveis especiais bloqueadas
        '__name__': 'restricted_module',
        '__file__': '<sandbox>',
        '__doc__': None,
    }
    
    return safe_env


def _record_metrics(monitor, code: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra métricas de execução no monitor (função auxiliar).
    
    Args:
        monitor: Instância do SandboxMonitor (ou None)
        code: Código executado
        result: Resultado da execução
        
    Returns:
        result com campo 'monitoring' adicionado (se monitor disponível)
    """
    if not monitor:
        return result
    
    logger = get_logger(__name__)
    
    try:
        metrics = monitor.record_execution(code, result)
        result['monitoring'] = {
            'execution_id': metrics.execution_id,
            'status': metrics.status,
            'code_hash': metrics.code_hash,
            'execution_time_ms': metrics.execution_time_ms,
            'memory_used_mb': metrics.memory_used_mb
        }
        logger.debug(f"✅ Métricas registradas: {metrics.execution_id}")
    except Exception as e:
        logger.debug(f"⚠️ Erro ao registrar métricas: {e}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL: execute_in_sandbox
# ═══════════════════════════════════════════════════════════════════════════

def execute_in_sandbox(
    code: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    allowed_imports: Optional[List[str]] = None,
    return_variable: str = 'resultado',
    custom_globals: Optional[Dict[str, Any]] = None,
    enable_monitoring: bool = True
) -> Dict[str, Any]:
    """
    Executa código Python em ambiente sandbox seguro.
    
    Args:
        code: Código Python a ser executado
        timeout_seconds: Tempo limite de execução em segundos (padrão: 5)
        memory_limit_mb: Limite de memória em MB (padrão: 100)
        allowed_imports: Lista customizada de imports permitidos (opcional)
        return_variable: Nome da variável a retornar como resultado (padrão: 'resultado')
        custom_globals: Dicionário com variáveis globais customizadas (ex: {'df': dataframe})
        enable_monitoring: Se True, coleta métricas via SandboxMonitor (padrão: True)
        
    Returns:
        Dict com:
            - success (bool): Se execução foi bem-sucedida
            - result (Any): Resultado da execução (valor da variável 'resultado')
            - execution_time_ms (float): Tempo de execução em milissegundos
            - error (str): Mensagem de erro (se success=False)
            - error_type (str): Tipo do erro (se success=False)
            - logs (List[str]): Logs da execução
            - monitoring (Dict): Métricas de monitoramento (se enable_monitoring=True)
            
    Raises:
        ValueError: Se RestrictedPython não estiver disponível
        
    Exemplo:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'A': [1, 2, 3]})
        >>> result = execute_in_sandbox(
        ...     code="resultado = df['A'].mean()",
        ...     custom_globals={'df': df}
        ... )
        >>> print(result['result'])  # 2.0
    """
    logger = get_logger(__name__)
    
    # Inicializar monitor se disponível
    monitor = None
    if enable_monitoring and MONITORING_AVAILABLE:
        try:
            monitor = SandboxMonitor(enable_persistence=True)
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível inicializar monitor: {e}")
            monitor = None
    
    # Verificar se RestrictedPython está disponível
    if not RESTRICTED_PYTHON_AVAILABLE:
        error_msg = "RestrictedPython não está instalado. Execute: pip install RestrictedPython"
        logger.error(error_msg)
        result = {
            'success': False,
            'result': None,
            'execution_time_ms': 0,
            'error': error_msg,
            'error_type': 'DependencyError',
            'logs': [error_msg]
        }
        
        # Registrar no monitor
        if monitor:
            try:
                metrics = monitor.record_execution(code, result)
                result['monitoring'] = {
                    'execution_id': metrics.execution_id,
                    'status': metrics.status
                }
            except Exception as e:
                logger.debug(f"Erro ao registrar no monitor: {e}")
        
        return result
    
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
            result = {
                'success': False,
                'result': None,
                'execution_time_ms': (time.time() - start_time) * 1000,
                'error': error_msg,
                'error_type': 'CompilationError',
                'logs': execution_logs
            }
            return _record_metrics(monitor, code, result)
        
        # compile_restricted retorna objeto 'code' diretamente quando sucesso
        # ou lança SyntaxError quando falha
        execution_logs.append("✅ Compilação bem-sucedida")
        
        # ═══════════════════════════════════════════════════════════════
        # 2. PREPARAR AMBIENTE DE EXECUÇÃO
        # ═══════════════════════════════════════════════════════════════
        logger.debug("🔧 Preparando ambiente de execução...")
        safe_env = build_safe_globals()
        
        # 🔧 INJETAR VARIÁVEIS GLOBAIS CUSTOMIZADAS (ex: DataFrame 'df')
        if custom_globals:
            logger.debug(f"🔧 Injetando {len(custom_globals)} variável(is) customizada(s)")
            safe_env.update(custom_globals)
            execution_logs.append(f"Variáveis customizadas injetadas: {list(custom_globals.keys())}")
        
        # Namespace local para variáveis do código
        local_namespace = {}
        
        # ═══════════════════════════════════════════════════════════════
        # 3. CONFIGURAR LIMITES DE RECURSOS
        # ═══════════════════════════════════════════════════════════════
        import platform
        platform_name = platform.system()
        
        # Detectar disponibilidade de limites de memória
        memory_limit_available = RESOURCE_AVAILABLE or PSUTIL_AVAILABLE
        
        if memory_limit_available:
            logger.debug(f"⚙️ Limites: timeout={timeout_seconds}s, memory={memory_limit_mb}MB")
            execution_logs.append(f"Limites configurados: {timeout_seconds}s, {memory_limit_mb}MB")
            
            if RESOURCE_AVAILABLE and platform_name in ('Linux', 'Darwin'):
                execution_logs.append(f"Plataforma: {platform_name} (limite HARD via resource)")
            elif PSUTIL_AVAILABLE:
                execution_logs.append(f"Plataforma: {platform_name} (limite SOFT via psutil)")
            else:
                execution_logs.append(f"Plataforma: {platform_name} (sem limite de memória)")
        else:
            logger.warning(f"⚠️ Limites de memória não disponíveis (instale psutil)")
            execution_logs.append(f"⚠️ Apenas timeout disponível: {timeout_seconds}s")
        
        # ═══════════════════════════════════════════════════════════════
        # 4. EXECUTAR CÓDIGO COM TIMEOUT E LIMITE DE MEMÓRIA
        # ═══════════════════════════════════════════════════════════════
        logger.info("▶️ Executando código no sandbox...")
        execution_logs.append("Iniciando execução")
        
        # Obter uso de memória inicial (para estatísticas)
        memory_before_mb = get_memory_usage_mb()
        if memory_before_mb > 0:
            execution_logs.append(f"Memória inicial: {memory_before_mb:.2f}MB")
        
        try:
            # Context manager para limite de memória (Unix) ou monitoramento (Windows)
            with memory_limit_context(memory_limit_mb, platform_name):
                with execution_timeout(timeout_seconds):
                    exec(byte_code, safe_env, local_namespace)
                    
                    # Verificação adicional de memória para Windows (soft limit)
                    # Usa DELTA de memória (mais justo) ao invés de memória total
                    if platform_name == 'Windows' and PSUTIL_AVAILABLE:
                        check_memory_limit(memory_limit_mb, memory_before=memory_before_mb)
                        
        except TimeoutException:
            error_msg = f"Execução excedeu o timeout de {timeout_seconds}s"
            logger.error(f"⏱️ {error_msg}")
            execution_logs.append(f"TIMEOUT: {error_msg}")
            result = {
                'success': False,
                'result': None,
                'execution_time_ms': (time.time() - start_time) * 1000,
                'error': error_msg,
                'error_type': 'TimeoutError',
                'logs': execution_logs
            }
            return _record_metrics(monitor, code, result)
            
        except MemoryLimitExceeded as e:
            error_msg = str(e)
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"💾 {error_msg}")
            execution_logs.append(f"MEMORY LIMIT: {error_msg}")
            
            # Estatísticas de memória
            memory_after_mb = get_memory_usage_mb()
            if memory_after_mb > 0:
                execution_logs.append(f"Memória final: {memory_after_mb:.2f}MB")
                if memory_before_mb > 0:
                    delta = memory_after_mb - memory_before_mb
                    execution_logs.append(f"Delta memória: {delta:.2f}MB")
            
            result = {
                'success': False,
                'result': None,
                'execution_time_ms': execution_time_ms,
                'error': error_msg,
                'error_type': 'MemoryLimitError',
                'logs': execution_logs
            }
            return _record_metrics(monitor, code, result)
            
        except MemoryError as e:
            # MemoryError do Python (limite hard atingido no Unix)
            error_msg = f"Execução esgotou memória disponível: {str(e)}"
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"💾 {error_msg}")
            execution_logs.append(f"MEMORY ERROR: {error_msg}")
            
            result = {
                'success': False,
                'result': None,
                'execution_time_ms': execution_time_ms,
                'error': error_msg,
                'error_type': 'MemoryError',
                'logs': execution_logs
            }
            return _record_metrics(monitor, code, result)
        
        # Obter uso de memória final (para estatísticas)
        memory_after_mb = get_memory_usage_mb()
        if memory_after_mb > 0:
            execution_logs.append(f"Memória final: {memory_after_mb:.2f}MB")
            if memory_before_mb > 0:
                delta = memory_after_mb - memory_before_mb
                execution_logs.append(f"Delta memória: {delta:.2f}MB")
        
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
        
        result = {
            'success': True,
            'result': result_value,
            'execution_time_ms': execution_time_ms,
            'error': None,
            'error_type': None,
            'logs': execution_logs
        }
        
        return _record_metrics(monitor, code, result)
        
    except SandboxImportError as e:
        # Import bloqueado
        error_msg = str(e)
        logger.error(f"🚨 Import bloqueado: {error_msg}")
        execution_logs.append(f"ERRO DE SEGURANÇA: {error_msg}")
        result = {
            'success': False,
            'result': None,
            'execution_time_ms': (time.time() - start_time) * 1000,
            'error': error_msg,
            'error_type': 'ImportError',
            'logs': execution_logs
        }
        return _record_metrics(monitor, code, result)
        
    except Exception as e:
        # Erro genérico
        error_msg = f"{type(e).__name__}: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error(f"❌ Erro durante execução: {error_msg}\n{error_trace}")
        execution_logs.append(f"ERRO: {error_msg}")
        
        result = {
            'success': False,
            'result': None,
            'execution_time_ms': (time.time() - start_time) * 1000,
            'error': error_msg,
            'error_type': type(e).__name__,
            'logs': execution_logs,
            'traceback': error_trace
        }
        
        return _record_metrics(monitor, code, result)


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
