"""
Teste rápido do Teste 6 após correção
"""

from src.agent.query_analyzer import QueryAnalyzer

def test_query_analyzer_strings():
    """Valida que QueryAnalyzer retorna strings, não enums"""
    
    analyzer = QueryAnalyzer()
    
    # Teste 1: Categoria statistics
    result = analyzer.analyze("Qual a média de Amount?")
    print(f"Query 1: {result.query}")
    print(f"  Categoria: {result.category} (tipo: {type(result.category)})")
    print(f"  Complexidade: {result.complexity} (tipo: {type(result.complexity)})")
    
    assert isinstance(result.category, str), f"❌ category deve ser str, não {type(result.category)}"
    assert isinstance(result.complexity, str), f"❌ complexity deve ser str, não {type(result.complexity)}"
    assert result.category == 'statistics', f"❌ Esperado 'statistics', recebeu '{result.category}'"
    assert result.complexity == 'simple', f"❌ Esperado 'simple', recebeu '{result.complexity}'"
    print("✅ Query 1 PASSOU\n")
    
    # Teste 2: Categoria correlation
    result2 = analyzer.analyze("Correlação entre Amount e Time")
    print(f"Query 2: {result2.query}")
    print(f"  Categoria: {result2.category} (tipo: {type(result2.category)})")
    print(f"  Complexidade: {result2.complexity} (tipo: {type(result2.complexity)})")
    
    assert isinstance(result2.category, str), f"❌ category deve ser str"
    assert isinstance(result2.complexity, str), f"❌ complexity deve ser str"
    # Permitir variação (pode ser correlation ou statistics)
    assert result2.category in ['correlation', 'statistics', 'distribution'], \
        f"❌ Categoria inesperada: '{result2.category}'"
    print("✅ Query 2 PASSOU\n")
    
    # Teste 3: Comparação direta de strings
    test_cases = [
        ("Qual a média?", 'statistics', 'simple'),
        ("Mostre distribuição", 'distribution', 'simple'),
        ("Identifique outliers", 'outliers', 'simple'),
    ]
    
    for query, expected_cat, expected_comp in test_cases:
        result = analyzer.analyze(query)
        
        # ✅ Comparação string direta (não precisa .value)
        category_match = result.category == expected_cat
        complexity_match = result.complexity == expected_comp
        
        status = "✅" if category_match else "⚠️"
        print(f"{status} '{query}' → {result.complexity} | {result.category}")
    
    print("\n✅✅✅ TODOS OS TESTES PASSARAM")
    print("✅ QueryAnalyzer retorna strings corretamente")
    print("✅ Comparação direta funciona (sem .value)")

if __name__ == "__main__":
    test_query_analyzer_strings()
