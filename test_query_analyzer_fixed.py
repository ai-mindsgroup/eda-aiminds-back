"""
Teste para validar correção do QueryAnalyzer
✅ Agora retorna objetos QueryAnalysis em vez de dict
✅ Mantém compatibilidade retroativa com acesso por dict
"""

import sys
import asyncio
from src.agent.query_analyzer import QueryAnalyzer, QueryAnalysis, QueryStrategy

def test_basic_analysis():
    """Testa análise básica retorna objeto"""
    print("=" * 80)
    print("TESTE 1: Análise básica retorna objeto QueryAnalysis")
    print("=" * 80)
    
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Qual a média de Amount?")
    
    # ✅ DEVE SER OBJETO
    print(f"Tipo retornado: {type(result)}")
    assert isinstance(result, QueryAnalysis), f"❌ Esperado QueryAnalysis, recebeu {type(result)}"
    print("✅ PASSOU: Retorna objeto QueryAnalysis")
    
    # ✅ ACESSO POR ATRIBUTO
    print(f"\n📊 Análise via atributo:")
    print(f"   result.category = {result.category}")
    print(f"   result.complexity = {result.complexity}")
    print(f"   result.requires_csv = {result.requires_csv}")
    assert hasattr(result, 'category'), "❌ Objeto não tem atributo 'category'"
    print("✅ PASSOU: Acesso por atributo funciona")
    
    # ✅ COMPATIBILIDADE: ACESSO POR DICT
    print(f"\n📊 Análise via dict (compatibilidade):")
    print(f"   result['category'] = {result['category']}")
    print(f"   result['complexity'] = {result['complexity']}")
    print(f"   result['requires_csv'] = {result['requires_csv']}")
    assert result['category'] == result.category, "❌ Acesso dict != atributo"
    print("✅ PASSOU: Acesso por dict mantém compatibilidade")
    
    # ✅ MÉTODO .get()
    print(f"\n📊 Método .get() (compatibilidade):")
    print(f"   result.get('category') = {result.get('category')}")
    print(f"   result.get('inexistente', 'default') = {result.get('inexistente', 'default')}")
    assert result.get('category') == result.category, "❌ .get() não funciona"
    print("✅ PASSOU: Método .get() funciona")
    
    print("\n✅✅✅ TESTE 1 PASSOU COMPLETAMENTE\n")


def test_strategy_object():
    """Testa que strategy também é objeto"""
    print("=" * 80)
    print("TESTE 2: QueryStrategy também é objeto tipado")
    print("=" * 80)
    
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Quais transações com Amount > 1000?")
    
    # ✅ STRATEGY DEVE SER OBJETO
    print(f"Tipo de strategy: {type(result.strategy)}")
    assert isinstance(result.strategy, QueryStrategy), f"❌ Esperado QueryStrategy, recebeu {type(result.strategy)}"
    print("✅ PASSOU: Strategy é objeto QueryStrategy")
    
    # ✅ ACESSO POR ATRIBUTO
    print(f"\n🎯 Strategy via atributo:")
    print(f"   result.strategy.action = {result.strategy.action}")
    print(f"   result.strategy.fallback_to_csv = {result.strategy.fallback_to_csv}")
    assert hasattr(result.strategy, 'action'), "❌ Strategy não tem atributo 'action'"
    print("✅ PASSOU: Strategy tem atributos")
    
    # ✅ COMPATIBILIDADE: ACESSO POR DICT
    print(f"\n🎯 Strategy via dict (compatibilidade):")
    print(f"   result.strategy['action'] = {result.strategy['action']}")
    print(f"   result['strategy']['action'] = {result['strategy']['action']}")
    assert result.strategy['action'] == result.strategy.action, "❌ Acesso dict != atributo"
    print("✅ PASSOU: Strategy mantém compatibilidade com dict")
    
    print("\n✅✅✅ TESTE 2 PASSOU COMPLETAMENTE\n")


def test_linguistic_variations():
    """Testa variações linguísticas (simula Teste 6 que falhava)"""
    print("=" * 80)
    print("TESTE 3: Variações Linguísticas (Simulação do Teste 6)")
    print("=" * 80)
    
    analyzer = QueryAnalyzer()
    
    test_queries = [
        "Calcule estatísticas da coluna Amount",
        "Me mostre a correlação entre variáveis",
        "Qual é a distribuição dos valores?",
        "Identifique outliers nos dados"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        result = analyzer.analyze(query)
        
        # ✅ NUNCA DEVE SER DICT
        assert not isinstance(result, dict) or isinstance(result, QueryAnalysis), \
            f"❌ Query {i}: retornou dict puro, não QueryAnalysis"
        
        # ✅ DEVE TER ATRIBUTO category
        try:
            category = result.category  # Acesso por atributo
            print(f"   ✅ Categoria (atributo): {category}")
        except AttributeError as e:
            print(f"   ❌ ERRO: {e}")
            raise
        
        # ✅ DEVE FUNCIONAR ACESSO POR DICT
        try:
            category_dict = result['category']  # Acesso por dict
            print(f"   ✅ Categoria (dict): {category_dict}")
        except (TypeError, KeyError) as e:
            print(f"   ❌ ERRO: {e}")
            raise
        
        assert category == category_dict, f"❌ Query {i}: atributo != dict"
    
    print("\n✅✅✅ TESTE 3 PASSOU COMPLETAMENTE")
    print("✅✅✅ CORREÇÃO DO TESTE 6 VALIDADA\n")


def test_to_dict_conversion():
    """Testa conversão para dict quando necessário"""
    print("=" * 80)
    print("TESTE 4: Conversão to_dict() para compatibilidade JSON")
    print("=" * 80)
    
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Média de Amount")
    
    # ✅ CONVERTER PARA DICT
    result_dict = result.to_dict()
    print(f"Tipo após to_dict(): {type(result_dict)}")
    assert isinstance(result_dict, dict), "❌ to_dict() não retornou dict"
    print("✅ PASSOU: to_dict() retorna dict puro")
    
    # ✅ VERIFICAR CAMPOS
    print(f"\n📋 Campos no dict:")
    for key in ['query', 'complexity', 'category', 'strategy']:
        print(f"   {key}: {result_dict.get(key)}")
        assert key in result_dict, f"❌ Campo '{key}' ausente"
    print("✅ PASSOU: Todos os campos presentes")
    
    # ✅ STRATEGY TAMBÉM DEVE SER DICT
    assert isinstance(result_dict['strategy'], dict), "❌ strategy não foi convertida para dict"
    print("✅ PASSOU: Strategy também convertida para dict")
    
    print("\n✅✅✅ TESTE 4 PASSOU COMPLETAMENTE\n")


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("VALIDAÇÃO COMPLETA: QueryAnalyzer retorna objetos tipados")
    print("Correção para Teste 6: 'dict' object has no attribute 'category'")
    print("🚀" * 40 + "\n")
    
    try:
        test_basic_analysis()
        test_strategy_object()
        test_linguistic_variations()
        test_to_dict_conversion()
        
        print("\n" + "=" * 80)
        print("✅✅✅ TODOS OS TESTES PASSARAM ✅✅✅")
        print("=" * 80)
        print("\n🎉 QueryAnalyzer agora retorna objetos QueryAnalysis tipados")
        print("🎉 Mantém 100% compatibilidade com código legado (acesso dict)")
        print("🎉 Teste 6 não terá mais erro: 'dict' has no attribute 'category'")
        print("\n✅ CORREÇÃO CRÍTICA VALIDADA COM SUCESSO\n")
        
    except Exception as e:
        print(f"\n❌❌❌ TESTE FALHOU: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
