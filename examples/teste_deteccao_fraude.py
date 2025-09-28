#!/usr/bin/env python3
"""Exemplo: Como verificar se o orquestrador está detectando fraudes
================================================================

Este exemplo mostra:
1. Quais colunas o sistema procura para detectar fraudes
2. Como testar diferentes consultas relacionadas à fraude  
3. Como interpretar as respostas do orquestrador
4. Como criar dados de teste para validar a detecção

Uso:
    python examples/teste_deteccao_fraude.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pandas as pd
from src.agent.orchestrator_agent import OrchestratorAgent

def criar_dataset_teste_fraude():
    """Cria um dataset de teste com coluna de fraude para validar o sistema."""
    print("📊 Criando dataset de teste com coluna de fraude...")
    
    # Dados sintéticos com diferentes nomes de coluna de fraude
    dados = {
        'id': range(1, 11),
        'valor': [100, 50, 250, 1500, 75, 300, 2000, 80, 120, 90],
        'categoria': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'B'],
        'is_fraud': [0, 0, 0, 1, 0, 0, 1, 0, 0, 0]  # 2 fraudes em 10 transações
    }
    
    df = pd.DataFrame(dados)
    
    # Salvar arquivo temporário
    arquivo_teste = "examples/teste_fraude.csv"
    df.to_csv(arquivo_teste, index=False)
    print(f"✅ Dataset criado: {arquivo_teste}")
    print(f"   📊 {len(df)} linhas, {len(df.columns)} colunas")
    print(f"   🚨 {df['is_fraud'].sum()} fraudes detectadas")
    
    return arquivo_teste

def testar_deteccao_fraudes():
    """Testa diferentes consultas para verificar detecção de fraudes."""
    print("\n" + "="*60)
    print("🕵️ TESTE DE DETECÇÃO DE FRAUDES".center(60))
    print("="*60)
    
    # 1. Criar dataset de teste
    arquivo_teste = criar_dataset_teste_fraude()
    
    # 2. Inicializar orquestrador
    print("\n🤖 Inicializando orquestrador...")
    orquestrador = OrchestratorAgent()
    print("✅ Sistema inicializado!")
    
    contexto = {"file_path": arquivo_teste}
    
    # 3. Consultas de teste para fraude
    consultas_teste = [
        "carregue os dados",
        "existe fraude nos dados?",
        "analise padrões de fraude", 
        "quantas fraudes foram detectadas?",
        "mostre estatísticas de fraude",
        "há transações suspeitas?",
        "detecte anomalias nos dados"
    ]
    
    print(f"\n📝 Testando {len(consultas_teste)} consultas relacionadas à fraude:")
    print("=" * 60)
    
    for i, consulta in enumerate(consultas_teste, 1):
        print(f"\n{i}. 💬 CONSULTA: '{consulta}'")
        print("-" * 40)
        
        try:
            resultado = orquestrador.process(consulta, context=contexto)
            
            if isinstance(resultado, dict):
                resposta = resultado.get("content", str(resultado))
                metadata = resultado.get("metadata", {})
            else:
                resposta = str(resultado)
                metadata = {}
            
            print(f"🤖 RESPOSTA: {resposta[:200]}{'...' if len(resposta) > 200 else ''}")
            
            # Verificar se detectou fraude
            fraude_detectada = any(palavra in resposta.lower() for palavra in ['fraude', 'fraud', 'suspeita'])
            
            if fraude_detectada:
                print("✅ FRAUDE DETECTADA na resposta")
            else:
                print("⚠️  Fraude não mencionada na resposta")
                
            # Mostrar agentes usados
            if metadata and "orchestrator" in metadata:
                agentes = metadata["orchestrator"].get("agents_used", [])
                print(f"🤖 Agentes utilizados: {agentes}")
                
        except Exception as e:
            print(f"❌ ERRO: {e}")
        
        print()

def verificar_colunas_fraude_suportadas():
    """Mostra quais nomes de coluna o sistema reconhece como fraude."""
    print("\n" + "="*60)
    print("📋 COLUNAS DE FRAUDE SUPORTADAS".center(60))
    print("="*60)
    
    colunas_suportadas = ['is_fraud', 'eh_fraude', 'fraud', 'fraude']
    
    print("O sistema procura automaticamente por estas colunas:")
    for i, coluna in enumerate(colunas_suportadas, 1):
        print(f"   {i}. '{coluna}'")
    
    print(f"\n💡 DICA: Seu dataset deve ter uma dessas colunas para detecção automática")
    print(f"💡 DICA: Valores devem ser 0 (não fraude) e 1 (fraude)")

def analisar_dataset_existente():
    """Analisa um dataset específico para verificar se tem colunas de fraude."""
    print("\n" + "="*60)
    print("🔍 ANÁLISE DE DATASET EXISTENTE".center(60))
    print("="*60)
    
    datasets_teste = [
        "examples/dados_exemplo.csv",
        "examples/teste_fraude.csv"
    ]
    
    for dataset in datasets_teste:
        arquivo = Path(dataset)
        if arquivo.exists():
            print(f"\n📁 Analisando: {dataset}")
            try:
                df = pd.read_csv(dataset)
                colunas = df.columns.tolist()
                
                print(f"   📊 {len(df)} linhas, {len(colunas)} colunas")
                print(f"   📋 Colunas: {', '.join(colunas[:5])}{'...' if len(colunas) > 5 else ''}")
                
                # Verificar colunas de fraude
                colunas_fraude = ['is_fraud', 'eh_fraude', 'fraud', 'fraude']
                colunas_encontradas = [col for col in colunas_fraude if col in colunas]
                
                if colunas_encontradas:
                    print(f"   ✅ Coluna(s) de fraude encontrada(s): {colunas_encontradas}")
                    
                    for col_fraude in colunas_encontradas:
                        fraudes = df[col_fraude].sum()
                        total = len(df)
                        taxa = (fraudes / total) * 100
                        print(f"   🚨 {fraudes}/{total} fraudes ({taxa:.1f}%)")
                else:
                    print(f"   ⚠️  Nenhuma coluna de fraude reconhecida")
                    
            except Exception as e:
                print(f"   ❌ Erro ao ler arquivo: {e}")
        else:
            print(f"\n📁 {dataset}: Arquivo não encontrado")

def main():
    """Função principal."""
    print("🕵️‍♀️ GUIA: COMO VERIFICAR SE O ORQUESTRADOR DETECTA FRAUDES")
    print("="*70)
    
    print("\n🎯 Este script irá:")
    print("1. Mostrar quais colunas o sistema reconhece como fraude")
    print("2. Criar um dataset de teste com fraudes") 
    print("3. Testar diferentes consultas de detecção")
    print("4. Analisar datasets existentes")
    
    # Executar testes
    verificar_colunas_fraude_suportadas()
    analisar_dataset_existente()
    
    resposta = input(f"\n❓ Deseja executar teste completo de detecção? (s/n): ").lower()
    if resposta in ['s', 'sim', 'y', 'yes']:
        testar_deteccao_fraudes()
    
    print("\n✅ Análise concluída!")
    print("\n💡 RESUMO:")
    print("   • Sistema procura colunas: 'is_fraud', 'eh_fraude', 'fraud', 'fraude'")
    print("   • Use consultas como: 'detecte fraudes', 'análise de fraude'")
    print("   • Valores: 0 = não fraude, 1 = fraude")

if __name__ == "__main__":
    main()