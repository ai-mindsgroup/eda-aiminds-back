#!/usr/bin/env python3
"""
Teste do Sistema de Fallback LLM
=================================

Este script testa especificamente o sistema de fallback:
Grok (primary) -> Google LLM (fallback) no OrchestratorAgent.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_orchestrator_fallback():
    """Testa o sistema de fallback no orquestrador."""
    print("🧪 TESTE DO SISTEMA DE FALLBACK LLM")
    print("=" * 50)
    
    try:
        # Verificar configurações
        from src.settings import GROK_API_KEY, GOOGLE_API_KEY
        print(f"🔑 GROK_API_KEY: {'✅ Configurado' if GROK_API_KEY else '❌ Ausente'}")
        print(f"🔑 GOOGLE_API_KEY: {'✅ Configurado' if GOOGLE_API_KEY else '❌ Ausente'}")
        
        # Inicializar orquestrador
        print("\n🔧 Inicializando OrchestratorAgent...")
        from src.agent.orchestrator_agent import OrchestratorAgent
        
        orchestrator = OrchestratorAgent(
            enable_csv_agent=False,        # Desabilitar para simplicidade
            enable_rag_agent=False,        # Desabilitar para simplicidade  
            enable_google_llm_agent=True,  # Habilitar Google como fallback
            enable_grok_llm_agent=True,    # Habilitar Grok como primary
            enable_data_processor=False    # Desabilitar para simplicidade
        )
        
        # Verificar agentes disponíveis
        agents = list(orchestrator.agents.keys())  
        print(f"✅ Agentes inicializados: {', '.join(agents)}")
        
        if "grok" in agents:
            print("🎯 Grok LLM disponível (primary)")
        if "llm" in agents:
            print("📱 Google LLM disponível (fallback)")
        
        # Testar consulta que aciona LLM
        test_query = "Explique os principais indicadores de fraude em transações financeiras"
        print(f"\n📝 Consulta: {test_query}")
        
        print("🚀 Processando consulta...")
        result = orchestrator.process(test_query)
        
        # Analisar resultado
        metadata = result.get('metadata', {})
        agents_used = metadata.get('agents_used', [])
        success = metadata.get('success', False)
        
        print(f"\n📊 RESULTADO:")
        print(f"   ✅ Sucesso: {success}")
        print(f"   🤖 Agentes usados: {', '.join(agents_used)}")
        
        if 'grok' in agents_used:
            print("   🎯 Grok foi utilizado! (Primary LLM)")
        elif 'llm' in agents_used:
            print("   📱 Google LLM foi utilizado! (Fallback funcionou)")
        else:
            print("   ⚠️ Nenhum LLM foi utilizado")
        
        content = result.get('content', '')
        if content and success:
            print(f"\n💬 Resposta (primeiros 200 chars):")
            print(f"   {content[:200]}...")
        elif not success:
            print(f"\n❌ Erro: {content}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro no teste de fallback: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_classification():
    """Testa se o orquestrador classifica corretamente consultas para LLM."""
    print("\n🧪 TESTE DE CLASSIFICAÇÃO DE CONSULTAS")
    print("=" * 50)
    
    try:
        from src.agent.orchestrator_agent import OrchestratorAgent
        orchestrator = OrchestratorAgent(
            enable_csv_agent=False,
            enable_rag_agent=False,
            enable_google_llm_agent=True,
            enable_grok_llm_agent=True,
            enable_data_processor=False
        )
        
        # Queries que devem acionar LLM
        llm_queries = [
            "explique padrões de fraude",
            "analise correlações nos dados", 
            "como interpretar anomalias",
            "quais são os principais indicadores de risco"
        ]
        
        for i, query in enumerate(llm_queries, 1):
            print(f"\n{i}️⃣ Query: {query}")
            
            # Classificar consulta (método interno)
            query_type = orchestrator._classify_query(query)
            print(f"   📋 Classificação: {query_type.value}")
            
            if query_type.value == "llm_analysis":
                print("   ✅ Corretamente classificada para LLM")
            else:
                print("   ⚠️ Não classificada para LLM")
        
    except Exception as e:
        print(f"❌ Erro na classificação: {e}")

def main():
    """Executa testes do sistema de fallback."""
    print("🚀 INICIANDO TESTES DO SISTEMA DE FALLBACK")
    print("=" * 60)
    
    # Teste 1: Fallback functionality
    success = test_orchestrator_fallback()
    
    # Teste 2: Query classification  
    test_llm_classification()
    
    print("\n🏁 TESTES CONCLUÍDOS")
    print("=" * 60)
    
    if success:
        print("✅ Sistema de fallback funcionando!")
    else:
        print("⚠️ Verificar configurações de API keys")

if __name__ == "__main__":
    main()