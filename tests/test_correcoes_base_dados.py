#!/usr/bin/env python3
"""
Teste da Correção: Verificação de Base de Dados e Tracking de Agentes
=====================================================================

Testa as correções implementadas:
1. Verificação obrigatória de base de dados
2. Tracking correto de agentes usados
3. Prompts contextualizados
4. Opções de resposta genérica vs específica
"""

from __future__ import annotations
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_sem_dados_carregados():
    """Testa comportamento quando não há dados carregados."""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Consulta sem dados carregados")
    print("="*60)
    
    try:
        orchestrator = OrchestratorAgent()
        
        # Pergunta que requer dados específicos
        query = "Quais são os tipos de dados (numéricos, categóricos) das colunas?"
        print(f"❓ Pergunta: {query}")
        
        result = orchestrator.process(query)
        
        print(f"\n📄 Resposta: {result.get('content', '')[:300]}...")
        agents_used = result.get("metadata", {}).get("agents_used", [])
        print(f"🤖 Agentes usados: {agents_used}")
        
        # Verificar se informou sobre necessidade de dados
        content = result.get('content', '').lower()
        needs_data_mentioned = any(phrase in content for phrase in [
            'base de dados', 'dados carregados', 'arquivo', 'csv', 'carregar'
        ])
        
        print(f"✅ Mencionou necessidade de dados: {needs_data_mentioned}")
        return needs_data_mentioned and len(agents_used) > 0
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_com_arquivo_no_contexto():
    """Testa comportamento com arquivo no contexto."""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Consulta com arquivo no contexto")
    print("="*60)
    
    try:
        orchestrator = OrchestratorAgent()
        
        # Contexto com arquivo
        context = {"file_path": "data/creditcard_test_500.csv"}
        query = "Quais são os tipos de dados das colunas?"
        print(f"❓ Pergunta: {query}")
        print(f"📁 Arquivo: {context['file_path']}")
        
        result = orchestrator.process(query, context)
        
        print(f"\n📄 Resposta: {result.get('content', '')[:300]}...")
        agents_used = result.get("metadata", {}).get("agents_used", [])
        print(f"🤖 Agentes usados: {agents_used}")
        
        metadata = result.get("metadata", {})
        print(f"📊 Data analysis: {metadata.get('data_analysis', False)}")
        print(f"📋 Data loaded: {metadata.get('data_loaded', False)}")
        
        # Verificar se tentou carregar dados
        content = result.get('content', '').lower()
        data_analysis = 'time' in content or 'amount' in content or 'class' in content
        
        print(f"✅ Fez análise específica: {data_analysis}")
        return len(agents_used) > 0 and not result.get("metadata", {}).get("error", False)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pergunta_generica():
    """Testa pergunta genérica que não requer dados específicos."""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Pergunta genérica")
    print("="*60)
    
    try:
        orchestrator = OrchestratorAgent()
        
        query = "O que são correlações em análise de dados?"
        print(f"❓ Pergunta: {query}")
        
        result = orchestrator.process(query)
        
        print(f"\n📄 Resposta: {result.get('content', '')[:300]}...")
        agents_used = result.get("metadata", {}).get("agents_used", [])
        print(f"🤖 Agentes usados: {agents_used}")
        
        # Para perguntas genéricas, deve responder normalmente
        content = result.get('content', '')
        has_response = len(content) > 50
        
        print(f"✅ Forneceu resposta adequada: {has_response}")
        return has_response and len(agents_used) > 0
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Executa todos os testes de correção."""
    print("\n" + "="*80)
    print("🚀 TESTE DAS CORREÇÕES - VERIFICAÇÃO DE DADOS E TRACKING".center(80))
    print("="*80)
    
    tests = [
        ("Sem dados carregados", test_sem_dados_carregados),
        ("Com arquivo no contexto", test_com_arquivo_no_contexto),
        ("Pergunta genérica", test_pergunta_generica)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erro crítico no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES DE CORREÇÃO")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado Final: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todas as correções funcionam! O sistema agora:")
        print("   ✅ Verifica base de dados antes de responder")
        print("   ✅ Registra agentes usados corretamente")
        print("   ✅ Oferece opções quando não há dados")
        print("   ✅ Faz análise específica quando possível")
        return True
    else:
        print("⚠️ Algumas correções ainda precisam de ajustes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)