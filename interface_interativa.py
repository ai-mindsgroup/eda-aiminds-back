#!/usr/bin/env python3
"""
Interface Interativa de Chat para EDA AI Minds V2.0

Sistema de chat via terminal para interagir com o agente multiagente.
✅ RAGDataAgent V2.0 com memória persistente e LangChain
✅ Contexto conversacional entre interações
✅ Histórico salvo em Supabase
"""

import sys
import os
from pathlib import Path
from uuid import uuid4
import asyncio

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def safe_print(text: str, **kwargs):
    """Print seguro que trata erros de encoding no Windows.
    
    Args:
        text: Texto a ser impresso
        **kwargs: Argumentos adicionais passados para print() (end, flush, etc)
    """
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        # Remove emojis e caracteres Unicode problemáticos
        import re
        text_ascii = re.sub(r'[^\x00-\x7F]+', '', text)
        print(text_ascii, **kwargs)


def print_banner():
    """Exibe banner inicial."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🤖 EDA AI MINDS - CHAT INTERATIVO V2.0 🤖          ║
║                                                              ║
║  ✅ Sistema Multiagente com RAG Vetorial + Memória          ║
║  ✅ LangChain Integrado (Google Gemini / OpenAI)            ║
║  ✅ Histórico Conversacional Persistente                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📋 Comandos Disponíveis:
  • Digite sua pergunta normalmente
  • 'status' - Verifica status do sistema e sessão de memória
  • 'limpar' - Limpa contexto e histórico
  • 'ajuda' - Mostra comandos disponíveis
  • 'sair' ou 'quit' - Encerra o chat

💡 Dica: O sistema mantém histórico conversacional!
💡 Certifique-se de ter carregado dados com: python load_csv_data.py

═══════════════════════════════════════════════════════════════
"""
    # Garantir encoding correto no Windows
    try:
        print(banner)
    except UnicodeEncodeError:
        # Fallback para versão ASCII simples
        print("""
=================================================================
           EDA AI MINDS - CHAT INTERATIVO V2.0
=================================================================

Sistema Multiagente com RAG Vetorial + Memoria
LangChain Integrado (Google Gemini / OpenAI)
Historico Conversacional Persistente

Comandos Disponiveis:
  * Digite sua pergunta normalmente
  * 'status' - Verifica status do sistema
  * 'limpar' - Limpa contexto e historico
  * 'ajuda' - Mostra comandos disponiveis
  * 'sair' ou 'quit' - Encerra o chat

Dica: O sistema mantem historico conversacional!

=================================================================
""")


def print_help():
    """Exibe ajuda com exemplos."""
    help_text = """
📚 EXEMPLOS DE PERGUNTAS:

📊 Descrição dos Dados:
  • Quais são os tipos de dados (numéricos, categóricos)?
  • Qual a distribuição de cada variável?
  • Qual o intervalo de cada variável (mínimo, máximo)?
  • Quais são as medidas de tendência central?
  • Qual a variabilidade dos dados (desvio padrão, variância)?

📈 Padrões e Tendências:
  • Existem padrões ou tendências temporais?
  • Quais os valores mais frequentes ou menos frequentes?
  • Existem agrupamentos (clusters) nos dados?

🔍 Detecção de Anomalias:
  • Existem valores atípicos nos dados?
  • Como esses outliers afetam a análise?
  • Podem ser removidos, transformados ou investigados?

🔗 Relações entre Variáveis:
  • Como as variáveis estão relacionadas?
  • Existe correlação entre as variáveis?
  • Quais variáveis têm maior influência?

═══════════════════════════════════════════════════════════════
"""
    print(help_text)


def process_command(command: str, orchestrator: OrchestratorAgent, session_id: str) -> bool:
    """
    Processa comandos especiais.
    
    Returns:
        True se deve continuar, False se deve sair
    """
    cmd_lower = command.lower().strip()
    
    if cmd_lower in ['sair', 'quit', 'exit', 'q']:
        safe_print("\n👋 Encerrando chat. Até logo!\n")
        return False
    
    elif cmd_lower in ['ajuda', 'help', '?']:
        print_help()
        return True
    
    elif cmd_lower == 'status':
        safe_print("\n📊 STATUS DO SISTEMA:")
        print(f"  • Agentes ativos: {len(orchestrator.agents)}")
        print(f"  • RAGDataAgent: V2.0 (memória + LangChain)")
        print(f"  • Sessão ID: {session_id}")
        safe_print(f"  • Memória persistente: {'✅ Ativa' if orchestrator.has_memory else '❌ Inativa'}")
        print(f"  • Busca: RAG Vetorial (Supabase embeddings)")
        print(f"  • Base de dados: PostgreSQL + pgvector")
        safe_print("\n💡 Para carregar novos dados CSV:")
        print("     python load_csv_data.py [caminho_arquivo.csv]")
        print()
        return True
    
    elif cmd_lower in ['limpar', 'clear', 'reset']:
        orchestrator.clear_data_context()
        safe_print("\n✅ Contexto e histórico limpos!\n")
        return True
    
    return None  # Não é um comando especial


