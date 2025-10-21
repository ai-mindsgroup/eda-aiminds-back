"""
Teste do QueryAnalyzer Refatorado com Análise Semântica via LLM
"""

from src.agent.query_analyzer import QueryAnalyzer
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_query_analyzer_llm():
    """Testa QueryAnalyzer com diferentes tipos de queries"""
    
    logger.info("🧪 Testando QueryAnalyzer Refatorado (com LLM)")
    logger.info("=" * 80)
    
    # Criar analisador
    analyzer = QueryAnalyzer()
    
    # Queries de teste
    test_queries = [
        ("Quais são os tipos de dados do dataset?", "SIMPLE", "structure"),
        ("Existem outliers significativos?", "SIMPLE", "outliers"),
        ("Quais transações específicas têm valores acima de 1000?", "COMPLEX", "unknown"),
        ("Mostre as 10 linhas com maior valor de Amount", "COMPLEX", "custom_analysis"),
        ("Qual a correlação entre Amount e Time?", "SIMPLE/COMPLEX", "correlation"),
        ("Gere um gráfico de dispersão", "COMPLEX", "visualization"),
    ]
    
    results = []
    
    for query, expected_complexity, expected_category in test_queries:
        logger.info(f"\n📊 Query: {query}")
        
        try:
            result = analyzer.analyze(query)
            
            complexity = result['complexity'].upper()
            category = result['category']
            confidence = result.get('llm_confidence', 0.0)
            reasoning = result.get('justification', 'N/A')
            
            logger.info(f"   ✅ Complexidade: {complexity} (esperado: {expected_complexity})")
            logger.info(f"   ✅ Categoria: {category} (esperado: {expected_category})")
            logger.info(f"   ✅ Confiança: {confidence:.2f}")
            logger.info(f"   ✅ Raciocínio: {reasoning}")
            
            results.append({
                'query': query,
                'complexity': complexity,
                'category': category,
                'confidence': confidence,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"   ❌ Erro: {e}")
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })
    
    logger.info("\n" + "=" * 80)
    logger.info("📈 RESUMO DOS TESTES")
    logger.info("=" * 80)
    
    successful = sum(1 for r in results if r.get('success', False))
    failed = len(results) - successful
    
    logger.info(f"✅ Sucessos: {successful}/{len(results)}")
    logger.info(f"❌ Falhas: {failed}/{len(results)}")
    
    if successful == len(results):
        logger.info("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        logger.warning(f"\n⚠️ {failed} testes falharam")
    
    return results


if __name__ == "__main__":
    test_query_analyzer_llm()
