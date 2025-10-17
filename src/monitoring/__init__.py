"""
🔍 SISTEMA DE MONITORAMENTO - Sandbox Segura

Módulo para monitoramento, métricas e alertas de execuções do sandbox.

Componentes:
- SandboxMonitor: Coleta e persiste métricas de execução
- AlertManager: Detecta anomalias e envia alertas
- MetricsAggregator: Agrega métricas para análise

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-17
Sprint: Sprint 4 - Monitoramento e Testes Integrados
"""

from .sandbox_monitor import SandboxMonitor, MetricsCollector
from .alert_manager import AlertManager, AlertRule, AlertLevel
from .metrics_aggregator import MetricsAggregator, MetricsReport

__all__ = [
    'SandboxMonitor',
    'MetricsCollector',
    'AlertManager',
    'AlertRule',
    'AlertLevel',
    'MetricsAggregator',
    'MetricsReport'
]

__version__ = '1.0.0'
