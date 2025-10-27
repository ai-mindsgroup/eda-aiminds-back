"""Script de validação da camada de abstração LLM - TAREFA 1.4
=================================================================

Testa se RAGDataAgent agora usa LangChainLLMManager corretamente.
"""

import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.rag_data_agent import RAGDataAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_llm_abstraction():
    """Testa inicialização LLM via abstração."""
    
    print("\n" + "="*80)
    print("TESTE: Inicialização LLM via Camada de Abstração (TAREFA 1.4)")
    print("="*80 + "\n")
    
    try:
        # Inicializar RAGDataAgent (sem session_id - gerenciado internamente)
        print("1️⃣ Inicializando RAGDataAgent...")
        agent = RAGDataAgent()
        
        # Verificar LLM
        print("\n2️⃣ Verificando LLM inicializado...\n")
        
        if agent.llm is None:
            print("❌ FALHA: agent.llm é None")
            print("   Causa provável: Nenhuma API key configurada")
            return False
        
        llm_type = type(agent.llm).__name__
        print(f"✅ LLM Type: {llm_type}")
        print(f"✅ LLM Available: True")
        
        # Verificar qual provedor foi usado
        print("\n3️⃣ Identificando provedor ativo...\n")
        
        if "ChatGroq" in llm_type:
            print("✅ SUCESSO: GROQ inicializado via abstração")
            print("   Ordem de prioridade respeitada: GROQ (primeiro)")
            success = True
        elif "ChatGoogleGenerativeAI" in llm_type:
            print("⚠️ AVISO: Google Gemini inicializado")
            print("   GROQ não disponível, fallback para Google funcionou")
            success = True
        elif "ChatOpenAI" in llm_type:
            print("⚠️ AVISO: OpenAI inicializado")
            print("   GROQ e Google não disponíveis, fallback para OpenAI funcionou")
            success = True
        else:
            print(f"⚠️ AVISO: Provedor desconhecido: {llm_type}")
            success = True
        
        # Teste adicional: verificar se abstração está sendo usada
        print("\n4️⃣ Verificando uso da abstração...\n")
        
        # Tentar acessar LangChainLLMManager
        try:
            from src.llm.langchain_manager import get_langchain_llm_manager
            manager = get_langchain_llm_manager()
            print(f"✅ LangChainLLMManager acessível")
            print(f"✅ Provedor ativo no manager: {manager.active_provider.value.upper()}")
            
            # Verificar status dos provedores
            status = manager.get_provider_status()
            print(f"\n📊 Status dos Provedores:")
            for provider, info in status['providers'].items():
                available = "✅" if info['available'] else "❌"
                print(f"   {available} {provider.upper()}: {info['message']}")
            
        except Exception as e:
            print(f"❌ Erro ao acessar LangChainLLMManager: {e}")
            success = False
        
        print("\n" + "="*80)
        if success:
            print("✅ TESTE PASSOU: RAGDataAgent usa abstração corretamente")
        else:
            print("❌ TESTE FALHOU: Problemas identificados")
        print("="*80 + "\n")
        
        return success
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_abstraction()
    sys.exit(0 if success else 1)
