#!/usr/bin/env python3
"""Teste para validar correção do erro 'dict' object has no attribute 'char_count'"""

import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_rag_correction():
    """Testa se a correção do RAG Agent funciona corretamente"""
    print("🧪 Teste: Validação da correção do RAG Agent")
    print("=" * 60)
    
    try:
        # Inicializar orquestrador
        print("🔧 Inicializando sistema...")
        orchestrator = OrchestratorAgent("orchestrator")
        print("✅ Sistema inicializado com sucesso!")
        
        # Teste 1: Pergunta sobre tipos de dados
        print("\n📝 Teste 1: Pergunta sobre tipos de dados")
        print("-" * 60)
        query = "Quais são os tipos de dados (numéricos, categóricos)?"
        
        print(f"🔄 Processando consulta: '{query}'")
        response = orchestrator.process(query)
        
        if response and 'answer' in response:
            print("✅ Resposta gerada com sucesso!")
            print(f"\n🤖 Resposta:\n{response['answer'][:500]}...")
            
            # Verificar se não há erro no processamento
            if 'error' not in response or not response.get('error'):
                print("\n✅ TESTE PASSOU: Nenhum erro detectado no processamento RAG")
                return True
            else:
                print(f"\n❌ TESTE FALHOU: Erro detectado - {response.get('error')}")
                return False
        else:
            print("❌ TESTE FALHOU: Resposta inválida ou vazia")
            return False
            
    except Exception as e:
        print(f"\n❌ TESTE FALHOU: Exceção capturada - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_correction()
    sys.exit(0 if success else 1)
