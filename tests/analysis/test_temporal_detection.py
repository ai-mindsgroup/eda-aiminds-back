"""
Testes automatizados para o módulo de detecção de colunas temporais.

Valida todos os cenários de detecção, edge cases e configurações paramétricas.

Autor: EDA AI Minds Team
Data: 2025-10-16
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from analysis.temporal_detection import (
    TemporalColumnDetector,
    TemporalDetectionConfig,
    DetectionMethod,
    DetectionResult
)


class TestTemporalDetectionConfig:
    """Testes para configuração parametrizável."""
    
    def test_default_config(self):
        """Testa configuração padrão."""
        config = TemporalDetectionConfig()
        
        assert "time" in config.common_names
        assert "date" in config.common_names
        assert config.conversion_threshold == 0.80
        assert config.min_unique_ratio == 0.01
        
    def test_custom_config(self):
        """Testa configuração customizada."""
        config = TemporalDetectionConfig(
            common_names=["custom_time", "custom_date"],
            conversion_threshold=0.90,
            enable_aggressive_detection=True
        )
        
        assert "custom_time" in config.common_names
        assert config.conversion_threshold == 0.90
        assert config.enable_aggressive_detection is True


class TestTemporalColumnDetector:
    """Testes para detector de colunas temporais."""
    
    @pytest.fixture
    def detector(self):
        """Fixture: detector padrão."""
        return TemporalColumnDetector()
    
    @pytest.fixture
    def df_no_temporal(self):
        """Fixture: DataFrame sem colunas temporais."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10.5, 20.3, 15.7, 30.2, 25.1],
            'category': ['A', 'B', 'A', 'C', 'B'],
            'Class': [0, 1, 0, 1, 0]
        })
    
    @pytest.fixture
    def df_native_datetime(self):
        """Fixture: DataFrame com coluna datetime nativa."""
        dates = pd.date_range('2025-01-01', periods=5, freq='D')
        return pd.DataFrame({
            'timestamp': dates,
            'value': [10, 20, 15, 30, 25]
        })
    
    @pytest.fixture
    def df_common_name(self):
        """Fixture: DataFrame com nome comum."""
        return pd.DataFrame({
            'time': range(5),
            'value': [10, 20, 15, 30, 25]
        })
    
    @pytest.fixture
    def df_string_temporal(self):
        """Fixture: DataFrame com strings temporais conversíveis."""
        return pd.DataFrame({
            'date_str': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
            'value': [10, 20, 15, 30, 25]
        })
    
    @pytest.fixture
    def df_mixed_temporal(self):
        """Fixture: DataFrame com múltiplas colunas temporais."""
        dates1 = pd.date_range('2025-01-01', periods=5, freq='D')
        return pd.DataFrame({
            'timestamp': dates1,
            'date': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
            'created_at': dates1 + timedelta(hours=12),
            'value': [10, 20, 15, 30, 25]
        })
    
    @pytest.fixture
    def df_partial_valid(self):
        """Fixture: DataFrame com strings parcialmente conversíveis (abaixo threshold)."""
        return pd.DataFrame({
            'mixed_col': ['2025-01-01', '2025-01-02', 'invalid', 'also_invalid', 'bad_data'],
            'value': [10, 20, 15, 30, 25]
        })
    
    # =============================================================
    # Testes de Detecção - Cenários Básicos
    # =============================================================
    
    def test_no_temporal_columns(self, detector, df_no_temporal):
        """Testa dataset sem colunas temporais."""
        results = detector.detect(df_no_temporal)
        temporal_cols = detector.get_detected_columns(results)
        
        assert len(temporal_cols) == 0
        assert all(not r.detected for r in results)
    
    def test_native_datetime_detection(self, detector, df_native_datetime):
        """Testa detecção de coluna datetime nativa."""
        results = detector.detect(df_native_datetime)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'timestamp' in temporal_cols
        assert len(temporal_cols) == 1
        
        # Verificar método e confiança
        timestamp_result = [r for r in results if r.column_name == 'timestamp'][0]
        assert timestamp_result.method == DetectionMethod.NATIVE_DATETIME
        assert timestamp_result.confidence == 0.95
    
    def test_common_name_detection(self, detector, df_common_name):
        """Testa detecção por nome comum (case-insensitive)."""
        results = detector.detect(df_common_name)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'time' in temporal_cols
        
        time_result = [r for r in results if r.column_name == 'time'][0]
        assert time_result.method == DetectionMethod.COMMON_NAME
        assert time_result.confidence == 0.85
    
    def test_string_conversion_detection(self, detector, df_string_temporal):
        """Testa conversão de strings temporais."""
        results = detector.detect(df_string_temporal)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'date_str' in temporal_cols
        
        date_result = [r for r in results if r.column_name == 'date_str'][0]
        assert date_result.method == DetectionMethod.STRING_CONVERSION
        assert date_result.confidence >= 0.60  # Confiança proporcional à conversão
        assert date_result.conversion_stats['valid_ratio'] >= 0.80
    
    def test_multiple_temporal_columns(self, detector, df_mixed_temporal):
        """Testa detecção de múltiplas colunas temporais."""
        results = detector.detect(df_mixed_temporal)
        temporal_cols = detector.get_detected_columns(results)
        
        # Deve detectar todas as 3 colunas temporais
        assert len(temporal_cols) == 3
        assert 'timestamp' in temporal_cols
        assert 'date' in temporal_cols
        assert 'created_at' in temporal_cols
    
    def test_partial_valid_strings(self, detector, df_partial_valid):
        """Testa strings parcialmente conversíveis (abaixo do threshold)."""
        results = detector.detect(df_partial_valid)
        temporal_cols = detector.get_detected_columns(results)
        
        # Apenas 40% válido - não deve detectar (threshold = 80%)
        assert 'mixed_col' not in temporal_cols
    
    # =============================================================
    # Testes de Override Manual
    # =============================================================
    
    def test_override_manual_valid(self, detector, df_no_temporal):
        """Testa override manual com coluna válida."""
        results = detector.detect(df_no_temporal, override_column='value')
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'value' in temporal_cols
        assert len(temporal_cols) == 1
        
        value_result = results[0]
        assert value_result.method == DetectionMethod.OVERRIDE_MANUAL
        assert value_result.confidence == 1.0
    
    def test_override_manual_invalid(self, detector, df_no_temporal):
        """Testa override manual com coluna inexistente."""
        with pytest.raises(ValueError, match="Coluna override .* não encontrada"):
            detector.detect(df_no_temporal, override_column='nonexistent')
    
    # =============================================================
    # Testes de Exclusão de Padrões
    # =============================================================
    
    def test_excluded_patterns(self, df_no_temporal):
        """Testa exclusão de padrões conhecidos não-temporais."""
        # Criar detector com patterns excludentes
        config = TemporalDetectionConfig()
        detector = TemporalColumnDetector(config)
        
        results = detector.detect(df_no_temporal)
        temporal_cols = detector.get_detected_columns(results)
        
        # 'id' e 'Class' devem ser excluídos
        assert 'id' not in temporal_cols
        assert 'Class' not in temporal_cols
    
    def test_case_insensitive_names(self, detector):
        """Testa detecção case-insensitive de nomes comuns."""
        df = pd.DataFrame({
            'TIME': range(5),  # Maiúsculo
            'Date': range(5),  # Capitalizado
            'timestamp': range(5),  # Minúsculo
            'value': [10, 20, 15, 30, 25]
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'TIME' in temporal_cols
        assert 'Date' in temporal_cols
        assert 'timestamp' in temporal_cols
    
    # =============================================================
    # Testes de Detecção Agressiva (Sequências Numéricas)
    # =============================================================
    
    def test_numeric_sequence_detection_enabled(self):
        """Testa detecção de sequências numéricas temporais (modo agressivo)."""
        config = TemporalDetectionConfig(enable_aggressive_detection=True)
        detector = TemporalColumnDetector(config)
        
        # Criar sequência monotônica regular (timestamps Unix)
        unix_timestamps = [1704067200 + i * 86400 for i in range(10)]  # Diário
        df = pd.DataFrame({
            'unix_time': unix_timestamps,
            'value': range(10)
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'unix_time' in temporal_cols
        
        unix_result = [r for r in results if r.column_name == 'unix_time'][0]
        assert unix_result.method == DetectionMethod.NUMERIC_SEQUENCE
    
    def test_numeric_sequence_detection_disabled(self):
        """Testa que sequências numéricas NÃO são detectadas com modo agressivo desabilitado."""
        config = TemporalDetectionConfig(enable_aggressive_detection=False)
        detector = TemporalColumnDetector(config)
        
        unix_timestamps = [1704067200 + i * 86400 for i in range(10)]
        df = pd.DataFrame({
            'unix_time': unix_timestamps,
            'value': range(10)
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        # Não deve detectar sem modo agressivo
        assert 'unix_time' not in temporal_cols
    
    # =============================================================
    # Testes de Métodos Auxiliares
    # =============================================================
    
    def test_get_detection_summary(self, detector, df_mixed_temporal):
        """Testa geração de resumo estatístico."""
        results = detector.detect(df_mixed_temporal)
        summary = detector.get_detection_summary(results)
        
        assert summary['total_columns'] == 4
        assert summary['detected_count'] == 3
        assert summary['detection_rate'] == 3 / 4
        assert 'avg_confidence' in summary
        assert 'methods_used' in summary
        assert len(summary['detected_columns']) == 3
    
    def test_empty_dataframe(self, detector):
        """Testa detector em DataFrame vazio."""
        df_empty = pd.DataFrame()
        results = detector.detect(df_empty)
        
        assert len(results) == 0
        assert detector.get_detected_columns(results) == []
    
    # =============================================================
    # Testes de Configuração Customizada
    # =============================================================
    
    def test_custom_common_names(self):
        """Testa nomes comuns personalizados."""
        config = TemporalDetectionConfig(common_names=["custom_timestamp", "my_date"])
        detector = TemporalColumnDetector(config)
        
        df = pd.DataFrame({
            'custom_timestamp': range(5),
            'my_date': range(5),
            'value': [10, 20, 15, 30, 25]
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'custom_timestamp' in temporal_cols
        assert 'my_date' in temporal_cols
    
    def test_custom_conversion_threshold(self):
        """Testa threshold de conversão customizado."""
        # Criar DataFrame com 70% de valores válidos
        df = pd.DataFrame({
            'partial_date': [
                '2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04',
                '2025-01-05', '2025-01-06', '2025-01-07', 'invalid',
                'bad', 'wrong'
            ]
        })
        
        # Threshold padrão (80%) - não deve detectar
        config_strict = TemporalDetectionConfig(conversion_threshold=0.80)
        detector_strict = TemporalColumnDetector(config_strict)
        results_strict = detector_strict.detect(df)
        assert 'partial_date' not in detector_strict.get_detected_columns(results_strict)
        
        # Threshold relaxado (60%) - deve detectar
        config_relaxed = TemporalDetectionConfig(conversion_threshold=0.60)
        detector_relaxed = TemporalColumnDetector(config_relaxed)
        results_relaxed = detector_relaxed.detect(df)
        assert 'partial_date' in detector_relaxed.get_detected_columns(results_relaxed)
    
    # =============================================================
    # Testes de Edge Cases
    # =============================================================
    
    def test_all_null_column(self, detector):
        """Testa coluna com todos valores nulos."""
        df = pd.DataFrame({
            'null_col': [None, None, None, None, None],
            'value': [10, 20, 15, 30, 25]
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'null_col' not in temporal_cols
    
    def test_single_row_dataframe(self, detector):
        """Testa DataFrame com apenas uma linha."""
        df = pd.DataFrame({
            'timestamp': [pd.Timestamp('2025-01-01')],
            'value': [10]
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        # Deve detectar mesmo com 1 linha
        assert 'timestamp' in temporal_cols
    
    def test_numeric_column_not_temporal(self, detector):
        """Testa que colunas numéricas comuns não são classificadas como temporais."""
        df = pd.DataFrame({
            'V1': np.random.randn(10),
            'V2': np.random.randn(10),
            'Amount': [100.5, 200.3, 150.7, 300.2, 250.1, 180.9, 220.4, 190.6, 210.8, 240.0],
            'value': range(10)
        })
        
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        # Nenhuma dessas colunas numéricas deve ser detectada como temporal
        assert 'V1' not in temporal_cols
        assert 'V2' not in temporal_cols
        assert 'Amount' not in temporal_cols
        assert 'value' not in temporal_cols
    
    # =============================================================
    # Testes de Performance e Robustez
    # =============================================================
    
    def test_large_dataframe(self, detector):
        """Testa detecção em DataFrame grande."""
        large_df = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=10000, freq='H'),
            'value': np.random.randn(10000)
        })
        
        results = detector.detect(large_df)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'timestamp' in temporal_cols
    
    def test_many_columns(self, detector):
        """Testa DataFrame com muitas colunas."""
        data = {f'col_{i}': range(10) for i in range(100)}
        data['timestamp'] = pd.date_range('2025-01-01', periods=10, freq='D')
        
        df = pd.DataFrame(data)
        results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(results)
        
        assert 'timestamp' in temporal_cols
        assert len(temporal_cols) == 1  # Apenas timestamp deve ser detectada
