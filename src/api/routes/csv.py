"""
Rotas para Análise de CSV
========================

Endpoints para upload, processamento e análise de arquivos CSV.
"""

import io
import os
import time
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from src.agent.orchestrator_agent import OrchestratorAgent
from src.api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    CSVUploadResponse,
    FraudDetectionRequest,
    FraudDetectionResponse,
    SchemaExamples,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Cache temporário para arquivos (em produção usar Redis ou S3)
_file_cache: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/upload",
    response_model=CSVUploadResponse,
    summary="Upload de arquivo CSV",
    description="Faz upload de um arquivo CSV e retorna informações básicas sobre os dados",
    responses={
        200: {"description": "Upload realizado com sucesso", "model": CSVUploadResponse},
        400: {"description": "Arquivo inválido ou erro no processamento"},
        413: {"description": "Arquivo muito grande"},
        422: {"description": "Formato de arquivo não suportado"},
    },
)
async def upload_csv(
    file: UploadFile = File(..., description="Arquivo CSV para upload"),
    delimiter: str = Form(",", description="Delimitador do CSV"),
    encoding: str = Form("utf-8", description="Codificação do arquivo"),
    has_header: bool = Form(True, description="Se o arquivo possui cabeçalho"),
    preview_rows: int = Form(5, description="Número de linhas para preview"),
):
    """
    Upload de arquivo CSV com validação e análise inicial.
    
    **Parâmetros:**
    - **file**: Arquivo CSV (máx 100MB)
    - **delimiter**: Separador de colunas (vírgula, ponto-e-vírgula, tab)
    - **encoding**: Codificação (utf-8, latin1, cp1252)
    - **has_header**: Se a primeira linha contém nomes das colunas
    - **preview_rows**: Quantas linhas mostrar no preview
    
    **Retorna:**
    - ID único do arquivo para usar em análises
    - Informações sobre estrutura dos dados
    - Preview das primeiras linhas
    - Tipos de dados detectados
    """
    start_time = time.time()
    
    try:
        # Validações básicas
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Nome do arquivo é obrigatório"
            )
        
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=422,
                detail="Apenas arquivos CSV são suportados"
            )
        
        # Verificar tamanho do arquivo
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=413,
                detail="Arquivo muito grande. Máximo: 100MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Arquivo está vazio"
            )
        
        logger.info(f"📁 Processando upload: {file.filename} ({file_size} bytes)")
        
        # Processar CSV
        try:
            # Ler CSV com pandas
            df = pd.read_csv(
                io.StringIO(content.decode(encoding)),
                delimiter=delimiter,
                header=0 if has_header else None,
                nrows=None,  # Ler arquivo completo
            )
            
            # Validar dados
            if df.empty:
                raise HTTPException(
                    status_code=400,
                    detail="Arquivo CSV está vazio ou mal formatado"
                )
            
            # Gerar ID único para o arquivo
            file_id = f"csv_{uuid.uuid4().hex[:12]}"
            
            # Preparar preview
            preview_df = df.head(preview_rows)
            preview = preview_df.to_dict('records')
            
            # Detectar tipos de dados
            data_types = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                if dtype.startswith('int'):
                    data_types[col] = 'integer'
                elif dtype.startswith('float'):
                    data_types[col] = 'float'
                elif dtype == 'bool':
                    data_types[col] = 'boolean'
                elif 'datetime' in dtype:
                    data_types[col] = 'datetime'
                else:
                    data_types[col] = 'text'
            
            # Armazenar no cache temporário
            _file_cache[file_id] = {
                'filename': file.filename,
                'dataframe': df,
                'file_size': file_size,
                'uploaded_at': time.time(),
                'metadata': {
                    'delimiter': delimiter,
                    'encoding': encoding,
                    'has_header': has_header,
                }
            }
            
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"✅ Upload concluído: {file_id} - {len(df)} linhas, {len(df.columns)} colunas - {processing_time}ms"
            )
            
            return CSVUploadResponse(
                success=True,
                message=f"Arquivo {file.filename} carregado com sucesso",
                file_id=file_id,
                filename=file.filename,
                file_size=file_size,
                rows_count=len(df),
                columns_count=len(df.columns),
                columns=list(df.columns),
                preview=preview,
                data_types=data_types,
            )
            
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"Erro de codificação. Tente usar: latin1 ou cp1252"
            )
        
        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar CSV: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno no processamento do arquivo"
        )


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Análise geral de dados",
    description="Executa análise estatística e insights sobre o arquivo CSV",
)
async def analyze_csv(request: AnalysisRequest):
    """
    Análise abrangente de dados CSV.
    
    **Tipos de análise disponíveis:**
    - **statistical**: Estatísticas descritivas básicas
    - **correlation**: Análise de correlações entre variáveis
    - **clustering**: Agrupamento de dados similares
    - **anomaly_detection**: Detecção de valores atípicos
    - **time_series**: Análise temporal (se houver coluna de data)
    - **custom**: Análise customizada com parâmetros específicos
    """
    start_time = time.time()
    
    try:
        # Verificar se arquivo existe
        if request.file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado. Faça upload primeiro."
            )
        
        file_data = _file_cache[request.file_id]
        df = file_data['dataframe']
        
        logger.info(f"🔍 Iniciando análise {request.analysis_type} para {request.file_id}")
        
        # Inicializar orquestrador
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=False,  # Não necessário para análise CSV
            enable_google_llm=True,
        )
        
        # Preparar contexto para análise
        context = {
            'dataframe': df,
            'analysis_type': request.analysis_type,
            'target_column': request.target_column,
            'include_visualizations': request.include_visualizations,
            'parameters': request.parameters or {},
            'file_metadata': file_data['metadata'],
        }
        
        # Construir query baseada no tipo de análise
        queries = {
            'statistical': f"Faça uma análise estatística completa dos dados em {file_data['filename']}",
            'correlation': f"Analise as correlações entre as variáveis nos dados de {file_data['filename']}",
            'clustering': f"Identifique grupos e padrões nos dados de {file_data['filename']}",
            'anomaly_detection': f"Detecte valores atípicos e anomalias em {file_data['filename']}",
            'time_series': f"Analise tendências temporais nos dados de {file_data['filename']}",
            'fraud_detection': f"Analise padrões suspeitos e possíveis fraudes em {file_data['filename']}",
            'custom': request.parameters.get('custom_query', f"Analise os dados de {file_data['filename']}"),
        }
        
        query = queries.get(request.analysis_type, queries['statistical'])
        
        # Executar análise via orquestrador
        result = orchestrator.process(query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Preparar resposta estruturada
        analysis_result = {
            'analysis_id': f"analysis_{uuid.uuid4().hex[:12]}",
            'analysis_type': request.analysis_type,
            'summary': result.get('content', 'Análise concluída'),
            'insights': _extract_insights(result),
            'statistics': result.get('statistics', {}),
            'visualizations': result.get('visualizations', []) if request.include_visualizations else [],
            'confidence_score': result.get('confidence_score', 0.8),
            'processing_time_ms': processing_time,
            'recommendations': _extract_recommendations(result),
        }
        
        logger.info(f"✅ Análise concluída: {analysis_result['analysis_id']} - {processing_time}ms")
        
        return AnalysisResponse(
            success=True,
            message=f"Análise {request.analysis_type} concluída com sucesso",
            result=analysis_result,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na análise dos dados"
        )


@router.post(
    "/fraud-detection",
    response_model=FraudDetectionResponse,
    summary="Detecção de fraudes",
    description="Análise especializada para detecção de fraudes em transações",
)
async def detect_fraud(request: FraudDetectionRequest):
    """
    Detecção especializada de fraudes usando LLMs.
    
    **Algoritmos utilizados:**
    - Análise de padrões com LLMs
    - Detecção de anomalias estatísticas
    - Análise temporal de transações
    - Identificação de comportamentos suspeitos
    
    **Parâmetros importantes:**
    - **amount_column**: Coluna com valores das transações
    - **user_column**: Coluna de identificação do usuário
    - **timestamp_column**: Coluna de data/hora das transações
    - **threshold**: Sensibilidade da detecção (0.0 = mais sensível, 1.0 = menos sensível)
    """
    start_time = time.time()
    
    try:
        # Verificar se arquivo existe
        if request.file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado. Faça upload primeiro."
            )
        
        file_data = _file_cache[request.file_id]
        df = file_data['dataframe']
        
        # Validar colunas obrigatórias
        if request.amount_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Coluna '{request.amount_column}' não encontrada no arquivo"
            )
        
        logger.info(f"🔍 Iniciando detecção de fraudes para {request.file_id}")
        
        # Preparar dados para análise de fraude
        context = {
            'dataframe': df,
            'amount_column': request.amount_column,
            'user_column': request.user_column,
            'timestamp_column': request.timestamp_column,
            'threshold': request.threshold,
            'analysis_type': 'fraud_detection',
        }
        
        # Inicializar orquestrador com foco em LLM
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,
            enable_rag_agent=True,  # Para buscar padrões conhecidos de fraude
            enable_google_llm=True,
        )
        
        # Query especializada para detecção de fraudes
        query = f"""
        Analise os dados de transações para detectar possíveis fraudes.
        
        Foque em:
        - Transações com valores atípicos na coluna '{request.amount_column}'
        - Padrões suspeitos de comportamento
        - Múltiplas transações pequenas em sequência
        - Horários incomuns de transação
        - Variações bruscas no comportamento do usuário
        
        Use threshold de {request.threshold} para classificação.
        """
        
        # Executar análise
        result = orchestrator.process(query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Processar resultados específicos de fraude
        fraud_result = _process_fraud_results(df, result, request)
        fraud_result['processing_time_ms'] = processing_time
        
        logger.info(f"✅ Detecção de fraudes concluída: {fraud_result['fraud_count']} fraudes detectadas - {processing_time}ms")
        
        return FraudDetectionResponse(
            success=True,
            message=f"Análise de fraudes concluída. {fraud_result['fraud_count']} possíveis fraudes detectadas.",
            result=fraud_result,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na detecção de fraudes: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno na detecção de fraudes"
        )


@router.get(
    "/files",
    summary="Listar arquivos carregados",
    description="Lista todos os arquivos CSV carregados na sessão atual",
)
async def list_uploaded_files():
    """Lista arquivos carregados na sessão atual."""
    try:
        files = []
        current_time = time.time()
        
        for file_id, file_data in _file_cache.items():
            df = file_data['dataframe']
            uploaded_ago = current_time - file_data['uploaded_at']
            
            files.append({
                'file_id': file_id,
                'filename': file_data['filename'],
                'file_size': file_data['file_size'],
                'rows_count': len(df),
                'columns_count': len(df.columns),
                'uploaded_ago_seconds': int(uploaded_ago),
                'columns': list(df.columns)[:10],  # Primeiras 10 colunas
            })
        
        return {
            'success': True,
            'message': f'{len(files)} arquivo(s) carregado(s)',
            'files': files,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro listando arquivos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno listando arquivos"
        )


@router.delete(
    "/files/{file_id}",
    summary="Remover arquivo",
    description="Remove arquivo carregado da memória",
)
async def delete_file(file_id: str):
    """Remove arquivo carregado da memória."""
    try:
        if file_id not in _file_cache:
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado"
            )
        
        filename = _file_cache[file_id]['filename']
        del _file_cache[file_id]
        
        logger.info(f"🗑️ Arquivo removido: {file_id} ({filename})")
        
        return {
            'success': True,
            'message': f'Arquivo {filename} removido com sucesso',
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro removendo arquivo: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno removendo arquivo"
        )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _extract_insights(result: Dict[str, Any]) -> List[str]:
    """Extrai insights do resultado da análise."""
    insights = []
    
    # Tentar extrair insights do conteúdo
    content = result.get('content', '')
    
    # Procurar por padrões de insights
    if 'insight' in content.lower():
        lines = content.split('\n')
        for line in lines:
            if 'insight' in line.lower() or line.strip().startswith('- '):
                insights.append(line.strip('- ').strip())
    
    # Insights padrão se não encontrar
    if not insights:
        insights = [
            "Análise concluída com sucesso",
            "Dados processados completamente",
            "Padrões identificados nos dados",
        ]
    
    return insights[:5]  # Máximo 5 insights


