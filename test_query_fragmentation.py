"""
Teste do Sistema de Fragmentação Inteligente de Queries
=======================================================

Valida fragmentação, cache, agregação e controle de tokens.

Autor: Sistema Multiagente EDA AI Minds
Data: 2025-01-20
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime

from src.llm.smart_query_processor import SmartQueryProcessor
from src.llm.query_fragmentation import TokenBudget
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def create_large_dataset(num_rows: int = 100000, num_cols: int = 30) -> pd.DataFrame:
    """Cria dataset grande para testar fragmentação."""
    np.random.seed(42)
    
    data = {}
    for i in range(num_cols):
        if i % 3 == 0:
            data[f'col_{i}'] = np.random.randint(0, 1000, num_rows)
        elif i % 3 == 1:
            data[f'col_{i}'] = np.random.randn(num_rows)
        else:
            data[f'col_{i}'] = np.random.choice(['A', 'B', 'C', 'D'], num_rows)
    
    df = pd.DataFrame(data)
    logger.info(f"✅ Dataset criado: {df.shape[0]} linhas, {df.shape[1]} colunas")
    
    return df


async def test_basic_fragmentation():
    """Testa fragmentação básica de query grande."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 1: Fragmentação Básica")
    logger.info("="*80)
    
    # Cria dataset grande
    df = create_large_dataset(num_rows=50000, num_cols=25)
    
    # Processa query
    processor = SmartQueryProcessor(
        session_id="test_session_1",
        token_budget=TokenBudget(max_tokens_per_request=3000),  # Limite menor para forçar fragmentação
        use_cache=False  # Desabilita cache para teste limpo
    )
    
    query = "Analise estatísticas descritivas completas de todas as colunas"
    
    result = await processor.process(query, df)
    
    # Validações
    assert result['success'], "Processamento deve ter sucesso"
    assert result['metrics']['total_fragments'] > 1, "Deve criar múltiplos fragmentos"
    
    logger.info("\n✅ TESTE 1 PASSOU")
    logger.info(f"   Fragmentos criados: {result['metrics']['total_fragments']}")
    logger.info(f"   Tempo total: {result['total_processing_time_seconds']:.2f}s")
    
    return result


async def test_column_selection():
    """Testa seleção inteligente de colunas."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 2: Seleção de Colunas")
    logger.info("="*80)
    
    df = create_large_dataset(num_rows=10000, num_cols=50)
    
    processor = SmartQueryProcessor(
        session_id="test_session_2",
        use_cache=False
    )
    
    # Query que precisa apenas de 2 colunas específicas
    query = "Qual a correlação entre col_0 e col_1?"
    
    result = await processor.process(query, df)
    
    assert result['success'], "Processamento deve ter sucesso"
    
    logger.info("\n✅ TESTE 2 PASSOU")
    logger.info(f"   Resposta: {result.get('response', '')[:100]}...")
    
    return result


async def test_cache_effectiveness():
    """Testa efetividade do cache."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 3: Cache de Fragmentos")
    logger.info("="*80)
    
    df = create_large_dataset(num_rows=30000, num_cols=20)
    
    processor = SmartQueryProcessor(
        session_id="test_session_3",
        token_budget=TokenBudget(max_tokens_per_request=3000),
        use_cache=True  # Habilita cache
    )
    
    query = "Mostre estatísticas gerais do dataset"
    
    # Primeira execução - sem cache
    logger.info("\n📊 Primeira execução (sem cache)...")
    result1 = await processor.process(query, df)
    time1 = result1['total_processing_time_seconds']
    cache_hits1 = result1['metrics']['cache_hits']
    
    # Segunda execução - com cache
    logger.info("\n📊 Segunda execução (com cache)...")
    result2 = await processor.process(query, df)
    time2 = result2['total_processing_time_seconds']
    cache_hits2 = result2['metrics']['cache_hits']
    
    # Validações
    assert result1['success'] and result2['success'], "Ambas devem ter sucesso"
    assert cache_hits2 > cache_hits1, "Segunda execução deve ter mais cache hits"
    
    logger.info("\n✅ TESTE 3 PASSOU")
    logger.info(f"   Primeira execução: {time1:.2f}s, cache hits: {cache_hits1}")
    logger.info(f"   Segunda execução: {time2:.2f}s, cache hits: {cache_hits2}")
    logger.info(f"   Speedup: {time1/time2:.2f}x" if time2 > 0 else "   Speedup: ∞")
    
    return result1, result2


async def test_token_budget_control():
    """Testa controle rigoroso de orçamento de tokens."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 4: Controle de Tokens")
    logger.info("="*80)
    
    df = create_large_dataset(num_rows=100000, num_cols=40)
    
    # Orçamento muito restritivo
    strict_budget = TokenBudget(
        max_tokens_per_request=2000,
        reserved_tokens=300,
        safety_margin=100
    )
    
    processor = SmartQueryProcessor(
        session_id="test_session_4",
        token_budget=strict_budget,
        use_cache=False
    )
    
    query = "Analise todo o dataset em detalhes"
    
    result = await processor.process(query, df)
    
    # Validações
    assert result['success'], "Deve processar mesmo com orçamento restrito"
    assert result['metrics']['total_fragments'] > 5, "Deve criar muitos fragmentos"
    
    logger.info("\n✅ TESTE 4 PASSOU")
    logger.info(f"   Orçamento: {strict_budget.available_tokens} tokens")
    logger.info(f"   Fragmentos criados: {result['metrics']['total_fragments']}")
    logger.info(f"   Tokens usados: {result['metrics']['total_tokens_used']}")
    
    return result


async def test_small_query_no_fragmentation():
    """Testa que queries pequenas não são fragmentadas."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 5: Query Pequena (Sem Fragmentação)")
    logger.info("="*80)
    
    # Dataset pequeno
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50],
        'C': ['x', 'y', 'z', 'w', 'v']
    })
    
    processor = SmartQueryProcessor(
        session_id="test_session_5",
        use_cache=False
    )
    
    query = "Qual a média da coluna A?"
    
    result = await processor.process(query, df)
    
    # Validações
    assert result['success'], "Processamento deve ter sucesso"
    assert result['metrics']['total_fragments'] == 0, "Não deve fragmentar query pequena"
    
    logger.info("\n✅ TESTE 5 PASSOU")
    logger.info(f"   Dataset: {df.shape}")
    logger.info(f"   Fragmentos: {result['metrics']['total_fragments']} (esperado 0)")
    
    return result


async def run_all_tests():
    """Executa todos os testes."""
    logger.info("\n" + "="*100)
    logger.info("🚀 INICIANDO BATERIA DE TESTES - Sistema de Fragmentação Inteligente")
    logger.info("="*100)
    
    start_time = datetime.now()
    
    try:
        # Teste 1: Fragmentação básica
        await test_basic_fragmentation()
        
        # Teste 2: Seleção de colunas
        await test_column_selection()
        
        # Teste 3: Cache
        await test_cache_effectiveness()
        
        # Teste 4: Controle de tokens
        await test_token_budget_control()
        
        # Teste 5: Query pequena
        await test_small_query_no_fragmentation()
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "="*100)
        logger.info("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        logger.info(f"⏱️  Tempo total: {total_time:.2f}s")
        logger.info("="*100 + "\n")
        
        return True
        
    except AssertionError as e:
        logger.error(f"\n❌ TESTE FALHOU: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"\n💥 ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Executa testes
    success = asyncio.run(run_all_tests())
    
    exit(0 if success else 1)
