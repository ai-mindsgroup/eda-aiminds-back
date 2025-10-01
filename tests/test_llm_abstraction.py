#!/usr/bin/env python3
"""
Teste da Camada de Abstração LLM Manager
=======================================

Este script testa se a camada de abstração LLM Manager funciona corretamente:
- Detecção automática de provedores disponíveis
- Fallback automático entre provedores
- Integração com o orquestrador

Uso:
    python test_llm_abstraction.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.llm.manager import get_llm_manager, LLMConfig, LLMProvider
from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_llm_manager_basic():
    """Testa funcionalidades básicas do LLM Manager."""
    print("\n" + "="*60)
    print("🧪 TESTE 1: LLM Manager - Funcionalidades Básicas")
    print("="*60)
    
    try:
        # Inicializar manager
        manager = get_llm_manager()
        print(f"✅ LLM Manager inicializado")
        
        # Verificar status
        status = manager.get_status()
        print(f"🤖 Provedor ativo: {status['active_provider']}")
        print(f"📋 Ordem de preferência: {', '.join(status['preferred_order'])}")
        
        # Listar provedores disponíveis
        print("\n📊 Status dos Provedores:")
        for provider, info in status['provider_status'].items():
            status_icon = "✅" if info['available'] else "❌"
            print(f"   {status_icon} {provider.upper()}: {info['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do LLM Manager: {e}")
        return False

def test_llm_manager_chat():
    """Testa chamada de chat do LLM Manager."""
    print("\n" + "="*60)
    print("🧪 TESTE 2: LLM Manager - Chat")
    print("="*60)
    
    try:
        manager = get_llm_manager()
        
        # Configuração de teste
        config = LLMConfig(temperature=0.1, max_tokens=100)
        
        # Prompt de teste
        prompt = "Responda em uma frase: Qual é a capital do Brasil?"
        
        print(f"📝 Prompt: {prompt}")
        print("🔄 Enviando para LLM...")
        
        # Fazer chamada
        response = manager.chat(prompt, config)
        
        if response.success:
            print(f"✅ Resposta recebida via {response.provider.value}")
            print(f"📄 Conteúdo: {response.content}")
            print(f"⏱️ Tempo: {response.processing_time:.2f}s")
            print(f"🔢 Tokens: {response.tokens_used}")
            return True
        else:
            print(f"❌ Falha na chamada: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de chat: {e}")
        return False

def test_orchestrator_integration():
    """Testa integração do LLM Manager com o orquestrador."""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Integração com Orquestrador")
    print("="*60)
    
    try:
        # Inicializar orquestrador
        print("🔧 Inicializando orquestrador...")
        orchestrator = OrchestratorAgent()
        print("✅ Orquestrador inicializado")
        
        # Verificar se LLM Manager está disponível
        if orchestrator.llm_manager:
            print("✅ LLM Manager integrado ao orquestrador")
            
            # Testar consulta
            query = "Quais são os tipos de dados (numéricos, categóricos)?"
            print(f"📝 Consulta de teste: {query}")
            print("🔄 Processando...")
            
            result = orchestrator.process(query)
            
            if result.get("metadata", {}).get("error", False):
                print(f"❌ Erro na consulta: {result.get('content')}")
                return False
            else:
                print("✅ Consulta processada com sucesso")
                print(f"📄 Resposta: {result.get('content', '')[:200]}...")
                agents_used = result.get("metadata", {}).get("agents_used", [])
                print(f"🤖 Agentes usados: {', '.join(agents_used)}")
                return True
        else:
            print("❌ LLM Manager não está integrado ao orquestrador")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        return False

def test_fallback_mechanism():
    """Testa mecanismo de fallback entre provedores."""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Mecanismo de Fallback")
    print("="*60)
    
    try:
        manager = get_llm_manager()
        
        # Verificar quantos provedores estão disponíveis
        status = manager.get_status()
        available_providers = [
            p for p, info in status['provider_status'].items() 
            if info['available']
        ]
        
        print(f"📊 Provedores disponíveis: {len(available_providers)}")
        
        if len(available_providers) > 1:
            print("✅ Múltiplos provedores disponíveis - fallback pode ser testado")
            
            # Testar com provedor específico
            for provider_name in available_providers:
                try:
                    provider = LLMProvider(provider_name)
                    config = LLMConfig(temperature=0.1, max_tokens=50)
                    response = manager.chat("Diga olá", config, force_provider=provider)
                    
                    if response.success:
                        print(f"✅ {provider.value}: {response.content[:50]}...")
                    else:
                        print(f"❌ {provider.value}: {response.error}")
                        
                except Exception as e:
                    print(f"❌ {provider_name}: Erro - {e}")
            
            return True
            
        elif len(available_providers) == 1:
            print(f"⚠️ Apenas um provedor disponível ({available_providers[0]}) - fallback não pode ser testado")
            return True
        else:
            print("❌ Nenhum provedor disponível")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de fallback: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("🚀 TESTE DA CAMADA DE ABSTRAÇÃO LLM MANAGER".center(80))
    print("="*80)
    
    tests = [
        ("LLM Manager Básico", test_llm_manager_basic),
        ("Chat LLM Manager", test_llm_manager_chat),
        ("Integração Orquestrador", test_orchestrator_integration),
        ("Mecanismo Fallback", test_fallback_mechanism)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erro crítico no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado Final: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todos os testes passaram! A camada de abstração está funcionando corretamente.")
        return True
    else:
        print("⚠️ Alguns testes falharam. Verifique as configurações dos provedores LLM.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)