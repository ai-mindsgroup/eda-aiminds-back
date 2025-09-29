#!/usr/bin/env python3
"""
Teste Simples do Grok LLM Agent
===============================

Este script testa apenas o GrokLLMAgent diretamente sem dependências complexas.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_grok_direct():
    """Testa o GrokLLMAgent diretamente."""
    print("\n🧪 TESTE DIRETO DO GROK LLM AGENT")
    print("=" * 50)
    
    try:
        # Verificar se GROK_API_KEY está configurado
        from src.settings import GROK_API_KEY
        if not GROK_API_KEY:
            print("❌ GROK_API_KEY não está configurado!")
            print("   Configure em configs/.env antes de executar os testes.")
            return
        else:
            print(f"✅ GROK_API_KEY configurado: {GROK_API_KEY[:10]}...")
        
        # Importar e inicializar agente Grok
        from src.agent.grok_llm_agent import GrokLLMAgent
        
        print("🔧 Inicializando GrokLLMAgent...")
        grok_agent = GrokLLMAgent()
        print(f"✅ Agente Grok inicializado: {grok_agent.name}")
        
        # Teste básico
        test_query = "Explique em 2 parágrafos como detectar padrões suspeitos em transações financeiras."
        print(f"\n📝 Query: {test_query}")
        
        print("🚀 Enviando consulta para Grok...")
        result = grok_agent.process(test_query)
        
        print(f"\n📊 Resultado:")
        metadata = result.get('metadata', {})
        print(f"   Sucesso: {metadata.get('success', False)}")
        print(f"   Modelo: {metadata.get('model', 'N/A')}")
        print(f"   Cache usado: {metadata.get('cache_used', False)}")
        print(f"   LLM usado: {metadata.get('llm_used', False)}")
        
        if 'usage' in metadata:
            usage = metadata['usage']
            print(f"   Tokens usados: {usage.get('total_tokens', 'N/A')}")
        
        content = result.get('content', '')
        if content:
            print(f"\n💬 Resposta:")
            print(f"{content}")
        else:
            print(f"\n❌ Nenhum conteúdo retornado")
            if 'error' in result:
                print(f"   Erro: {result.get('error', 'Desconhecido')}")
            
    except Exception as e:
        print(f"❌ Erro no teste direto: {e}")
        import traceback
        traceback.print_exc()

def test_grok_specialized_methods():
    """Testa métodos especializados do Grok."""
    print("\n🧪 TESTE DOS MÉTODOS ESPECIALIZADOS")
    print("=" * 50)
    
    try:
        from src.agent.grok_llm_agent import GrokLLMAgent
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
        success = result.get('metadata', {}).get('success', False)
        print(f"   Resultado: {'✅ Sucesso' if success else '❌ Falha'}")
        
        if success:
            content = result.get('content', '')[:200]
            print(f"   Resumo: {content}...")
        
    except Exception as e:
        print(f"❌ Erro nos testes especializados: {e}")

def main():
    """Executa testes simples do Grok LLM Agent."""
    print("🚀 INICIANDO TESTES SIMPLES DO GROK LLM AGENT")
    print("=" * 60)
    
    test_grok_direct()
    test_grok_specialized_methods()
    
    print("\n🏁 TESTES CONCLUÍDOS")
    print("=" * 60)

if __name__ == "__main__":
    main()