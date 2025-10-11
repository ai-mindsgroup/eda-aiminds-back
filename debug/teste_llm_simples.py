#!/usr/bin/env python3
"""
Teste Simples da LLM - EDA AI Minds
===================================

Script direto para testar LLM sem complexidade do sistema multiagente.
Permite fazer perguntas diretas e receber respostas.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.manager import get_llm_manager, LLMConfig

def test_simple_llm():
    """Teste simples da LLM com perguntas diretas."""
    print("🚀 TESTE SIMPLES DA LLM - EDA AI MINDS")
    print("=" * 50)
    
    try:
        # Inicializar LLM Manager
        print("🔧 Inicializando LLM Manager...")
        manager = get_llm_manager()
        print(f"✅ LLM Manager inicializado - Provedor: {manager.active_provider.value}")
        
        # Configuração para testes
        config = LLMConfig(
            temperature=0.2,
            max_tokens=1000
        )
        
        print("\n" + "=" * 50)
        print("💬 CHAT INTERATIVO")
        print("Digite suas perguntas (ou 'sair' para encerrar)")
        print("=" * 50)
        
        while True:
            # Solicitar pergunta do usuário
            print("\n🤔 Sua pergunta:")
            pergunta = input(">>> ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit', '']:
                print("\n👋 Até logo!")
                break
            
            # Processar pergunta
            print(f"\n🤖 Pensando... (usando {manager.active_provider.value})")
            
            try:
                response = manager.chat(pergunta, config)
                
                print(f"\n✅ **Resposta** ({response.provider.value}):")
                print("-" * 30)
                print(response.content)
                print("-" * 30)
                print(f"⏱️  Tempo: {response.processing_time:.2f}s")
                
                if response.tokens_used:
                    print(f"🔢 Tokens: {response.tokens_used}")
                    
            except Exception as e:
                print(f"\n❌ Erro ao processar pergunta: {str(e)}")
                print("💡 Verifique sua conexão de internet e chaves de API")
        
    except Exception as e:
        print(f"\n❌ Erro na inicialização: {str(e)}")
        print("\n💡 Soluções:")
        print("   1. Verifique se configurou o arquivo configs/.env")
        print("   2. Execute: python check_config.py")
        print("   3. Certifique-se que tem pelo menos um LLM configurado")

if __name__ == "__main__":
    test_simple_llm()