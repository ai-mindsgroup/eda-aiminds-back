#!/usr/bin/env python3
"""Teste para verificar se a correção da verificação de dados funciona."""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_verificacao_dados_corrigida():
    """Testa se o sistema agora detecta corretamente dados na base."""
    
    print("🧪 TESTE: Verificação de dados corrigida")
    print("=" * 50)
    
    try:
        # Criar agente orquestrador
        orchestrator = OrchestratorAgent()
        
        # Teste 1: Verificar se detecta dados na base
        print("\n📊 TESTE 1: Verificando detecção de dados na base...")
        has_data = orchestrator._check_data_availability()
        print(f"   Resultado: {has_data}")
        
        if has_data:
            print("   ✅ SUCESSO: Sistema detectou dados na base de dados!")
        else:
            print("   ❌ FALHA: Sistema ainda não detecta dados na base")
            return False
        
        # Teste 2: Testar consulta que requer dados específicos
        print("\n📊 TESTE 2: Testando consulta 'Quais são os tipos de dados?'...")
        query = "Quais são os tipos de dados (numéricos, categóricos)?"
        response = orchestrator.process(query)
        
        print(f"   Resposta: {response['content'][:100]}...")
        print(f"   Agentes usados: {response.get('metadata', {}).get('agents_used', [])}")
        print(f"   Erro: {response.get('metadata', {}).get('error', False)}")
        
        # Verificar se não retornou a mensagem de "Base de Dados Necessária"
        if "Base de Dados Necessária" in response['content']:
            print("   ❌ FALHA: Sistema ainda pede para carregar dados")
            return False
        else:
            print("   ✅ SUCESSO: Sistema processou a consulta corretamente!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste de verificação de dados corrigida...")
    
    success = test_verificacao_dados_corrigida()
    
    if success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema agora detecta corretamente dados na base de dados")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("ℹ️ Verifique os logs acima para detalhes")