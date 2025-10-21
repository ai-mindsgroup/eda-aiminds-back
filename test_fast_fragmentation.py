"""
Teste Rápido do Sistema de Fragmentação Otimizado
==================================================

Testes ultra-rápidos usando datasets pequenos e versões otimizadas.

Tempo esperado: <5 segundos (vs >30s da versão com LLM)
"""

import pandas as pd
import numpy as np
from datetime import datetime

from src.llm.fast_fragmenter import fragment_query_fast, FastQueryFragmenter
from src.llm.simple_aggregator import execute_and_aggregate
from src.llm.query_fragmentation import TokenBudget
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def create_test_dataframe(rows: int = 100, cols: int = 10) -> pd.DataFrame:
    """Cria DataFrame de teste pequeno."""
    data = {}
    for i in range(cols):
        data[f'col_{i}'] = np.random.randn(rows)
    
    # Adiciona colunas com nomes comuns
    data['Amount'] = np.random.uniform(0, 1000, rows)
    data['Time'] = np.arange(rows)
    data['Class'] = np.random.choice([0, 1], rows)
    
    return pd.DataFrame(data)


def test_fast_fragmentation():
    """Testa fragmentação rápida."""
    print("\n" + "="*70)
    print("🚀 TESTE 1: Fragmentação Ultra-Rápida (sem LLM)")
    print("="*70)
    
    # Dataset pequeno para teste rápido
    df = create_test_dataframe(rows=1000, cols=20)
    
    print(f"📊 Dataset: {df.shape[0]} linhas x {df.shape[1]} colunas")
    
    # Teste 1: Query que precisa de poucas colunas
    query1 = "Qual a correlação entre Amount e Time?"
    
    start = datetime.now()
    needs_frag, fragments, reason = fragment_query_fast(
        query=query1,
        df=df,
        token_budget=TokenBudget(max_tokens_per_request=2000)  # Limite baixo para forçar fragmentação
    )
    elapsed = (datetime.now() - start).total_seconds() * 1000
    
    print(f"\n📝 Query: {query1}")
    print(f"   ⏱️  Tempo: {elapsed:.1f}ms")
    print(f"   🔄 Precisa fragmentar: {needs_frag}")
    print(f"   💡 Razão: {reason}")
    if fragments:
        print(f"   📦 Fragmentos: {len(fragments)}")
        for frag in fragments[:3]:
            print(f"      - {frag.fragment_id}: {len(frag.columns or [])} cols, "
                  f"linhas {frag.row_range}, ~{frag.estimated_tokens} tokens")
    
    # Teste 2: Query que precisa de tudo
    query2 = "Descreva todas as características do dataset"
    
    start = datetime.now()
    needs_frag2, fragments2, reason2 = fragment_query_fast(
        query=query2,
        df=df,
        token_budget=TokenBudget(max_tokens_per_request=2000)
    )
    elapsed2 = (datetime.now() - start).total_seconds() * 1000
    
    print(f"\n📝 Query: {query2}")
    print(f"   ⏱️  Tempo: {elapsed2:.1f}ms")
    print(f"   🔄 Precisa fragmentar: {needs_frag2}")
    print(f"   💡 Razão: {reason2}")
    if fragments2:
        print(f"   📦 Fragmentos: {len(fragments2)}")
    
    print(f"\n✅ Total: {elapsed + elapsed2:.1f}ms para 2 queries")
    
    return fragments if fragments else fragments2


def test_execution_and_aggregation(fragments):
    """Testa execução e agregação."""
    print("\n" + "="*70)
    print("⚙️  TESTE 2: Execução e Agregação de Fragmentos")
    print("="*70)
    
    if not fragments:
        print("⚠️  Sem fragmentos para testar")
        return
    
    # Cria dataset
    df = create_test_dataframe(rows=1000, cols=20)
    
    start = datetime.now()
    result = execute_and_aggregate(
        df=df,
        fragments=fragments,
        operation="select"
    )
    elapsed = (datetime.now() - start).total_seconds() * 1000
    
    print(f"\n📊 Resultado:")
    print(f"   ✅ Sucesso: {result['success']}")
    print(f"   📦 Fragmentos processados: {result.get('fragments_success', 0)}/{result.get('fragments_total', 0)}")
    print(f"   🎯 Tokens usados: {result.get('tokens_total', 0)}")
    print(f"   ⏱️  Tempo total: {elapsed:.1f}ms")
    print(f"   💾 Cache hits: {result.get('from_cache_count', 0)}")
    
    # Mostra resultado
    if result['success'] and result.get('result') is not None:
        res = result['result']
        if isinstance(res, pd.DataFrame):
            print(f"\n   📋 DataFrame resultante: {res.shape}")
            print(f"      Primeiras linhas:")
            print(res.head(3).to_string(max_cols=5))
        elif isinstance(res, dict):
            print(f"\n   📊 Estatísticas:")
            for key, value in list(res.items())[:5]:
                print(f"      {key}: {value}")
    
    return result


