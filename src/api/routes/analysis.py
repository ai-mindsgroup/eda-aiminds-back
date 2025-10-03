"""
Rotas para Análises Avançadas
=============================

Endpoints para análises especializadas e visualizações.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.agent.orchestrator_agent import OrchestratorAgent
from src.api.schemas import BaseResponse, SystemStats
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/stats",
    response_model=SystemStats,
    summary="Estatísticas do sistema",
    description="Estatísticas gerais de uso do sistema",
)
async def get_system_stats():
    """
    Estatísticas gerais do sistema.
    
    Retorna métricas de uso, performance e dados armazenados.
    """
    try:
        from src.vectorstore.supabase_client import supabase
        
        # Contar embeddings
        embeddings_result = supabase.table('embeddings').select('id', count='exact').execute()
        embeddings_count = embeddings_result.count or 0
        
        # Contar análises (metadados)
        metadata_result = supabase.table('metadata').select('id', count='exact').execute()
        analyses_count = metadata_result.count or 0
        
        # Simular outras métricas (em produção, seria real)
        stats = SystemStats(
            total_files_processed=50,  # TODO: Implementar contador real
            total_analyses_performed=analyses_count,
            total_queries_answered=150,  # TODO: Implementar contador real
            active_sessions=len(getattr(router, '_chat_sessions', {})),
            database_size_mb=25.5,  # TODO: Calcular tamanho real
            vectorstore_embeddings=embeddings_count,
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno obtendo estatísticas"
        )


@router.post(
    "/correlation",
    summary="Análise de correlação",
    description="Analisa correlações entre variáveis dos dados",
)
async def correlation_analysis(
    file_id: str,
    variables: Optional[List[str]] = None,
    correlation_method: str = "pearson",
):
    """
    Análise de correlação entre variáveis.
    
    **Métodos disponíveis:**
    - **pearson**: Correlação de Pearson (linear)
    - **spearman**: Correlação de Spearman (não-linear)
    - **kendall**: Correlação de Kendall (ordinal)
    """
    start_time = time.time()
    
    try:
        # Importar cache de arquivos
        from src.api.routes.csv import _file_cache
        
        if file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado"
            )
        
        file_data = _file_cache[file_id]
        df = file_data['dataframe']
        
        logger.info(f"📊 Análise de correlação: {file_id} (método: {correlation_method})")
        
        # Preparar contexto
        context = {
            'dataframe': df,
            'analysis_type': 'correlation',
            'variables': variables,
            'correlation_method': correlation_method,
        }
        
        # Executar análise
        orchestrator = OrchestratorAgent(enable_csv_agent=True)
        query = f"Analise as correlações entre as variáveis usando o método {correlation_method}"
        
        result = orchestrator.process(query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'success': True,
            'message': 'Análise de correlação concluída',
            'analysis_id': f"corr_{uuid.uuid4().hex[:12]}",
            'result': result.get('content', 'Análise concluída'),
            'processing_time_ms': processing_time,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na análise de correlação: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na análise de correlação"
        )


@router.post(
    "/clustering",
    summary="Análise de clustering",
    description="Agrupa dados similares usando algoritmos de clustering",
)
async def clustering_analysis(
    file_id: str,
    n_clusters: int = 3,
    algorithm: str = "kmeans",
    features: Optional[List[str]] = None,
):
    """
    Análise de clustering (agrupamento).
    
    **Algoritmos disponíveis:**
    - **kmeans**: K-Means clustering
    - **dbscan**: DBSCAN clustering
    - **hierarchical**: Clustering hierárquico
    """
    start_time = time.time()
    
    try:
        from src.api.routes.csv import _file_cache
        
        if file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado"
            )
        
        file_data = _file_cache[file_id]
        df = file_data['dataframe']
        
        logger.info(f"🎯 Análise de clustering: {file_id} (algoritmo: {algorithm}, clusters: {n_clusters})")
        
        context = {
            'dataframe': df,
            'analysis_type': 'clustering',
            'n_clusters': n_clusters,
            'algorithm': algorithm,
            'features': features,
        }
        
        orchestrator = OrchestratorAgent(enable_csv_agent=True)
        query = f"Execute clustering com {algorithm} para {n_clusters} grupos"
        
        result = orchestrator.process(query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'success': True,
            'message': f'Clustering {algorithm} concluído',
            'analysis_id': f"cluster_{uuid.uuid4().hex[:12]}",
            'result': result.get('content', 'Análise concluída'),
            'n_clusters': n_clusters,
            'algorithm': algorithm,
            'processing_time_ms': processing_time,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no clustering: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na análise de clustering"
        )


@router.post(
    "/time-series",
    summary="Análise de séries temporais",
    description="Analisa tendências e padrões temporais nos dados",
)
async def time_series_analysis(
    file_id: str,
    date_column: str,
    value_column: str,
    frequency: str = "D",
    forecast_periods: int = 30,
):
    """
    Análise de séries temporais.
    
    **Parâmetros:**
    - **date_column**: Coluna com datas
    - **value_column**: Coluna com valores a analisar
    - **frequency**: Frequência dos dados (D=diário, M=mensal, H=horário)
    - **forecast_periods**: Períodos para previsão
    """
    start_time = time.time()
    
    try:
        from src.api.routes.csv import _file_cache
        
        if file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado"
            )
        
        file_data = _file_cache[file_id]
        df = file_data['dataframe']
        
        # Validar colunas
        if date_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Coluna de data '{date_column}' não encontrada"
            )
        
        if value_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Coluna de valor '{value_column}' não encontrada"
            )
        
        logger.info(f"📈 Análise temporal: {file_id} ({date_column} vs {value_column})")
        
        context = {
            'dataframe': df,
            'analysis_type': 'time_series',
            'date_column': date_column,
            'value_column': value_column,
            'frequency': frequency,
            'forecast_periods': forecast_periods,
        }
        
        orchestrator = OrchestratorAgent(enable_csv_agent=True)
        query = f"Analise a série temporal de {value_column} ao longo de {date_column}"
        
        result = orchestrator.process(query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'success': True,
            'message': 'Análise de séries temporais concluída',
            'analysis_id': f"timeseries_{uuid.uuid4().hex[:12]}",
            'result': result.get('content', 'Análise concluída'),
            'date_column': date_column,
            'value_column': value_column,
            'forecast_periods': forecast_periods,
            'processing_time_ms': processing_time,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na análise temporal: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na análise temporal"
        )


@router.post(
    "/anomaly-detection",
    summary="Detecção de anomalias",
    description="Identifica valores atípicos e anomalias nos dados",
)
async def anomaly_detection(
    file_id: str,
    target_column: str,
    method: str = "isolation_forest",
    contamination: float = 0.1,
):
    """
    Detecção de anomalias.
    
    **Métodos disponíveis:**
    - **isolation_forest**: Isolation Forest
    - **one_class_svm**: One-Class SVM
    - **local_outlier_factor**: Local Outlier Factor
    - **statistical**: Métodos estatísticos (Z-score, IQR)
    """
    start_time = time.time()
    
    try:
        from src.api.routes.csv import _file_cache
        
        if file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado"
            )
        
        file_data = _file_cache[file_id]
        df = file_data['dataframe']
        
        if target_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Coluna '{target_column}' não encontrada"
            )
        
        logger.info(f"🔍 Detecção de anomalias: {file_id} (coluna: {target_column}, método: {method})")
        
        context = {
            'dataframe': df,
            'analysis_type': 'anomaly_detection',
            'target_column': target_column,
            'method': method,
            'contamination': contamination,
        }
        
        orchestrator = OrchestratorAgent(enable_csv_agent=True)
        query = f"Detecte anomalias na coluna {target_column} usando {method}"
        
        result = orchestrator.process(query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'success': True,
            'message': f'Detecção de anomalias concluída usando {method}',
            'analysis_id': f"anomaly_{uuid.uuid4().hex[:12]}",
            'result': result.get('content', 'Análise concluída'),
            'target_column': target_column,
            'method': method,
            'contamination': contamination,
            'processing_time_ms': processing_time,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na detecção de anomalias: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na detecção de anomalias"
        )


@router.get(
    "/history",
    summary="Histórico de análises",
    description="Lista análises realizadas recentemente",
)
async def get_analysis_history(
    limit: int = Query(20, ge=1, le=100, description="Número máximo de análises"),
    analysis_type: Optional[str] = Query(None, description="Filtrar por tipo de análise"),
):
    """
    Histórico de análises realizadas.
    
    Lista as análises mais recentes com informações básicas.
    """
    try:
        # Em implementação real, buscar do banco de dados
        # Por enquanto, retornar estrutura simulada
        
        analyses = [
            {
                'analysis_id': f"analysis_{i}",
                'type': 'fraud_detection',
                'file_name': f'transactions_{i}.csv',
                'created_at': time.time() - (i * 3600),  # Cada uma 1h mais antiga
                'status': 'completed',
                'processing_time_ms': 1500 + (i * 100),
            }
            for i in range(1, min(limit + 1, 21))
        ]
        
        # Filtrar por tipo se especificado
        if analysis_type:
            analyses = [a for a in analyses if a['type'] == analysis_type]
        
        return {
            'success': True,
            'message': f'{len(analyses)} análise(s) encontrada(s)',
            'analyses': analyses,
            'total_count': len(analyses),
        }
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo histórico: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno obtendo histórico"
        )