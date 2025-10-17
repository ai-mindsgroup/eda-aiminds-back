"""Configuração avançada de logging centralizada com suporte a JSON estruturado.

Sprint 4 - Sistema de Monitoramento

Funcionalidades:
- Logging estruturado em JSON
- Metadata customizada por contexto
- Rotação automática de arquivos
- Formatação colorida para console (desenvolvimento)
- Formatação JSON para produção

Uso Básico:
    from src.utils.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Mensagem simples")

Uso Avançado (JSON estruturado):
    from src.utils.logging_config import get_logger, log_with_context
    logger = get_logger(__name__)
    
    # Com contexto estruturado
    log_with_context(
        logger=logger,
        level="info",
        message="Execução sandbox concluída",
        execution_id="exec_123",
        duration_ms=150.5,
        memory_mb=45.2,
        status="success"
    )

Author: GitHub Copilot with Sonnet 4.5
Date: 2025-10-17
"""
from __future__ import annotations
import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum


# Configuração de ambiente
_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()  # 'json' ou 'text'
_LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
_LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"

# Garantir que diretório de logs existe
_LOG_DIR.mkdir(parents=True, exist_ok=True)


class LogFormat(str, Enum):
    """Formatos de log disponíveis"""
    JSON = "json"
    TEXT = "text"
    COLORED = "colored"


class JSONFormatter(logging.Formatter):
    """
    Formatter que produz logs estruturados em JSON
    
    Exemplo de saída:
    {
        "timestamp": "2025-10-17T18:51:30.123456Z",
        "level": "INFO",
        "logger": "src.security.sandbox",
        "message": "Sandbox executado com sucesso",
        "execution_id": "exec_123",
        "duration_ms": 150.5,
        "memory_mb": 45.2,
        "process_id": 12345,
        "thread_name": "MainThread",
        "filename": "sandbox.py",
        "line_number": 245,
        "function": "execute_in_sandbox"
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata LogRecord como JSON estruturado"""
        # Campos base sempre presentes
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adicionar informações de contexto
        log_data["process_id"] = record.process
        log_data["thread_name"] = record.threadName
        
        # Adicionar informações de código-fonte
        log_data["filename"] = record.filename
        log_data["line_number"] = record.lineno
        log_data["function"] = record.funcName
        
        # Adicionar campos extras (metadata customizada)
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formatter com cores para melhor legibilidade no console
    Útil em ambiente de desenvolvimento
    """
    
    # Códigos ANSI para cores
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    # Emojis por nível
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '📊',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata com cores e emojis"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        emoji = self.EMOJIS.get(record.levelname, '📝')
        reset = self.COLORS['RESET']
        
        # Formato: [TIME] EMOJI LEVEL | logger | message
        formatted = (
            f"{color}{emoji} {record.levelname:8}{reset} | "
            f"{record.name:40} | {record.getMessage()}"
        )
        
        # Adicionar exceção se presente
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class ContextAdapter(logging.LoggerAdapter):
    """
    Adapter que facilita logging com contexto estruturado
    
    Uso:
        adapter = ContextAdapter(logger, {"user_id": "123", "request_id": "abc"})
        adapter.info("Operação concluída", duration_ms=150.5)
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Adiciona contexto aos kwargs"""
        # Mesclar contexto do adapter com kwargs
        extra = kwargs.get('extra', {})
        
        # Adicionar campos do contexto
        if isinstance(self.extra, dict):
            extra.update(self.extra)
        
        # Adicionar campos extras passados na chamada
        extra_fields = {
            k: v for k, v in kwargs.items() 
            if k not in ['extra', 'exc_info', 'stack_info', 'stacklevel']
        }
        
        if extra_fields:
            extra['extra_fields'] = {**extra.get('extra_fields', {}), **extra_fields}
        elif self.extra:
            extra['extra_fields'] = self.extra
        
        kwargs['extra'] = extra
        
        # Remover campos que não são válidos para logging
        for key in list(kwargs.keys()):
            if key not in ['extra', 'exc_info', 'stack_info', 'stacklevel']:
                kwargs.pop(key)
        
        return msg, kwargs


def _configure_root_once() -> None:
    """Configura logging root uma única vez com handlers apropriados"""
    root_logger = logging.getLogger()
    
    # Se já está configurado, não reconfigurar
    if root_logger.handlers:
        return
    
    root_logger.setLevel(_LEVEL)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_LEVEL)
    
    # Escolher formatter baseado no ambiente
    if _LOG_FORMAT == LogFormat.JSON:
        console_formatter = JSONFormatter()
    elif _LOG_FORMAT == LogFormat.COLORED and sys.stdout.isatty():
        console_formatter = ColoredFormatter()
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo (JSON sempre)
    if _LOG_TO_FILE:
        # Arquivo principal (rotação diária)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=_LOG_DIR / "eda-aiminds.log",
            when="midnight",
            interval=1,
            backupCount=30,  # Manter 30 dias
            encoding="utf-8"
        )
        file_handler.setLevel(_LEVEL)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
        
        # Arquivo de erros (apenas ERROR e CRITICAL)
        error_handler = logging.handlers.RotatingFileHandler(
            filename=_LOG_DIR / "eda-aiminds-errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)


# Configurar na importação
_configure_root_once()


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger configurado para o módulo especificado
    
    Args:
        name: Nome do módulo (geralmente __name__)
        
    Returns:
        Logger configurado
        
    Example:
        logger = get_logger(__name__)
        logger.info("Mensagem de log")
    """
    return logging.getLogger(name)


def get_context_logger(name: str, **context) -> ContextAdapter:
    """
    Retorna logger com contexto pré-definido
    
    Args:
        name: Nome do módulo
        **context: Campos de contexto que serão incluídos em todos os logs
        
    Returns:
        ContextAdapter configurado
        
    Example:
        logger = get_context_logger(__name__, user_id="123", session_id="abc")
        logger.info("Operação executada", duration_ms=150.5)
        # Resultado JSON incluirá: user_id, session_id, duration_ms
    """
    base_logger = get_logger(name)
    return ContextAdapter(base_logger, context)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context
) -> None:
    """
    Helper para logging estruturado com contexto
    
    Args:
        logger: Logger a ser usado
        level: Nível do log ('debug', 'info', 'warning', 'error', 'critical')
        message: Mensagem do log
        **context: Campos adicionais estruturados
        
    Example:
        log_with_context(
            logger=logger,
            level="info",
            message="Execução sandbox concluída",
            execution_id="exec_123",
            duration_ms=150.5,
            memory_mb=45.2,
            status="success"
        )
    """
    log_method = getattr(logger, level.lower())
    
    # Criar extra com campos estruturados
    extra = {'extra_fields': context}
    
    log_method(message, extra=extra)


def configure_logger_for_module(
    module_name: str,
    level: Optional[str] = None,
    propagate: bool = True
) -> logging.Logger:
    """
    Configura logger específico para um módulo
    
    Args:
        module_name: Nome do módulo
        level: Nível de log específico (opcional)
        propagate: Se deve propagar para handlers parent
        
    Returns:
        Logger configurado
        
    Example:
        # Silenciar logs do httpx
        configure_logger_for_module("httpx", level="WARNING", propagate=False)
    """
    logger = logging.getLogger(module_name)
    
    if level:
        logger.setLevel(level.upper())
    
    logger.propagate = propagate
    
    return logger


# Configurar loggers de bibliotecas externas (reduzir verbosidade)
configure_logger_for_module("httpx", level="WARNING")
configure_logger_for_module("urllib3", level="WARNING")
configure_logger_for_module("supabase", level="INFO")
