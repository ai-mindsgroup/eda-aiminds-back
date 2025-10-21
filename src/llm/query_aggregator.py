"""
Query Aggregator - Execução e Agregação de Fragmentos
=====================================================

Sistema que executa fragmentos sequencialmente, usa cache inteligente
e agrega resultados finais de múltiplos fragmentos.

Autor: Sistema Multiagente EDA AI Minds
Data: 2025-01-20
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
import pandas as pd
import json
from datetime import datetime
import time

from src.utils.logging_config import get_logger
from src.llm.manager import LLMConfig
from src.llm.query_fragmentation import (
    QueryFragment,
    FragmentResult,
    FragmentCache,
    FragmentStrategy,
    get_fragmenter_llm
)

logger = get_logger(__name__)


class FragmentExecutor:
    """
    Executor de fragmentos individuais.
    
    Executa um fragmento aplicando filtros de colunas/linhas
    e retorna o resultado.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o executor.
        
        Args:
            df: DataFrame completo (será filtrado por fragmento)
        """
        self.df = df
        self.logger = get_logger(f"{__name__}.FragmentExecutor")
    
    def execute(self, fragment: QueryFragment) -> pd.DataFrame:
        """
        Executa um fragmento aplicando filtros.
        
        Args:
            fragment: Fragmento a executar
            
        Returns:
            DataFrame filtrado
        """
        df_result = self.df
        
        # Aplica filtro de colunas
        if fragment.columns:
            # Valida que colunas existem
            valid_cols = [col for col in fragment.columns if col in self.df.columns]
            if valid_cols:
                df_result = df_result[valid_cols]
            else:
                self.logger.warning(f"Nenhuma coluna válida em {fragment.fragment_id}")
        
        # Aplica filtro de linhas
        if fragment.row_range:
            start, end = fragment.row_range
            df_result = df_result.iloc[start:end]
        
        # Aplica filtros adicionais
        if fragment.filters:
            for column, value in fragment.filters.items():
                if column in df_result.columns:
                    df_result = df_result[df_result[column] == value]
        
        return df_result


class QueryAggregator:
    """
    Agregador inteligente de resultados de múltiplos fragmentos.
    
    Executa fragmentos sequencialmente, usa cache, e agrega
    resultados finais de forma inteligente.
    """
    
    def __init__(
        self,
        session_id: str,
        df: pd.DataFrame,
        use_cache: bool = True
    ):
        """
        Inicializa o agregador.
        
        Args:
            session_id: ID da sessão para cache
            df: DataFrame completo
            use_cache: Se deve usar cache de fragmentos
        """
        self.session_id = session_id
        self.df = df
        self.use_cache = use_cache
        self.executor = FragmentExecutor(df)
        self.cache = FragmentCache(session_id) if use_cache else None
        self.llm_manager = get_fragmenter_llm()
        self.logger = get_logger(f"{__name__}.QueryAggregator")
        
        # Métricas de execução
        self.metrics = {
            'total_fragments': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_tokens_used': 0,
            'total_processing_time_ms': 0,
            'fragments_executed': 0,
            'fragments_failed': 0
        }
    
    async def execute_fragment(
        self,
        fragment: QueryFragment,
        analysis_function: Optional[Callable] = None
    ) -> FragmentResult:
        """
        Executa um fragmento individual com cache.
        
        Args:
            fragment: Fragmento a executar
            analysis_function: Função customizada para analisar fragmento (opcional)
            
        Returns:
            Resultado do fragmento
        """
        self.logger.info(f"▶️  Executando fragmento: {fragment.fragment_id}")
        
        # Tenta buscar em cache
        if self.use_cache and self.cache:
            cached = await self.cache.get_cached_result(fragment)
            if cached:
                self.metrics['cache_hits'] += 1
                return cached
            self.metrics['cache_misses'] += 1
        
        # Executa fragmento
        start_time = time.time()
        
        try:
            # Aplica filtros e obtém subset do DataFrame
            df_fragment = self.executor.execute(fragment)
            
            # Se tem função de análise customizada, usa
            if analysis_function:
                result_data = analysis_function(df_fragment)
            else:
                # Análise padrão: retorna estatísticas básicas
                result_data = {
                    'shape': df_fragment.shape,
                    'statistics': df_fragment.describe().to_dict() if not df_fragment.empty else {},
                    'sample': df_fragment.head(10).to_dict('records') if not df_fragment.empty else []
                }
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Estima tokens usados (baseado no tamanho do resultado)
            result_str = json.dumps(result_data, default=str)
            tokens_used = len(result_str) // 4 + 1
            
            result = FragmentResult(
                fragment_id=fragment.fragment_id,
                success=True,
                result=result_data,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                from_cache=False
            )
            
            # Salva em cache
            if self.use_cache and self.cache:
                await self.cache.save_result(fragment, result, ttl_hours=24)
            
            self.metrics['fragments_executed'] += 1
            self.metrics['total_tokens_used'] += tokens_used
            self.metrics['total_processing_time_ms'] += processing_time_ms
            
            self.logger.info(
                f"✅ {fragment.fragment_id}: "
                f"{processing_time_ms}ms, "
                f"~{tokens_used} tokens, "
                f"shape={df_fragment.shape}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao executar {fragment.fragment_id}: {str(e)}")
            self.metrics['fragments_failed'] += 1
            
            return FragmentResult(
                fragment_id=fragment.fragment_id,
                success=False,
                result=None,
                tokens_used=0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )
    
    async def execute_all_fragments(
        self,
        fragments: List[QueryFragment],
        analysis_function: Optional[Callable] = None,
        max_concurrent: int = 1  # Sequencial por padrão para evitar rate limits
    ) -> List[FragmentResult]:
        """
        Executa todos os fragmentos.
        
        Args:
            fragments: Lista de fragmentos a executar
            analysis_function: Função de análise customizada
            max_concurrent: Máximo de fragmentos concorrentes
            
        Returns:
            Lista de resultados
        """
        self.metrics['total_fragments'] = len(fragments)
        
        self.logger.info(f"🚀 Executando {len(fragments)} fragmentos...")
        
        if max_concurrent == 1:
            # Execução sequencial
            results = []
            for i, fragment in enumerate(fragments, 1):
                self.logger.info(f"📦 Fragmento {i}/{len(fragments)}")
                result = await self.execute_fragment(fragment, analysis_function)
                results.append(result)
        else:
            # Execução concorrente (com semáforo para limitar concorrência)
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def execute_with_semaphore(frag):
                async with semaphore:
                    return await self.execute_fragment(frag, analysis_function)
            
            results = await asyncio.gather(*[
                execute_with_semaphore(frag) for frag in fragments
            ])
        
        # Log métricas finais
        self.logger.info("\n" + "="*80)
        self.logger.info("📊 MÉTRICAS DE EXECUÇÃO")
        self.logger.info("="*80)
        self.logger.info(f"Total fragmentos: {self.metrics['total_fragments']}")
        self.logger.info(f"✅ Executados: {self.metrics['fragments_executed']}")
        self.logger.info(f"❌ Falhados: {self.metrics['fragments_failed']}")
        self.logger.info(f"💾 Cache hits: {self.metrics['cache_hits']}")
        self.logger.info(f"🔄 Cache misses: {self.metrics['cache_misses']}")
        if self.metrics['total_fragments'] > 0:
            hit_rate = (self.metrics['cache_hits'] / self.metrics['total_fragments']) * 100
            self.logger.info(f"📈 Cache hit rate: {hit_rate:.1f}%")
        self.logger.info(f"🎯 Tokens totais: {self.metrics['total_tokens_used']}")
        self.logger.info(f"⏱️  Tempo total: {self.metrics['total_processing_time_ms']}ms")
        self.logger.info("="*80 + "\n")
        
        return results
    
    async def aggregate_results(
        self,
        query: str,
        fragments: List[QueryFragment],
        results: List[FragmentResult],
        strategy: FragmentStrategy
    ) -> Dict[str, Any]:
        """
        Agrega resultados de múltiplos fragmentos usando LLM.
        
        Args:
            query: Query original do usuário
            fragments: Fragmentos executados
            results: Resultados dos fragmentos
            strategy: Estratégia de fragmentação usada
            
        Returns:
            Resultado agregado final
        """
        self.logger.info(f"🔄 Agregando {len(results)} resultados...")
        
        # Filtra apenas sucessos
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {
                'success': False,
                'error': 'Todos os fragmentos falharam',
                'metrics': self.metrics
            }
        
        # Se estratégia é COLUMN_GROUPS ou HYBRID, pode precisar merge lateral
        if strategy in [FragmentStrategy.COLUMN_GROUPS, FragmentStrategy.HYBRID]:
            # Agrega resultados de colunas diferentes
            aggregated_data = self._aggregate_column_results(successful_results)
        else:
            # Agrega resultados de segmentos de linhas
            aggregated_data = self._aggregate_row_results(successful_results)
        
        # Usa LLM para gerar resposta final baseada nos dados agregados
        final_response = await self._generate_final_response(
            query=query,
            aggregated_data=aggregated_data,
            strategy=strategy
        )
        
        return {
            'success': True,
            'response': final_response,
            'aggregated_data': aggregated_data,
            'fragments_used': len(successful_results),
            'metrics': self.metrics
        }
    
    def _aggregate_column_results(self, results: List[FragmentResult]) -> Dict[str, Any]:
        """Agrega resultados de fragmentos com colunas diferentes."""
        self.logger.info("   🔀 Agregando por colunas...")
        
        # Combina estatísticas de todas as colunas
        all_statistics = {}
        all_samples = []
        
        for result in results:
            if isinstance(result.result, dict):
                if 'statistics' in result.result:
                    all_statistics.update(result.result['statistics'])
                if 'sample' in result.result:
                    all_samples.extend(result.result['sample'][:5])  # Pega amostra de cada
        
        return {
            'statistics': all_statistics,
            'sample': all_samples[:20],  # Limita amostra total
            'num_fragments': len(results)
        }
    
    def _aggregate_row_results(self, results: List[FragmentResult]) -> Dict[str, Any]:
        """Agrega resultados de fragmentos com linhas diferentes."""
        self.logger.info("   📊 Agregando por linhas...")
        
        # Para segmentos de linhas, pode combinar amostras e calcular estatísticas globais
        all_samples = []
        total_rows = 0
        
        for result in results:
            if isinstance(result.result, dict):
                if 'sample' in result.result:
                    all_samples.extend(result.result['sample'][:10])
                if 'shape' in result.result:
                    total_rows += result.result['shape'][0]
        
        return {
            'total_rows_analyzed': total_rows,
            'sample': all_samples[:30],  # Amostra combinada
            'num_fragments': len(results)
        }
    
    async def _generate_final_response(
        self,
        query: str,
        aggregated_data: Dict[str, Any],
        strategy: FragmentStrategy
    ) -> str:
        """
        Usa LLM para gerar resposta final baseada nos dados agregados.
        
        Args:
            query: Query original
            aggregated_data: Dados agregados
            strategy: Estratégia usada
            
        Returns:
            Resposta final em linguagem natural
        """
        self.logger.info("   🤖 Gerando resposta final com LLM...")
        
        # Prepara contexto para o LLM
        data_summary = json.dumps(aggregated_data, indent=2, default=str)[:3000]  # Limita tamanho
        
        prompt = f"""Você é um assistente de análise de dados.

