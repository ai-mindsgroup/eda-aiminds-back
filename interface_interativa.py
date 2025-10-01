#!/usr/bin/env python3
"""Interface Interativa para Consultas ao Sistema Multiagente EDA AI Minds"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent
import traceback

class InteractiveInterface:
    """Interface interativa para consultas ao sistema multiagente"""
    
    def __init__(self):
        self.orchestrator = None
        self.session_history = []
        
    def initialize_system(self):
        """Inicializa o sistema multiagente"""
        print("🚀 EDA AI Minds - Sistema Multiagente Interativo")
        print("=" * 60)
        print("🔧 Inicializando sistema...")
        
        try:
            self.orchestrator = OrchestratorAgent("orchestrator")
            print("✅ Sistema inicializado com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro na inicialização: {str(e)}")
            return False
    
    def display_help(self):
        """Exibe ajuda e comandos disponíveis"""
        print("\n📖 COMANDOS DISPONÍVEIS:")
        print("─" * 40)
        print("🔸 'help' ou '?' - Mostrar esta ajuda")
        print("🔸 'status' - Status do sistema e dados")
        print("🔸 'history' - Histórico de perguntas")
        print("🔸 'clear' - Limpar histórico")
        print("🔸 'quit' ou 'exit' - Sair do sistema")
        print("🔸 Qualquer outra entrada - Fazer pergunta ao sistema")
        
        print("\n💡 EXEMPLOS DE PERGUNTAS:")
        print("─" * 40)
        print("• Quais são os tipos de dados?")
        print("• Quantas transações fraudulentas existem?")
        print("• Qual é a distribuição das colunas?")
        print("• Mostre estatísticas descritivas")
        print("• Há outliers nos dados?")
        print("• Como é a correlação entre variáveis?")
    
    def display_status(self):
        """Exibe status do sistema"""
        print("\n📊 STATUS DO SISTEMA:")
        print("─" * 40)
        
        if self.orchestrator:
            # Verificar dados disponíveis
            has_data = self.orchestrator._check_data_availability()
            data_status = "✅ Dados disponíveis" if has_data else "❌ Sem dados"
            print(f"🔸 Orquestrador: ✅ Ativo")
            print(f"🔸 Base de dados: {data_status}")
            
            # Verificar agentes
            agents_count = len(self.orchestrator.agents)
            print(f"🔸 Agentes ativos: {agents_count}")
            
            # Verificar LLM
            llm_provider = getattr(self.orchestrator.llm_manager, 'active_provider', 'N/A') if self.orchestrator.llm_manager else "N/A"
            print(f"🔸 Provedor LLM: {llm_provider}")
            
            # Estatísticas de sessão
            print(f"🔸 Perguntas feitas: {len(self.session_history)}")
        else:
            print("❌ Sistema não inicializado")
    
    def display_history(self):
        """Exibe histórico de perguntas"""
        if not self.session_history:
            print("\n📝 Histórico vazio - nenhuma pergunta feita ainda.")
            return
        
        print(f"\n📝 HISTÓRICO DA SESSÃO ({len(self.session_history)} perguntas):")
        print("─" * 60)
        
        for i, (question, success) in enumerate(self.session_history, 1):
            status_icon = "✅" if success else "❌"
            question_preview = question[:50] + "..." if len(question) > 50 else question
            print(f"{i:2d}. {status_icon} {question_preview}")
    
    def process_question(self, question: str):
        """Processa uma pergunta do usuário"""
        if not self.orchestrator:
            print("❌ Sistema não inicializado. Reinicie a aplicação.")
            return False
        
        print(f"\n❓ Pergunta: {question}")
        print("🔄 Processando...")
        print("─" * 60)
        
        try:
            # Processar consulta
            result = self.orchestrator.process(question)
            
            if result and not result.get("metadata", {}).get("error", False):
                # Sucesso
                print("🤖 Resposta:")
                print(result.get("content", "Sem conteúdo"))
                
                # Mostrar metadados
                metadata = result.get("metadata", {})
                agents_used = metadata.get("agents_used", [])
                if agents_used:
                    print(f"\n🛠️ Agentes utilizados: {', '.join(agents_used)}")
                
                provider = metadata.get("provider")
                if provider:
                    print(f"🤖 Provedor LLM: {provider}")
                
                processing_time = metadata.get("processing_time")
                if processing_time:
                    print(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
                
                # Registrar sucesso
                self.session_history.append((question, True))
                return True
                
            else:
                # Erro
                error_msg = result.get("content", "Erro desconhecido") if result else "Nenhuma resposta"
                print(f"❌ Erro: {error_msg}")
                self.session_history.append((question, False))
                return False
                
        except Exception as e:
            print(f"❌ Erro interno: {str(e)}")
            print("\n🔍 Detalhes do erro:")
            traceback.print_exc()
            self.session_history.append((question, False))
            return False
    
    def run(self):
        """Executa a interface interativa"""
        # Inicializar sistema
        if not self.initialize_system():
            return
        
        # Mostrar ajuda inicial
        self.display_help()
        self.display_status()
        
        print("\n🎯 Sistema pronto! Digite sua pergunta ou 'help' para ajuda.")
        print("=" * 60)
        
        # Loop principal
        while True:
            try:
                # Solicitar entrada do usuário
                user_input = input("\n💬 Sua pergunta: ").strip()
                
                # Verificar comandos especiais
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    print("\n👋 Encerrando sistema. Até logo!")
                    break
                
                elif user_input.lower() in ['help', '?', 'ajuda']:
                    self.display_help()
                
                elif user_input.lower() == 'status':
                    self.display_status()
                
                elif user_input.lower() in ['history', 'historico']:
                    self.display_history()
                
                elif user_input.lower() == 'clear':
                    self.session_history.clear()
                    print("✅ Histórico limpo!")
                
                elif not user_input:
                    print("⚠️ Digite uma pergunta ou comando. Use 'help' para ajuda.")
                
                else:
                    # Processar pergunta
                    self.process_question(user_input)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupção detectada. Digite 'quit' para sair ou continue...")
            
            except EOFError:
                print("\n\n👋 Encerrando sistema...")
                break
            
            except Exception as e:
                print(f"\n❌ Erro inesperado: {str(e)}")

def main():
    """Função principal"""
    interface = InteractiveInterface()
    interface.run()

if __name__ == "__main__":
    main()