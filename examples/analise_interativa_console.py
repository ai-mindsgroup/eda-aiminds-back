#!/usr/bin/env python3
"""
Exemplo Interativo Console: Análise de CSV via Terminal (Sem GUI)
================================================================

Este script é uma versão simplificada do analise_interativa.py que funciona
diretamente no terminal sem interface gráfica.

Uso:
    python examples/analise_interativa_console.py [caminho_para_csv]
    
    ou 
    
    python examples/analise_interativa_console.py
    (será solicitado o caminho do arquivo)
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# --- Importações para o sistema ---
from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def obter_arquivo_csv() -> str | None:
    """
    Obtém o caminho do arquivo CSV via linha de comando ou entrada do usuário.
    """
    # Verifica se foi passado como argumento
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
        if Path(arquivo).exists():
            return arquivo
        else:
            print(f"❌ Arquivo não encontrado: {arquivo}")
            return None
    
    # Se não foi passado como argumento, pede ao usuário
    print("📂 Digite o caminho para o arquivo CSV:")
    print("   (ou pressione Enter para usar um arquivo de exemplo)")
    
    arquivo = input("Caminho: ").strip()
    
    if not arquivo:
        # Usa arquivo de exemplo se disponível
        exemplo = Path("examples/dados_exemplo.csv")
        if exemplo.exists():
            print(f"✅ Usando arquivo de exemplo: {exemplo}")
            return str(exemplo)
        else:
            print("❌ Nenhum arquivo especificado e exemplo não encontrado.")
            return None
    
    if Path(arquivo).exists():
        return arquivo
    else:
        print(f"❌ Arquivo não encontrado: {arquivo}")
        return None

def iniciar_sessao_analise(orchestrator: OrchestratorAgent, file_path: str):
    """
    Inicia o loop interativo para o usuário fazer perguntas sobre o CSV carregado.
    """
    print("\n" + "="*60)
    print("🤖 SESSÃO DE ANÁLISE INTERATIVA INICIADA".center(60))
    print("="*60)
    print(f"📊 Arquivo em análise: {Path(file_path).name}")
    print("\n💡 Agora você pode fazer suas perguntas sobre os dados.")
    print("   Digite 'ajuda' para ver exemplos ou 'sair' para encerrar.")
    
    # Contexto que será enviado ao orquestrador
    context = {"file_path": file_path}

    while True:
        try:
            # Pede a entrada do usuário
            query = input("\n❓ Sua pergunta: ").strip()

            if not query:
                continue
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print("👋 Encerrando a sessão de análise. Até mais!")
                break
            
            if query.lower() == 'ajuda':
                print("\n📋 --- Exemplos de Perguntas ---")
                print("   • Qual a distribuição de cada variável?")
                print("   • Existem padrões ou tendências temporais?") 
                print("   • Como as variáveis estão relacionadas umas com as outras?")
                print("   • Quais as conclusões que você obteve a partir dos dados?")
                print("   • Faça um resumo dos dados")
                print("   • Analise correlações entre variáveis")
                print("   • Detecte possíveis fraudes nos dados")
                print("   ------------------------------")
                continue

            print("\n🔄 Processando sua pergunta com o agente...")
            
            # Processa a consulta usando o orquestrador
            resultado = orchestrator.process(query, context=context)
            
            # Extrai e exibe a resposta
            if isinstance(resultado, dict):
                resposta = resultado.get("content", "Não foi possível obter uma resposta.")
                
                # Se há metadata de erro, mostra
                if resultado.get("metadata", {}).get("error"):
                    print(f"\n⚠️ Erro: {resposta}")
                    continue
                    
            else:
                resposta = str(resultado)

            print(f"\n🤖 Resposta do Agente:")
            print("─" * 50)
            print(resposta)
            print("─" * 50)

        except KeyboardInterrupt:
            print("\n\n⏹️ Sessão interrompida. Encerrando...")
            break
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            print(f"⚠️ Ocorreu um erro: {e}")

def main():
    """
    Função principal que orquestra todo o processo.
    """
    print("\n" + "="*60)
    print("🧠 EDA AI MINDS - ANÁLISE INTERATIVA DE DADOS".center(60))
    print("="*60)

    # Passo 1: Obter o arquivo CSV
    arquivo_csv = obter_arquivo_csv()
    if not arquivo_csv:
        return

    print(f"✅ Arquivo selecionado: {arquivo_csv}")

    # Passo 2: Inicializar o sistema multiagente
    print("\n🔧 Inicializando o sistema multiagente (Orquestrador)...")
    try:
        orchestrator = OrchestratorAgent()
        print("✅ Sistema inicializado com sucesso!")
        agentes = list(orchestrator.agents.keys())
        print(f"🤖 Agentes disponíveis: {', '.join(agentes)}")
    except Exception as e:
        logger.error(f"Falha ao inicializar o orquestrador: {e}")
        print(f"\n❌ Erro crítico: Não foi possível inicializar o sistema.")
        print(f"   Causa: {e}")
        return

    # Passo 3: Carregar e validar o arquivo usando o orquestrador
    print("\n📂 Carregando e validando o arquivo CSV...")
    contexto_inicial = {"file_path": arquivo_csv}
    
    try:
        resultado_carga = orchestrator.process("carregar e validar os dados do arquivo", contexto_inicial)
        
        # Verifica se o carregamento foi bem-sucedido
        if resultado_carga.get("metadata", {}).get("error", False):
            print("\n" + "="*60)
            print("❌ ERRO AO CARREGAR O ARQUIVO".center(60))
            print("="*60)
            print("Não foi possível carregar ou validar o arquivo CSV.")
            print(f"Motivo: {resultado_carga.get('content')}")
            return
        
        print("✅ Arquivo carregado e validado com sucesso!")
        print(f"📊 {resultado_carga.get('content')}")
        
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo: {e}")
        print(f"\n❌ Erro ao carregar arquivo: {e}")
        return

    # Passo 4: Iniciar a sessão de perguntas e respostas
    iniciar_sessao_analise(orchestrator, arquivo_csv)

if __name__ == "__main__":
    main()