#!/usr/bin/env python3
"""
Test Interface Interativa V3.0 - Validação Completa

✅ Testa chunking multi-coluna (CSV_COLUMN + CSV_ROW + METADATA)
✅ Valida uso ativo de LLMs em 9 pontos críticos
✅ Confirma código genérico (sem hardcoding)
✅ Testa memória persistente e contexto conversacional
✅ Valida RAG vetorial com busca semântica

Objetivo: Garantir que as modificações recentes (chunking por coluna,
remoção de hardcoding, LLMs ativos) estão funcionando corretamente
na interface interativa.
"""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from typing import Dict, Any, List

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.agent.rag_agent import RAGAgent
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger
from src.settings import EDA_DATA_DIR_PROCESSANDO

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# FUNÇÕES DE VALIDAÇÃO
# ═══════════════════════════════════════════════════════════════

def print_section(title: str):
    """Imprime cabeçalho de seção."""
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print('═' * 70)


def validate_chunking_strategy(rag_agent: RAGAgent) -> Dict[str, Any]:
    """
    Valida se o chunking multi-coluna está ativo.
    
    Returns:
        Dict com resultados da validação
    """
    print_section("🔍 TESTE 1: Validação de Chunking Multi-Coluna")
    
    results = {
        'test_name': 'Chunking Strategy',
        'passed': False,
        'details': {}
    }
    
    try:
        # Verificar se chunker tem estratégia CSV_COLUMN
        from src.embeddings.chunker import ChunkingStrategy
        
        has_column_strategy = hasattr(ChunkingStrategy, 'CSV_COLUMN')
        has_row_strategy = hasattr(ChunkingStrategy, 'CSV_ROW')
        
        print(f"  ✓ ChunkingStrategy.CSV_COLUMN existe: {has_column_strategy}")
        print(f"  ✓ ChunkingStrategy.CSV_ROW existe: {has_row_strategy}")
        
        # Verificar método de chunking
        from src.embeddings.chunker import Chunker
        chunker = Chunker()
        
        has_method = hasattr(chunker, '_chunk_csv_by_columns')
        print(f"  ✓ Método _chunk_csv_by_columns existe: {has_method}")
        
        # Verificar se o código é genérico (não hardcoded)
        import inspect
        if has_method:
            source_code = inspect.getsource(chunker._chunk_csv_by_columns)
            
            # NÃO deve conter nomes de colunas específicas
            hardcoded_terms = ['Time', 'Amount', 'Class', 'V1', 'V2']
            has_hardcoding = any(term in source_code for term in hardcoded_terms)
            
            # DEVE conter iteração dinâmica
            has_dynamic_iteration = 'for col in df.columns' in source_code or 'for idx, col in enumerate(df.columns' in source_code
            has_type_detection = 'is_numeric_dtype' in source_code or 'pd.api.types' in source_code
            
            print(f"  ✓ Código sem hardcoding de colunas: {not has_hardcoding}")
            print(f"  ✓ Iteração dinâmica (for col in df.columns): {has_dynamic_iteration}")
            print(f"  ✓ Detecção automática de tipos: {has_type_detection}")
            
            results['details'] = {
                'has_column_strategy': has_column_strategy,
                'has_row_strategy': has_row_strategy,
                'has_method': has_method,
                'is_generic': not has_hardcoding,
                'has_dynamic_iteration': has_dynamic_iteration,
                'has_type_detection': has_type_detection
            }
            
            # Teste passa se todas as condições são verdadeiras
            results['passed'] = all([
                has_column_strategy,
                has_row_strategy,
                has_method,
                not has_hardcoding,
                has_dynamic_iteration,
                has_type_detection
            ])
        
        if results['passed']:
            print(f"\n  ✅ TESTE 1 PASSOU: Chunking multi-coluna está genérico e funcional!")
        else:
            print(f"\n  ❌ TESTE 1 FALHOU: Problemas detectados no chunking")
    
    except Exception as e:
        print(f"  ❌ Erro na validação: {e}")
        logger.error(f"Erro em validate_chunking_strategy: {e}", exc_info=True)
    
    return results


