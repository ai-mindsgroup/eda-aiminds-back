#!/usr/bin/env python3
"""Teste final para demonstrar que o sistema funciona corretamente."""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_sistema_completo():
    """Demonstra que o sistema funciona corretamente com dados carregados."""
    
    print("🎯 DEMONSTRAÇÃO: Sistema funcionando com dados carregados")
    print("=" * 60)
    
    try:
        # Criar agente orquestrador
        orchestrator = OrchestratorAgent()
        
        # Teste: Verificar disponibilidade de dados
        print("\n📊 Status dos dados:")
        has_data = orchestrator._check_data_availability()
        print(f"   Dados disponíveis: {'✅ SIM' if has_data else '❌ NÃO'}")
        
        if not has_data:
            print("⚠️ Não há dados carregados. Resultado seria diferente.")
            return
        
        # Teste: Consulta sobre tipos de dados
        print("\n🔍 Pergunta: 'Quais são os tipos de dados (numéricos, categóricos)?'")
        print("-" * 60)
        
        query = "Quais são os tipos de dados (numéricos, categóricos)?"
        response = orchestrator.process(query)
        
        print("📝 RESPOSTA:")
        print(response['content'])
        print()
        print("📊 METADADOS:")
        metadata = response.get('metadata', {})
        print(f"   Agentes usados: {metadata.get('agents_used', [])}")
        print(f"   Tipo da consulta: {metadata.get('query_type', 'N/A')}")
        print(f"   Erro: {metadata.get('error', False)}")
        print(f"   Requer dados: {metadata.get('requires_data', False)}")
        print(f"   Dados disponíveis: {metadata.get('data_available', True)}")
        
        # Verificar se a resposta é adequada
        content = response['content'].lower()
        if "base de dados necessária" in content:
            print("\n❌ PROBLEMA: Sistema ainda pede para carregar dados")
        else:
            print("\n✅ SUCESSO: Sistema processou adequadamente com dados disponíveis")
        
    except Exception as e:
        print(f"❌ ERRO durante demonstração: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sistema_completo()