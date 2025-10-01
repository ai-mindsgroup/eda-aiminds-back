#!/usr/bin/env python3
"""Teste focado na distribuição de classes"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_class_distribution():
    """Testa especificamente a pergunta sobre distribuição de classes"""
    
    print("🧪 Teste Distribuição de Classes")
    print("=" * 50)
    
    # Inicializar orquestrador
    print("🔧 Inicializando orquestrador...")
    orchestrator = OrchestratorAgent("orchestrator")
    print("✅ Orquestrador inicializado")
    
    # Pergunta sobre distribuição de classes
    query = "Qual é a distribuição das classes de fraude? Quantos % são normais vs fraudulentas?"
    print(f"\n❓ Pergunta: {query}")
    print("🔄 Processando...")
    
    result = orchestrator.process(query)
    
    if result:
        print("\n✅ Sucesso!")
        print("🤖 Resposta:")
        print(result.get("content", "Sem resposta"))
        
        metadata = result.get("metadata", {})
        print(f"\n🛠️ Agentes usados: {', '.join(metadata.get('agents_used', []))}")
        print(f"🤖 Provedor LLM: {metadata.get('provider', 'N/A')}")
        print(f"⏱️ Tempo: {metadata.get('processing_time', 0):.2f}s")
        
        if metadata.get("error", False):
            print("🎯 Resultado: ❌ FALHA")
            return False
        else:
            print("🎯 Resultado: ✅ SUCESSO")
            return True
    else:
        print("❌ Erro: Nenhuma resposta recebida")
        return False

if __name__ == "__main__":
    success = test_class_distribution()
    exit(0 if success else 1)