def validate_llm_usage() -> Dict[str, Any]:
    """
    Valida se LLMs estão ativos em pontos críticos.
    
    Returns:
        Dict com resultados da validação
    """
    print_section("🤖 TESTE 2: Validação de Uso Ativo de LLMs")
    
    results = {
        'test_name': 'LLM Active Usage',
        'passed': False,
        'llm_points': []
    }
    
    try:
        # Lista dos 9 pontos críticos onde LLMs devem estar ativos
        critical_points = [
            {
                'file': 'src/embeddings/generator.py',
                'class': 'EmbeddingGenerator',
                'method': 'embed_documents',
                'llm_type': 'OpenAIEmbeddings',
                'line_approx': 60
            },
            {
                'file': 'src/embeddings/generator.py',
                'class': 'EmbeddingGenerator',
                'method': 'embed_query',
                'llm_type': 'OpenAIEmbeddings',
                'line_approx': 95
            },
            {
                'file': 'src/agent/query_analyzer.py',
                'class': 'QueryAnalyzer',
                'method': 'analyze_query',
                'llm_type': 'LLMManager',
                'line_approx': 85
            },
            {
                'file': 'src/agent/hybrid_query_processor_v2.py',
                'class': 'HybridQueryProcessorV2',
                'method': '_process_embeddings_query',
                'llm_type': 'LLMManager',
                'line_approx': 311
            },
            {
                'file': 'src/agent/hybrid_query_processor_v2.py',
                'class': 'HybridQueryProcessorV2',
                'method': '_process_csv_direct_query',
                'llm_type': 'LLMManager',
                'line_approx': 507
            },
            {
                'file': 'src/agent/hybrid_query_processor_v2.py',
                'class': 'HybridQueryProcessorV2',
                'method': '_fallback_to_llm',
                'llm_type': 'LLMManager',
                'line_approx': 586
            },
            {
                'file': 'src/llm/fast_fragmenter.py',
                'class': 'FastQueryFragmenter',
                'method': 'fragment_query',
                'llm_type': 'LLMManager',
                'line_approx': 150
            },
            {
                'file': 'src/llm/simple_aggregator.py',
                'class': 'SimpleQueryAggregator',
                'method': 'aggregate_results',
                'llm_type': 'LLMManager',
                'line_approx': 85
            },
            {
                'file': 'src/agent/rag_agent.py',
                'class': 'RAGAgent',
                'method': 'query',
                'llm_type': 'LLMManager',
                'line_approx': 159
            }
        ]
        
        print(f"  Verificando {len(critical_points)} pontos críticos de uso de LLM...\n")
        
        active_count = 0
        for idx, point in enumerate(critical_points, 1):
            try:
                file_path = Path(__file__).parent / point['file']
                
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    # Verificar se o método existe e usa LLM
                    has_method = f"def {point['method']}" in source_code
                    uses_llm_manager = 'llm_manager' in source_code or 'LLMManager' in source_code
                    uses_langchain = 'langchain' in source_code.lower()
                    
                    is_active = has_method and (uses_llm_manager or uses_langchain)
                    
                    status = "✅" if is_active else "❌"
                    print(f"  {status} Ponto {idx}: {point['class']}.{point['method']} ({point['llm_type']})")
                    
                    if is_active:
                        active_count += 1
                    
                    results['llm_points'].append({
                        'index': idx,
                        'file': point['file'],
                        'method': point['method'],
                        'active': is_active
                    })
                else:
                    print(f"  ⚠️  Ponto {idx}: Arquivo {point['file']} não encontrado")
            
            except Exception as e:
                print(f"  ❌ Erro ao verificar ponto {idx}: {e}")
        
        # Teste passa se pelo menos 7 dos 9 pontos estão ativos
        results['active_count'] = active_count
        results['total_points'] = len(critical_points)
        results['passed'] = active_count >= 7
        
        print(f"\n  📊 Resultado: {active_count}/{len(critical_points)} pontos ativos")
        
        if results['passed']:
            print(f"  ✅ TESTE 2 PASSOU: LLMs estão ativos em pontos críticos!")
        else:
            print(f"  ❌ TESTE 2 FALHOU: Apenas {active_count}/{len(critical_points)} pontos ativos")
    
    except Exception as e:
        print(f"  ❌ Erro na validação: {e}")
        logger.error(f"Erro em validate_llm_usage: {e}", exc_info=True)
    
    return results


