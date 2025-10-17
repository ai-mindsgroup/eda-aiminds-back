"""Demo interativo do CSVAnalysisAgent.

Execute este script para ver o agente em ação.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np
# Removido: agente obsoleto csv_analysis_agent.py


def create_comprehensive_demo():
    """Demonstração completa do agente."""
    print("🎯 DEMO: Agente de Análise CSV - EDA AI Minds")
    print("=" * 60)
    
    # Criar dados mais realistas
    np.random.seed(42)
    n = 2000
    
    # Dados de transações de cartão mais realistas
    data = {
        'id': range(1, n + 1),
        'valor': np.random.lognormal(4, 1.2, n),
        'categoria': np.random.choice(['mercado', 'combustivel', 'restaurante', 'online', 'farmacia', 'shopping'], n),
        'hora': np.random.randint(0, 24, n),
        'dia_semana': np.random.randint(1, 8, n),
        'idade_cliente': np.random.normal(40, 12, n).astype(int),
        'saldo_conta': np.random.normal(3000, 1500, n),
        'num_transacoes_dia': np.random.poisson(2, n),
        'eh_fim_semana': np.random.choice([0, 1], n, p=[0.71, 0.29]),
        'distancia_casa_km': np.random.exponential(5, n),
    }
    
    # Lógica de fraude mais sofisticada
    fraude_prob = np.zeros(n)
    
    # Transações de alto valor = mais provável fraude
    fraude_prob += (data['valor'] > np.percentile(data['valor'], 95)) * 0.4
    
    # Horários suspeitos (madrugada)
    fraude_prob += ((data['hora'] >= 2) & (data['hora'] <= 6)) * 0.3
    
    # Muitas transações no dia
    fraude_prob += (data['num_transacoes_dia'] > 8) * 0.5
    
    # Longe de casa
    fraude_prob += (data['distancia_casa_km'] > 20) * 0.2
    
    # Ruído aleatório
    fraude_prob += np.random.random(n) * 0.1
    
    data['eh_fraude'] = (fraude_prob > 0.6).astype(int)
    
    df = pd.DataFrame(data)
    
    # Adicionar valores faltantes de forma realística
    missing_indices = np.random.choice(df.index, int(0.03 * len(df)), replace=False)
    df.loc[missing_indices, 'saldo_conta'] = np.nan
    
    missing_indices = np.random.choice(df.index, int(0.01 * len(df)), replace=False)
    df.loc[missing_indices, 'idade_cliente'] = np.nan
    
    # Salvar dados
    filename = "demo_transacoes.csv"
    df.to_csv(filename, index=False)
    
    print(f"✅ Dataset criado: {filename}")
    print(f"📊 {len(df)} transações, {df['eh_fraude'].sum()} fraudes ({df['eh_fraude'].mean()*100:.1f}% taxa)")
    
    # Inicializar agente
    print("\n🤖 Inicializando Agente CSV...")
    agent = CSVAnalysisAgent()
    
    # Carregar dados
    print("\n📂 Carregando dados...")
    result = agent.load_csv(filename)
    print("✅", result['content'])
    
    # Série de testes
    queries = [
        "Faça um resumo dos dados",
        "Analise as correlações entre as variáveis numéricas", 
        "Quantas transações são fraudulentas?",
        "Qual a média de valor das transações?",
        "Quantas transações temos por categoria?",
        "Crie um gráfico da distribuição de fraudes"
    ]
    
    print("\n" + "="*60)
    print("🔍 EXECUTANDO ANÁLISES")
    print("="*60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Consulta {i}: {query}")
        print("-" * 50)
        
        result = agent.process(query)
        print(result['content'])
        
        # Mostrar metadados interessantes
        if result.get('metadata') and not result.get('metadata', {}).get('error'):
            metadata = result['metadata']
            
            if 'fraud_count' in metadata:
                print(f"💡 Insight: Taxa de fraude = {metadata['fraud_rate']:.2f}%")
            
            if 'significant_correlations' in metadata:
                correlations = metadata['significant_correlations']
                if correlations:
                    strongest = correlations[0]
                    print(f"💡 Correlação mais forte: {strongest[0]} ↔ {strongest[1]} ({strongest[2]:.3f})")
    
    print("\n" + "="*60)
    print("✅ DEMO CONCLUÍDO!")
    print("="*60)
    
    # Informações do agente
    info = agent.get_dataset_info()
    print(f"📈 Dataset final: {info['rows']} linhas, {info['columns']} colunas")
    print(f"🔢 {len(info['numeric_columns'])} numéricas, {len(info['categorical_columns'])} categóricas")
    print(f"⚠️  Valores faltantes: {sum(info['missing_values'].values())}")
    
    # Limpeza
    if os.path.exists(filename):
        os.remove(filename)
        print(f"\n🗑️ Arquivo removido: {filename}")


if __name__ == "__main__":
    create_comprehensive_demo()