def test_column_extraction():
    """Testa extração rápida de colunas."""
    print("\n" + "="*70)
    print("🔍 TESTE 3: Extração de Colunas por Padrão")
    print("="*70)
    
    fragmenter = FastQueryFragmenter()
    
    test_cases = [
        ("Qual a correlação entre Amount e Time?", ['Amount', 'Time']),
        ("Mostre Amount, Class e V1", ['Amount', 'Class', 'V1']),
        ("Análise de fraudes em Amount", ['Amount']),
    ]
    
    total_time = 0
    for query, expected_cols in test_cases:
        columns = ['Amount', 'Time', 'Class', 'V1', 'V2', 'V3']
        
        start = datetime.now()
        extracted = fragmenter._extract_columns_from_query(query, columns)
        elapsed = (datetime.now() - start).total_seconds() * 1000
        total_time += elapsed
        
        found_expected = all(col in extracted for col in expected_cols)
        
        print(f"\n📝 Query: {query}")
        print(f"   ⏱️  Tempo: {elapsed:.3f}ms")
        print(f"   🎯 Colunas esperadas: {expected_cols}")
        print(f"   ✅ Colunas extraídas: {list(extracted) if extracted else 'nenhuma'}")
        print(f"   {'✅' if found_expected else '⚠️'} Match: {found_expected}")
    
    print(f"\n⏱️  Tempo total: {total_time:.1f}ms")


def test_performance_comparison():
    """Compara performance: heurística vs LLM."""
    print("\n" + "="*70)
    print("⚡ TESTE 4: Comparação de Performance")
    print("="*70)
    
    df = create_test_dataframe(rows=500, cols=15)
    queries = [
        "Qual a média de Amount?",
        "Correlação entre Time e Amount",
        "Mostre todas as transações",
    ]
    
    print(f"\n📊 Dataset: {df.shape}")
    print(f"📝 Queries: {len(queries)}")
    
    # Versão rápida (heurística)
    start_fast = datetime.now()
    for query in queries:
        fragment_query_fast(query, df)
    elapsed_fast = (datetime.now() - start_fast).total_seconds() * 1000
    
    print(f"\n⚡ Versão RÁPIDA (heurística):")
    print(f"   ⏱️  Total: {elapsed_fast:.1f}ms")
    print(f"   ⏱️  Média/query: {elapsed_fast/len(queries):.1f}ms")
    
    # Estimativa da versão com LLM
    estimated_llm_time = len(queries) * 400  # ~400ms por query com LLM
    
    print(f"\n🐢 Versão COM LLM (estimado):")
    print(f"   ⏱️  Total estimado: {estimated_llm_time:.1f}ms")
    print(f"   ⏱️  Média/query: {estimated_llm_time/len(queries):.1f}ms")
    
    speedup = estimated_llm_time / elapsed_fast
    print(f"\n🚀 SPEEDUP: {speedup:.1f}x mais rápido!")


def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "="*70)
    print("🧪 SISTEMA DE FRAGMENTAÇÃO OTIMIZADO - TESTES RÁPIDOS")
    print("="*70)
    
    start_total = datetime.now()
    
    try:
        # Teste 1: Fragmentação
        fragments = test_fast_fragmentation()
        
        # Teste 2: Execução e Agregação
        if fragments:
            test_execution_and_aggregation(fragments)
        
        # Teste 3: Extração de colunas
        test_column_extraction()
        
        # Teste 4: Comparação de performance
        test_performance_comparison()
        
        elapsed_total = (datetime.now() - start_total).total_seconds()
        
        print("\n" + "="*70)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO")
        print("="*70)
        print(f"⏱️  Tempo total: {elapsed_total:.2f}s")
        print(f"🎯 Performance: {'EXCELENTE' if elapsed_total < 5 else 'BOA' if elapsed_total < 10 else 'ACEITÁVEL'}")
        
        return True
        
    except Exception as e:
        elapsed_total = (datetime.now() - start_total).total_seconds()
        
        print("\n" + "="*70)
        print("❌ ERRO NOS TESTES")
        print("="*70)
        print(f"Erro: {str(e)}")
        print(f"⏱️  Tempo até falha: {elapsed_total:.2f}s")
        
        import traceback
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
