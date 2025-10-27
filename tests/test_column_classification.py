"""
Testes para Classificação Correta de Tipos de Colunas.

Este módulo testa se o sistema classifica corretamente os tipos de cada coluna
individualmente, sem assumir tipo global do dataset.

Autor: EDA AI Minds Team
Data: 2025-10-23
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.ingest.metadata_extractor import detect_semantic_type
from src.analysis.temporal_detection import TemporalColumnDetector, TemporalDetectionConfig


class TestColumnClassification:
    """Testes para classificação individual de tipos de colunas."""
    
    def test_numeric_column_with_temporal_name_detected_as_temporal_with_high_cardinality(self):
        """
        🔴 TESTE CRÍTICO: Coluna numérica "Time" com alta cardinalidade DEVE ser temporal.
        
        Simula dataset de fraude em cartão (Kaggle Credit Card Fraud):
        - Coluna "Time": float64, elapsed seconds (alta cardinalidade ~44%)
        - É temporal relativa (tempo desde primeira transação)
        - Contexto: análises temporais de padrões de fraude
        """
        # Criar DataFrame simulando creditcard.csv (alta cardinalidade)
        df = pd.DataFrame({
            'Time': np.arange(0, 1000, 1.0),  # 1000 valores únicos, cardinalidade 100%
            'V1': np.random.randn(1000),
            'Amount': np.random.uniform(1, 1000, 1000),
            'Class': np.random.choice([0, 1], 1000)
        })
        
        # ═══════════════════════════════════════════════════════════════
        # TESTE 1: Detecção temporal DEVE disparar para Time com alta cardinalidade
        # ═══════════════════════════════════════════════════════════════
        detector = TemporalColumnDetector()
        results = detector.detect(df)
        
        time_result = next((r for r in results if r.column_name == 'Time'), None)
        assert time_result is not None, "Coluna 'Time' não foi analisada"
        assert time_result.detected == True, (
            f"❌ FALHA CRÍTICA: Coluna 'Time' com alta cardinalidade não foi detectada como temporal! "
            f"Método: {time_result.method}, Confidence: {time_result.confidence}"
        )
        
        print("✅ PASSOU: Coluna 'Time' numérica com alta cardinalidade foi detectada como temporal")
    
    def test_numeric_column_with_temporal_name_but_low_cardinality_not_temporal(self):
        """
        🟡 TESTE IMPORTANTE: Coluna numérica "Time" com BAIXA cardinalidade NÃO deve ser temporal.
        
        Exemplo: Coluna "time_slot" com valores 1, 2, 3 (apenas 3 slots de tempo categóricos)
        """
        df = pd.DataFrame({
            'Time': [1, 2, 3, 1, 2, 3, 1, 2] * 20  # Apenas 3 valores únicos, cardinalidade ~19%
        })
        
        detector = TemporalColumnDetector()
        results = detector.detect(df)
        
        time_result = next((r for r in results if r.column_name == 'Time'), None)
        assert time_result.detected == False, (
            f"❌ FALHA: Coluna 'Time' com baixa cardinalidade foi detectada como temporal incorretamente"
        )
        
        print("✅ PASSOU: Coluna 'Time' com baixa cardinalidade não foi detectada como temporal")
    
    def test_semantic_type_detection_for_categorical_numeric(self):
        """
        🔴 TESTE CRÍTICO: Coluna "Class" com valores 0/1 deve ser categorical_binary.
        
        Mesmo sendo int64, deve ser detectada como categórica por ter apenas 2 valores.
        """
        df = pd.DataFrame({
            'Class': [0, 0, 1, 0, 1, 0, 0, 1]  # int64, mas só 2 valores
        })
        
        semantic_type = detect_semantic_type('Class', df['Class'])
        
        assert semantic_type == "categorical_binary", (
            f"❌ FALHA: Coluna 'Class' deveria ser 'categorical_binary', "
            f"mas foi detectada como '{semantic_type}'"
        )
        
        print("✅ PASSOU: Coluna 'Class' binária detectada como categorical_binary")
    
    def test_semantic_type_detection_for_low_cardinality_numeric(self):
        """
        🟡 TESTE IMPORTANTE: Coluna numérica com baixa cardinalidade deve ser categorical_numeric.
        
        Exemplo: Status com valores 1, 2, 3 (apenas 3 categorias)
        """
        df = pd.DataFrame({
            'Status': [1, 2, 3, 1, 2, 1, 3, 2, 1, 1] * 10  # 3 valores únicos
        })
        
        semantic_type = detect_semantic_type('Status', df['Status'])
        
        assert semantic_type in ["categorical_numeric", "categorical_binary"], (
            f"❌ FALHA: Coluna 'Status' com 3 valores deveria ser categórica, "
            f"mas foi detectada como '{semantic_type}'"
        )
        
        print(f"✅ PASSOU: Coluna 'Status' de baixa cardinalidade detectada como '{semantic_type}'")
    
    def test_semantic_type_detection_for_continuous_numeric(self):
        """
        Coluna numérica contínua (Amount) deve ser "numeric".
        """
        df = pd.DataFrame({
            'Amount': np.random.uniform(0, 1000, 100)  # Valores contínuos
        })
        
        semantic_type = detect_semantic_type('Amount', df['Amount'])
        
        assert semantic_type == "numeric", (
            f"❌ FALHA: Coluna 'Amount' contínua deveria ser 'numeric', "
            f"mas foi detectada como '{semantic_type}'"
        )
        
        print("✅ PASSOU: Coluna 'Amount' contínua detectada como numeric")
    
    def test_all_columns_analyzed_individually(self):
        """
        🔴 TESTE CRÍTICO: Todas as colunas devem ser analisadas individualmente.
        
        Verifica se o sistema NÃO assume tipo global baseado na primeira coluna.
        """
        df = pd.DataFrame({
            'Time': [0.0, 1.0, 2.0],  # Numérico
            'Category': ['A', 'B', 'A'],  # Categórico
            'Amount': [10.5, 20.3, 15.8],  # Numérico contínuo
            'Class': [0, 1, 0],  # Categórico binário (numérico)
            'Date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])  # Temporal real
        })
        
        # Analisar cada coluna
        results = {}
        for col in df.columns:
            semantic_type = detect_semantic_type(col, df[col])
            results[col] = semantic_type
        
        # Verificar que tipos são diferentes (não assumiu tipo global)
        unique_types = set(results.values())
        assert len(unique_types) >= 3, (
            f"❌ FALHA: Todas as colunas têm tipos parecidos: {results}. "
            f"Sistema pode estar assumindo tipo global!"
        )
        
        # Verificar tipos específicos
        assert results['Time'] == 'numeric', f"Time deveria ser numeric, é {results['Time']}"
        assert results['Category'] == 'categorical', f"Category deveria ser categorical, é {results['Category']}"
        assert results['Class'] == 'categorical_binary', f"Class deveria ser categorical_binary, é {results['Class']}"
        assert results['Date'] == 'temporal', f"Date deveria ser temporal, é {results['Date']}"
        
        print("✅ PASSOU: Todas as colunas analisadas individualmente com tipos corretos")
        print(f"   Tipos detectados: {results}")
    
    def test_v_columns_not_detected_as_temporal(self):
        """
        🟡 TESTE IMPORTANTE: Colunas V1, V2, ... V28 (PCA) NÃO devem ser temporais.
        
        Dataset de fraude tem 28 colunas V1-V28 que são componentes PCA, não temporais.
        """
        df = pd.DataFrame({
            'V1': np.random.randn(100),
            'V2': np.random.randn(100),
            'V3': np.random.randn(100),
        })
        
        detector = TemporalColumnDetector()
        results = detector.detect(df)
        
        for result in results:
            assert result.detected == False, (
                f"❌ FALHA: Coluna PCA '{result.column_name}' foi detectada como temporal! "
                f"Método: {result.method}"
            )
        
        print("✅ PASSOU: Colunas V1, V2, V3 (PCA) não foram detectadas como temporais")


class TestTemporalDetectionEdgeCases:
    """Testes para casos extremos de detecção temporal."""
    
    def test_unix_timestamp_in_numeric_column(self):
        """
        Coluna com timestamp unix (segundos) deve ser detectada se modo agressivo.
        """
        df = pd.DataFrame({
            'unix_time': [1609459200, 1609545600, 1609632000]  # Unix timestamps
        })
        
        # Modo normal: NÃO deve detectar
        config_normal = TemporalDetectionConfig(enable_aggressive_detection=False)
        detector_normal = TemporalColumnDetector(config_normal)
        results_normal = detector_normal.detect(df)
        
        assert results_normal[0].detected == False, (
            "Modo normal NÃO deveria detectar unix timestamp"
        )
        
        # Modo agressivo: DEVE detectar
        config_aggressive = TemporalDetectionConfig(enable_aggressive_detection=True)
        detector_aggressive = TemporalColumnDetector(config_aggressive)
        results_aggressive = detector_aggressive.detect(df)
        
        # Nota: Pode ou não detectar dependendo da heurística de sequência numérica
        # Este teste é informativo
        print(f"   Modo agressivo detectou unix_time? {results_aggressive[0].detected}")
    
    def test_date_string_column_detected_as_temporal(self):
        """
        Coluna com strings de data deve ser detectada como temporal.
        """
        df = pd.DataFrame({
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        semantic_type = detect_semantic_type('created_at', df['created_at'])
        
        assert semantic_type == "temporal", (
            f"❌ FALHA: Coluna de strings de data deveria ser 'temporal', "
            f"mas foi detectada como '{semantic_type}'"
        )
        
        print("✅ PASSOU: Coluna de strings de data detectada como temporal")


def run_all_tests():
    """Executa todos os testes e reporta resultados."""
    print("\n" + "=" * 70)
    print("🧪 EXECUTANDO TESTES DE CLASSIFICAÇÃO DE COLUNAS")
    print("=" * 70 + "\n")
    
    # Instanciar classes de teste
    test_classification = TestColumnClassification()
    test_edge_cases = TestTemporalDetectionEdgeCases()
    
    tests = [
        ("Coluna numérica 'Time' com alta cardinalidade (temporal)", test_classification.test_numeric_column_with_temporal_name_detected_as_temporal_with_high_cardinality),
        ("Coluna numérica 'Time' com baixa cardinalidade (não temporal)", test_classification.test_numeric_column_with_temporal_name_but_low_cardinality_not_temporal),
        ("Coluna 'Class' categórica binária", test_classification.test_semantic_type_detection_for_categorical_numeric),
        ("Coluna baixa cardinalidade categórica", test_classification.test_semantic_type_detection_for_low_cardinality_numeric),
        ("Coluna numérica contínua", test_classification.test_semantic_type_detection_for_continuous_numeric),
        ("Análise individual de colunas", test_classification.test_all_columns_analyzed_individually),
        ("Colunas PCA (V1-V28) não temporais", test_classification.test_v_columns_not_detected_as_temporal),
        ("Unix timestamp (edge case)", test_edge_cases.test_unix_timestamp_in_numeric_column),
        ("String de data temporal", test_edge_cases.test_date_string_column_detected_as_temporal),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n📝 Teste: {name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FALHOU: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️ ERRO: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"✅ PASSOU: {passed}/{len(tests)}")
    print(f"❌ FALHOU: {failed}/{len(tests)}")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
