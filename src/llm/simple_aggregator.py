"""
Simple Query Aggregator - Agregação Leve de Resultados
=======================================================

Agregador simplificado que consolida resultados de fragmentos
sem usar LLM, usando regras heurísticas rápidas.

**OTIMIZAÇÕES:**
- Sem LLM para agregação (usa Pandas diretamente)
- Agregação em memória eficiente
- Regras simples baseadas no tipo de dados

Autor: Sistema Multiagente EDA AI Minds
Data: 2025-01-20
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime

from src.utils.logging_config import get_logger
from src.llm.query_fragmentation import FragmentResult, FragmentStrategy

logger = get_logger(__name__)


class SimpleQueryAggregator:
    """
    Agregador ultra-simples que não usa LLM.
    
    **ESTRATÉGIAS:**
    - COLUMN_GROUPS: Merge horizontal (concatena colunas)
    - ROW_SEGMENTS: Concatena verticalmente
    - HYBRID: Concatena verticalmente
    """
    
    def __init__(self):
        """Inicializa o agregador."""
        self.logger = get_logger(f"{__name__}.SimpleQueryAggregator")
    
    def aggregate_results(
        self,
        results: List[FragmentResult],
        strategy: FragmentStrategy
    ) -> Dict[str, Any]:
        """
        Agrega resultados de múltiplos fragmentos.
        
        Args:
            results: Lista de resultados de fragmentos
            strategy: Estratégia de fragmentação usada
            
        Returns:
            Resultado agregado
        """
        start_time = datetime.now()
        
        # Filtra apenas sucessos
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {
                'success': False,
                'error': 'Nenhum fragmento retornou sucesso',
                'fragments_total': len(results),
                'fragments_success': 0
            }
        
        self.logger.info(
            f"📊 Agregando {len(successful_results)}/{len(results)} resultados "
            f"(estratégia: {strategy.value})"
        )
        
        # Tenta agregar baseado no tipo de resultado
        first_result = successful_results[0].result
        
        # Se todos são DataFrames, concatena
        if all(isinstance(r.result, pd.DataFrame) for r in successful_results):
            aggregated = self._aggregate_dataframes(successful_results, strategy)
        
        # Se todos são dicts com estatísticas, merge
        elif all(isinstance(r.result, dict) for r in successful_results):
            aggregated = self._aggregate_dicts(successful_results, strategy)
        
        # Se todos são listas, concatena
        elif all(isinstance(r.result, list) for r in successful_results):
            aggregated = self._aggregate_lists(successful_results)
        
        # Fallback: retorna primeiro resultado
        else:
            self.logger.warning("Tipos mistos, retornando primeiro resultado")
            aggregated = first_result
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            'success': True,
            'result': aggregated,
            'fragments_total': len(results),
            'fragments_success': len(successful_results),
            'tokens_total': sum(r.tokens_used for r in successful_results),
            'processing_time_ms': int(processing_time),
            'from_cache_count': sum(1 for r in results if r.from_cache),
            'strategy': strategy.value
        }
    
    def _aggregate_dataframes(
        self,
        results: List[FragmentResult],
        strategy: FragmentStrategy
    ) -> pd.DataFrame:
        """Agrega DataFrames."""
        dfs = [r.result for r in results if isinstance(r.result, pd.DataFrame)]
        
        if not dfs:
            return pd.DataFrame()
        
        if strategy == FragmentStrategy.ROW_SEGMENTS or strategy == FragmentStrategy.HYBRID:
            # Concatena verticalmente (linhas)
            self.logger.info("   📑 Concatenando DataFrames verticalmente...")
            return pd.concat(dfs, axis=0, ignore_index=True)
        
        elif strategy == FragmentStrategy.COLUMN_GROUPS:
            # Concatena horizontalmente (colunas)
            self.logger.info("   📑 Concatenando DataFrames horizontalmente...")
            # Assume que têm mesmo índice
            return pd.concat(dfs, axis=1)
        
        else:
            # Default: vertical
            return pd.concat(dfs, axis=0, ignore_index=True)
    
    def _aggregate_dicts(
        self,
        results: List[FragmentResult],
        strategy: FragmentStrategy
    ) -> Dict:
        """Agrega dicionários (estatísticas)."""
        merged = {}
        
        for result in results:
            if isinstance(result.result, dict):
                # Merge simples
                for key, value in result.result.items():
                    if key not in merged:
                        merged[key] = []
                    merged[key].append(value)
        
        # Para valores numéricos, calcula média
        aggregated = {}
        for key, values in merged.items():
            if all(isinstance(v, (int, float)) for v in values):
                aggregated[key] = sum(values) / len(values)
            else:
                # Mantém lista
                aggregated[key] = values
        
        self.logger.info(f"   📊 {len(aggregated)} campos agregados")
        return aggregated
    
    def _aggregate_lists(self, results: List[FragmentResult]) -> List:
        """Agrega listas."""
        all_items = []
        for result in results:
            if isinstance(result.result, list):
                all_items.extend(result.result)
        
        self.logger.info(f"   📋 {len(all_items)} itens agregados")
        return all_items


class FragmentExecutor:
    """
    Executor simples de fragmentos sem LLM.
    
    Executa operações diretamente no DataFrame.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa executor.
        
        Args:
            df: DataFrame completo
        """
        self.df = df
        self.logger = get_logger(f"{__name__}.FragmentExecutor")
    
    def execute_fragment(
        self,
        fragment,  # QueryFragment
        operation: str = "select"
    ) -> FragmentResult:
        """
        Executa um fragmento.
        
        Args:
            fragment: Fragmento a executar
            operation: Tipo de operação ("select", "describe", "count")
            
        Returns:
            Resultado da execução
        """
        from src.llm.query_fragmentation import FragmentResult
        
        start_time = datetime.now()
        
        try:
            # Seleciona dados do fragmento
            if fragment.row_range:
                start_row, end_row = fragment.row_range
                df_fragment = self.df.iloc[start_row:end_row]
            else:
                df_fragment = self.df
            
            if fragment.columns:
                df_fragment = df_fragment[fragment.columns]
            
            # Executa operação
            if operation == "select":
                result = df_fragment
            elif operation == "describe":
                result = df_fragment.describe().to_dict()
            elif operation == "count":
                result = {
                    'count': len(df_fragment),
                    'columns': len(df_fragment.columns)
                }
            else:
                result = df_fragment
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return FragmentResult(
                fragment_id=fragment.fragment_id,
                success=True,
                result=result,
                tokens_used=fragment.estimated_tokens,
                processing_time_ms=int(processing_time),
                from_cache=False
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.error(f"Erro ao executar fragmento {fragment.fragment_id}: {str(e)}")
            
            return FragmentResult(
                fragment_id=fragment.fragment_id,
                success=False,
                result=None,
                tokens_used=0,
                processing_time_ms=int(processing_time),
                error=str(e)
            )


def execute_and_aggregate(
    df: pd.DataFrame,
    fragments: List,
    operation: str = "select"
) -> Dict[str, Any]:
    """
    Helper para executar e agregar fragmentos rapidamente.
    
    Args:
        df: DataFrame completo
        fragments: Lista de QueryFragment
        operation: Operação a executar
        
    Returns:
        Resultado agregado
    """
    if not fragments:
        return {
            'success': False,
            'error': 'Nenhum fragmento fornecido'
        }
    
    executor = FragmentExecutor(df)
    aggregator = SimpleQueryAggregator()
    
    # Executa todos os fragmentos
    results = []
    for fragment in fragments:
        result = executor.execute_fragment(fragment, operation)
        results.append(result)
    
    # Agrega resultados
    strategy = fragments[0].strategy if fragments else None
    return aggregator.aggregate_results(results, strategy)
