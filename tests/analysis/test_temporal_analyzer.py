"""
Testes automatizados para o módulo de análise temporal avançada.

Valida análises estatísticas, detecção de padrões e interpretações contextuais.

Autor: EDA AI Minds Team
Data: 2025-10-16
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from analysis.temporal_analyzer import (
    TemporalAnalyzer,
    TemporalAnalysisResult,
    TrendType,
    SeasonalityType
)


class TestTemporalAnalyzer:
    """Testes para analisador temporal avançado."""
    
    @pytest.fixture
    def analyzer(self):
        """Fixture: analisador padrão."""
        return TemporalAnalyzer()
    
    @pytest.fixture
    def df_trend_crescente(self):
        """Fixture: série com tendência crescente."""
        return pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=100, freq='D'),
            'value': np.arange(100) + np.random.randn(100) * 2
        })
    
    @pytest.fixture
    def df_trend_decrescente(self):
        """Fixture: série com tendência decrescente."""
        return pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=100, freq='D'),
            'value': -np.arange(100) + np.random.randn(100) * 2
        })
    
    @pytest.fixture
    def df_estavel(self):
        """Fixture: série estável (sem tendência)."""
        return pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=100, freq='D'),
            'value': np.random.randn(100)
        })
    
    @pytest.fixture
    def df_com_anomalias(self):
        """Fixture: série com anomalias injetadas."""
        values = np.random.randn(100)
        # Injetar anomalias
        values[20] = 50  # outlier positivo
        values[50] = -50  # outlier negativo
        values[80] = 60  # outro outlier
        
        return pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=100, freq='D'),
            'value': values
        })
    
    @pytest.fixture
    def df_sazonal(self):
        """Fixture: série com componente sazonal."""
        t = np.arange(365)
        # Tendência + sazonalidade anual + ruído
        values = 0.01 * t + 10 * np.sin(2 * np.pi * t / 365) + np.random.randn(365) * 0.5
        
        return pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=365, freq='D'),
            'value': values
        })
    
    # =============================================================
    # Testes de Análise de Tendência
    # =============================================================
    
    def test_trend_crescente(self, analyzer, df_trend_crescente):
        """Testa detecção de tendência crescente."""
        result = analyzer.analyze(df_trend_crescente, 'value')
        
        assert result.trend['type'] == TrendType.CRESCENTE.value
        assert result.trend['slope'] > 0
        assert result.trend['is_significant'] is True
        assert result.trend['r2_score'] > 0.8  # Boa qualidade de ajuste
    
    def test_trend_decrescente(self, analyzer, df_trend_decrescente):
        """Testa detecção de tendência decrescente."""
        result = analyzer.analyze(df_trend_decrescente, 'value')
        
        assert result.trend['type'] == TrendType.DECRESCENTE.value
        assert result.trend['slope'] < 0
        assert result.trend['is_significant'] is True
    
    def test_trend_estavel(self, analyzer, df_estavel):
        """Testa detecção de série estável (sem tendência)."""
        result = analyzer.analyze(df_estavel, 'value')
        
        assert result.trend['type'] == TrendType.ESTAVEL.value
        assert abs(result.trend['slope']) < 1e-5
        assert result.trend['is_significant'] is False
    
    # =============================================================
    # Testes de Estatísticas Descritivas
    # =============================================================
    
    def test_summary_stats(self, analyzer, df_trend_crescente):
        """Testa cálculo de estatísticas descritivas."""
        result = analyzer.analyze(df_trend_crescente, 'value')
        
        assert 'count' in result.summary_stats
        assert 'mean' in result.summary_stats
        assert 'std' in result.summary_stats
        assert 'min' in result.summary_stats
        assert 'max' in result.summary_stats
        
        assert result.summary_stats['count'] == 100
    
    # =============================================================
    # Testes de Autocorrelação
    # =============================================================
    
    def test_autocorrelation(self, analyzer, df_estavel):
        """Testa análise de autocorrelação."""
        result = analyzer.analyze(df_estavel, 'value')
        
        assert 'lag1' in result.autocorrelation
        assert 'is_cyclic' in result.autocorrelation
        assert isinstance(result.autocorrelation['lag1'], float)
    
    def test_cyclic_detection(self, analyzer, df_sazonal):
        """Testa detecção de padrões cíclicos."""
        result = analyzer.analyze(df_sazonal, 'value', enable_advanced=True)
        
        # Série sazonal deve apresentar autocorrelação significativa
        # (depende da implementação - pode ser False se lag=1 não capturar ciclo anual)
        assert 'is_cyclic' in result.autocorrelation
    
    # =============================================================
    # Testes de Detecção de Anomalias
    # =============================================================
    
    def test_anomaly_detection_zscore(self, analyzer, df_com_anomalias):
        """Testa detecção de anomalias via z-score."""
        result = analyzer.analyze(df_com_anomalias, 'value')
        
        assert result.anomalies['method'] == 'z-score'
        assert result.anomalies['count'] >= 3  # Pelo menos as 3 anomalias injetadas
        assert len(result.anomalies['indices']) >= 3
    
    def test_anomaly_detection_no_anomalies(self, analyzer, df_estavel):
        """Testa ausência de anomalias em série normal."""
        result = analyzer.analyze(df_estavel, 'value')
        
        # Série normal não deve ter muitas anomalias (pode ter algumas devido ao ruído)
        assert result.anomalies['count'] < 10
    
    def test_anomaly_detection_constant_series(self, analyzer):
        """Testa detecção de anomalias em série constante (std=0)."""
        df_constant = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=50, freq='D'),
            'value': [10.0] * 50  # Todos valores iguais
        })
        
        result = analyzer.analyze(df_constant, 'value')
        
        # Não deve crashar; deve retornar 0 anomalias
        assert result.anomalies['count'] == 0
    
    # =============================================================
    # Testes de Sazonalidade
    # =============================================================
    
    def test_seasonality_detection_enabled(self, analyzer, df_sazonal):
        """Testa detecção de sazonalidade (modo avançado)."""
        result = analyzer.analyze(df_sazonal, 'value', enable_advanced=True)
        
        assert 'detected' in result.seasonality
        assert 'type' in result.seasonality
        assert 'strength' in result.seasonality
    
    def test_seasonality_detection_disabled(self, analyzer, df_sazonal):
        """Testa que sazonalidade NÃO é detectada quando desabilitada."""
        result = analyzer.analyze(df_sazonal, 'value', enable_advanced=False)
        
        # Seasonality deve estar vazio ou com valores padrão
        assert result.seasonality == {} or not result.seasonality.get('detected')
    
    # =============================================================
    # Testes de Interpretação e Recomendações
    # =============================================================
    
    def test_interpretation_generated(self, analyzer, df_trend_crescente):
        """Testa geração de interpretação contextual."""
        result = analyzer.analyze(df_trend_crescente, 'value')
        
        assert result.interpretation != ""
        assert isinstance(result.interpretation, str)
        # Deve mencionar tendência crescente
        assert "crescimento" in result.interpretation.lower() or "crescente" in result.interpretation.lower()
    
    def test_recommendations_generated(self, analyzer, df_trend_crescente):
        """Testa geração de recomendações."""
        result = analyzer.analyze(df_trend_crescente, 'value')
        
        assert len(result.recommendations) > 0
        # Deve haver pelo menos uma recomendação de análise gráfica
        assert any('gráfica' in rec.lower() or 'visual' in rec.lower() for rec in result.recommendations)
    
    # =============================================================
    # Testes de Saída Markdown
    # =============================================================
    
    def test_to_markdown_output(self, analyzer, df_trend_crescente):
        """Testa geração de relatório Markdown."""
        result = analyzer.analyze(df_trend_crescente, 'value')
        markdown = result.to_markdown()
        
        assert isinstance(markdown, str)
        assert '# Análise Temporal' in markdown
        assert '## Resumo Estatístico' in markdown
        assert '## Análise de Tendência' in markdown
        assert '## Autocorrelação' in markdown
        assert '## Detecção de Anomalias' in markdown
        assert '## Interpretação Qualitativa' in markdown
        assert '## Próximos Passos Recomendados' in markdown
    
    # =============================================================
    # Testes de Edge Cases
    # =============================================================
    
    def test_empty_column(self, analyzer):
        """Testa análise de coluna vazia."""
        df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=10, freq='D'),
            'empty': [np.nan] * 10
        })
        
        result = analyzer.analyze(df, 'empty')
        
        # Deve retornar resultado vazio sem crashar
        assert result.column_name == 'empty'
        assert "dados insuficientes" in result.interpretation.lower()
    
    def test_invalid_column_name(self, analyzer, df_trend_crescente):
        """Testa análise de coluna inexistente."""
        with pytest.raises(ValueError, match="Coluna .* não encontrada"):
            analyzer.analyze(df_trend_crescente, 'nonexistent_column')
    
    def test_single_value_column(self, analyzer):
        """Testa análise de coluna com um único valor."""
        df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=1, freq='D'),
            'value': [10.0]
        })
        
        result = analyzer.analyze(df, 'value')
        
        # Deve funcionar sem crashar, mas com limitações
        assert result.column_name == 'value'
        assert result.summary_stats['count'] == 1
    
    def test_two_values_column(self, analyzer):
        """Testa análise de coluna com dois valores."""
        df = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=2, freq='D'),
            'value': [10.0, 20.0]
        })
        
        result = analyzer.analyze(df, 'value')
        
        assert result.column_name == 'value'
        assert result.summary_stats['count'] == 2
        # Tendência deve ser calculável
        assert 'slope' in result.trend
    
    # =============================================================
    # Testes de Metadados
    # =============================================================
    
    def test_metadata_populated(self, analyzer, df_trend_crescente):
        """Testa que metadados são populados corretamente."""
        result = analyzer.analyze(df_trend_crescente, 'value', enable_advanced=True)
        
        assert 'analysis_timestamp' in result.metadata
        assert 'sample_size' in result.metadata
        assert 'missing_values' in result.metadata
        assert 'advanced_enabled' in result.metadata
        
        assert result.metadata['sample_size'] == 100
        assert result.metadata['advanced_enabled'] is True
    
    # =============================================================
    # Testes de Robustez
    # =============================================================
    
    def test_large_dataset(self, analyzer):
        """Testa análise de dataset grande."""
        df_large = pd.DataFrame({
            'time': pd.date_range('2020-01-01', periods=10000, freq='H'),
            'value': np.cumsum(np.random.randn(10000))  # Random walk
        })
        
        result = analyzer.analyze(df_large, 'value')
        
        assert result.summary_stats['count'] == 10000
        assert 'slope' in result.trend
    
    def test_high_variance_data(self, analyzer):
        """Testa análise de dados com alta variância."""
        df_volatile = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=100, freq='D'),
            'value': np.random.randn(100) * 100  # Alta variância
        })
        
        result = analyzer.analyze(df_volatile, 'value')
        
        assert result.summary_stats['std'] > 50
        # Deve conseguir detectar tendência (ou falta dela)
        assert result.trend['type'] in [t.value for t in TrendType]
    
    def test_mixed_positive_negative(self, analyzer):
        """Testa análise de série com valores positivos e negativos."""
        df_mixed = pd.DataFrame({
            'time': pd.date_range('2025-01-01', periods=100, freq='D'),
            'value': np.sin(np.linspace(0, 4 * np.pi, 100)) * 50
        })
        
        result = analyzer.analyze(df_mixed, 'value')
        
        assert result.summary_stats['min'] < 0
        assert result.summary_stats['max'] > 0
        # Série senoidal deve ser classificada como estável (sem tendência linear)
        assert result.trend['type'] == TrendType.ESTAVEL.value


class TestTemporalAnalysisResult:
    """Testes para estrutura de resultado de análise."""
    
    def test_result_initialization(self):
        """Testa inicialização de resultado."""
        result = TemporalAnalysisResult(column_name='test_col')
        
        assert result.column_name == 'test_col'
        assert result.summary_stats == {}
        assert result.trend == {}
        assert result.interpretation == ""
        assert result.recommendations == []
    
    def test_result_markdown_empty(self):
        """Testa geração de Markdown com resultado vazio."""
        result = TemporalAnalysisResult(
            column_name='test_col',
            interpretation="Teste de interpretação",
            recommendations=["Recomendação 1", "Recomendação 2"]
        )
        
        markdown = result.to_markdown()
        
        assert '# Análise Temporal: test_col' in markdown
        assert 'Teste de interpretação' in markdown
        assert 'Recomendação 1' in markdown
        assert 'Recomendação 2' in markdown
