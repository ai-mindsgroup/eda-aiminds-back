#!/usr/bin/env python3
"""
Teste: Verificação de Base de Dados
===================================

Testa se o sistema verifica corretamente a base de dados antes de responder.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_sem_dados():
    """Testa resposta quando não há dados carregados."""
    print("🧪 TESTE 1: Pergunta sem dados carregados")
    print("="*50)
    
    orchestrator = OrchestratorAgent()
    
    # Pergunta que precisa de dados específicos
    query = "Quais são os tipos de dados (numéricos, categóricos)?"
    print(f"❓ Pergunta: {query}")
    
    result = orchestrator.process(query)
    
    print(f"\n📄 Resposta:")
    print(result.get('content', ''))
    
    metadata = result.get('metadata', {})
    print(f"\n🔍 Metadados:")
    print(f"   - Erro: {metadata.get('error', False)}")
    print(f"   - Requer dados: {metadata.get('requires_data', False)}")
    print(f"   - Dados disponíveis: {metadata.get('data_available', True)}")
    print(f"   - Agentes usados: {metadata.get('agents_used', [])}")
    
    return result

def test_com_dados():
    """Testa resposta quando há dados carregados."""
    print("\n🧪 TESTE 2: Pergunta com dados carregados")
    print("="*50)
    
    orchestrator = OrchestratorAgent()
    
    # Primeiro carregar dados
    print("🔄 Carregando dados...")
    load_result = orchestrator.process("carregar arquivo data/creditcard_test_500.csv")
    
    if load_result.get('metadata', {}).get('error', False):
        print(f"❌ Erro no carregamento: {load_result.get('content')}")
        return None
    
    print("✅ Dados carregados com sucesso!")
    
    # Agora fazer a pergunta sobre tipos de dados
    query = "Quais são os tipos de dados (numéricos, categóricos)?"
    print(f"\n❓ Pergunta: {query}")
    
    result = orchestrator.process(query)
    
    print(f"\n📄 Resposta:")
    print(result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', ''))
    
    metadata = result.get('metadata', {})
    print(f"\n🔍 Metadados:")
    print(f"   - Erro: {metadata.get('error', False)}")
    print(f"   - Agentes usados: {metadata.get('agents_used', [])}")
    
    return result

def main():
    print("🚀 TESTE: VERIFICAÇÃO DE BASE DE DADOS")
    print("="*60)
    
    try:
        # Teste 1: Sem dados
        result1 = test_sem_dados()
        
        # Teste 2: Com dados
        result2 = test_com_dados()
        
        print("\n🎯 RESUMO DOS TESTES")
        print("="*30)
        
        # Verificar se o teste 1 detectou corretamente a falta de dados
        metadata1 = result1.get('metadata', {})
        if metadata1.get('requires_data') and not metadata1.get('data_available', True):
            print("✅ TESTE 1: Sistema detectou corretamente a falta de dados")
        else:
            print("❌ TESTE 1: Sistema não detectou a falta de dados")
        
        # Verificar se o teste 2 usou os dados corretamente
        if result2:
            metadata2 = result2.get('metadata', {})
            agents_used = metadata2.get('agents_used', [])
            if 'llm_manager' in agents_used:
                print("✅ TESTE 2: Sistema usou o LLM Manager corretamente")
                if len(agents_used) > 1:
                    print(f"✅ TESTE 2: Múltiplos agentes registrados: {agents_used}")
                else:
                    print("⚠️ TESTE 2: Apenas LLM Manager registrado (pode ser correto)")
            else:
                print("❌ TESTE 2: LLM Manager não foi registrado")
        else:
            print("❌ TESTE 2: Falhou no carregamento de dados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)