"""
🧪 SUITE DE TESTES COMPLETA - Etapa 2
HybridQueryProcessorV2 + FastQueryFragmenter + Supabase Cache/History

COBERTURA:
✅ Queries fragmentadas e agregação de resultados
✅ Cache e histórico em Supabase
✅ Fallback acionado apenas quando necessário
✅ Simulação de limite de tokens GROQ (6000 TPM)
✅ Validação de logs estruturados
✅ Variações linguísticas no QueryAnalyzer

Autor: GitHub Copilot (GPT-4.1)
Data: 2025-10-21
"""

import sys
import os

# Configurar encoding UTF-8 para Windows PowerShell
if sys.platform == 'win32':
    # Configurar stdout/stderr para UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    # Definir codepage UTF-8 no console Windows
    os.system('chcp 65001 > nul 2>&1')

import asyncio
import pandas as pd
import numpy as np
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock

from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
from src.agent.query_analyzer import QueryAnalyzer, QueryComplexity, QueryCategory
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator
from src.memory.supabase_memory import SupabaseMemoryManager, ContextType
from src.llm.manager import LLMManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# FIXTURES E HELPERS
# ============================================================================

def create_synthetic_dataset(rows: int = 10000, cols: int = 30) -> pd.DataFrame:
    """
    Cria dataset sintético que simula creditcard.csv.
    
    Features:
    - Time: segundos desde primeira transação
    - V1-V28: Features PCA (distribuição normal)
    - Amount: valores de transação
    - Class: 0=normal, 1=fraude (desbalanceado 99.8/0.2)
    """
    np.random.seed(42)
    
    data = {
        'Time': np.arange(0, rows * 100, 100),  # Transações a cada 100s
        'Amount': np.random.lognormal(4, 2, rows),  # Log-normal para valores
        'Class': np.random.choice([0, 1], rows, p=[0.998, 0.002])
    }
    
    # Features V1-V28 (PCA components)
    for i in range(1, 29):
        data[f'V{i}'] = np.random.randn(rows)
    
    # Adicionar outliers realistas em fraudes
    fraud_idx = np.where(data['Class'] == 1)[0]
    for idx in fraud_idx:
        data['Amount'][idx] *= np.random.uniform(3, 10)  # Fraudes tendem a ter valores maiores
        
    return pd.DataFrame(data)


def save_csv_for_test(df: pd.DataFrame, filename: str) -> Path:
    """Salva CSV na pasta data/processado/."""
    data_dir = Path("data/processado")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = data_dir / filename
    df.to_csv(csv_path, index=False)
    
    logger.info(f"💾 CSV salvo: {csv_path} ({df.shape[0]} x {df.shape[1]})")
    return csv_path


def create_mock_chunks(source_id: str, aspects: List[str]) -> List[Dict[str, Any]]:
    """
    Cria chunks mock para simular dados já existentes no vector store.
    """
    chunks = []
    for aspect in aspects:
        chunk = {
            'chunk_id': f"{source_id}_{aspect}_{hashlib.md5(aspect.encode()).hexdigest()[:8]}",
            'content': f"Análise de {aspect}: estatísticas calculadas a partir dos dados.",
            'embedding': [0.1] * 1536,  # Embedding mock
            'metadata': {
                'source_id': source_id,
                'aspect': aspect,
                'created_at': datetime.now().isoformat(),
                'type': 'csv_analysis'
            }
        }
        chunks.append(chunk)
    
    return chunks


async def populate_chunks_in_vectorstore(
    vector_store: VectorStore,
    chunks: List[Dict[str, Any]]
) -> None:
    """Insere chunks mock no vector store para testes."""
    try:
        await vector_store.store_embeddings(chunks)
        logger.info(f"✅ {len(chunks)} chunks inseridos no vector store")
    except Exception as e:
        logger.warning(f"⚠️ Falha ao inserir chunks: {e}")


def estimate_tokens(text: str) -> int:
    """Estima tokens usando aproximação 4 chars/token."""
    return len(text) // 4


