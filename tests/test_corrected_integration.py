#!/usr/bin/env python3
"""
Teste de Integração - Módulos Corrigidos
==========================================

Valida que os módulos corrigidos estão integrados no fluxo principal.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path.cwd()))

import pytest
from src.agent.orchestrator_agent import OrchestratorAgent
from src.agent.query_analyzer import QueryAnalyzer
from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2


class TestCorrectedIntegration:
    """Testes de integração para módulos corrigidos."""
    
    def test_orchestrator_uses_query_analyzer(self):
        """Verificar que Orchestrator usa QueryAnalyzer."""
        orchestrator = OrchestratorAgent()
        
        # Verificar que analyzer existe
        assert hasattr(orchestrator, 'analyzer'), \
            "Orchestrator deve ter atributo 'analyzer'"
        assert orchestrator.analyzer is not None, \
            "Analyzer não deve ser None"
        
        # Verificar que é a classe correta
        assert isinstance(orchestrator.analyzer, QueryAnalyzer), \
            f"Analyzer deve ser instância de QueryAnalyzer, é {type(orchestrator.analyzer)}"
        
        # Verificar que tem fallback heurístico
        assert hasattr(orchestrator.analyzer, '_fallback_heuristic_analysis'), \
            "QueryAnalyzer deve ter método '_fallback_heuristic_analysis'"
        
        print("✅ Orchestrator usa QueryAnalyzer correto com fallback heurístico")
    
    def test_rag_agent_uses_v2_processor(self):
        """Verificar que RAGAgent usa HybridQueryProcessorV2."""
        orchestrator = OrchestratorAgent()
        
        # Verificar que RAGAgent existe
        assert "rag" in orchestrator.agents, \
            "RAGAgent não foi inicializado no Orchestrator"
        
        rag_agent = orchestrator.agents["rag"]
        
        # Verificar que processor é V2
        assert hasattr(rag_agent, 'hybrid_processor'), \
            "RAGAgent deve ter atributo 'hybrid_processor'"
        assert rag_agent.hybrid_processor is not None, \
            "hybrid_processor não deve ser None"
        
        assert isinstance(rag_agent.hybrid_processor, HybridQueryProcessorV2), \
            f"Processor deve ser V2, é {type(rag_agent.hybrid_processor)}"
        
        print("✅ RAGAgent usa HybridQueryProcessorV2")
    
    def test_diagnostic_endpoint_exists(self):
        """Verificar que diagnóstico está disponível."""
        orchestrator = OrchestratorAgent()
        
        # Verificar que método existe
        assert hasattr(orchestrator, 'get_diagnostic_info'), \
            "Orchestrator deve ter método 'get_diagnostic_info'"
        
        # Executar diagnóstico
        diagnostic = orchestrator.get_diagnostic_info()
        
        # Verificar estrutura
        assert isinstance(diagnostic, dict), "Diagnóstico deve retornar dict"
        assert 'analyzer' in diagnostic, "Diagnóstico deve incluir 'analyzer'"
        assert 'rag_agent' in diagnostic, "Diagnóstico deve incluir 'rag_agent'"
        assert 'llm_manager' in diagnostic, "Diagnóstico deve incluir 'llm_manager'"
        
        print("✅ Método get_diagnostic_info() disponível")
    
    def test_diagnostic_shows_correct_components(self):
        """Verificar que diagnóstico retorna info correta."""
        orchestrator = OrchestratorAgent()
        
        diagnostic = orchestrator.get_diagnostic_info()
        
        # Verificar analyzer
        assert diagnostic['analyzer']['available'] is True, \
            "Analyzer deve estar disponível"
        assert diagnostic['analyzer']['class'] == 'QueryAnalyzer', \
            f"Analyzer class incorreta: {diagnostic['analyzer']['class']}"
        assert diagnostic['analyzer']['has_fallback'] is True, \
            "Analyzer deve ter fallback heurístico"
        
        # Verificar processor (se RAG agent disponível)
        if diagnostic['rag_agent']['available']:
            processor_version = diagnostic['rag_agent']['processor_version']
            assert processor_version == 'HybridQueryProcessorV2', \
                f"Processor deve ser V2, é {processor_version}"
        
        print("✅ Diagnóstico retorna informações corretas")
        print(f"  → Analyzer: {diagnostic['analyzer']['class']}")
        print(f"  → Processor: {diagnostic['rag_agent'].get('processor_version', 'N/A')}")
        print(f"  → LLM: {diagnostic['llm_manager'].get('active_provider', 'N/A')}")
    
    def test_query_analyzer_classifies_simple_stats(self):
        """Verificar que QueryAnalyzer classifica queries simples corretamente."""
        orchestrator = OrchestratorAgent()
        
        # Queries que devem ser classificadas como SIMPLE
        simple_queries = [
            "Qual a média de Amount?",
            "Qual a correlação entre Amount e Time?",
            "Mostre a mediana de Amount",
            "Qual a distribuição de Amount?"
        ]
        
        passed = 0
        failed = []
        
        for query in simple_queries:
            analysis = orchestrator.analyzer.analyze(query)
            
            if analysis.complexity == 'simple':
                passed += 1
            else:
                failed.append(f"{query} → {analysis.complexity}")
        
        success_rate = (passed / len(simple_queries)) * 100
        
        print(f"✅ Classificação de queries simples: {success_rate:.1f}% ({passed}/{len(simple_queries)})")
        
        if failed:
            print("⚠️ Queries mal classificadas:")
            for f in failed:
                print(f"  - {f}")
        
        # Esperamos pelo menos 75% de acerto (consistente com Teste 6)
        assert success_rate >= 75.0, \
            f"Taxa de acerto muito baixa: {success_rate:.1f}%"


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TESTE DE INTEGRAÇÃO - MÓDULOS CORRIGIDOS")
    print("=" * 70)
    print()
    
    # Executar testes
    tester = TestCorrectedIntegration()
    
    tests = [
        ("1. Orchestrator usa QueryAnalyzer", tester.test_orchestrator_uses_query_analyzer),
        ("2. RAGAgent usa HybridQueryProcessorV2", tester.test_rag_agent_uses_v2_processor),
        ("3. Método get_diagnostic_info() existe", tester.test_diagnostic_endpoint_exists),
        ("4. Diagnóstico retorna info correta", tester.test_diagnostic_shows_correct_components),
        ("5. QueryAnalyzer classifica queries simples", tester.test_query_analyzer_classifies_simple_stats),
    ]
    
    passed = 0
    failed = []
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: {e}")
            failed.append((name, str(e)))
        except Exception as e:
            print(f"❌ {name}: ERRO - {e}")
            failed.append((name, f"ERRO: {e}"))
        print()
    
    # Resultado final
    print("=" * 70)
    print("📊 RESULTADOS")
    print("=" * 70)
    print(f"Total de testes: {len(tests)}")
    print(f"Testes passaram: {passed}")
    print(f"Testes falharam: {len(failed)}")
    print()
    
    if failed:
        print("❌ FALHAS:")
        for name, error in failed:
            print(f"  - {name}")
            print(f"    {error}")
        print()
    
    success_rate = (passed / len(tests)) * 100
    print(f"Taxa de sucesso: {success_rate:.1f}%")
    print()
    
    if success_rate == 100:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("🎉 Integração corrigida com sucesso!")
        sys.exit(0)
    elif success_rate >= 80:
        print("⚠️ MAIORIA DOS TESTES PASSOU")
        print("🔍 Revisar falhas antes de deploy")
        sys.exit(1)
    else:
        print("❌ MUITOS TESTES FALHARAM")
        print("🚨 Correções não foram aplicadas corretamente")
        sys.exit(1)
