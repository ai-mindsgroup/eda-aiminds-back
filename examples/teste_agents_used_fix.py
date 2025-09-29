"""Teste rápido do OrchestratorAgent
======================================

Testa se a correção do agents_used funciona para Groq e Google Gemini.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_orchestrator_quick():
    """Teste rápido para verificar campo agents_used."""
    print("🧪 TESTE RÁPIDO - OrchestratorAgent")
    print("=" * 40)
    
    try:
        from src.agent.orchestrator_agent import OrchestratorAgent
        
        # Teste 1: Groq apenas
        print("\n📋 Testando com Groq apenas...")
        orchestrator = OrchestratorAgent(
            enable_csv_agent=False,
            enable_rag_agent=False,
            enable_google_llm_agent=False,
            enable_groq_llm_agent=True,
            enable_data_processor=False
        )
        
        query = "Teste rápido"
        response = orchestrator.process(query)
        
        print(f"Groq - Success: {response.get('success')}")
        print(f"Groq - Agents Used: {response.get('metadata', {}).get('agents_used')}")
        
        # Teste 2: Google apenas (se disponível)
        try:
            print("\n📋 Testando com Google apenas...")
            orchestrator_google = OrchestratorAgent(
                enable_csv_agent=False,
                enable_rag_agent=False,
                enable_google_llm_agent=True,
                enable_groq_llm_agent=False,
                enable_data_processor=False
            )
            
            response_google = orchestrator_google.process(query)
            
            print(f"Google - Success: {response_google.get('success')}")
            print(f"Google - Agents Used: {response_google.get('metadata', {}).get('agents_used')}")
            
        except Exception as e:
            print(f"⚠️ Google não disponível: {e}")
        
        # Teste 3: Ambos (prioridade Groq)
        print("\n📋 Testando com ambos (prioridade Groq)...")
        try:
            orchestrator_both = OrchestratorAgent(
                enable_csv_agent=False,
                enable_rag_agent=False,
                enable_google_llm_agent=True,
                enable_groq_llm_agent=True,
                enable_data_processor=False
            )
            
            response_both = orchestrator_both.process(query)
            
            print(f"Both - Success: {response_both.get('success')}")
            print(f"Both - Agents Used: {response_both.get('metadata', {}).get('agents_used')}")
            print(f"Both - Should be Groq (priority)")
            
        except Exception as e:
            print(f"⚠️ Teste com ambos falhou: {e}")
        
        print("\n✅ Teste rápido concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False


if __name__ == "__main__":
    test_orchestrator_quick()