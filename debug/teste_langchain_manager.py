#!/usr/bin/env python3
"""
Teste Simples do LangChain Manager - EDA AI Minds
================================================

Script para testar o LangChain Manager corrigido.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_langchain_manager():
    """Teste básico do LangChain Manager."""
    print("🧪 TESTE DO LANGCHAIN MANAGER")
    print("=" * 40)
    
    try:
        from src.llm.langchain_manager import LANGCHAIN_AVAILABLE, get_langchain_llm_manager
        
        print(f"📦 LangChain disponível: {LANGCHAIN_AVAILABLE}")
        
        if not LANGCHAIN_AVAILABLE:
            print("❌ LangChain não está disponível")
            print("💡 Instale com: pip install langchain langchain-openai langchain-google-genai langchain-groq")
            return
        
        print("🔧 Inicializando LangChain Manager...")
        manager = get_langchain_llm_manager()
        
        print(f"✅ Manager inicializado")
        print(f"🤖 Provedor ativo: {manager.active_provider.value if manager.active_provider else 'Nenhum'}")
        
        # Testar status
        status = manager.get_provider_status()
        print("\n📊 Status dos provedores:")
        for provider_name, provider_status in status["providers"].items():
            available = "✅" if provider_status["available"] else "❌"
            print(f"  {available} {provider_name.upper()}: {provider_status['message']}")
        
        # Teste simples se houver provedor disponível
        if manager.active_provider:
            print(f"\n🧪 Testando chat com {manager.active_provider.value}...")
            try:
                response = manager.chat("Diga apenas 'OK' se funcionou")
                print(f"✅ Resposta: {response.content}")
                print(f"⏱️  Tempo: {response.processing_time:.2f}s")
            except Exception as e:
                print(f"❌ Erro no teste: {str(e)}")
        else:
            print("\n⚠️ Nenhum provedor disponível para teste")
            
    except Exception as e:
        print(f"❌ Erro na inicialização: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_langchain_manager()