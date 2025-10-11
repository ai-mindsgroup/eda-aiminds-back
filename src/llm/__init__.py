"""
Módulo de gerenciamento de LLMs
================================

Fornece roteamento inteligente entre diferentes modelos LLM
baseado na complexidade da consulta.
"""

from .llm_router import (
    LLMRouter,
    ComplexityLevel,
    LLMModel,
    create_llm_with_routing
)

__all__ = [
    "LLMRouter",
    "ComplexityLevel",
    "LLMModel",
    "create_llm_with_routing"
]
