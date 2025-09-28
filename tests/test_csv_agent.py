"""Script de teste para o CSVAnalysisAgent.

Demonstra as capacidades do agente de análise de CSV.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np
from src.agent.csv_analysis_agent import CSVAnalysisAgent


def create_sample_data():
    """Cria dados de exemplo para teste."""
    np.random.seed(42)
    
    # Simular dados de fraude de cartão de crédito (simplificado)
    n_samples = 1000
    
    data = {
        'transaction_id': range(1, n_samples + 1),
        'amount': np.random.lognormal(3, 1, n_samples),
        'merchant_category': np.random.choice(['grocery', 'gas', 'restaurant', 'online', 'retail'], n_samples),
        'hour': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(1, 8, n_samples),
        'customer_age': np.random.normal(45, 15, n_samples).astype(int),
        'account_balance': np.random.normal(5000, 2000, n_samples),
        'transaction_count_today': np.random.poisson(3, n_samples),
        'is_weekend': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
    }
    
    # Criar target de fraude baseado em regras simples
    fraud_probability = (
        (data['amount'] > np.percentile(data['amount'], 90)) * 0.3 +
        (data['hour'] < 6) * 0.2 +
        (data['transaction_count_today'] > 10) * 0.4 +
        np.random.random(n_samples) * 0.1
    )
    
    data['is_fraud'] = (fraud_probability > 0.5).astype(int)
    
    df = pd.DataFrame(data)
    
    # Adicionar alguns valores faltantes
    df.loc[np.random.choice(df.index, 50), 'account_balance'] = np.nan
    df.loc[np.random.choice(df.index, 20), 'customer_age'] = np.nan
    
    return df


def test_csv_agent():
    """Testa as funcionalidades do CSVAnalysisAgent."""
    print("🚀 Testando CSVAnalysisAgent")
    print("=" * 50)
    
    # Criar dados de teste
    print("📊 Criando dados de exemplo...")
    df = create_sample_data()
    
    # Salvar CSV
    test_file = "test_fraud_data.csv"
    df.to_csv(test_file, index=False)
    print(f"✅ Dados salvos em: {test_file}")
    
    # Inicializar agente
    print("\n🤖 Inicializando agente CSV...")
    agent = CSVAnalysisAgent()
    
    # Teste 1: Carregar dados
    print("\n📁 Teste 1: Carregando dados...")
    result = agent.load_csv(test_file)
    print(f"Resultado: {result['content']}")
    
    # Teste 2: Resumo dos dados
    print("\n📋 Teste 2: Resumo dos dados...")
    result = agent.process("Faça um resumo dos dados")
    print(result['content'])
    
    # Teste 3: Análise de correlação
    print("\n🔗 Teste 3: Análise de correlação...")
    result = agent.process("Analise as correlações entre as variáveis numéricas")
    print(result['content'])
    
    # Teste 4: Consulta sobre fraude
    print("\n🚨 Teste 4: Análise de fraude...")
    result = agent.process("Quantas transações são fraudulentas? Qual a taxa de fraude?")
    print(result['content'])
    
    # Teste 5: Informações do dataset
    print("\n📊 Teste 5: Informações detalhadas...")
    info = agent.get_dataset_info()
    print(f"Dataset: {info['rows']} linhas, {info['columns']} colunas")
    print(f"Colunas numéricas: {len(info['numeric_columns'])}")
    print(f"Colunas categóricas: {len(info['categorical_columns'])}")
    
    # Limpeza
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🗑️ Arquivo de teste removido: {test_file}")
    
    print("\n✅ Testes concluídos!")


if __name__ == "__main__":
    test_csv_agent()