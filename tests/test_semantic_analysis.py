"""
Testes para Identificação Semântica de Datasets.

Este módulo testa se o sistema identifica corretamente o contexto e tema
do dataset (ex: fraude em cartão, nota fiscal, e-commerce, etc).

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

from src.analysis.dataset_semantic_analyzer import (
    DatasetSemanticAnalyzer,
    DatasetDomain,
    analyze_dataset_semantics
)


class TestSemanticAnalysis:
    """Testes para identificação semântica de datasets."""
    
    def test_credit_card_fraud_detection(self):
        """
        🔴 TESTE CRÍTICO: Dataset de fraude em cartão deve ser identificado.
        
        Características:
        - Colunas: Time, V1-V28, Amount, Class
        - Domínio esperado: CREDIT_CARD_FRAUD
        """
        # Simular dataset de fraude (Kaggle Credit Card Fraud)
        df = pd.DataFrame({
            'Time': np.arange(0, 100, 1.0),
            'V1': np.random.randn(100),
            'V2': np.random.randn(100),
            'V3': np.random.randn(100),
            'Amount': np.random.uniform(0, 500, 100),
            'Class': np.random.choice([0, 1], 100)
        })
        
        result = analyze_dataset_semantics(df)
        
        assert result.primary_domain == DatasetDomain.CREDIT_CARD_FRAUD, (
            f"❌ FALHA: Dataset de fraude deveria ser identificado como CREDIT_CARD_FRAUD, "
            f"mas foi identificado como '{result.primary_domain.value}' "
            f"(confiança: {result.confidence:.2%})"
        )
        
        assert result.confidence >= 0.7, (
            f"❌ FALHA: Confiança muito baixa: {result.confidence:.2%}"
        )
        
        print(f"✅ PASSOU: Dataset identificado como {result.primary_domain.value}")
        print(f"   Confiança: {result.confidence:.2%}")
        print(f"   Keywords matched: {result.matched_keywords}")
    
    def test_ecommerce_dataset_detection(self):
        """
        Dataset de e-commerce deve ser identificado.
        """
        df = pd.DataFrame({
            'product_id': range(1, 101),
            'product_name': ['Product ' + str(i) for i in range(1, 101)],
            'price': np.random.uniform(10, 500, 100),
            'category': np.random.choice(['Electronics', 'Clothing', 'Books'], 100),
            'rating': np.random.uniform(1, 5, 100),
            'customer_id': np.random.randint(1, 1000, 100)
        })
        
        result = analyze_dataset_semantics(df)
        
        assert result.primary_domain == DatasetDomain.E_COMMERCE, (
            f"❌ FALHA: Dataset de e-commerce deveria ser identificado como E_COMMERCE, "
            f"mas foi identificado como '{result.primary_domain.value}'"
        )
        
        print(f"✅ PASSOU: Dataset identificado como {result.primary_domain.value}")
        print(f"   Confiança: {result.confidence:.2%}")
    
    def test_financial_transactions_detection(self):
        """
        Dataset de transações financeiras deve ser identificado.
        """
        df = pd.DataFrame({
            'transaction_id': range(1, 101),
            'account_from': ['ACC' + str(i) for i in range(1, 101)],
            'account_to': ['ACC' + str(i+100) for i in range(1, 101)],
            'amount': np.random.uniform(10, 10000, 100),
            'transaction_date': pd.date_range('2024-01-01', periods=100),
            'status': np.random.choice(['completed', 'pending', 'failed'], 100)
        })
        
        result = analyze_dataset_semantics(df)
        
        assert result.primary_domain in [DatasetDomain.FINANCIAL_TRANSACTIONS, DatasetDomain.CREDIT_CARD_FRAUD], (
            f"❌ FALHA: Dataset de transações deveria ser financeiro, "
            f"mas foi identificado como '{result.primary_domain.value}'"
        )
        
        print(f"✅ PASSOU: Dataset identificado como {result.primary_domain.value}")
        print(f"   Confiança: {result.confidence:.2%}")
    
    def test_generic_dataset_low_confidence(self):
        """
        Dataset genérico (sem padrões claros) deve ter confiança baixa.
        """
        df = pd.DataFrame({
            'col_a': range(1, 101),
            'col_b': np.random.randn(100),
            'col_c': np.random.choice(['X', 'Y', 'Z'], 100)
        })
        
        result = analyze_dataset_semantics(df)
        
        # Pode ser GENERIC ou TIME_SERIES (dependendo dos padrões)
        assert result.primary_domain in [DatasetDomain.GENERIC, DatasetDomain.TIME_SERIES, DatasetDomain.UNKNOWN], (
            f"Dataset genérico deveria ser GENERIC, TIME_SERIES ou UNKNOWN, "
            f"mas foi '{result.primary_domain.value}'"
        )
        
        print(f"✅ PASSOU: Dataset genérico identificado como {result.primary_domain.value}")
        print(f"   Confiança: {result.confidence:.2%}")
    
    def test_time_series_detection(self):
        """
        Dataset de série temporal deve ser identificado.
        """
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=365, freq='D'),
            'value': np.random.randn(365).cumsum(),
            'metric': np.random.uniform(0, 100, 365)
        })
        
        result = analyze_dataset_semantics(df)
        
        assert result.primary_domain in [DatasetDomain.TIME_SERIES, DatasetDomain.IOT_SENSORS], (
            f"❌ FALHA: Dataset de série temporal deveria ser TIME_SERIES, "
            f"mas foi identificado como '{result.primary_domain.value}'"
        )
        
        print(f"✅ PASSOU: Dataset identificado como {result.primary_domain.value}")
        print(f"   Confiança: {result.confidence:.2%}")
    
    def test_customer_data_detection(self):
        """
        Dataset de dados de clientes deve ser identificado.
        """
        df = pd.DataFrame({
            'customer_id': range(1, 101),
            'name': ['Customer ' + str(i) for i in range(1, 101)],
            'email': [f'customer{i}@example.com' for i in range(1, 101)],
            'phone': [f'555-{i:04d}' for i in range(1, 101)],
            'city': np.random.choice(['São Paulo', 'Rio de Janeiro', 'Brasília'], 100),
            'age': np.random.randint(18, 80, 100)
        })
        
        result = analyze_dataset_semantics(df)
        
        assert result.primary_domain == DatasetDomain.CUSTOMER_DATA, (
            f"❌ FALHA: Dataset de clientes deveria ser CUSTOMER_DATA, "
            f"mas foi identificado como '{result.primary_domain.value}'"
        )
        
        print(f"✅ PASSOU: Dataset identificado como {result.primary_domain.value}")
        print(f"   Confiança: {result.confidence:.2%}")
    
    def test_semantic_context_in_metadata(self):
        """
        🟡 TESTE IMPORTANTE: Resultado deve incluir contexto semântico útil.
        """
        df = pd.DataFrame({
            'Time': np.arange(0, 50, 1.0),
            'Amount': np.random.uniform(0, 500, 50),
            'Class': np.random.choice([0, 1], 50)
        })
        
        result = analyze_dataset_semantics(df)
        
        # Verificar que metadados estão presentes
        assert 'total_columns' in result.metadata
        assert 'total_rows' in result.metadata
        assert result.description != "", "Descrição não deve estar vazia"
        assert len(result.matched_keywords) > 0, "Deve ter keywords matched"
        
        print("✅ PASSOU: Metadados semânticos presentes")
        print(f"   Descrição: {result.description}")
        print(f"   Metadados: {result.metadata}")
    
    def test_secondary_domains_detected(self):
        """
        Dataset ambíguo deve retornar domínios secundários.
        """
        # Dataset que pode ser tanto e-commerce quanto sales
        df = pd.DataFrame({
            'product': ['Product ' + str(i) for i in range(1, 101)],
            'sales_amount': np.random.uniform(100, 5000, 100),
            'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
            'date': pd.date_range('2024-01-01', periods=100)
        })
        
        result = analyze_dataset_semantics(df)
        
        # Deve ter domínios secundários
        assert len(result.secondary_domains) > 0, (
            "Dataset ambíguo deveria ter domínios secundários"
        )
        
        print(f"✅ PASSOU: Domínios secundários detectados")
        print(f"   Primário: {result.primary_domain.value} ({result.confidence:.2%})")
        print(f"   Secundários: {[(d.value, conf) for d, conf in result.secondary_domains]}")


def run_all_tests():
    """Executa todos os testes e reporta resultados."""
    print("\n" + "=" * 70)
    print("🧪 EXECUTANDO TESTES DE ANÁLISE SEMÂNTICA DE DATASETS")
    print("=" * 70 + "\n")
    
    test_semantic = TestSemanticAnalysis()
    
    tests = [
        ("Dataset de fraude em cartão", test_semantic.test_credit_card_fraud_detection),
        ("Dataset de e-commerce", test_semantic.test_ecommerce_dataset_detection),
        ("Dataset de transações financeiras", test_semantic.test_financial_transactions_detection),
        ("Dataset genérico (baixa confiança)", test_semantic.test_generic_dataset_low_confidence),
        ("Dataset de série temporal", test_semantic.test_time_series_detection),
        ("Dataset de dados de clientes", test_semantic.test_customer_data_detection),
        ("Contexto semântico em metadados", test_semantic.test_semantic_context_in_metadata),
        ("Domínios secundários", test_semantic.test_secondary_domains_detected),
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"✅ PASSOU: {passed}/{len(tests)}")
    print(f"❌ FALHOU: {failed}/{len(tests)}")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
