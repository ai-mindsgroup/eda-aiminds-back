"""
Módulo de análises avançadas para o sistema EDA AI Minds.

Fornece detecção inteligente de colunas temporais e análises estatísticas/temporais modulares.
"""

from .temporal_detection import TemporalColumnDetector, TemporalDetectionConfig
from .temporal_analyzer import TemporalAnalyzer, TemporalAnalysisResult

__all__ = [
    'TemporalColumnDetector',
    'TemporalDetectionConfig',
    'TemporalAnalyzer',
    'TemporalAnalysisResult',
]
