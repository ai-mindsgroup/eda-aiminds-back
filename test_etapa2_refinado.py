"""
Teste de Validação - ETAPA 2 REFINADA: Fallback Guiado com Chunks como Referência

OBJETIVO:
Validar que o sistema:
1. Identifica corretamente SIMPLE vs COMPLEX queries
2. Prioriza chunks existentes (6 metadata analíticos)
3. Faz fallback GUIADO ao CSV apenas quando necessário
4. Evita duplicação de análises (usa chunks como guia)
5. Gera chunks complementares somente para gaps

CENÁRIOS TESTADOS:
- SIMPLE: Usa APENAS chunks existentes (sem CSV)
- COMPLEX GUIDED: Usa chunks como GUIA + CSV complementar
- Análise de gaps: Identifica o que falta e complementa
- Batch: Comportamento consistente em queries variadas
"""

import pytest
from pathlib import Path

from src.agent.rag_agent import RAGAgent
from src.agent.query_analyzer import QueryAnalyzer, QueryComplexity
from src.agent.hybrid_query_processor import HybridQueryProcessor
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator
from src.utils.logging_config import get_logger

logger = get_logger("test_etapa2_refinado")


def test_etapa2_simple_query():
    """
    Teste 1: Query SIMPLE deve usar APENAS chunks existentes (sem CSV).
    """
    logger.info("="*80)
    logger.info("TESTE 1: SIMPLE Query - Prioriza Chunks Existentes")
    logger.info("="*80)
    
    # Query simples que pode ser respondida com chunks existentes
    query = "Quais são os tipos de dados do dataset?"
    
    # Configurar agente (sem parâmetro llm_provider)
    rag_agent = RAGAgent()
    
    # Processar query com estratégia híbrida
    # NOTA: source_id correto após ingestão: creditcard_ec8721dc
    result = rag_agent.process_query_hybrid(query, source_id="creditcard_ec8721dc")
    
    # Validações
    assert result['status'] == 'success', "Falha no processamento da query"
    assert result['strategy'] == 'simple', "Deveria usar estratégia SIMPLE"
    assert result.get('csv_accessed') == False, "❌ FALHA: CSV foi acessado quando NÃO deveria!"
    assert len(result.get('chunks_used', [])) > 0, "Nenhum chunk foi usado"
    
    logger.info(f"✅ TESTE 1 PASSOU: Strategy={result['strategy']}, CSV Accessed={result.get('csv_accessed')}")
    logger.info(f"   Chunks usados: {result.get('chunks_used')}")
    logger.info(f"   Contexto gerado: {len(result.get('context', ''))} caracteres")


def test_etapa2_complex_query_with_guide():
    """
    Teste 2: Query COMPLEX deve usar chunks como GUIA + CSV complementar.
    """
    logger.info("="*80)
    logger.info("TESTE 2: COMPLEX Query - Fallback Guiado com Chunks")
    logger.info("="*80)
    
    # Query complexa que requer análise detalhada
    query = "Quais transações específicas têm valores acima de 1000 e são suspeitas de fraude?"
    
    rag_agent = RAGAgent()
    result = rag_agent.process_query_hybrid(query, source_id="creditcard_ec8721dc")
    
    # Validações
    assert result['status'] == 'success', "Falha no processamento"
    assert result['strategy'] == 'complex_guided', "Deveria usar estratégia COMPLEX GUIDED"
    assert result.get('csv_accessed') == True, "CSV deveria ser acessado"
    
    # Validar que chunks foram usados PRIMEIRO
    assert 'covered_aspects' in result, "Deveria identificar aspectos cobertos"
    assert 'required_gaps' in result, "Deveria identificar gaps"
    
    logger.info(f"✅ TESTE 2 PASSOU: Strategy={result['strategy']}, CSV Accessed={result.get('csv_accessed')}")
    logger.info(f"   Aspectos cobertos: {result.get('covered_aspects')}")
    logger.info(f"   Gaps identificados: {result.get('required_gaps')}")
    logger.info(f"   Chunks complementares gerados: {result.get('new_chunks_generated')}")


def test_etapa2_outliers_query():
    """
    Teste 3: Query sobre outliers deve verificar se chunks existentes cobrem ou requerem CSV.
    """
    logger.info("="*80)
    logger.info("TESTE 3: Outliers Query - Verificação de Cobertura")
    logger.info("="*80)
    
    query = "Existem outliers significativos no dataset?"
    
    rag_agent = RAGAgent()
    result = rag_agent.process_query_hybrid(query, source_id="creditcard_ec8721dc")
    
    # Validações
    assert result['status'] == 'success', "Falha no processamento"
    
    # Se chunk 'metadata_frequency_outliers' existe → deveria ser SIMPLE
    # Se não existe ou insuficiente → deveria ser COMPLEX com fallback
    
    if result['strategy'] == 'simple':
        logger.info("✅ Chunk de outliers existente é suficiente - Sem CSV")
        assert result.get('csv_accessed') == False
    
    elif result['strategy'] == 'complex_guided':
        logger.info("✅ Fallback guiado ativado - Análise complementar")
        assert result.get('csv_accessed') == True
        assert 'outliers' in result.get('covered_aspects', []) or 'outliers' in result.get('required_gaps', [])
    
    logger.info(f"   Strategy: {result['strategy']}")
    logger.info(f"   Chunks usados: {result.get('chunks_used')}")


