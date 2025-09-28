#!/usr/bin/env python3
"""Exemplo Interativo: Análise de CSV com Orquestrador
=====================================

Este exemplo permite ao usuário:
1. Carregar um arquivo CSV real
2. Interagir com o orquestrador através de consultas naturais
3. Realizar análises completas dos dados
4. Usar tanto agentes CSV quanto RAG (se disponível)

Uso:
    python examples/exemplo_csv_interativo.py
    
    Ou especificando um arquivo:
    python examples/exemplo_csv_interativo.py --arquivo dados.csv
"""

from __future__ import annotations
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import argparse
from typing import Optional
import pandas as pd

from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Função principal do exemplo interativo."""
    parser = argparse.ArgumentParser(
        description="Exemplo interativo de análise CSV com Orquestrador"
    )
    parser.add_argument(
        "--arquivo", 
        help="Caminho para arquivo CSV (opcional)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 EDA AI MINDS - ANÁLISE INTERATIVA DE CSV".center(60))
    print("="*60)
    
    # 1. Obter arquivo CSV
    arquivo_csv = args.arquivo
    if not arquivo_csv:
        while True:
            print("\n📁 Opções de arquivo CSV:")
            print("1. Usar arquivo de exemplo (examples/dados_exemplo.csv)")
            print("2. Especificar meu próprio arquivo")
            print("3. Sair")
            
            opcao = input("\nEscolha uma opção (1-3): ").strip()
            
            if opcao == "1":
                arquivo_csv = "examples/dados_exemplo.csv"
                break
            elif opcao == "2":
                arquivo_csv = input("Digite o caminho completo do arquivo CSV: ").strip()
                arquivo_csv = arquivo_csv.strip('"\'')  # Remove aspas se houver
                break
            elif opcao == "3":
                print("✅ Saindo...")
                return
            else:
                print("❌ Opção inválida! Digite 1, 2 ou 3.")
                continue
    
    # Verificar se arquivo existe
    if not Path(arquivo_csv).exists():
        print(f"❌ Arquivo não encontrado: {arquivo_csv}")
        return
    
    print(f"✅ Arquivo selecionado: {arquivo_csv}")
    
    # 2. Inicializar orquestrador
    print("\n🤖 Inicializando sistema...")
    try:
        orquestrador = OrchestratorAgent()
        print("✅ Sistema inicializado!")
        
        agentes = list(orquestrador.agents.keys())
        print(f"🤖 Agentes disponíveis: {', '.join(agentes)}")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        return
    
    # 3. Sessão interativa simplificada
    print("\n" + "="*60)
    print("💬 SESSÃO INTERATIVA".center(60))
    print("="*60)
    print("\nDigite suas consultas ou 'sair' para encerrar.")
    print("Exemplo: 'faça um resumo dos dados'")
    
    contexto = {"file_path": arquivo_csv}
    
    while True:
        try:
            consulta = input("\n💬 Sua consulta: ").strip()
            
            if not consulta:
                continue
                
            if consulta.lower() in ['sair', 'exit', 'quit']:
                print("✅ Encerrando...")
                break
            
            print("� Processando...")
            
            # CHAMADA CORRETA DO MÉTODO
            resultado = orquestrador.process(consulta, context=contexto)
            
            # Extrair conteúdo
            if isinstance(resultado, dict):
                resposta = resultado.get("content", str(resultado))
            else:
                resposta = str(resultado)
            
            print(f"\n🤖 Resposta:\n{resposta}")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrompido. Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            continue
    
    print("\n✅ Sessão finalizada!")


if __name__ == "__main__":
    main()