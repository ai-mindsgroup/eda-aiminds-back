"""Teste do GroqLLMAgent
======================

Script para testar a integração com a API do Groq.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.agent.groq_llm_agent import GroqLLMAgent
from src.settings import GROQ_API_KEY


def test_groq_agent():
    """Testa o GroqLLMAgent."""
    print("🚀 Testando GroqLLMAgent")
    print("=" * 50)
    
    # Verificar API key
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY não configurado!")
        return False
    
    print(f"✅ API Key configurado: {GROQ_API_KEY[:10]}...")
    
    try:
        # Inicializar agente
        print("\n📋 Inicializando GroqLLMAgent...")
        agent = GroqLLMAgent()
        print(f"✅ Agente inicializado: {agent.name}")
        
        # Testar informações do modelo
        print("\n📋 Informações do modelo:")
        model_info = agent.get_model_info()
        for key, value in model_info.items():
            print(f"  {key}: {value}")
        
        # Testar modelos disponíveis
        print(f"\n📋 Modelos disponíveis:")
        models = agent.get_available_models()
        for model in models:
            print(f"  - {model}")
        
        # Teste simples
        print(f"\n📋 Teste simples:")
        query = "Explique em poucas palavras o que é análise de dados."
        print(f"Query: {query}")
        
        response = agent.process(query)
        
        if response.get("success"):
            print("✅ Resposta recebida:")
            print(f"Content: {response['content'][:200]}...")
            print(f"Model: {response['metadata']['model']}")
            print(f"Usage: {response['metadata']['usage']}")
        else:
            print("❌ Erro na resposta:")
            print(response)
            return False
        
        # Teste com análise de dados
        print(f"\n📋 Teste de análise de dados:")
        data_summary = {
            "total_transactions": 1000,
            "fraud_count": 50,
            "fraud_rate": 0.05,
            "avg_amount": 250.75
        }
        
        analysis_response = agent.analyze_data_insights(data_summary)
        
        if analysis_response.get("success"):
            print("✅ Análise de dados realizada:")
            print(f"Content: {analysis_response['content'][:300]}...")
        else:
            print("❌ Erro na análise:")
            print(analysis_response)
            return False
        
        print(f"\n🎉 Todos os testes passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False


def test_orchestrator_with_groq():
    """Testa o OrchestratorAgent com GroqLLMAgent."""
    print("\n🎭 Testando OrchestratorAgent com Groq")
    print("=" * 50)
    
    try:
        from src.agent.orchestrator_agent import OrchestratorAgent
        
        # Inicializar orquestrador apenas com Groq
        orchestrator = OrchestratorAgent(
            enable_csv_agent=False,
            enable_rag_agent=False,
            enable_google_llm_agent=False,
            enable_groq_llm_agent=True,
            enable_data_processor=False
        )
        
        print(f"✅ Orquestrador inicializado")
        print(f"Agentes disponíveis: {list(orchestrator.agents.keys())}")
        
        # Teste via orquestrador
        query = "Como detectar fraudes em transações financeiras?"
        print(f"\nQuery: {query}")
        
        response = orchestrator.process(query)
        
        if response.get("success"):
            print("✅ Resposta do orquestrador:")
            print(f"Content: {response['content'][:200]}...")
            print(f"Agents used: {response['metadata']['agents_used']}")
        else:
            print("❌ Erro no orquestrador:")
            print(response)
            return False
        
        print(f"\n🎉 Teste do orquestrador passou!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do orquestrador: {e}")
        return False


if __name__ == "__main__":
    print("🧪 INICIANDO TESTES DO GROQ")
    print("=" * 60)
    
    success = True
    
    # Teste 1: GroqLLMAgent direto
    success &= test_groq_agent()
    
    # Teste 2: Via OrchestratorAgent
    success &= test_orchestrator_with_groq()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ GroqLLMAgent está funcionando corretamente")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique a configuração e as dependências")
    
    print("=" * 60)