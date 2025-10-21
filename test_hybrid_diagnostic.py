"""
Teste Simplificado - Diagnóstico de Erros no HybridQueryProcessorV2
"""

import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import io

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def create_test_csv():
    """Cria CSV simples de teste."""
    df = pd.DataFrame({
        'Time': range(100),
        'Amount': np.random.uniform(0, 1000, 100),
        'Class': np.random.choice([0, 1], 100)
    })
    
    path = Path("data/processado")
    path.mkdir(parents=True, exist_ok=True)
    
    csv_path = path / "test_simple.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ CSV criado: {csv_path}")
    return csv_path, df


async def test_basic_initialization():
    """Teste 1: Inicialização básica."""
    print("\n" + "="*60)
    print("TESTE 1: Inicialização Básica")
    print("="*60)
    
    try:
        vector_store = VectorStore()
        embedding_gen = EmbeddingGenerator()
        
        processor = HybridQueryProcessorV2(
            vector_store=vector_store,
            embedding_generator=embedding_gen,
            agent_name="test_basic"
        )
        
        print("✅ HybridQueryProcessorV2 inicializado com sucesso")
        print(f"   Agent name: {processor.agent_name}")
        print(f"   Token budget: {processor.token_budget.max_tokens_per_request}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        logger.error("Erro na inicialização", exc_info=True)
        return False


async def test_simple_query():
    """Teste 2: Query simples."""
    print("\n" + "="*60)
    print("TESTE 2: Query Simples")
    print("="*60)
    
    try:
        # Setup
        csv_path, df = create_test_csv()
        
        vector_store = VectorStore()
        embedding_gen = EmbeddingGenerator()
        
        processor = HybridQueryProcessorV2(
            vector_store=vector_store,
            embedding_generator=embedding_gen,
            agent_name="test_simple_query"
        )
        
        # Query simples
        query = "Qual a média de Amount?"
        source_id = "test_simple"
        
        print(f"📝 Query: {query}")
        print(f"🔍 Processando...")
        
        result = await processor.process_query(
            query=query,
            source_id=source_id
        )
        
        print(f"\n📊 Resultado:")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Estratégia: {result.get('strategy_decision', {}).get('strategy', 'N/A')}")
        print(f"   Tempo: {result.get('processing_time_seconds', 0):.2f}s")
        print(f"   Erro: {result.get('error', 'N/A')}")
        
        if result.get('status') == 'error':
            print(f"\n❌ DETALHES DO ERRO:")
            print(f"   {result.get('error', 'Erro desconhecido')}")
            
            # Mostrar traceback se disponível
            import traceback
            if 'traceback' in result:
                print(f"\n   Traceback:")
                print(f"   {result['traceback']}")
        
        # Cleanup
        csv_path.unlink()
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        logger.error("Erro no teste de query simples", exc_info=True)
        return False


async def test_analyze_query():
    """Teste 3: Apenas análise de query (sem processar)."""
    print("\n" + "="*60)
    print("TESTE 3: Análise de Query")
    print("="*60)
    
    try:
        vector_store = VectorStore()
        embedding_gen = EmbeddingGenerator()
        
        processor = HybridQueryProcessorV2(
            vector_store=vector_store,
            embedding_generator=embedding_gen,
            agent_name="test_analyze"
        )
        
        query = "Qual a correlação entre Amount e Time?"
        source_id = "test_analyze"
        
        print(f"📝 Query: {query}")
        print(f"🔍 Analisando...")
        
        # Análise sem LLM (usar apenas QueryAnalyzer)
        analysis = processor.query_analyzer.analyze(query, available_chunks=[])
        
        print(f"\n📊 Análise:")
        print(f"   Complexidade: {analysis.get('complexity', 'N/A')}")
        print(f"   Categoria: {analysis.get('category', 'N/A')}")
        print(f"   Requer CSV: {analysis.get('requires_csv', False)}")
        
        print("\n✅ Análise completada")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        logger.error("Erro na análise", exc_info=True)
        return False


async def test_memory_connection():
    """Teste 4: Conexão com SupabaseMemoryManager."""
    print("\n" + "="*60)
    print("TESTE 4: Conexão com Memória")
    print("="*60)
    
    try:
        from src.memory.supabase_memory import SupabaseMemoryManager
        
        memory = SupabaseMemoryManager(agent_name="test_memory")
        
        print("✅ SupabaseMemoryManager inicializado")
        
        # Tentar criar sessão
        session = await memory.create_session(metadata={'test': True})
        
        print(f"✅ Sessão criada: {session.session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        print(f"   Isso pode ser esperado se Supabase não está configurado")
        logger.warning("Erro na conexão com memória (pode ser esperado)", exc_info=True)
        return False


async def run_diagnostic_tests():
    """Executa testes de diagnóstico."""
    print("\n" + "="*70)
    print("DIAGNÓSTICO - HybridQueryProcessorV2")
    print("="*70)
    
    results = []
    
    # Teste 1: Inicialização
    r1 = await test_basic_initialization()
    results.append(("Inicialização", r1))
    
    # Teste 2: Query simples
    r2 = await test_simple_query()
    results.append(("Query Simples", r2))
    
    # Teste 3: Análise
    r3 = await test_analyze_query()
    results.append(("Análise", r3))
    
    # Teste 4: Memória
    r4 = await test_memory_connection()
    results.append(("Memória", r4))
    
    # Resumo
    print("\n" + "="*70)
    print("RESUMO")
    print("="*70)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name:20s} {status}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\nTaxa de sucesso: {passed}/{total} ({passed/total*100:.0f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_diagnostic_tests())
    exit(0 if success else 1)
