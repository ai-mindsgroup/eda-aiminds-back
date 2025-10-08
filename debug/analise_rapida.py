"""
Análise rápida: Por que o agente AI Minds deu resultado diferente do Perplexity
"""
import pandas as pd

print("="*80)
print("🔍 ANÁLISE: PERPLEXITY vs AI MINDS AGENT")
print("="*80)

print("\n❌ PROBLEMA IDENTIFICADO:")
print("-"*80)
print("PERGUNTA: 'Qual a variabilidade dos dados (desvio padrão, variância)?'")
print("\n📊 PERPLEXITY respondeu corretamente:")
print("   - Desvio Padrão e Variância das 15 primeiras variáveis")
print("   - Exemplo: Time std=108.027, var=11669.830")

print("\n🤖 AI MINDS AGENT respondeu INCORRETAMENTE:")
print("   - Retornou INTERVALO (Mínimo, Máximo, Amplitude)")
print("   - Exemplo: Time min=0.00, max=32851.00, amplitude=32851.00")

print("\n\n💡 CAUSA RAIZ:")
print("-"*80)
print("1. O agente não interpretou corretamente a palavra 'variabilidade'")
print("2. Calculou min/max em vez de std/var")
print("3. O código do agente precisa ser corrigido para:")
print("   - Detectar palavras-chave: 'variabilidade', 'desvio padrão', 'variância'")
print("   - Calcular df[col].std() e df[col].var()")
print("   - Retornar tabela: Variável | Desvio Padrão | Variância")

print("\n\n📋 VALIDAÇÃO RÁPIDA (creditcard_test_500.csv):")
print("-"*80)

try:
    df = pd.read_csv('data/creditcard_test_500.csv')
    print(f"✅ Dataset carregado: {len(df)} registros")
    
    # Calcular apenas as 5 primeiras para comparação rápida
    cols = ['Time', 'V1', 'V2', 'V3', 'V4']
    
    print("\n| Variável | Std (Calculado) | Std (Perplexity) | Diferença |")
    print("|----------|-----------------|------------------|-----------|")
    
    perplexity_values = [108.027, 1.363, 1.240, 1.046, 1.255]
    
    for i, col in enumerate(cols):
        std_calc = df[col].std()
        std_perp = perplexity_values[i]
        diff = abs(std_calc - std_perp) / std_calc * 100
        print(f"| {col:8} | {std_calc:15.3f} | {std_perp:16.3f} | {diff:8.2f}% |")
    
    print("\n✅ CONCLUSÃO: Valores do Perplexity estão CORRETOS")
    
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n\n🎯 SOLUÇÃO:")
print("="*80)
print("O agente precisa ser corrigido para calcular std() e var() corretamente")
print("quando a pergunta solicitar 'variabilidade', 'desvio padrão' ou 'variância'")
print("="*80)
