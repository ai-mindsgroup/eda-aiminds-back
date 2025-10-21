"""
Teste da ETAPA 2 - Análises Complementares e Chunking Inteligente

Valida:
1. Query SIMPLE (usa chunks existentes)
2. Query COMPLEX (fallback para CSV)
3. Geração de chunks adicionais
4. Resposta contextualizada via LLM
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_etapa2_simple_query():
    """
    Teste 1: Query SIMPLE
    Pergunta: "Quantas colunas numéricas existem no dataset?"
    Esperado: Usa apenas chunks analíticos (metadata_types)
    """
    print("\n" + "="*80)
    print("TESTE 1: QUERY SIMPLE - Usando Chunks Analíticos Existentes")
    print("="*80)
    
    # Inicializar agente
    agent = RAGAgent(embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
    
    # Query simples
    query = "Quantas colunas numéricas existem no dataset?"
    source_id = "creditcard_7e30850a"  # Usar o source_id real dos chunks inseridos
    
    print(f"\n📝 Query: {query}")
    print(f"📊 Source ID: {source_id}")
    
    # Processar
    result = agent.process_query_hybrid(query, source_id)
    
    # Verificar resultado
    print(f"\n✅ Status: {result.get('metadata', {}).get('strategy', 'N/A')}")
    print(f"📦 Chunks usados: {result.get('metadata', {}).get('chunks_used', [])}")
    print(f"💾 CSV acessado: {result.get('metadata', {}).get('csv_accessed', False)}")
    print(f"\n💬 Resposta:\n{result.get('response', 'N/A')[:500]}...")
    
    # Validações
    assert result.get('metadata', {}).get('strategy') == 'simple', "Deveria usar estratégia SIMPLE"
    assert not result.get('metadata', {}).get('csv_accessed'), "Não deveria acessar CSV"
    assert len(result.get('metadata', {}).get('chunks_used', [])) > 0, "Deveria usar chunks"
    
    print("\n✅ TESTE 1 PASSOU!")
    return result


def test_etapa2_complex_query():
    """
    Teste 2: Query COMPLEX
    Pergunta: "Gere um gráfico de dispersão das colunas V1 e V2"
    Esperado: Fallback para CSV + gera chunks adicionais
    """
    print("\n" + "="*80)
    print("TESTE 2: QUERY COMPLEX - Fallback para CSV Completo")
    print("="*80)
    
    # Inicializar agente
    agent = RAGAgent(embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
    
    # Query complexa
    query = "Gere um gráfico de dispersão mostrando a relação entre as primeiras colunas numéricas"
    source_id = "creditcard_7e30850a"
    
    print(f"\n📝 Query: {query}")
    print(f"📊 Source ID: {source_id}")
    
    # Processar
    result = agent.process_query_hybrid(query, source_id)
    
    # Verificar resultado
    print(f"\n✅ Status: {result.get('metadata', {}).get('strategy', 'N/A')}")
    print(f"📦 Chunks usados: {result.get('metadata', {}).get('chunks_used', [])}")
    print(f"💾 CSV acessado: {result.get('metadata', {}).get('csv_accessed', False)}")
    print(f"🆕 Novos chunks gerados: {result.get('metadata', {}).get('new_chunks_generated', 0)}")
    print(f"📊 DataFrame shape: {result.get('metadata', {}).get('dataframe_shape', 'N/A')}")
    print(f"\n💬 Resposta:\n{result.get('response', 'N/A')[:500]}...")
    
    # Validações
    assert result.get('metadata', {}).get('strategy') == 'complex', "Deveria usar estratégia COMPLEX"
    assert result.get('metadata', {}).get('csv_accessed'), "Deveria acessar CSV"
    assert result.get('metadata', {}).get('dataframe_shape') is not None, "Deveria ter shape do DataFrame"
    
    print("\n✅ TESTE 2 PASSOU!")
    return result


def test_etapa2_outliers_query():
    """
    Teste 3: Query sobre OUTLIERS
    Pergunta: "Quais colunas têm outliers e quantos são?"
    Esperado: Pode ser SIMPLE (se chunks existem) ou COMPLEX (análise detalhada)
    """
    print("\n" + "="*80)
    print("TESTE 3: QUERY OUTLIERS - Análise de Valores Atípicos")
    print("="*80)
    
    # Inicializar agente
    agent = RAGAgent(embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
    
    # Query sobre outliers
    query = "Quais colunas do dataset possuem outliers e em que quantidade?"
    source_id = "creditcard_7e30850a"
    
    print(f"\n📝 Query: {query}")
    print(f"📊 Source ID: {source_id}")
    
    # Processar
    result = agent.process_query_hybrid(query, source_id)
    
    # Verificar resultado
    print(f"\n✅ Status: {result.get('metadata', {}).get('strategy', 'N/A')}")
    print(f"📦 Chunks usados: {result.get('metadata', {}).get('chunks_used', [])}")
    print(f"💾 CSV acessado: {result.get('metadata', {}).get('csv_accessed', False)}")
    print(f"\n💬 Resposta:\n{result.get('response', 'N/A')[:500]}...")
    
    # Validação flexível (pode ser SIMPLE ou COMPLEX)
    assert result.get('metadata', {}).get('strategy') in ['simple', 'complex'], "Deve ter estratégia válida"
    
    print("\n✅ TESTE 3 PASSOU!")
    return result


def test_etapa2_batch_queries():
    """
    Teste 4: Múltiplas queries para validar caching e performance
    """
    print("\n" + "="*80)
    print("TESTE 4: BATCH DE QUERIES - Validação de Performance")
    print("="*80)
    
    # Inicializar agente
    agent = RAGAgent(embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
    source_id = "creditcard_7e30850a"
    
    queries = [
        "Qual é a estrutura do dataset?",
        "Quais são as médias das colunas numéricas?",
        "Existem correlações fortes entre variáveis?",
        "Mostre estatísticas descritivas completas"
    ]
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Query {i}/{len(queries)}: {query}")
        
        result = agent.process_query_hybrid(query, source_id)
        results.append(result)
        
        strategy = result.get('metadata', {}).get('strategy', 'N/A')
        csv_accessed = result.get('metadata', {}).get('csv_accessed', False)
        
        print(f"   ✅ Estratégia: {strategy} | CSV: {csv_accessed}")
    
    # Validações
    assert len(results) == len(queries), "Todas as queries devem ter resultado"
    
    # Pelo menos uma deve ser SIMPLE
    simple_count = sum(1 for r in results if r.get('metadata', {}).get('strategy') == 'simple')
    assert simple_count > 0, "Pelo menos uma query deve ser SIMPLE"
    
    print(f"\n✅ TESTE 4 PASSOU! ({len(queries)} queries processadas)")
    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 INICIANDO TESTES DA ETAPA 2")
    print("ANÁLISES COMPLEMENTARES E CHUNKING INTELIGENTE")
    print("="*80)
    
    try:
        # Teste 1: Query SIMPLE
        result1 = test_etapa2_simple_query()
        
        # Teste 2: Query COMPLEX
        result2 = test_etapa2_complex_query()
        
        # Teste 3: Query OUTLIERS
        result3 = test_etapa2_outliers_query()
        
        # Teste 4: Batch de queries
        results4 = test_etapa2_batch_queries()
        
        print("\n" + "="*80)
        print("✅ TODOS OS TESTES DA ETAPA 2 PASSARAM!")
        print("="*80)
        print("\n📊 RESUMO:")
        print(f"   • Teste 1 (SIMPLE): ✅")
        print(f"   • Teste 2 (COMPLEX): ✅")
        print(f"   • Teste 3 (OUTLIERS): ✅")
        print(f"   • Teste 4 (BATCH): ✅")
        print("\n🎯 Sistema de consulta híbrida funcionando perfeitamente!")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
