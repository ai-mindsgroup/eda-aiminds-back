#!/usr/bin/env python3
"""
Teste Direto dos Agentes LLM
============================

Este script testa apenas os agentes LLM diretamente, sem dependências complexas.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_grok_direct():
    """Testa GrokLLMAgent diretamente."""
    print("🧪 TESTE DIRETO - GROK LLM AGENT")
    print("=" * 45)
    
    try:
        from src.agent.grok_llm_agent import GrokLLMAgent
        
        print("🔧 Inicializando Grok LLM Agent...")
        grok_agent = GrokLLMAgent()
        print(f"✅ {grok_agent.name} inicializado")
        
        # Teste simples
        query = "Em uma frase, o que é detecção de fraude?"
        print(f"📝 Query: {query}")
        
        result = grok_agent.process(query)
        metadata = result.get('metadata', {})
        
        print(f"📊 Resultado:")
        print(f"   Sucesso: {metadata.get('success', False)}")
        print(f"   Modelo: {metadata.get('model', 'N/A')}")
        print(f"   LLM usado: {metadata.get('llm_used', False)}")
        
        if metadata.get('success'):
            content = result.get('content', '')[:100]
            print(f"   Resposta: {content}...")
            return True
        else:
            print(f"   Erro: {result.get('content', 'Desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_google_direct():
    """Testa GoogleLLMAgent diretamente."""
    print("\n🧪 TESTE DIRETO - GOOGLE LLM AGENT")
    print("=" * 45)
    
    try:
        from src.agent.google_llm_agent import GoogleLLMAgent
        
        print("🔧 Inicializando Google LLM Agent...")
        google_agent = GoogleLLMAgent()
        print(f"✅ {google_agent.name} inicializado")
        
        # Teste simples
        query = "Em uma frase, o que é análise de dados?"
        print(f"📝 Query: {query}")
        
        result = google_agent.process(query)
        metadata = result.get('metadata', {})
        
        print(f"📊 Resultado:")
        print(f"   Sucesso: {metadata.get('success', False)}")
        print(f"   Modelo: {metadata.get('model', 'N/A')}")
        print(f"   LLM usado: {metadata.get('llm_used', False)}")
        
        if metadata.get('success'):
            content = result.get('content', '')[:100]
            print(f"   Resposta: {content}...")
            return True
        else:
            print(f"   Erro: {result.get('content', 'Desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_base_agent_llm():
    """Testa funcionalidade básica do BaseAgent."""
    print("\n🧪 TESTE - BASE AGENT LLM")
    print("=" * 45)
    
    try:
        # Criar um agente simples para testar BaseAgent
        from src.agent.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__("test_agent", "Agente de teste")
            
            def process(self, query: str, context=None):
                # Usar a funcionalidade _call_llm do BaseAgent
                return self._call_llm(query, context)
        
        print("🔧 Inicializando Test Agent...")
        test_agent = TestAgent()
        print(f"✅ {test_agent.name} inicializado")
        
        # Teste com Sonar API (via BaseAgent)
        query = "Responda em uma palavra: qual a cor do céu?"
        print(f"📝 Query: {query}")
        
        result = test_agent.process(query)
        
        print(f"📊 Resultado:")
        if 'error' not in result:
            print(f"   ✅ Sonar API funcionando")
            content = str(result).get('content', str(result))[:100]
            print(f"   Resposta: {content}...")
            return True
        else:
            print(f"   ❌ Erro na Sonar API: {result.get('message', 'Desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def check_api_keys():
    """Verifica quais API keys estão configuradas."""
    print("🔍 VERIFICAÇÃO DE API KEYS")
    print("=" * 30)
    
    from src.settings import GROK_API_KEY, GOOGLE_API_KEY, SONAR_API_KEY
    
    print(f"🔑 GROK_API_KEY: {'✅ Configurado' if GROK_API_KEY else '❌ Ausente'}")
    print(f"🔑 GOOGLE_API_KEY: {'✅ Configurado' if GOOGLE_API_KEY else '❌ Ausente'}")
    print(f"🔑 SONAR_API_KEY: {'✅ Configurado' if SONAR_API_KEY else '❌ Ausente'}")
    
    available_llms = []
    if GROK_API_KEY: available_llms.append("Grok")
    if GOOGLE_API_KEY: available_llms.append("Google")
    if SONAR_API_KEY: available_llms.append("Sonar")
    
    if available_llms:
        print(f"🤖 LLMs disponíveis: {', '.join(available_llms)}")
    else:
        print("⚠️ Nenhuma API key configurada")
    
    return available_llms

def main():
    """Executa todos os testes diretos."""
    print("🚀 TESTES DIRETOS DOS AGENTES LLM")
    print("=" * 50)
    
    # Verificar API keys
    available_llms = check_api_keys()
    
    results = []
    
    # Testar Grok se disponível
    if "Grok" in available_llms:
        grok_success = test_grok_direct()
        results.append(("Grok", grok_success))
    
    # Testar Google se disponível
    if "Google" in available_llms:
        google_success = test_google_direct()
        results.append(("Google", google_success))
    
    # Testar Sonar se disponível
    if "Sonar" in available_llms:
        sonar_success = test_base_agent_llm()
        results.append(("Sonar", sonar_success))
    
    # Resumo final
    print("\n🏁 RESUMO DOS TESTES")
    print("=" * 30)
    
    for llm_name, success in results:
        status = "✅ Funcionando" if success else "❌ Com problemas"
        print(f"   {llm_name}: {status}")
    
    working_llms = [name for name, success in results if success]
    if working_llms:
        print(f"\n🎉 LLMs funcionando: {', '.join(working_llms)}")
    else:
        print("\n⚠️ Nenhum LLM está funcionando completamente")
        print("   Verifique as API keys e configurações")

if __name__ == "__main__":
    main()