def test_etapa2_batch_queries():
    """
    Teste 4: Batch de queries variadas para validar comportamento consistente.
    """
    logger.info("="*80)
    logger.info("TESTE 4: Batch de Queries Variadas")
    logger.info("="*80)
    
    queries = [
        "Quantas colunas tem o dataset?",  # SIMPLE
        "Qual a correlação entre Amount e Time?",  # COMPLEX (se não tem chunk de correlação)
        "Mostre estatísticas descritivas completas",  # SIMPLE (chunk de central_variability)
        "Identifique padrões temporais suspeitos"  # COMPLEX (análise temporal avançada)
    ]
    
    rag_agent = RAGAgent()
    
    results = []
    for i, query in enumerate(queries, 1):
        logger.info(f"\n--- Query {i}: {query}")
        
        result = rag_agent.process_query_hybrid(query, source_id="creditcard_ec8721dc")
        
        logger.info(f"   Strategy: {result['strategy']}")
        logger.info(f"   CSV Accessed: {result.get('csv_accessed')}")
        logger.info(f"   Chunks Used: {result.get('chunks_used')}")
        
        results.append({
            'query': query,
            'strategy': result['strategy'],
            'csv_accessed': result.get('csv_accessed'),
            'chunks_used': len(result.get('chunks_used', []))
        })
    
    # Validações
    assert all(r['chunks_used'] > 0 for r in results), "Todas as queries devem usar chunks"
    
    # Pelo menos 1 query deve ser SIMPLE (sem CSV)
    simple_count = sum(1 for r in results if r['strategy'] == 'simple')
    assert simple_count >= 1, "Pelo menos 1 query deveria ser SIMPLE"
    
    logger.info("\n✅ TESTE 4 PASSOU: Comportamento consistente em batch")
    logger.info(f"   SIMPLE queries: {simple_count}")
    logger.info(f"   COMPLEX queries: {len(results) - simple_count}")


def test_etapa2_avoid_duplication():
    """
    Teste 5: Sistema deve EVITAR duplicação de análises (usar chunks como guia).
    """
    logger.info("="*80)
    logger.info("TESTE 5: Verificação de Não-Duplicação de Análises")
    logger.info("="*80)
    
    # Query que poderia gerar análise duplicada
    query = "Calcule estatísticas descritivas das variáveis numéricas"
    
    rag_agent = RAGAgent()
    result = rag_agent.process_query_hybrid(query, source_id="creditcard_ec8721dc")
    
    # Validações
    assert result['status'] == 'success'
    
    # Se chunk de estatísticas existe (metadata_central_variability) → SIMPLE
    if result['strategy'] == 'simple':
        logger.info("✅ Chunk de estatísticas já existe - Sem duplicação")
        assert result.get('csv_accessed') == False
        assert result.get('new_chunks_generated', 0) == 0
    
    # Se fallback ativado → deve identificar cobertura e complementar SOMENTE gaps
    elif result['strategy'] == 'complex_guided':
        logger.info("✅ Fallback guiado - Complementa SOMENTE gaps")
        covered = result.get('covered_aspects', [])
        assert 'statistics' in covered or 'central_tendency' in covered, "Deveria identificar estatísticas já cobertas"
    
    logger.info(f"   Strategy: {result['strategy']}")
    logger.info(f"   Covered Aspects: {result.get('covered_aspects')}")
    logger.info(f"   Required Gaps: {result.get('required_gaps')}")


if __name__ == "__main__":
    logger.info("🚀 Iniciando Testes - ETAPA 2 REFINADA: Fallback Guiado\n")
    
    try:
        test_etapa2_simple_query()
        print("\n")
        
        test_etapa2_complex_query_with_guide()
        print("\n")
        
        test_etapa2_outliers_query()
        print("\n")
        
        test_etapa2_batch_queries()
        print("\n")
        
        test_etapa2_avoid_duplication()
        
        logger.info("\n" + "="*80)
        logger.info("🎉 TODOS OS TESTES PASSARAM - ETAPA 2 REFINADA VALIDADA!")
        logger.info("="*80)
        logger.info("\nCONCLUSÕES:")
        logger.info("✅ Sistema identifica corretamente SIMPLE vs COMPLEX")
        logger.info("✅ Prioriza chunks existentes (6 metadata analíticos)")
        logger.info("✅ Fallback guiado usa chunks como referência")
        logger.info("✅ Evita duplicação de análises")
        logger.info("✅ Gera chunks complementares apenas para gaps")
    
    except AssertionError as e:
        logger.error(f"\n❌ TESTE FALHOU: {e}")
        raise
    
    except Exception as e:
        logger.error(f"\n❌ ERRO INESPERADO: {e}")
        raise

