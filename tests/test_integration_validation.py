#!/usr/bin/env python3
"""
Teste de Validação Rápida - Integração de Módulos
==================================================

Valida que todos os módulos corrigidos estão integrados corretamente.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path.cwd()))

print("=" * 70)
print("🧪 TESTE DE VALIDAÇÃO RÁPIDA - INTEGRAÇÃO DE MÓDULOS")
print("=" * 70)
print()

# Contadores
total_tests = 0
passed_tests = 0
errors = []
warnings = []

def test_module(name: str, test_func):
    """Helper para executar testes."""
    global total_tests, passed_tests
    total_tests += 1
    
    try:
        test_func()
        print(f"✅ {name}")
        passed_tests += 1
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        errors.append(f"{name}: {e}")
        return False


# =============================================================================
# TESTE 1: QueryAnalyzer
# =============================================================================
def test_query_analyzer():
    from src.agent.query_analyzer import QueryAnalyzer
    
    analyzer = QueryAnalyzer()
    
    # Verificar métodos
    assert hasattr(analyzer, 'analyze'), "QueryAnalyzer não possui método 'analyze'"
    assert hasattr(analyzer, '_fallback_heuristic_analysis'), "Fallback heurístico ausente"
    
    # Testar análise simples
    query = "Qual a média de Amount?"
    analysis = analyzer.analyze(query)
    
    # Verificar que retorna objeto, não dict
    assert hasattr(analysis, 'complexity'), "Análise não retorna objeto com 'complexity'"
    assert hasattr(analysis, 'category'), "Análise não retorna objeto com 'category'"
    
    # Verificar que complexity é string
    assert isinstance(analysis.complexity, str), f"complexity deveria ser str, é {type(analysis.complexity)}"
    
    # Verificar que categoriza corretamente
    assert analysis.complexity in ['simple', 'moderate', 'complex'], f"complexity inválida: {analysis.complexity}"
    
    print(f"  → Análise: complexity={analysis.complexity}, category={analysis.category}")


test_module("1. QueryAnalyzer", test_query_analyzer)


# =============================================================================
# TESTE 2: HybridQueryProcessorV2
# =============================================================================
def test_hybrid_processor():
    from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
    from src.embeddings.vector_store import VectorStore
    from src.embeddings.generator import EmbeddingGenerator
    
    # Criar instância
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    processor = HybridQueryProcessorV2(
        vector_store=vector_store,
        embedding_generator=embedding_gen
    )
    
    # Verificar métodos
    assert hasattr(processor, 'process_query'), "HybridQueryProcessorV2 não possui 'process_query'"
    
    print(f"  → Instância criada com sucesso")


test_module("2. HybridQueryProcessorV2", test_hybrid_processor)


# =============================================================================
# TESTE 3: LLMManager
# =============================================================================
def test_llm_manager():
    from src.llm.manager import LLMManager
    
    manager = LLMManager()
    
    # Verificar método chat()
    assert hasattr(manager, 'chat'), "LLMManager não possui método 'chat'"
    
    # Verificar provider ativo
    if hasattr(manager, 'active_provider'):
        print(f"  → Provider ativo: {manager.active_provider.value}")
    else:
        warnings.append("LLMManager não expõe active_provider")
        print(f"  → Provider: desconhecido")


test_module("3. LLMManager", test_llm_manager)


# =============================================================================
# TESTE 4: VectorStore com Cache
# =============================================================================
def test_vector_store():
    from src.embeddings.vector_store import VectorStore
    
    vector_store = VectorStore()
    
    # Verificar métodos de busca
    assert hasattr(vector_store, 'search_similar'), "VectorStore não possui 'search_similar'"
    
    print(f"  → VectorStore pronto para busca")


test_module("4. VectorStore", test_vector_store)


# =============================================================================
# TESTE 5: SupabaseMemoryManager
# =============================================================================
def test_memory_manager():
    from src.memory.supabase_memory import SupabaseMemoryManager
    
    memory = SupabaseMemoryManager()
    
    # Verificar métodos de memória
    assert hasattr(memory, 'create_session'), "SupabaseMemoryManager não possui 'create_session'"
    
    print(f"  → SupabaseMemoryManager pronto")


test_module("5. SupabaseMemoryManager", test_memory_manager)


# =============================================================================
# TESTE 6: OrchestratorAgent (Integração)
# =============================================================================
def test_orchestrator():
    try:
        from src.agent.orchestrator_agent import OrchestratorAgent
        
        orchestrator = OrchestratorAgent()
        
        # Verificar método principal
        assert hasattr(orchestrator, 'process_with_persistent_memory'), \
            "OrchestratorAgent não possui 'process_with_persistent_memory'"
        
        # Verificar se usa módulos corretos (se possível)
        if hasattr(orchestrator, 'analyzer'):
            from src.agent.query_analyzer import QueryAnalyzer
            assert isinstance(orchestrator.analyzer, QueryAnalyzer), \
                "Orchestrator não usa QueryAnalyzer"
            print(f"  → Usa QueryAnalyzer ✅")
        else:
            warnings.append("Orchestrator não expõe 'analyzer' - verificação manual necessária")
        
        if hasattr(orchestrator, 'processor'):
            from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
            assert isinstance(orchestrator.processor, HybridQueryProcessorV2), \
                "Orchestrator não usa HybridQueryProcessorV2"
            print(f"  → Usa HybridQueryProcessorV2 ✅")
        else:
            warnings.append("Orchestrator não expõe 'processor' - verificação manual necessária")
        
        print(f"  → OrchestratorAgent pronto")
        
    except ImportError as e:
        warnings.append(f"OrchestratorAgent não disponível: {e}")
        raise


test_module("6. OrchestratorAgent", test_orchestrator)


# =============================================================================
# TESTE 7: Interface Interativa (Imports)
# =============================================================================
def test_interface():
    interface_file = Path('interface_interativa.py')
    
    assert interface_file.exists(), "interface_interativa.py não encontrado"
    
    # Verificar imports críticos
    with open(interface_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar uso correto
    assert 'OrchestratorAgent' in content, "Interface não usa OrchestratorAgent"
    assert 'process_with_persistent_memory' in content, "Interface não usa memória persistente"
    
    print(f"  → Interface usa OrchestratorAgent com memória")


test_module("7. Interface Interativa", test_interface)


# =============================================================================
# TESTE 8: API Backend (Imports)
# =============================================================================
def test_api():
    api_file = Path('api_completa.py')
    
    assert api_file.exists(), "api_completa.py não encontrado"
    
    # Verificar imports críticos
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar uso correto
    assert 'OrchestratorAgent' in content, "API não usa OrchestratorAgent"
    assert 'process_with_persistent_memory' in content, "API não usa memória persistente"
    
    # Verificar que NÃO tem chamadas diretas
    direct_calls = []
    if 'openai.ChatCompletion' in content:
        direct_calls.append('openai.ChatCompletion')
    if 'groq.chat(' in content:
        direct_calls.append('groq.chat')
    
    if direct_calls:
        warnings.append(f"API tem chamadas diretas a LLMs: {', '.join(direct_calls)}")
    
    print(f"  → API usa OrchestratorAgent com memória")
    if not direct_calls:
        print(f"  → Sem chamadas diretas a LLMs ✅")


test_module("8. API Backend", test_api)


# =============================================================================
# RESULTADOS
# =============================================================================
print()
print("=" * 70)
print("📊 RESULTADOS")
print("=" * 70)
print()
print(f"Total de testes: {total_tests}")
print(f"Testes passaram: {passed_tests}")
print(f"Testes falharam: {total_tests - passed_tests}")
print()

if errors:
    print("❌ ERROS CRÍTICOS:")
    for error in errors:
        print(f"  - {error}")
    print()

if warnings:
    print("⚠️ AVISOS:")
    for warning in warnings:
        print(f"  - {warning}")
    print()

# Taxa de sucesso
success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
print(f"Taxa de sucesso: {success_rate:.1f}%")
print()

# Conclusão
if success_rate >= 100:
    print("✅ TODOS OS TESTES PASSARAM!")
    print("🎉 Sistema integrado corretamente!")
    sys.exit(0)
elif success_rate >= 75:
    print("⚠️ MAIORIA DOS TESTES PASSOU")
    print("🔍 Revisar avisos e erros antes de deploy")
    sys.exit(0 if not errors else 1)
else:
    print("❌ MUITOS TESTES FALHARAM")
    print("🚨 Sistema precisa de correções antes de usar")
    sys.exit(1)
