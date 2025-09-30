#!/usr/bin/env python3
"""
Teste Rápido: Pergunta Específica sobre Tipos de Dados
======================================================

Testa se a pergunta original funciona com o novo sistema.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def main():
    print("🚀 Teste da Pergunta Original")
    print("="*50)
    
    try:
        # Inicializar orquestrador
        print("🔧 Inicializando orquestrador...")
        orchestrator = OrchestratorAgent()
        print("✅ Orquestrador inicializado")
        
        # A pergunta original que estava falhando
        query = "Quais são os tipos de dados (numéricos, categóricos)?"
        print(f"\n❓ Pergunta: {query}")
        print("🔄 Processando...")
        
        # Processar
        result = orchestrator.process(query)
        
        # Verificar resultado
        if result.get("metadata", {}).get("error", False):
            print(f"\n❌ Erro: {result.get('content')}")
            return False
        else:
            print(f"\n✅ Sucesso!")
            print("="*50)
            print("🤖 Resposta:")
            print(result.get('content', ''))
            print("="*50)
            
            agents_used = result.get("metadata", {}).get("agents_used", [])
            print(f"🛠️ Agentes usados: {', '.join(agents_used) if agents_used else 'Nenhum'}")
            return True
            
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🎯 Resultado: {'✅ SUCESSO' if success else '❌ FALHA'}")
    sys.exit(0 if success else 1)