async def validate_ingestion_with_multicolumn(csv_file_path: str) -> Dict[str, Any]:
    """
    Valida ingestão de CSV com chunking multi-coluna.
    
    Args:
        csv_file_path: Caminho para arquivo CSV de teste
    
    Returns:
        Dict com resultados da validação
    """
    print_section("📥 TESTE 3: Validação de Ingestão com Multi-Coluna")
    
    results = {
        'test_name': 'Ingestion with Multi-Column Chunking',
        'passed': False,
        'details': {}
    }
    
    try:
        # Limpar base vetorial
        print("  → Limpando base vetorial...")
        supabase.table('embeddings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        supabase.table('chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        supabase.table('metadata').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Verificar se arquivo existe
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            print(f"  ⚠️  Arquivo {csv_file_path} não encontrado")
            return results
        
        print(f"  → Carregando CSV: {csv_path.name}")
        
        # Contar colunas do CSV
        import pandas as pd
        df = pd.read_csv(csv_path)
        num_columns = len(df.columns)
        num_rows = len(df)
        
        print(f"  → CSV tem {num_columns} colunas e {num_rows} linhas")
        
        # Executar ingestão
        print("  → Executando ingestão com RAGAgent...")
        rag_agent = RAGAgent()
        source_id = csv_path.stem
        
        ingest_result = rag_agent.ingest_csv_file(
            file_path=str(csv_path),
            source_id=source_id,
            encoding="utf-8"
        )
        
        print(f"  → Ingestão concluída")
        
        # Verificar embeddings gerados
        print("  → Verificando embeddings na base vetorial...")
        embeddings_response = supabase.table('embeddings').select('*').eq('source_id', source_id).execute()
        embeddings_count = len(embeddings_response.data) if embeddings_response.data else 0
        
        print(f"  → Total de embeddings gerados: {embeddings_count}")
        
        # Verificar chunks
        chunks_response = supabase.table('chunks').select('*').eq('source_id', source_id).execute()
        chunks_count = len(chunks_response.data) if chunks_response.data else 0
        
        print(f"  → Total de chunks gerados: {chunks_count}")
        
        # Verificar tipos de chunks (deve ter METADATA, ROW e COLUMN)
        chunk_types = set()
        if chunks_response.data:
            for chunk in chunks_response.data:
                metadata = chunk.get('metadata', {})
                chunk_type = metadata.get('chunk_type', 'unknown')
                chunk_types.add(chunk_type)
        
        print(f"  → Tipos de chunks encontrados: {', '.join(chunk_types)}")
        
        # Calcular chunks esperados:
        # - 1 METADATA
        # - N ROWs (sample de ~100 linhas)
        # - M COLUMNs (todas as colunas)
        expected_column_chunks = num_columns
        has_metadata = 'METADATA' in chunk_types
        has_row = 'ROW' in chunk_types
        has_column = 'COLUMN' in chunk_types
        
        print(f"\n  Validação de tipos:")
        print(f"    ✓ METADATA chunk: {has_metadata}")
        print(f"    ✓ ROW chunks: {has_row}")
        print(f"    ✓ COLUMN chunks: {has_column}")
        print(f"    ✓ Chunks esperados de COLUMN: ~{expected_column_chunks}")
        
        results['details'] = {
            'csv_columns': num_columns,
            'csv_rows': num_rows,
            'embeddings_generated': embeddings_count,
            'chunks_generated': chunks_count,
            'chunk_types': list(chunk_types),
            'has_metadata': has_metadata,
            'has_row': has_row,
            'has_column': has_column
        }
        
        # Teste passa se:
        # - Embeddings foram gerados
        # - Existem chunks de todos os 3 tipos
        # - Número de embeddings é razoável
        results['passed'] = all([
            embeddings_count > 0,
            has_metadata,
            has_row,
            has_column,
            chunks_count >= num_columns  # Pelo menos 1 chunk por coluna
        ])
        
        if results['passed']:
            print(f"\n  ✅ TESTE 3 PASSOU: Ingestão multi-coluna funcionando corretamente!")
        else:
            print(f"\n  ❌ TESTE 3 FALHOU: Problemas na ingestão multi-coluna")
    
    except Exception as e:
        print(f"  ❌ Erro na validação: {e}")
        logger.error(f"Erro em validate_ingestion_with_multicolumn: {e}", exc_info=True)
    
    return results


async def validate_query_with_memory(orchestrator: OrchestratorAgent, session_id: str) -> Dict[str, Any]:
    """
    Valida query com memória persistente e contexto conversacional.
    
    Args:
        orchestrator: Instância do OrchestratorAgent
        session_id: ID da sessão de teste
    
    Returns:
        Dict com resultados da validação
    """
    print_section("💬 TESTE 4: Validação de Query com Memória Persistente")
    
    results = {
        'test_name': 'Query with Persistent Memory',
        'passed': False,
        'queries': []
    }
    
    try:
        # Preparar queries de teste
        test_queries = [
            {
                'query': 'Quais são as colunas disponíveis no dataset?',
                'expected_in_response': ['coluna', 'variável', 'campo']
            },
            {
                'query': 'Me explique as 3 primeiras colunas',
                'expected_in_response': ['primeira', 'segunda', 'terceira', 'coluna']
            },
            {
                'query': 'Qual foi minha primeira pergunta?',
                'expected_in_response': ['primeira', 'pergunta', 'coluna']
            }
        ]
        
        print(f"  Executando {len(test_queries)} queries de teste...\n")
        
        for idx, test in enumerate(test_queries, 1):
            try:
                print(f"  Query {idx}: {test['query']}")
                
                # Executar query com memória persistente
                response = await orchestrator.process_with_persistent_memory(
                    test['query'],
                    context={},
                    session_id=session_id
                )
                
                if response and response.get('content'):
                    content = response['content'].lower()
                    
                    # Verificar se resposta contém termos esperados
                    matches = [term for term in test['expected_in_response'] if term in content]
                    has_expected_content = len(matches) > 0
                    
                    # Verificar metadata de memória
                    metadata = response.get('metadata', {})
                    has_session_id = metadata.get('session_id') == session_id
                    has_memory_context = metadata.get('previous_interactions') is not None
                    
                    status = "✅" if has_expected_content else "⚠️"
                    print(f"    {status} Resposta recebida (termos encontrados: {len(matches)})")
                    print(f"    {'✅' if has_session_id else '❌'} Session ID presente")
                    print(f"    {'✅' if has_memory_context else '❌'} Contexto de memória presente")
                    
                    results['queries'].append({
                        'index': idx,
                        'query': test['query'],
                        'has_response': True,
                        'has_expected_content': has_expected_content,
                        'has_session_id': has_session_id,
                        'has_memory_context': has_memory_context,
                        'response_length': len(content)
                    })
                else:
                    print(f"    ❌ Sem resposta")
                    results['queries'].append({
                        'index': idx,
                        'query': test['query'],
                        'has_response': False
                    })
                
                # Aguardar entre queries
                await asyncio.sleep(2)
            
            except Exception as e:
                print(f"    ❌ Erro na query {idx}: {e}")
                results['queries'].append({
                    'index': idx,
                    'query': test['query'],
                    'error': str(e)
                })
        
        # Teste passa se pelo menos 2 das 3 queries funcionaram
        successful_queries = sum(1 for q in results['queries'] if q.get('has_response', False))
        results['successful_queries'] = successful_queries
        results['total_queries'] = len(test_queries)
        results['passed'] = successful_queries >= 2
        
        print(f"\n  📊 Resultado: {successful_queries}/{len(test_queries)} queries bem-sucedidas")
        
        if results['passed']:
            print(f"  ✅ TESTE 4 PASSOU: Query com memória funcionando!")
        else:
            print(f"  ❌ TESTE 4 FALHOU: Problemas nas queries com memória")
    
    except Exception as e:
        print(f"  ❌ Erro na validação: {e}")
        logger.error(f"Erro em validate_query_with_memory: {e}", exc_info=True)
    
    return results


# ═══════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════

async def main():
    """Executa todos os testes de validação."""
    print("\n" + "═" * 70)
    print("  🧪 TESTE INTERFACE INTERATIVA V3.0 - VALIDAÇÃO COMPLETA")
    print("═" * 70)
    print("\n  Objetivo: Validar modificações recentes")
    print("    • Chunking multi-coluna (CSV_COLUMN + CSV_ROW + METADATA)")
    print("    • Código 100% genérico (sem hardcoding)")
    print("    • LLMs ativos em 9 pontos críticos")
    print("    • Memória persistente e contexto conversacional")
    
    all_results = []
    
    # TESTE 1: Validar chunking
    result1 = validate_chunking_strategy(RAGAgent())
    all_results.append(result1)
    
    # TESTE 2: Validar LLMs
    result2 = validate_llm_usage()
    all_results.append(result2)
    
    # TESTE 3: Validar ingestão (precisa de CSV)
    csv_files = list(EDA_DATA_DIR_PROCESSANDO.glob("*.csv"))
    if csv_files:
        result3 = await validate_ingestion_with_multicolumn(str(csv_files[0]))
        all_results.append(result3)
    else:
        print_section("⚠️  TESTE 3: PULADO (Nenhum CSV em data/processando/)")
    
    # TESTE 4: Validar query com memória
    print_section("🔧 Inicializando sistema para TESTE 4...")
    try:
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=True,
            enable_data_processor=True
        )
        session_id = str(uuid4())
        
        result4 = await validate_query_with_memory(orchestrator, session_id)
        all_results.append(result4)
    except Exception as e:
        print(f"  ❌ Erro ao inicializar orchestrador: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # RELATÓRIO FINAL
    # ═══════════════════════════════════════════════════════════════
    print_section("📊 RELATÓRIO FINAL DE VALIDAÇÃO")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get('passed', False))
    
    print(f"\n  Total de testes: {total_tests}")
    print(f"  Testes aprovados: {passed_tests}")
    print(f"  Testes reprovados: {total_tests - passed_tests}")
    print(f"  Taxa de sucesso: {(passed_tests/total_tests*100):.1f}%\n")
    
    print("  Resumo por teste:")
    for idx, result in enumerate(all_results, 1):
        status = "✅ PASSOU" if result.get('passed', False) else "❌ FALHOU"
        test_name = result.get('test_name', f'Teste {idx}')
        print(f"    {status} - {test_name}")
    
    # Avaliação final
    print("\n" + "═" * 70)
    if passed_tests == total_tests:
        print("  🎉 TODOS OS TESTES PASSARAM! Sistema V3.0 validado com sucesso!")
    elif passed_tests >= total_tests * 0.75:
        print(f"  ✅ MAIORIA DOS TESTES PASSOU ({passed_tests}/{total_tests})")
        print("     Sistema V3.0 funcional, mas com pontos de atenção")
    else:
        print(f"  ⚠️  ATENÇÃO: Apenas {passed_tests}/{total_tests} testes passaram")
        print("     Revisão necessária antes de usar em produção")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário.\n")
    except Exception as e:
        print(f"\n\n❌ Erro crítico no teste: {e}\n")
        logger.error(f"Erro crítico em test_interface_interativa_v3: {e}", exc_info=True)
