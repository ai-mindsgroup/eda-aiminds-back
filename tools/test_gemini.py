#!/usr/bin/env python3
"""
Teste Rápido do Google Gemini
==============================

Valida se o Gemini está configurado e funcionando.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
root = Path(__file__).parent
sys.path.insert(0, str(root))

def test_gemini_basic():
    """Teste básico de conexão com Gemini."""
    print("🧪 TESTE DO GOOGLE GEMINI")
    print("=" * 60)
    
    # 1. Verificar variável de ambiente
    print("\n1️⃣ Verificando configuração...")
    from src.settings import GOOGLE_API_KEY
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY não configurada!")
        print("\n📝 Como corrigir:")
        print("   1. Acesse: https://makersuite.google.com/app/apikey")
        print("   2. Crie uma API key")
        print("   3. Adicione no configs/.env:")
        print("      GOOGLE_API_KEY=sua_chave_aqui")
        return False
    
    print(f"✅ API Key configurada: {GOOGLE_API_KEY[:20]}...")
    
    # 2. Verificar biblioteca
    print("\n2️⃣ Verificando biblioteca...")
    try:
        import google.generativeai as genai
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ Bibliotecas instaladas")
    except ImportError as e:
        print(f"❌ Erro ao importar: {e}")
        print("\n📝 Instale com:")
        print("   pip install langchain-google-genai google-generativeai")
        return False
    
    # 3. Testar LLM Manager
    print("\n3️⃣ Testando LLM Manager...")
    try:
        from src.llm.manager import LLMManager, LLMProvider
        
        # Forçar uso do Google
        manager = LLMManager(preferred_providers=[LLMProvider.GOOGLE])
        print(f"✅ LLM Manager inicializado: {manager.active_provider.value}")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        return False
    
    # 4. Teste real de chat
    print("\n4️⃣ Testando chat com Gemini...")
    try:
        response = manager.chat("Responda apenas 'OK' se você for o Google Gemini.")
        
        print(f"\n✅ Resposta recebida!")
        print(f"   Provedor: {response.provider.value}")
        print(f"   Modelo: {response.model}")
        print(f"   Tempo: {response.processing_time:.2f}s")
        print(f"   Tokens: {response.tokens_used or 'N/A'}")
        print(f"\n💬 Resposta:")
        print(f"   {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        print(f"\n🔍 Detalhes do erro:")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_advanced():
    """Teste avançado com análise de dados."""
    print("\n" + "=" * 60)
    print("🧪 TESTE AVANÇADO - ANÁLISE DE DADOS")
    print("=" * 60)
    
    try:
        from src.llm.manager import LLMManager, LLMProvider, LLMConfig
        
        manager = LLMManager(preferred_providers=[LLMProvider.GOOGLE])
        
        config = LLMConfig(
            temperature=0.3,
            max_tokens=500
        )
        
        prompt = """
        Analise este resumo de dados de transações de cartão de crédito:
        
        - Total de transações: 1000
        - Transações fraudulentas: 15 (1.5%)
        - Valor médio de transação normal: $88.00
        - Valor médio de transação fraudulenta: $234.50
        
        Forneça 3 insights principais sobre este padrão.
        """
        
        print("\n📊 Enviando análise para Gemini...")
        response = manager.chat(prompt, config)
        
        print(f"\n✅ Análise completa!")
        print(f"   Tempo de processamento: {response.processing_time:.2f}s")
        print(f"\n🎯 Insights do Gemini:")
        print("-" * 60)
        print(response.content)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na análise avançada: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("\n🚀 TESTE COMPLETO DO GOOGLE GEMINI")
    print("=" * 60)
    print()
    
    # Teste básico
    basic_ok = test_gemini_basic()
    
    if not basic_ok:
        print("\n❌ Teste básico falhou. Corrija a configuração antes de continuar.")
        return
    
    # Teste avançado
    advanced_ok = test_gemini_advanced()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Teste Básico:    {'✅ PASSOU' if basic_ok else '❌ FALHOU'}")
    print(f"Teste Avançado:  {'✅ PASSOU' if advanced_ok else '❌ FALHOU'}")
    
    if basic_ok and advanced_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Google Gemini está configurado e funcionando perfeitamente!")
        print("\n📚 Próximos passos:")
        print("   1. Use na API: uvicorn src.api.main:app --reload")
        print("   2. Teste os endpoints de chat e análise")
        print("   3. Monitore os logs para ver o Gemini em ação")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique a configuração.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
