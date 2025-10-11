"""
Script de análise comparativa: Perplexity vs AI Minds Agent
Análise de variabilidade (desvio padrão e variância)
"""
import pandas as pd
import numpy as np

# Dados do Perplexity (creditcard_test_500.csv)
perplexity_data = {
    'Variável': ['Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14'],
    'Desvio_Padrão': [108.027, 1.363, 1.240, 1.046, 1.255, 1.196, 1.301, 0.859, 0.826, 0.862, 0.961, 0.991, 0.643, 0.909, 0.802],
    'Variância': [11669.830, 1.859, 1.537, 1.093, 1.576, 1.430, 1.692, 0.739, 0.682, 0.743, 0.924, 0.982, 0.414, 0.827, 0.644]
}

df_perplexity = pd.DataFrame(perplexity_data)

print("="*80)
print("🔍 ANÁLISE COMPARATIVA: PERPLEXITY vs AI MINDS AGENT")
print("="*80)
print("\n📊 DADOS DO PERPLEXITY (creditcard_test_500.csv - 500 registros):")
print(df_perplexity.to_string(index=False))

print("\n\n🤖 PROBLEMA IDENTIFICADO:")
print("-"*80)
print("O agente AI Minds retornou INTERVALO (mín-máx) em vez de VARIABILIDADE (std, var)")
print("\nPergunta feita: 'Qual a variabilidade dos dados (desvio padrão, variância)?'")
print("Resposta dada: Tabela com Mínimo, Máximo e Amplitude")
print("\n❌ ERRO: O agente não respondeu corretamente à pergunta")
print("   - Esperado: Desvio padrão e variância de cada variável")
print("   - Obtido: Valores mínimo e máximo de cada variável")

print("\n\n💡 ANÁLISE TÉCNICA:")
print("-"*80)
print("1. O agente usou dados da tabela embeddings (20.000 registros)")
print("2. O Perplexity usou creditcard_test_500.csv (500 registros)")
print("3. Mesmo com datasets diferentes, o agente deveria calcular std() e var()")
print("4. O código do agente não interpretou corretamente a pergunta")

print("\n\n🔧 CORREÇÃO NECESSÁRIA:")
print("-"*80)
print("O agente deve:")
print("  1. Identificar palavras-chave: 'variabilidade', 'desvio padrão', 'variância'")
print("  2. Calcular df[col].std() e df[col].var() para cada coluna numérica")
print("  3. Retornar tabela com colunas: Variável | Desvio Padrão | Variância")

print("\n\n📋 VAMOS CALCULAR OS VALORES CORRETOS DO DATASET DE 500 REGISTROS:")
print("-"*80)

# Carregar o arquivo real de 500 registros
try:
    df_500 = pd.read_csv('data/creditcard_test_500.csv')
    print(f"\n✅ Dataset carregado: {len(df_500)} registros, {len(df_500.columns)} colunas")
    
    # Selecionar as 15 primeiras variáveis
    cols_to_analyze = ['Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14']
    
    print("\n📊 CÁLCULO REAL (usando pandas):")
    print("-"*80)
    
    results = []
    for col in cols_to_analyze:
        std = df_500[col].std()
        var = df_500[col].var()
        results.append({
            'Variável': col,
            'Desvio Padrão (Calculado)': std,
            'Variância (Calculada)': var,
            'Desvio Padrão (Perplexity)': df_perplexity[df_perplexity['Variável'] == col]['Desvio_Padrão'].values[0],
            'Variância (Perplexity)': df_perplexity[df_perplexity['Variável'] == col]['Variância'].values[0],
            'Diferença Std (%)': abs(std - df_perplexity[df_perplexity['Variável'] == col]['Desvio_Padrão'].values[0]) / std * 100 if std > 0 else 0,
            'Diferença Var (%)': abs(var - df_perplexity[df_perplexity['Variável'] == col]['Variância'].values[0]) / var * 100 if var > 0 else 0
        })
    
    df_comparison = pd.DataFrame(results)
    
    print("\n📈 COMPARAÇÃO DETALHADA:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.float_format', '{:.3f}'.format)
    print(df_comparison.to_string(index=False))
    
    print("\n\n📊 RESUMO ESTATÍSTICO DAS DIFERENÇAS:")
    print(f"Diferença média (Desvio Padrão): {df_comparison['Diferença Std (%)'].mean():.2f}%")
    print(f"Diferença média (Variância): {df_comparison['Diferença Var (%)'].mean():.2f}%")
    print(f"Maior diferença (Desvio Padrão): {df_comparison['Diferença Std (%)'].max():.2f}% ({df_comparison.loc[df_comparison['Diferença Std (%)'].idxmax(), 'Variável']})")
    print(f"Maior diferença (Variância): {df_comparison['Diferença Var (%)'].max():.2f}% ({df_comparison.loc[df_comparison['Diferença Var (%)'].idxmax(), 'Variável']})")
    
    if df_comparison['Diferença Std (%)'].mean() < 0.1:
        print("\n✅ CONCLUSÃO: Valores do Perplexity estão CORRETOS (diferença < 0.1%)")
    else:
        print(f"\n⚠️ ATENÇÃO: Diferença média de {df_comparison['Diferença Std (%)'].mean():.2f}% detectada")

except FileNotFoundError:
    print("\n❌ Arquivo data/creditcard_test_500.csv não encontrado")
    print("   Execute este script a partir da raiz do projeto")

print("\n\n🎯 CONCLUSÃO FINAL:")
print("="*80)
print("O agente AI Minds respondeu com dados INCORRETOS para a pergunta feita.")
print("A pergunta solicitava VARIABILIDADE (std, var), mas o agente retornou INTERVALO (min, max).")
print("\nAção recomendada:")
print("  1. Corrigir o agente para identificar corretamente a intenção da pergunta")
print("  2. Implementar cálculo de .std() e .var() quando solicitado")
print("  3. Adicionar testes automatizados para perguntas sobre variabilidade")
print("="*80)
