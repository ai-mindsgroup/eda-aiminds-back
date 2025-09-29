#!/usr/bin/env python3
"""
Teste do Grok LLM Agent
======================

Este script testa especificamente se o GrokLLMAgent está funcionando
corretamente integrado ao sistema multiagente.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.agent.grok_llm_agent import GrokLLMAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_grok_direct():
    """Testa o GrokLLMAgent diretamente."""
    print("\n🧪 TESTE DIRETO DO GROK LLM AGENT")
    print("=" * 50)
    
    try:
        # Inicializar agente Grok diretamente
        grok_agent = GrokLLMAgent()
        print(f"✅ Agente Grok inicializado: {grok_agent.name}")
        
        # Teste básico
        test_query = "Explique como detectar padrões suspeitos em transações financeiras."
        print(f"\n📝 Query: {test_query}")
        
        result = grok_agent.process(test_query)
        
        print(f"\n📊 Resultado:")
        print(f"   Sucesso: {result.get('metadata', {}).get('success', False)}")
        print(f"   Modelo: {result.get('metadata', {}).get('model', 'N/A')}")
        print(f"   Cache usado: {result.get('metadata', {}).get('cache_used', False)}")
        print(f"   LLM usado: {result.get('metadata', {}).get('llm_used', False)}")
        
        content = result.get('content', '')
        if content:
            print(f"\n💬 Resposta (primeiros 300 chars):")
            print(f"   {content[:300]}...")
        else:
            print(f"\n❌ Nenhum conteúdo retornado")
            
    except Exception as e:
        print(f"❌ Erro no teste direto: {e}")
        import traceback
        traceback.print_exc()

def test_grok_via_orchestrator():
    """Testa o Grok via OrchestratorAgent."""
    print("\n🧪 TESTE VIA ORCHESTRATOR")
    print("=" * 50)
    
    try:
        # Inicializar orquestrador
        print("🔧 Inicializando orquestrador...")
        orchestrator = OrchestratorAgent()
        
        # Verificar agentes disponíveis
        agents = list(orchestrator.agents.keys())
        print(f"✅ Agentes disponíveis: {', '.join(agents)}")
        
        if "grok" in agents:
            print("✅ Grok LLM Agent está disponível no orquestrador!")
        else:
            print("⚠️ Grok LLM Agent NÃO está disponível no orquestrador")
            if "llm" in agents:
                print("ℹ️ Google LLM Agent disponível como fallback")
        
        # Testar consultas que acionam análise LLM
        test_queries = [
            "analise os padrões de fraude em cartões de crédito",
            "explique correlações entre variáveis financeiras",
            "quais são os principais indicadores de transações suspeitas?",
            "como interpretar anomalias em dados de pagamento?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Teste {i}: {query}")
            
            try:
                result = orchestrator.process(query)
                
                metadata = result.get('metadata', {})
                agents_used = metadata.get('agents_used', [])
                success = metadata.get('success', False)
                
                print(f"   ✅ Sucesso: {success}")
                print(f"   🤖 Agentes usados: {', '.join(agents_used)}")
                
                if 'grok' in agents_used:
                    print("   🎯 Grok foi utilizado!")
                elif 'llm' in agents_used:
                    print("   📱 Google LLM foi utilizado (fallback)")
                
                content = result.get('content', '')
                if content and success:
                    print(f"   💬 Resposta: {content[:100]}...")
                elif not success:
                    print(f"   ❌ Erro: {content}")
                    
            except Exception as e:
                print(f"   ❌ Erro na consulta: {e}")
                
    except Exception as e:
        print(f"❌ Erro na inicialização do orquestrador: {e}")
        import traceback
        traceback.print_exc()

def test_grok_specialized_methods():
    """Testa métodos especializados do Grok."""
    print("\n🧪 TESTE DOS MÉTODOS ESPECIALIZADOS")
    print("=" * 50)
    
    try:
        grok_agent = GrokLLMAgent()
        
        # Teste 1: Análise de insights
        print("\n1️⃣ Testando analyze_data_insights:")
        data_summary = {
            "rows": 10000,
            "columns": 15,
            "fraud_rate": 0.03,
            "missing_values": 250,
            "top_correlations": ["amount_transaction_hour", "merchant_category_amount"]
        }
        
        result = grok_agent.analyze_data_insights(data_summary)
        if result.get('metadata', {}).get('success'):
            print("   ✅ Insights gerados com sucesso")
        else:
            print("   ❌ Falha na geração de insights")
        
        # Teste 2: Detecção de fraude
        print("\n2️⃣ Testando detect_fraud_patterns:")
        fraud_data = {
            "total_transactions": 10000,
            "fraud_count": 300,
            "fraud_rate": 0.03,
            "top_fraud_indicators": ["high_amount", "unusual_time", "new_merchant"]
        }
        
        result = grok_agent.detect_fraud_patterns(fraud_data)
        if result.get('metadata', {}).get('success'):
            print("   ✅ Padrões de fraude analisados com sucesso")
        else:
            print("   ❌ Falha na análise de fraude")
        
        # Teste 3: Explicação de correlações
        print("\n3️⃣ Testando explain_correlations:")
        correlation_data = {
            "strong_correlations": [
                {"variables": ["amount", "transaction_hour"], "correlation": 0.75},
                {"variables": ["merchant_category", "location"], "correlation": -0.65}
            ]
        }
        
        result = grok_agent.explain_correlations(correlation_data)
        if result.get('metadata', {}).get('success'):
            print("   ✅ Correlações explicadas com sucesso")
        else:
            print("   ❌ Falha na explicação de correlações")
            
    except Exception as e:
        print(f"❌ Erro nos testes especializados: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Executa todos os testes do Grok LLM Agent."""
    print("🚀 INICIANDO TESTES DO GROK LLM AGENT")
    print("=" * 60)
    
    # Verificar se GROK_API_KEY está configurado
    from src.settings import GROK_API_KEY
    if not GROK_API_KEY:
        print("❌ GROK_API_KEY não está configurado!")
        print("   Configure em configs/.env antes de executar os testes.")
        return
    else:
        print(f"✅ GROK_API_KEY configurado: {GROK_API_KEY[:10]}...")
    
    # Executar testes
    test_grok_direct()
    test_grok_via_orchestrator()
    test_grok_specialized_methods()
    
    print("\n🏁 TESTES CONCLUÍDOS")
    print("=" * 60)

if __name__ == "__main__":
    main()