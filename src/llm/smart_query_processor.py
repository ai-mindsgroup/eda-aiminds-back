"""
Smart Query Processor - Processador Inteligente de Queries com Fragmentação Automática
=======================================================================================

Wrapper de alto nível que integra fragmentação, cache e agregação automaticamente.

Uso:
    processor = SmartQueryProcessor(session_id="session123")
    result = await processor.process(query="Analise todas as transações", df=dataset)

Autor: Sistema Multiagente EDA AI Minds
Data: 2025-01-20
"""

import asyncio
from typing import Dict, Optional, Any, Callable
import pandas as pd
from datetime import datetime

from src.utils.logging_config import get_logger
from src.llm.query_fragmentation import TokenBudget, FragmentStrategy
from src.llm.query_fragmenter import QueryFragmenter, fragment_query
from src.llm.query_aggregator import QueryAggregator, execute_fragmented_query

logger = get_logger(__name__)


class SmartQueryProcessor:
    """
    Processador inteligente de queries com fragmentação automática.
    
    Detecta automaticamente se query precisa de fragmentação,
    aplica estratégia ideal, usa cache e agrega resultados.
    """
    
    def __init__(
        self,
        session_id: str,
        token_budget: Optional[TokenBudget] = None,
        use_cache: bool = True,
        auto_fragment: bool = True
    ):
        """
        Inicializa o processador.
        
        Args:
            session_id: ID da sessão para cache e memória
            token_budget: Orçamento de tokens (usa padrão se None)
            use_cache: Se deve usar cache de fragmentos
            auto_fragment: Se deve fragmentar automaticamente queries grandes
        """
        self.session_id = session_id
        self.token_budget = token_budget or TokenBudget()
        self.use_cache = use_cache
        self.auto_fragment = auto_fragment
        self.logger = get_logger(f"{__name__}.SmartQueryProcessor")
        
        # Histórico de processamento
        self.processing_history = []
    
    async def process(
        self,
        query: str,
        df: pd.DataFrame,
        analysis_function: Optional[Callable] = None,
        force_fragment: bool = False
    ) -> Dict[str, Any]:
        """
        Processa uma query de forma inteligente.
        
        Args:
            query: Query do usuário
            df: DataFrame a processar
            analysis_function: Função customizada de análise (opcional)
            force_fragment: Força fragmentação mesmo se não necessário
            
        Returns:
            Resultado processado
        """
        start_time = datetime.now()
        self.logger.info("\n" + "="*80)
        self.logger.info(f"🎯 PROCESSANDO QUERY INTELIGENTE")
        self.logger.info("="*80)
        self.logger.info(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        self.logger.info(f"Dataset: {df.shape[0]} linhas, {df.shape[1]} colunas")
        self.logger.info(f"Session: {self.session_id}")
        self.logger.info("="*80)
        
        # Decide se precisa fragmentar
        if not self.auto_fragment and not force_fragment:
            self.logger.info("⚡ Modo sem fragmentação - executando diretamente")
            result = await self._process_without_fragmentation(
                query, df, analysis_function
            )
        else:
            # Analisa necessidade de fragmentação
            needs_frag, fragments, reason = await fragment_query(
                query=query,
                df=df,
                token_budget=self.token_budget
            )
            
            if not needs_frag and not force_fragment:
                self.logger.info(f"✅ {reason}")
                result = await self._process_without_fragmentation(
                    query, df, analysis_function
                )
            else:
                self.logger.info(f"🔀 Fragmentação necessária: {reason}")
                result = await self._process_with_fragmentation(
                    query, df, fragments, analysis_function
                )
        
        # Calcula tempo total
        total_time = (datetime.now() - start_time).total_seconds()
        result['total_processing_time_seconds'] = total_time
        result['session_id'] = self.session_id
        result['query'] = query
        result['timestamp'] = datetime.now().isoformat()
        
        # Salva no histórico
        self.processing_history.append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'success': result.get('success', False),
            'fragmented': result.get('metrics', {}).get('total_fragments', 0) > 0,
            'processing_time_seconds': total_time
        })
        
        self.logger.info("\n" + "="*80)
        self.logger.info(f"✅ PROCESSAMENTO CONCLUÍDO em {total_time:.2f}s")
        self.logger.info("="*80 + "\n")
        
        return result
    
    async def _process_without_fragmentation(
        self,
        query: str,
        df: pd.DataFrame,
        analysis_function: Optional[Callable]
    ) -> Dict[str, Any]:
        """Processa query sem fragmentação."""
        try:
            if analysis_function:
                result_data = analysis_function(df)
            else:
                # Análise padrão simples
                result_data = {
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'statistics': df.describe().to_dict(),
                    'sample': df.head(20).to_dict('records')
                }
            
            return {
                'success': True,
                'response': f"Análise concluída para dataset com {df.shape[0]} linhas e {df.shape[1]} colunas.",
                'data': result_data,
                'metrics': {
                    'total_fragments': 0,
                    'cache_hits': 0,
                    'fragments_executed': 1
                }
            }
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'metrics': {'total_fragments': 0}
            }
    
    async def _process_with_fragmentation(
        self,
        query: str,
        df: pd.DataFrame,
        fragments: list,
        analysis_function: Optional[Callable]
    ) -> Dict[str, Any]:
        """Processa query com fragmentação."""
        # Detecta estratégia usada
        strategy = fragments[0].strategy if fragments else FragmentStrategy.ROW_SEGMENTS
        
        # Executa fragmentos e agrega
        result = await execute_fragmented_query(
            query=query,
            df=df,
            fragments=fragments,
            strategy=strategy,
            session_id=self.session_id,
            analysis_function=analysis_function,
            use_cache=self.use_cache
        )
        
        return result
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo de métricas do processador."""
        total_queries = len(self.processing_history)
        successful = sum(1 for h in self.processing_history if h['success'])
        fragmented = sum(1 for h in self.processing_history if h['fragmented'])
        
        avg_time = sum(h['processing_time_seconds'] for h in self.processing_history) / total_queries if total_queries > 0 else 0
        
        return {
            'total_queries_processed': total_queries,
            'successful_queries': successful,
            'failed_queries': total_queries - successful,
            'queries_fragmented': fragmented,
            'queries_direct': total_queries - fragmented,
            'fragmentation_rate': (fragmented / total_queries * 100) if total_queries > 0 else 0,
            'average_processing_time_seconds': avg_time,
            'session_id': self.session_id
        }


# Função helper síncrona
def process_query_smart(
    query: str,
    df: pd.DataFrame,
    session_id: str,
    analysis_function: Optional[Callable] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Função síncrona helper para processar query inteligente.
    
    Args:
        query: Query do usuário
        df: DataFrame a processar
        session_id: ID da sessão
        analysis_function: Função de análise customizada (opcional)
        use_cache: Se deve usar cache
        
    Returns:
        Resultado processado
    """
    processor = SmartQueryProcessor(
        session_id=session_id,
        use_cache=use_cache
    )
    
    # Executa assincronamente
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Se já tem event loop rodando, cria task
        import nest_asyncio
        nest_asyncio.apply()
    
    result = loop.run_until_complete(
        processor.process(query, df, analysis_function)
    )
    
    return result
