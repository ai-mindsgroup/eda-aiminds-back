"""Exemplo completo de como carregar e analisar CSV com o sistema EDA AI Minds.

Este script demonstra as diferentes formas de carregar e processar dados CSV.
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.csv_analysis_agent import CSVAnalysisAgent
import pandas as pd
import numpy as np


def exemplo_basico_csv():
    """Exemplo básico de carregamento de CSV."""
    print("📊 EXEMPLO BÁSICO - CARREGAMENTO CSV")
    print("=" * 50)
    
    # 1. Criar o agente CSV
    csv_agent = CSVAnalysisAgent()
    
    # 2. Carregar arquivo CSV
    # Substitua pelo caminho do seu arquivo
    arquivo_csv = "seu_arquivo.csv"  # ← Coloque o caminho do seu arquivo aqui
    
    try:
        result = csv_agent.load_csv(arquivo_csv)
        print(f"✅ {result['content']}")
        
        # 3. Fazer análises
        analises = [
            "Faça um resumo dos dados",
            "Quantas linhas e colunas temos?", 
            "Quais são os tipos de dados?",
            "Há valores faltantes?",
            "Mostre as primeiras linhas"
        ]
        
        for pergunta in analises:
            print(f"\n❓ {pergunta}")
            resposta = csv_agent.process(pergunta)
            print(f"💡 {resposta['content']}")
            
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")


def exemplo_deteccao_fraude():
    """Exemplo específico para detecção de fraudes."""
    print("\n🕵️ EXEMPLO - DETECÇÃO DE FRAUDES")
    print("=" * 50)
    
    csv_agent = CSVAnalysisAgent()
    
    # Arquivo de exemplo (pode ser qualquer CSV com dados financeiros)
    arquivo_csv = "dados_fraude.csv"
    
    try:
        # Carregar dados
        csv_agent.load_csv(arquivo_csv)
        
        # Consultas específicas para fraude
        consultas_fraude = [
            "Quantas transações fraudulentas foram detectadas?",
            "Qual é o valor médio das transações fraudulentas?",
            "Em que horários ocorrem mais fraudes?",
            "Quais são os padrões suspeitos nos dados?",
            "Faça uma análise de correlação das variáveis"
        ]
        
        for consulta in consultas_fraude:
            print(f"\n🔍 {consulta}")
            resultado = csv_agent.process(consulta)
            print(f"📋 {resultado['content']}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_com_pandas_direto():
    """Exemplo usando pandas diretamente (sem agente)."""
    print("\n🐼 EXEMPLO - PANDAS DIRETO")
    print("=" * 50)
    
    try:
        # Carregar com pandas
        df = pd.read_csv("seu_arquivo.csv")
        
        print(f"✅ Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"📊 Colunas: {list(df.columns)}")
        print(f"📈 Tipos de dados:\n{df.dtypes}")
        print(f"🔍 Primeiras 5 linhas:\n{df.head()}")
        print(f"📋 Estatísticas:\n{df.describe()}")
        
        # Verificar valores faltantes
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(f"⚠️ Valores faltantes:\n{missing[missing > 0]}")
        else:
            print("✅ Nenhum valor faltante encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao carregar com pandas: {e}")


def exemplo_csv_online():
    """Exemplo carregando CSV de uma URL."""
    print("\n🌐 EXEMPLO - CSV ONLINE")
    print("=" * 50)
    
    # Exemplo com dataset público do Kaggle
    url_exemplo = "https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv"
    
    try:
        df = pd.read_csv(url_exemplo)
        print(f"✅ Dados online carregados: {len(df)} linhas")
        print(f"📊 Colunas: {list(df.columns)}")
        print(f"🔍 Amostra dos dados:\n{df.head()}")
        
        # Usar o agente CSV com dados carregados
        csv_agent = CSVAnalysisAgent()
        csv_agent.df = df  # Atribuir o DataFrame diretamente
        
        # Fazer análise
        resultado = csv_agent.process("Faça um resumo destes dados")
        print(f"🤖 Análise do agente: {resultado['content']}")
        
    except Exception as e:
        print(f"❌ Erro ao carregar CSV online: {e}")


def criar_csv_exemplo():
    """Cria um arquivo CSV de exemplo para testes."""
    print("\n📝 CRIANDO ARQUIVO CSV DE EXEMPLO")
    print("=" * 50)
    
    # Dados de exemplo simulando transações
    np.random.seed(42)
    
    dados = {
        'id_transacao': range(1, 1001),
        'valor': np.random.lognormal(3, 1, 1000),
        'categoria': np.random.choice(['Alimentação', 'Transporte', 'Lazer', 'Saúde'], 1000),
        'horario': np.random.randint(0, 24, 1000),
        'dia_semana': np.random.randint(1, 8, 1000),
        'fraude': np.random.choice([0, 1], 1000, p=[0.95, 0.05]),  # 5% fraude
        'valor_suspeito': np.random.choice([0, 1], 1000, p=[0.9, 0.1])
    }
    
    df = pd.DataFrame(dados)
    
    # Salvar arquivo
    nome_arquivo = "dados_exemplo.csv"
    df.to_csv(nome_arquivo, index=False)
    
    print(f"✅ Arquivo '{nome_arquivo}' criado com {len(df)} transações")
    print(f"📊 Colunas: {list(df.columns)}")
    print(f"🔍 Primeiras linhas:\n{df.head()}")
    
    return nome_arquivo


def main():
    """Executa todos os exemplos."""
    print("🚀 GUIA COMPLETO - CARREGAMENTO E ANÁLISE DE CSV")
    print("=" * 60)
    print("ℹ️ Este guia mostra diferentes formas de trabalhar com CSV no sistema")
    
    # Criar arquivo de exemplo
    arquivo_exemplo = criar_csv_exemplo()
    
    # Testar carregamento com agente
    print(f"\n🤖 Testando com arquivo criado: {arquivo_exemplo}")
    csv_agent = CSVAnalysisAgent()
    
    try:
        # Carregar arquivo de exemplo
        resultado = csv_agent.load_csv(arquivo_exemplo)
        print(f"✅ {resultado['content']}")
        
        # Fazer algumas análises
        consultas = [
            "Quantas transações temos no total?",
            "Quantas são fraudulentas?", 
            "Qual categoria tem mais fraudes?",
            "Qual o valor médio das transações?",
            "Mostre a correlação entre as variáveis"
        ]
        
        for consulta in consultas:
            print(f"\n❓ {consulta}")
            resposta = csv_agent.process(consulta)
            print(f"💡 {resposta['content'][:200]}...")  # Primeiros 200 caracteres
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
    
    print(f"\n📚 RESUMO DOS MÉTODOS:")
    print("1. 🤖 csv_agent.load_csv('arquivo.csv') - Recomendado")
    print("2. 🐼 pd.read_csv('arquivo.csv') - Pandas direto") 
    print("3. 🌐 pd.read_csv('http://...') - URLs online")
    print("4. 📊 Análises via csv_agent.process('pergunta')")
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    print("1. Substitua 'seu_arquivo.csv' pelo seu arquivo real")
    print("2. Execute python exemplo_csv.py")
    print("3. Faça perguntas específicas sobre seus dados")
    print("4. Use o sistema RAG para análises mais avançadas")


if __name__ == "__main__":
    main()