A query do usuário foi fragmentada e processada em partes. Agora você deve gerar uma resposta coesa baseada nos resultados agregados.

**QUERY ORIGINAL:**
"{query}"

**ESTRATÉGIA DE FRAGMENTAÇÃO:**
{strategy.value}

**DADOS AGREGADOS:**
{data_summary}

**INSTRUÇÕES:**
1. Responda à query do usuário de forma clara e direta
2. Use os dados agregados para embasar sua resposta
3. Se houver limitações nos dados (fragmentação, amostras), mencione brevemente
4. Seja conciso mas completo

**RESPOSTA:**"""

        try:
            config = LLMConfig(temperature=0.3, max_tokens=800)
            response = self.llm_manager.chat(prompt=prompt, config=config)
            
            if response.success:
                self.logger.info("   ✅ Resposta final gerada com sucesso")
                return response.content
            else:
                self.logger.warning(f"   ⚠️ LLM falhou: {response.error}")
                # Fallback: retorna dados brutos
                return f"Análise concluída com {aggregated_data.get('num_fragments', 0)} fragmentos. Dados: {json.dumps(aggregated_data, indent=2, default=str)[:500]}"
                
        except Exception as e:
            self.logger.error(f"   ❌ Erro ao gerar resposta: {str(e)}")
            return f"Erro ao gerar resposta final: {str(e)}"


async def execute_fragmented_query(
    query: str,
    df: pd.DataFrame,
    fragments: List[QueryFragment],
    strategy: FragmentStrategy,
    session_id: str,
    analysis_function: Optional[Callable] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Função helper para executar query fragmentada completa.
    
    Args:
        query: Query original do usuário
        df: DataFrame completo
        fragments: Lista de fragmentos
        strategy: Estratégia de fragmentação
        session_id: ID da sessão
        analysis_function: Função de análise customizada (opcional)
        use_cache: Se deve usar cache
        
    Returns:
        Resultado agregado final
    """
    aggregator = QueryAggregator(session_id, df, use_cache)
    
    # Executa todos os fragmentos
    results = await aggregator.execute_all_fragments(fragments, analysis_function)
    
    # Agrega resultados
    final_result = await aggregator.aggregate_results(query, fragments, results, strategy)
    
    return final_result