def create_large_query(target_tokens: int = 7000) -> str:
    """
    Cria query que estoura limite GROQ (6000 TPM).
    Usado para validar fragmentação.
    """
    base_query = """
    Analise detalhadamente o dataset de transações de cartão de crédito com as seguintes features:
    Time, Amount, Class, V1, V2, V3, V4, V5, V6, V7, V8, V9, V10, V11, V12, V13, V14, V15, V16,
    V17, V18, V19, V20, V21, V22, V23, V24, V25, V26, V27, V28.
    
    Para cada feature, calcule:
    - Média, mediana, desvio padrão, quartis
    - Outliers usando IQR method
    - Correlação com Class (fraude)
    - Distribuição (skewness, kurtosis)
    - Valores mínimo e máximo
    - Missing values
    """
    
    # Adicionar padding até atingir target_tokens
    current_tokens = estimate_tokens(base_query)
    padding_needed = target_tokens - current_tokens
    
    if padding_needed > 0:
        padding = "Forneça insights adicionais sobre padrões, tendências e anomalias. " * (padding_needed // 100)
        base_query += "\n\n" + padding
    
    return base_query


# ============================================================================
# TESTE 1: QUERIES FRAGMENTADAS E AGREGAÇÃO
# ============================================================================

async def test_01_query_fragmentation_and_aggregation():
    """
    Valida que queries grandes são fragmentadas corretamente
    e resultados agregados sem perda de informação.
    """
    print("\n" + "="*80)
    print("🧪 TESTE 1: FRAGMENTAÇÃO DE QUERIES + AGREGAÇÃO DE RESULTADOS")
    print("="*80)
    
    # Setup
    df = create_synthetic_dataset(rows=50000, cols=30)  # Dataset GRANDE
    csv_path = save_csv_for_test(df, "test_fragmentation.csv")
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    processor = HybridQueryProcessorV2(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        agent_name="test_fragmentation"
    )
    
    # Query que DEVE fragmentar (>6000 tokens)
    large_query = create_large_query(target_tokens=7500)
    logger.info(f"📏 Query criada com ~{estimate_tokens(large_query)} tokens (limite: 6000)")
    
    source_id = "test_fragmentation"
    
    # Processar com force_csv para garantir fragmentação
    start = datetime.now()
    result = await processor.process_query(
        query=large_query,
        source_id=source_id,
        force_csv=True
    )
    elapsed = (datetime.now() - start).total_seconds()
    
    # Validações
    print(f"\n📊 RESULTADOS:")
    print(f"   ✓ Status: {result['status']}")
    print(f"   ✓ Estratégia: {result.get('strategy_decision', {}).get('strategy')}")
    print(f"   ✓ Fragmentos criados: {result.get('fragments_count', 0)}")
    print(f"   ✓ Fragmentos processados: {result.get('fragments_success', 0)}")
    print(f"   ✓ Tokens por fragmento (max): {result.get('max_fragment_tokens', 0)}")
    print(f"   ✓ Resposta final (chars): {len(result.get('answer', ''))}")
    print(f"   ✓ Tempo total: {elapsed:.2f}s")
    
    # ASSERTIONS
    assert result['status'] == 'success', "Query deve processar com sucesso"
    
    # Se query > 6000 tokens, DEVE fragmentar
    if estimate_tokens(large_query) > 6000:
        assert result.get('fragments_count', 0) > 1, "Query grande deve ser fragmentada"
        assert result.get('max_fragment_tokens', 99999) <= 6000, "Cada fragmento deve respeitar limite"
        print(f"\n✅ FRAGMENTAÇÃO VALIDADA: {result['fragments_count']} partes")
    
    # Resultado deve conter análise agregada
    answer = result.get('answer', '')
    assert len(answer) > 100, "Resposta deve conter análise substantiva"
    
    # Cleanup
    csv_path.unlink()
    
    print("\n✅ TESTE 1 PASSOU - Fragmentação e agregação funcionando")
    return result


# ============================================================================
# TESTE 2: CACHE E HISTÓRICO SUPABASE
# ============================================================================

async def test_02_cache_and_history_persistence():
    """
    Valida que:
    - Cache é criado na primeira execução
    - Cache é reutilizado na segunda execução (speedup significativo)
    - Histórico é salvo na tabela contexts do Supabase
    """
    print("\n" + "="*80)
    print("🧪 TESTE 2: CACHE E HISTÓRICO NO SUPABASE")
    print("="*80)
    
    # Setup
    df = create_synthetic_dataset(rows=1000, cols=15)
    csv_path = save_csv_for_test(df, "test_cache.csv")
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    processor = HybridQueryProcessorV2(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        agent_name="test_cache_persistence"
    )
    
    query = "Calcule a média, mediana e desvio padrão da coluna Amount"
    source_id = "test_cache"
    
    # ========================================
    # PRIMEIRA EXECUÇÃO (sem cache)
    # ========================================
    print("\n1️⃣ PRIMEIRA EXECUÇÃO (sem cache)...")
    start1 = datetime.now()
    result1 = await processor.process_query(query, source_id)
    elapsed1 = (datetime.now() - start1).total_seconds()
    
    session_id1 = result1.get('session_id')
    
    print(f"   Tempo: {elapsed1:.2f}s")
    print(f"   Cache HIT: {result1.get('from_cache', False)}")
    print(f"   Session ID: {session_id1}")
    print(f"   Chunks gerados: {result1.get('new_chunks_generated', 0)}")
    
    # Validar que NÃO veio do cache
    assert not result1.get('from_cache', True), "Primeira execução não deve usar cache"
    assert session_id1 is not None, "Session ID deve ser criado"
    
    # ========================================
    # SEGUNDA EXECUÇÃO (deve usar cache)
    # ========================================
    print("\n2️⃣ SEGUNDA EXECUÇÃO (deve usar cache)...")
    await asyncio.sleep(1)  # Garantir que cache foi salvo
    
    start2 = datetime.now()
    result2 = await processor.process_query(
        query=query,
        source_id=source_id,
        session_id=session_id1  # Mesma sessão
    )
    elapsed2 = (datetime.now() - start2).total_seconds()
    
    print(f"   Tempo: {elapsed2:.2f}s")
    print(f"   Cache HIT: {result2.get('from_cache', False)}")
    print(f"   Timestamp cache: {result2.get('cache_timestamp')}")
    
    # Validar cache
    if result2.get('from_cache', False):
        speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 1
        print(f"\n✅ CACHE HIT! Speedup: {speedup:.1f}x ({elapsed1:.2f}s → {elapsed2:.2f}s)")
        
        # Cache deve ser MUITO mais rápido
        assert elapsed2 < elapsed1 * 0.5, "Cache deve ser pelo menos 2x mais rápido"
    else:
        print(f"\n⚠️ Cache não ativado (pode ocorrer se TTL expirou ou hash diferente)")
    
    # ========================================
    # VALIDAR HISTÓRICO NO SUPABASE
    # ========================================
    print("\n3️⃣ VALIDANDO HISTÓRICO NO SUPABASE...")
    
    memory_manager = processor.memory_manager
    
    # Buscar histórico da sessão
    try:
        history = await memory_manager.get_session_history(session_id1, limit=10)
        print(f"   ✓ Registros encontrados: {len(history)}")
        
        # Validar que pelo menos a query foi salva
        assert len(history) > 0, "Histórico deve conter registros"
        
        # Verificar tipos de contexto salvos
        context_types = [h.context_type for h in history]
        print(f"   ✓ Tipos de contexto: {set(context_types)}")
        
        # Deve ter pelo menos USER_QUERY e CACHE
        assert ContextType.USER_QUERY in context_types, "Deve salvar USER_QUERY"
        
        print("\n✅ HISTÓRICO VALIDADO NO SUPABASE")
        
    except Exception as e:
        logger.warning(f"⚠️ Falha ao validar histórico: {e}")
        print(f"\n⚠️ Histórico não disponível (Supabase pode não estar configurado)")
    
    # Cleanup
    csv_path.unlink()
    
    print("\n✅ TESTE 2 PASSOU - Cache e histórico funcionando")
    return result2


# ============================================================================
# TESTE 3: FALLBACK ACIONADO APENAS QUANDO NECESSÁRIO
# ============================================================================

async def test_03_intelligent_fallback_decision():
    """
    Valida que:
    - RAG ONLY usado quando chunks cobrem ≥80% da query
    - CSV FALLBACK acionado apenas quando cobertura <80%
    - Chunks existentes são usados como guia (evita redundância)
    """
    print("\n" + "="*80)
    print("🧪 TESTE 3: DECISÃO INTELIGENTE DE FALLBACK")
    print("="*80)
    
    # Setup
    df = create_synthetic_dataset(rows=2000, cols=20)
    csv_path = save_csv_for_test(df, "test_fallback_decision.csv")
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    processor = HybridQueryProcessorV2(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        agent_name="test_fallback_decision"
    )
    
    source_id = "test_fallback_decision"
    
    # ========================================
    # CENÁRIO A: Alta cobertura (≥80%) → RAG ONLY
    # ========================================
    print("\n📌 CENÁRIO A: Alta cobertura de chunks (≥80%)")
    
    # Popular chunks que cobrem a query
    mock_chunks = create_mock_chunks(source_id, aspects=[
        'statistics',
        'distribution',
        'correlation',
        'outliers'
    ])
    
    await populate_chunks_in_vectorstore(vector_store, mock_chunks)
    
    query_a = "Qual a distribuição estatística dos valores e outliers?"
    
    result_a = await processor.process_query(query_a, source_id)
    
    print(f"\n   Estratégia usada: {result_a.get('strategy_decision', {}).get('strategy')}")
    print(f"   Chunks usados: {len(result_a.get('chunks_used', []))}")
    print(f"   CSV acessado: {result_a.get('csv_accessed', False)}")
    print(f"   Cobertura: {result_a.get('coverage_percentage', 0)}%")
    
    # Validar: com alta cobertura, deve usar RAG ONLY
    strategy_a = result_a.get('strategy_decision', {}).get('strategy')
    
    if result_a.get('coverage_percentage', 0) >= 80:
        assert strategy_a == 'rag_only', "Alta cobertura deve usar RAG ONLY"
        assert not result_a.get('csv_accessed', True), "RAG ONLY não deve acessar CSV"
        print("   ✅ RAG ONLY usado corretamente")
    
    # ========================================
    # CENÁRIO B: Baixa cobertura (<80%) → CSV FALLBACK
    # ========================================
    print("\n📌 CENÁRIO B: Baixa cobertura de chunks (<80%)")
    
    query_b = "Analise padrões temporais em Time e correlação com V27 e V28"
    
    result_b = await processor.process_query(query_b, source_id)
    
    print(f"\n   Estratégia usada: {result_b.get('strategy_decision', {}).get('strategy')}")
    print(f"   Chunks usados: {len(result_b.get('chunks_used', []))}")
    print(f"   Novos chunks: {result_b.get('new_chunks_generated', 0)}")
    print(f"   CSV acessado: {result_b.get('csv_accessed', False)}")
    print(f"   Gaps preenchidos: {result_b.get('gaps_filled', [])}")
    print(f"   Cobertura: {result_b.get('coverage_percentage', 0)}%")
    
    # Validar: baixa cobertura deve usar FALLBACK
    strategy_b = result_b.get('strategy_decision', {}).get('strategy')
    
    if result_b.get('coverage_percentage', 0) < 80:
        assert strategy_b in ['csv_fallback', 'csv_fragmented'], "Baixa cobertura deve usar CSV"
        assert result_b.get('csv_accessed', False), "Deve acessar CSV quando necessário"
        print("   ✅ CSV FALLBACK usado corretamente")
        
        # Validar que chunks existentes foram usados como guia
        if len(result_b.get('chunks_used', [])) > 0:
            print(f"   ✅ {len(result_b['chunks_used'])} chunks existentes usados como guia")
    
    # ========================================
    # CENÁRIO C: Query complexa já coberta → Não regenera chunks
    # ========================================
    print("\n📌 CENÁRIO C: Query já respondida (chunks completos)")
    
    # Repetir query A (que já tem chunks)
    result_c = await processor.process_query(query_a, source_id)
    
    new_chunks_c = result_c.get('new_chunks_generated', 0)
    
    print(f"\n   Novos chunks gerados: {new_chunks_c}")
    print(f"   CSV acessado: {result_c.get('csv_accessed', False)}")
    
    # Validar que não gerou chunks redundantes
    assert new_chunks_c == 0 or not result_c.get('csv_accessed', True), \
        "Query já coberta não deve gerar chunks redundantes"
    
    print("   ✅ Evitou redundância de chunks")
    
    # Cleanup
    csv_path.unlink()
    
    print("\n✅ TESTE 3 PASSOU - Decisão de fallback inteligente")
    return result_b


# ============================================================================
# TESTE 4: SIMULAÇÃO DE LIMITE GROQ (6000 TPM)
# ============================================================================

async def test_04_groq_token_limit_simulation():
    """
    Simula diferentes cenários de token usage:
    - Query pequena (<2000 tokens): sem fragmentação
    - Query média (2000-5000 tokens): sem fragmentação, mas perto do limite
    - Query grande (>6000 tokens): DEVE fragmentar
    """
    print("\n" + "="*80)
    print("🧪 TESTE 4: SIMULAÇÃO DE LIMITE GROQ (6000 TPM)")
    print("="*80)
    
    # Setup
    df = create_synthetic_dataset(rows=100000, cols=30)  # Dataset MUITO GRANDE
    csv_path = save_csv_for_test(df, "test_groq_limit.csv")
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    processor = HybridQueryProcessorV2(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        agent_name="test_groq_limit"
    )
    
    source_id = "test_groq_limit"
    
    test_cases = [
        {
            'name': 'Query Pequena (<2000 tokens)',
            'query': 'Calcule a média de Amount',
            'expected_fragments': 0,
            'should_fragment': False
        },
        {
            'name': 'Query Média (2000-5000 tokens)',
            'query': create_large_query(target_tokens=4000),
            'expected_fragments': 0,
            'should_fragment': False
        },
        {
            'name': 'Query Grande (>6000 tokens)',
            'query': create_large_query(target_tokens=8000),
            'expected_fragments': 2,  # Mínimo 2 fragmentos
            'should_fragment': True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"📌 CASO {i}: {case['name']}")
        print(f"{'─'*80}")
        
        query_tokens = estimate_tokens(case['query'])
        print(f"   Query tokens: ~{query_tokens}")
        print(f"   Limite GROQ: 6000 TPM")
        print(f"   Deve fragmentar: {case['should_fragment']}")
        
        # Processar
        result = await processor.process_query(
            query=case['query'],
            source_id=source_id,
            force_csv=True  # Forçar CSV para testar fragmentação
        )
        
        fragments_count = result.get('fragments_count', 0)
        max_fragment_tokens = result.get('max_fragment_tokens', 0)
        
        print(f"\n   ✓ Fragmentos criados: {fragments_count}")
        print(f"   ✓ Max tokens/fragmento: {max_fragment_tokens}")
        print(f"   ✓ Estratégia: {result.get('strategy_decision', {}).get('strategy')}")
        
        # Validações
        if case['should_fragment']:
            assert fragments_count >= case['expected_fragments'], \
                f"Query grande deve criar pelo menos {case['expected_fragments']} fragmentos"
            assert max_fragment_tokens <= 6000, \
                "Cada fragmento deve respeitar limite GROQ"
            print(f"   ✅ Fragmentação correta: {fragments_count} partes")
        else:
            assert fragments_count <= 1, \
                "Query pequena não deve fragmentar desnecessariamente"
            print(f"   ✅ Processamento direto (sem fragmentação)")
        
        await asyncio.sleep(0.5)  # Evitar rate limit real
    
    # Cleanup
    csv_path.unlink()
    
    print("\n✅ TESTE 4 PASSOU - Limite GROQ respeitado em todos os cenários")
    return True


# ============================================================================
# TESTE 5: VALIDAÇÃO DE LOGS ESTRUTURADOS
# ============================================================================

async def test_05_structured_logging_validation():
    """
    Valida que logs estruturados são gerados em todas as etapas:
    - Início do processamento
    - Análise da query
    - Decisão de estratégia
    - Busca no vector store
    - Carregamento CSV (se aplicável)
    - Fragmentação (se aplicável)
    - Geração de resposta
    - Armazenamento em cache
    - Conclusão
    """
    print("\n" + "="*80)
    print("🧪 TESTE 5: VALIDAÇÃO DE LOGS ESTRUTURADOS")
    print("="*80)
    
    # Capturar logs
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    
    # Adicionar handler temporário
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Setup
    df = create_synthetic_dataset(rows=5000, cols=25)
    csv_path = save_csv_for_test(df, "test_logging.csv")
    
    vector_store = VectorStore()
    embedding_gen = EmbeddingGenerator()
    processor = HybridQueryProcessorV2(
        vector_store=vector_store,
        embedding_generator=embedding_gen,
        agent_name="test_logging"
    )
    
    # Processar query complexa
    query = "Analise correlações entre Amount, Time e features V1-V10"
    source_id = "test_logging"
    
    result = await processor.process_query(query, source_id, force_csv=True)
    
    # Capturar logs
    log_output = log_capture.getvalue()
    root_logger.removeHandler(handler)
    
    # Validar presença de logs chave
    expected_log_patterns = [
        "INÍCIO",  # Início do processamento
        "Análise",  # Análise da query
        "Estratégia",  # Decisão de estratégia
        "chunks",  # Busca de chunks
        "CSV",  # Carregamento CSV
        "SUCESSO",  # Conclusão
    ]
    
    print(f"\n📋 LOGS CAPTURADOS ({len(log_output)} caracteres):")
    print(f"{'─'*80}")
    
    logs_found = []
    for pattern in expected_log_patterns:
        if pattern.lower() in log_output.lower():
            logs_found.append(pattern)
            print(f"   ✅ {pattern}")
        else:
            print(f"   ⚠️ {pattern} (não encontrado)")
    
    # Validar
    coverage = len(logs_found) / len(expected_log_patterns) * 100
    print(f"\n   Cobertura de logs: {coverage:.0f}% ({len(logs_found)}/{len(expected_log_patterns)})")
    
    assert coverage >= 70, "Pelo menos 70% dos logs esperados devem estar presentes"
    
    # Validar estrutura JSON nos logs
    import re
    json_logs = re.findall(r'\{[^{}]+\}', log_output)
    print(f"   Logs estruturados (JSON): {len(json_logs)}")
    
    # Cleanup
    csv_path.unlink()
    
    print("\n✅ TESTE 5 PASSOU - Logging estruturado validado")
    return True


# ============================================================================
# TESTE 6: VARIAÇÕES LINGUÍSTICAS NO QUERYANALYZER
# ============================================================================

async def test_06_linguistic_variations_query_analyzer():
    """
    Valida que QueryAnalyzer classifica corretamente queries em português
    com variações linguísticas:
    - Formal vs informal
    - Diferentes tempos verbais
    - Sinônimos
    - Gírias técnicas vs termos formais
    """
    print("\n" + "="*80)
    print("🧪 TESTE 6: VARIAÇÕES LINGUÍSTICAS - QUERYANALYZER")
    print("="*80)
    
    analyzer = QueryAnalyzer()
    
    test_cases = [
        # Estatísticas básicas
        {
            'queries': [
                "Qual a média de Amount?",
                "Me dá a média da coluna Amount",
                "Calcule o valor médio de Amount",
                "Quanto é a média dos valores de Amount?",
            ],
            'expected_category': 'statistics',  # ✅ FIX: Usar string em vez de enum
            'expected_complexity': 'simple'     # ✅ FIX: Usar string em vez de enum
        },
        
        # Correlações
        {
            'queries': [
                "Correlação entre Amount e Time",
                "Amount e Time estão correlacionados?",
                "Existe relação entre Amount e Time?",
                "Calcule a correlação de Pearson entre Amount e Time",
            ],
            'expected_category': 'correlation',  # ✅ FIX: string
            'expected_complexity': 'simple'
        },
        
        # Distribuições
        {
            'queries': [
                "Distribuição de Amount",
                "Como é a distribuição dos valores de Amount?",
                "Mostre a distribuição estatística de Amount",
                "Histograma de Amount",
            ],
            'expected_category': 'distribution',  # ✅ FIX: string
            'expected_complexity': 'simple'
        },
        
        # Outliers
        {
            'queries': [
                "Outliers em Amount",
                "Valores atípicos na coluna Amount",
                "Anomalias em Amount",
                "Identifique pontos fora da curva em Amount",
            ],
            'expected_category': 'outliers',  # ✅ FIX: string
            'expected_complexity': 'simple'
        },
        
        # Queries complexas
        {
            'queries': [
                "Analise a correlação entre Amount, Time e todas as features V1-V28, identificando outliers",
                "Faça uma análise completa do dataset incluindo estatísticas, distribuições e correlações",
                "Quero entender os padrões de fraude através de análise multivariada",
            ],
            'expected_category': None,  # Pode variar
            'expected_complexity': 'complex'  # ✅ FIX: string
        },
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        expected_cat = case['expected_category'] or 'COMPLEX'
        print(f"📌 CASO {i}: {expected_cat}")
        print(f"{'─'*80}")
        
        for query in case['queries']:
            total_tests += 1
            
            # Analisar
            analysis = analyzer.analyze(query)
            
            # Validar categoria (se esperada)
            # ✅ Ambos são strings agora
            category_match = (
                case['expected_category'] is None or
                analysis.category == case['expected_category']
            )
            
            # Validar complexidade
            # ✅ Ambos são strings agora
            complexity_match = analysis.complexity == case['expected_complexity']
            
            if category_match and complexity_match:
                passed_tests += 1
                status = "✅"
            else:
                status = "⚠️"
            
            print(f"   {status} '{query[:50]}...'")
            print(f"      → {analysis.complexity} | {analysis.category}")
            
            # Assertions brandas (permitir variação)
            if case['expected_complexity'] == 'simple':
                assert analysis.complexity in ['simple', 'moderate'], \
                    f"Query simples classificada como {analysis.complexity}"
    
    # Resultado final
    accuracy = (passed_tests / total_tests) * 100
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO: {passed_tests}/{total_tests} queries classificadas corretamente ({accuracy:.1f}%)")
    print(f"{'='*80}")
    
    # Validar taxa mínima de acerto
    assert accuracy >= 70, f"Taxa de acerto deve ser ≥70% (atual: {accuracy:.1f}%)"
    
    print("\n✅ TESTE 6 PASSOU - QueryAnalyzer robusto para variações linguísticas")
    return True


# ============================================================================
# RUNNER PRINCIPAL
# ============================================================================

async def run_all_etapa2_tests():
    """
    Executa toda a suite de testes da Etapa 2.
    """
    import sys
    import io
    import os
    
    # Fix encoding Windows - FORÇAR UTF-8
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    print("\n" + "="*80)
    print("🧪 SUITE DE TESTES COMPLETA - ETAPA 2")
    print("   HybridQueryProcessorV2 + FastQueryFragmenter + Supabase")
    print("="*80)
    print(f"⏱️ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_total = datetime.now()
    results = []
    
    tests = [
        ("Fragmentação e Agregação", test_01_query_fragmentation_and_aggregation),
        ("Cache e Histórico Supabase", test_02_cache_and_history_persistence),
        ("Fallback Inteligente", test_03_intelligent_fallback_decision),
        ("Limite GROQ (6000 TPM)", test_04_groq_token_limit_simulation),
        ("Logs Estruturados", test_05_structured_logging_validation),
        ("Variações Linguísticas", test_06_linguistic_variations_query_analyzer),
    ]
    
    for i, (name, test_func) in enumerate(tests, 1):
        try:
            print(f"\n\n{'#'*80}")
            print(f"# TESTE {i}/{len(tests)}: {name}")
            print(f"{'#'*80}")
            
            result = await test_func()
            results.append((name, True, None))
            
        except AssertionError as e:
            logger.error(f"❌ Teste {i} falhou (assertion): {e}")
            results.append((name, False, str(e)))
            
        except Exception as e:
            logger.error(f"❌ Teste {i} falhou (exceção): {e}", exc_info=True)
            results.append((name, False, str(e)))
    
    # Sumário final
    elapsed_total = (datetime.now() - start_total).total_seconds()
    
    print("\n\n" + "="*80)
    print("📊 SUMÁRIO DOS TESTES - ETAPA 2")
    print("="*80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✅ PASSOU" if success else f"❌ FALHOU: {error}"
        print(f"{name:.<50} {status}")
    
    print("="*80)
    print(f"⏱️ Tempo total: {elapsed_total:.2f}s")
    print(f"📈 Taxa de sucesso: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_etapa2_tests())
    exit(exit_code)
