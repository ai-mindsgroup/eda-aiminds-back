#!/usr/bin/env python3
"""Teste simplificado da pergunta original sem RAG"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_simple_question():
    """Teste da pergunta original com sistema simplificado"""
    
    print("🚀 Teste Simplificado da Pergunta Original")
    print("=" * 50)
    
    # Inicializar orquestrador apenas com agentes essenciais
    print("🔧 Inicializando orquestrador...")
    orchestrator = OrchestratorAgent("orchestrator")
    
    print("✅ Orquestrador inicializado")
    
    # Fazer pergunta sobre tipos de dados
    query = "Quais são os tipos de dados (numéricos, categóricos)?"
    print(f"\n❓ Pergunta: {query}")
    print("🔄 Processando...")
    
    # Processar consulta
    result = orchestrator.process(query)
    
    if result:
        print("\n✅ Sucesso!")
        print("=" * 50)
        print("🤖 Resposta:")
        print(result.get("content", "Sem resposta"))
        print("=" * 50)
        
        # Mostrar metadados
        metadata = result.get("metadata", {})
        agents_used = metadata.get("agents_used", [])
        print(f"🛠️ Agentes usados: {', '.join(agents_used)}")
        
        if metadata.get("error", False):
            print("🎯 Resultado: ❌ FALHA")
            return False
        else:
            print("🎯 Resultado: ✅ SUCESSO")
            return True
    else:
        print("❌ Erro: Nenhuma resposta recebida")
        print("🎯 Resultado: ❌ FALHA")
        return False

if __name__ == "__main__":
    success = test_simple_question()
    exit(0 if success else 1)