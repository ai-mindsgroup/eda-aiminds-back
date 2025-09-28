#!/usr/bin/env python3
"""
Teste do Sistema com LLM Agent
=============================

Este script testa especificamente se o GoogleLLMAgent está sendo chamado
pelo OrchestratorAgent.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_llm_integration():
    """Testa se o LLM Agent está sendo utilizado."""
    print("\n🧪 TESTE DE INTEGRAÇÃO LLM AGENT")
    print("=" * 50)
    
    # Inicializar orquestrador
    print("🔧 Inicializando orquestrador...")
    try:
        orchestrator = OrchestratorAgent()
        agents = list(orchestrator.agents.keys())
        print(f"✅ Agentes disponíveis: {', '.join(agents)}")
        
        # Verificar se LLM está disponível
        if "llm" in agents:
            print("✅ Google LLM Agent está disponível!")
        else:
            print("⚠️ Google LLM Agent NÃO está disponível")
            return
            
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        return
    
    # Testes específicos para acionar LLM
    test_queries = [
        "explique os padrões de fraude",
        "qual sua conclusão sobre os dados?",
        "dê uma recomendação baseada na análise",  
        "interprete os resultados",
        "faça um sumário detalhado",
    ]
    
    print(f"\n🎯 Testando {len(test_queries)} consultas LLM:")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Teste {i}/5 ---")
        print(f"❓ Consulta: '{query}'")
        
        try:
            result = orchestrator.process(query)
            
            # Debug: ver toda a estrutura da resposta
            print(f"📋 Estrutura resposta: {result.keys() if isinstance(result, dict) else type(result)}")
            
            # Verificar se LLM foi usado  
            metadata = result.get("metadata", {})
            orchestrator_meta = metadata.get("orchestrator", {})
            agents_used = orchestrator_meta.get("agents_used", metadata.get("agents_used", []))
            llm_used = metadata.get("llm_used", False)
            
            print(f"📝 Tipo identificado: {metadata.get('query_type', 'unknown')}")
            print(f"🤖 Agentes usados: {agents_used}")
            print(f"🧠 LLM usado: {llm_used}")
            
            if "llm" in agents_used or llm_used:
                print("✅ LLM Agent foi utilizado!")
                content = result.get("content", "")
                if content:
                    print(f"💬 Resposta: {content[:100]}...")
                else:
                    print("⚠️ Resposta vazia")
            else:
                print("⚠️ LLM Agent NÃO foi utilizado")
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
    
    print(f"\n🏁 Teste concluído!")

def test_with_data_context():
    """Testa LLM com contexto de dados."""
    print("\n🧪 TESTE LLM COM CONTEXTO DE DADOS")
    print("=" * 50)
    
    try:
        orchestrator = OrchestratorAgent()
        
        # Simular contexto de dados carregados
        context = {
            "file_path": "examples/dados_exemplo.csv",
            "data_info": {
                "rows": 1000,
                "columns": 7,
                "fraud_detected": 44
            }
        }
        
        llm_queries = [
            "interprete esses dados de fraude",
            "que conclusões você tira?",
            "recomende próximos passos"
        ]
        
        for query in llm_queries:
            print(f"\n❓ Consulta com contexto: '{query}'")
            
            result = orchestrator.process(query, context=context)
            
            # Debug: ver estrutura completa
            metadata = result.get("metadata", {})
            orchestrator_meta = metadata.get("orchestrator", {})
            agents_used = orchestrator_meta.get("agents_used", metadata.get("agents_used", []))
            llm_used = metadata.get("llm_used", False)
            
            print(f"🤖 Agentes usados: {agents_used}")
            print(f"🧠 LLM usado: {llm_used}")
            
            if "llm" in agents_used or llm_used:
                print("✅ LLM processou consulta com contexto!")
                content = result.get("content", "")
                if content:
                    print(f"💬 Resposta: {content[:200]}...")
            else:
                print("⚠️ LLM não foi utilizado")
                
    except Exception as e:
        print(f"❌ Erro no teste com contexto: {e}")

if __name__ == "__main__":
    test_llm_integration()
    test_with_data_context()