async def main():
    """Loop principal do chat interativo com memória persistente."""
    print_banner()
    
    # Gerar session_id único para esta sessão de chat
    session_id = str(uuid4())
    safe_print(f"🔑 Sessão iniciada: {session_id[:8]}...\n")


    # INTEGRAÇÃO: Executar ingestão de CSVs da pasta processando
    safe_print("🧹 Verificando arquivos CSV em data/processando/...")
    from src.agent.rag_agent import RAGAgent
    from src.data.csv_file_manager import CSVFileManager
    from src.settings import EDA_DATA_DIR_PROCESSANDO

    rag_agent = RAGAgent()
    file_manager = CSVFileManager()

    # Buscar todos os arquivos CSV em data/processando/
    csv_files = list(EDA_DATA_DIR_PROCESSANDO.glob("*.csv"))

    active_source_id = None
    if not csv_files:
        safe_print("⚠️ Nenhum arquivo CSV encontrado em data/processando/")
        safe_print("💡 Coloque seus arquivos CSV em data/processando/ para processá-los\n")
    else:
        safe_print(f"📥 Encontrados {len(csv_files)} arquivo(s) CSV para processar\n")

        for csv_file in csv_files:
            try:
                safe_print(f"📄 Processando: {csv_file.name}")

                # Limpar base vetorial e memória do agente antes da ingestão
                safe_print("  → Limpando base vetorial e memória...")
                from src.vectorstore.supabase_client import supabase
                supabase.table('embeddings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                supabase.table('chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                supabase.table('metadata').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                rag_agent.clear_memory()

                # Processar arquivo usando RAGAgent
                safe_print("  → Executando ingestão robusta via RAGAgent...")
                source_id = csv_file.stem
                ingest_result = rag_agent.ingest_csv_file(
                    file_path=str(csv_file),
                    source_id=source_id,
                    encoding="utf-8"
                )
                active_source_id = source_id

                # Mover para pasta processado
                safe_print("  → Movendo para pasta 'processado'...")
                processed_path = file_manager.move_to_processed(csv_file)

                safe_print(f"  ✅ Arquivo processado com sucesso!")
                safe_print(f"  📁 Localização final: {processed_path}\n")
                safe_print(f"  🟢 Dataset ativo: {source_id}\n")

            except Exception as e:
                safe_print(f"  ❌ Erro ao processar {csv_file.name}: {e}\n")
                logger.error(f"Erro no processamento de {csv_file.name}: {e}", exc_info=True)
        safe_print("✅ Processamento de arquivos concluído!\n")

    # Inicializar orchestrador
    safe_print("🔧 Inicializando sistema multiagente...")
    try:
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=True,
            enable_data_processor=True
        )
        safe_print("✅ Sistema inicializado com sucesso!")
        safe_print(f"✅ RAGDataAgent V2.0: Memória persistente + LangChain\n")
        if active_source_id:
            safe_print(f"🟢 Dataset ativo: {active_source_id}\n")
        # Patch: garantir que toda consulta do orquestrador inclua o source_id do dataset ativo
        orchestrator._active_source_id = active_source_id
    except Exception as e:
        safe_print(f"❌ Erro ao inicializar sistema: {e}")
        logger.error(f"Erro na inicialização: {e}", exc_info=True)
        return
    
    # Loop do chat
    safe_print("💬 Chat pronto! Digite sua pergunta ou 'ajuda' para ver exemplos.\n")
    print("═" * 63)
    
    while True:
        try:
            # Prompt do usuário
            user_input = input("\n👤 Você: ").strip()
            
            if not user_input:
                continue
            
            # Processar comandos especiais
            should_continue = process_command(user_input, orchestrator, session_id)
            if should_continue is False:
                break
            elif should_continue is True:
                continue
            
            # Processar pergunta normal COM MEMÓRIA PERSISTENTE
            safe_print("\n🤖 Agente: Processando...", end="")
            sys.stdout.flush()
            
            try:
                # USAR MÉTODO ASYNC COM MEMÓRIA PERSISTENTE
                # Patch: garantir que o contexto da consulta inclua o source_id do dataset ativo
                context = {"source_id": getattr(orchestrator, "_active_source_id", None)}
                response = await orchestrator.process_with_persistent_memory(
                    user_input,
                    context=context,
                    session_id=session_id
                )
                
                # Limpar linha de "Processando..."
                print("\r" + " " * 50 + "\r", end="")
                
                if response and response.get('content'):
                    safe_print(f"🤖 Agente:\n{response['content']}\n")
                    
                    # Mostrar metadados se disponíveis
                    metadata = response.get('metadata', {})
                    if metadata.get('agent_used'):
                        safe_print(f"   📌 Agente usado: {metadata['agent_used']}")
                    if metadata.get('session_id'):
                        safe_print(f"   📌 Sessão: {metadata['session_id'][:8]}...")
                    if metadata.get('previous_interactions') is not None:
                        safe_print(f"   📌 Interações anteriores: {metadata['previous_interactions']}")
                else:
                    safe_print("🤖 Agente: Desculpe, não consegui processar sua solicitação.\n")
            
            except Exception as e:
                print("\r" + " " * 50 + "\r", end="")
                safe_print(f"❌ Erro ao processar: {str(e)}\n")
                logger.error(f"Erro no processamento: {e}", exc_info=True)
        
        except KeyboardInterrupt:
            safe_print("\n\n👋 Chat interrompido. Digite 'sair' para encerrar ou continue.\n")
            continue
        
        except EOFError:
            safe_print("\n\n👋 Encerrando chat. Até logo!\n")
            break


if __name__ == "__main__":
    # Executar loop async
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("\n\n👋 Encerrando chat. Até logo!\n")