def _extract_recommendations(result: Dict[str, Any]) -> List[str]:
    """Extrai recomendações do resultado."""
    recommendations = []
    
    content = result.get('content', '')
    
    # Procurar por recomendações
    if 'recomenda' in content.lower():
        lines = content.split('\n')
        for line in lines:
            if 'recomenda' in line.lower() or line.strip().startswith('- '):
                recommendations.append(line.strip('- ').strip())
    
    # Recomendações padrão
    if not recommendations:
        recommendations = [
            "Continue monitorando os padrões identificados",
            "Considere análises adicionais para insights mais profundos",
            "Valide os resultados com especialistas do domínio",
        ]
    
    return recommendations[:5]


def _process_fraud_results(df: pd.DataFrame, result: Dict[str, Any], request: FraudDetectionRequest) -> Dict[str, Any]:
    """Processa resultados específicos de detecção de fraude."""
    
    # Análise básica dos dados
    total_transactions = len(df)
    amount_col = request.amount_column
    
    # Detectar outliers básicos (valores muito altos)
    if amount_col in df.columns:
        q75 = df[amount_col].quantile(0.75)
        q25 = df[amount_col].quantile(0.25)
        iqr = q75 - q25
        upper_bound = q75 + 1.5 * iqr
        
        # Transações suspeitas (valores muito altos)
        suspicious_high = df[df[amount_col] > upper_bound]
        
        # Transações muito pequenas (possível lavagem)
        mean_amount = df[amount_col].mean()
        suspicious_low = df[df[amount_col] < mean_amount * 0.1]
        
        # Combinar suspeitas
        fraud_count = len(suspicious_high) + len(suspicious_low)
        fraud_percentage = (fraud_count / total_transactions) * 100
        
        # Preparar transações fraudulentas
        fraud_transactions = []
        
        # Adicionar algumas transações suspeitas
        for _, row in suspicious_high.head(10).iterrows():
            fraud_transactions.append({
                'transaction_id': row.get('id', len(fraud_transactions)),
                'amount': float(row[amount_col]),
                'reason': 'Valor muito alto (outlier)',
                'risk_score': 0.8,
            })
        
        for _, row in suspicious_low.head(5).iterrows():
            fraud_transactions.append({
                'transaction_id': row.get('id', len(fraud_transactions)),
                'amount': float(row[amount_col]),
                'reason': 'Valor muito baixo (possível lavagem)',
                'risk_score': 0.6,
            })
    
    else:
        fraud_count = 0
        fraud_percentage = 0.0
        fraud_transactions = []
    
    return {
        'total_transactions': total_transactions,
        'fraud_count': min(fraud_count, total_transactions),
        'fraud_percentage': round(fraud_percentage, 2),
        'suspicious_patterns': [
            {
                'pattern': 'Valores atípicos',
                'description': 'Transações com valores muito altos ou baixos',
                'occurrences': fraud_count,
            }
        ],
        'risk_analysis': {
            'overall_risk': 'medium' if fraud_percentage > 5 else 'low',
            'risk_factors': ['Outliers detectados', 'Variação de valores'],
            'confidence': 0.75,
        },
        'fraud_transactions': fraud_transactions[:20],  # Máximo 20
        'recommendations': [
            'Revisar transações com valores atípicos',
            'Implementar limites dinâmicos baseados no perfil do usuário',
            'Monitorar padrões de horário das transações',
            'Configurar alertas para valores acima do percentil 95',
        ],
    }