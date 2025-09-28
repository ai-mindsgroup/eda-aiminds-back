#!/usr/bin/env python3
"""
Exemplo Interativo Completo: Análise de CSV com Seleção de Arquivo e Sessão de Perguntas
=======================================================================================

Este script orquestra o fluxo completo de uma sessão de análise de dados:
1.  Abre uma janela para o usuário selecionar um arquivo CSV.
2.  Utiliza o DataProcessor para carregar e validar o arquivo.
3.  Se o arquivo for válido, inicia uma sessão interativa no terminal.
4.  O usuário pode fazer perguntas em linguagem natural, como as descritas na atividade.
5.  O OrchestratorAgent processa as perguntas e retorna as análises.

Uso:
    python examples/analise_interativa.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
# Isso garante que os módulos de 'src' possam ser importados
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# --- Importações para a interface e o sistema ---
import tkinter as tk
from tkinter import filedialog
from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def selecionar_arquivo_csv() -> str | None:
    """
    Abre uma janela de diálogo para o usuário selecionar um arquivo .csv.
    """
    print(" Abrindo janela de seleção de arquivo...")
    # Esconde a janela principal do tkinter que não será usada
    root = tk.Tk()
    root.withdraw()
    
    # Define os tipos de arquivo permitidos na janela
    file_path = filedialog.askopenfilename(
        title="Selecione um arquivo CSV para análise",
        filetypes=(("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*"))
    )
    
    if not file_path:
        print(" Nenhuma arquivo selecionado.")
        return None
        
    return file_path

def iniciar_sessao_analise(orchestrator: OrchestratorAgent, file_path: str):
    """
    Inicia o loop interativo para o usuário fazer perguntas sobre o CSV carregado.
    """
    print("\n" + "="*60)
    print(" SESSÃO DE ANÁLISE INTERATIVA INICIADA".center(60))
    print("="*60)
    print(f" Arquivo em análise: {Path(file_path).name}")
    print("\n Agora você pode fazer suas perguntas sobre os dados.")
    print(" Digite 'ajuda' para ver exemplos de perguntas ou 'sair' para encerrar.")
    
    # Contexto que será enviado ao orquestrador em cada chamada
    context = {"file_path": file_path}

    while True:
        try:
            # Pede a entrada do usuário
            query = input("\n Sua pergunta: ").strip()

            if not query:
                continue
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print(" encerrando a sessão de análise. Até mais!")
                break
            
            if query.lower() == 'ajuda':
                print("\n--- Exemplos de Perguntas ---")
                print(" - Qual a distribuição de cada variável?")
                print(" - Existem padrões ou tendências temporais?")
                print(" - Como as variáveis estão relacionadas umas com as outras?")
                print(" - Quais as conclusões que você obteve a partir dos dados?")
                print("-----------------------------")
                continue

            print("\n Processando sua pergunta com o agente...")
            
            # Processa a consulta usando o orquestrador
            resultado = orchestrator.process(query, context=context)
            
            # Extrai e exibe a resposta
            if isinstance(resultado, dict):
                resposta = resultado.get("content", "Não foi possível obter uma resposta.")
            else:
                resposta = str(resultado)

            print(f"\n Resposta do Agente:\n---\n{resposta}\n---")

        except KeyboardInterrupt:
            print("\n Sessão interrompida. Encerrando...")
            break
        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado: {e}")
            print(f"⚠️ Ocorreu um erro: {e}")

def main():
    """
    Função principal que orquestra todo o processo.
    """
    print("\n" + "="*60)
    print(" EDA AI MINDS - ANÁLISE INTERATIVA DE DADOS".center(60))
    print("="*60)

    # Passo 1: Selecionar o arquivo CSV
    arquivo_csv = selecionar_arquivo_csv()
    if not arquivo_csv:
        return # Encerra se nenhum arquivo for selecionado

    print(f" Arquivo selecionado: {arquivo_csv}")

    # Passo 2: Inicializar o sistema multiagente
    print("\n Inicializando o sistema multiagente (Orquestrador)...")
    try:
        orchestrator = OrchestratorAgent()
        print(" Sistema inicializado com sucesso!")
        agentes = list(orchestrator.agents.keys())
        print(f" Agentes disponíveis: {', '.join(agentes)}")
    except Exception as e:
        logger.error(f"Falha ao inicializar o orquestrador: {e}")
        print(f"\n Erro crítico: Não foi possível inicializar o sistema de agentes. Causa: {e}")
        return

    # Passo 3: Carregar e validar o arquivo usando o orquestrador
    print("\n Carregando e validando o arquivo CSV...")
    contexto_inicial = {"file_path": arquivo_csv}
    resultado_carga = orchestrator.process("carregar e validar os dados do arquivo", contexto_inicial)

    # Verifica se o carregamento foi bem-sucedido
    if resultado_carga.get("metadata", {}).get("error", False):
        print("\n" + "="*60)
        print(" ERRO AO CARREGAR O ARQUIVO".center(60))
        print("="*60)
        print("Não foi possível carregar ou validar o arquivo CSV.")
        print(f"Motivo: {resultado_carga.get('content')}")
        return
    
    print(" Arquivo carregado e validado com sucesso pelo agente!")
    print(resultado_carga.get('content'))

    # Passo 4: Iniciar a sessão de perguntas e respostas
    iniciar_sessao_analise(orchestrator, arquivo_csv)

if __name__ == "__main__":
    main()