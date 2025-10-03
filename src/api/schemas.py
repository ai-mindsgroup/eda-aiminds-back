"""
Modelos Pydantic para API
========================

Schemas para requests e responses da API REST.
Validação automática e documentação OpenAPI.
"""

from __future__ import annotations

import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


# ============================================================================
# MODELOS BASE
# ============================================================================

class BaseResponse(BaseModel):
    """Modelo base para todas as respostas da API."""
    success: bool = Field(description="Se a operação foi bem-sucedida")
    message: str = Field(description="Mensagem descritiva da operação")
    timestamp: float = Field(default_factory=time.time, description="Timestamp da resposta")
    request_id: Optional[str] = Field(None, description="ID único da requisição")


class ErrorResponse(BaseResponse):
    """Modelo para respostas de erro."""
    success: bool = Field(False, description="Sempre false para erros")
    error_code: Optional[str] = Field(None, description="Código específico do erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais do erro")


class PaginationParams(BaseModel):
    """Parâmetros de paginação."""
    page: int = Field(1, ge=1, description="Número da página (inicia em 1)")
    page_size: int = Field(20, ge=1, le=100, description="Itens por página (máx 100)")


class PaginatedResponse(BaseResponse):
    """Resposta paginada."""
    data: List[Any] = Field(description="Dados da página")
    pagination: Dict[str, Any] = Field(description="Informações de paginação")
    

# ============================================================================
# ENUMS
# ============================================================================

class AnalysisType(str, Enum):
    """Tipos de análise disponíveis."""
    STATISTICAL = "statistical"
    FRAUD_DETECTION = "fraud_detection"
    CORRELATION = "correlation"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"
    CUSTOM = "custom"


class FileFormat(str, Enum):
    """Formatos de arquivo suportados."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"


class QueryType(str, Enum):
    """Tipos de consulta RAG."""
    SEMANTIC_SEARCH = "semantic_search"
    CHAT = "chat"
    DOCUMENT_QUERY = "document_query"
    ANALYSIS_QUERY = "analysis_query"


# ============================================================================
# SCHEMAS DE CSV E ANÁLISE
# ============================================================================

class CSVUploadResponse(BaseResponse):
    """Resposta do upload de CSV."""
    file_id: str = Field(description="ID único do arquivo")
    filename: str = Field(description="Nome do arquivo")
    file_size: int = Field(description="Tamanho em bytes")
    rows_count: int = Field(description="Número de linhas")
    columns_count: int = Field(description="Número de colunas")
    columns: List[str] = Field(description="Nomes das colunas")
    preview: List[Dict[str, Any]] = Field(description="Primeiras 5 linhas")
    data_types: Dict[str, str] = Field(description="Tipos de dados das colunas")
    

class AnalysisRequest(BaseModel):
    """Requisição para análise de dados."""
    file_id: str = Field(description="ID do arquivo CSV")
    analysis_type: AnalysisType = Field(description="Tipo de análise")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parâmetros específicos da análise")
    target_column: Optional[str] = Field(None, description="Coluna alvo para análise")
    include_visualizations: bool = Field(True, description="Incluir gráficos na resposta")
    session_id: Optional[str] = Field(None, description="ID da sessão para cache")


class AnalysisResult(BaseModel):
    """Resultado de uma análise."""
    analysis_id: str = Field(description="ID único da análise")
    analysis_type: AnalysisType = Field(description="Tipo de análise")
    summary: str = Field(description="Resumo dos resultados")
    insights: List[str] = Field(description="Insights descobertos")
    statistics: Dict[str, Any] = Field(description="Estatísticas calculadas")
    visualizations: Optional[List[Dict[str, Any]]] = Field(None, description="Gráficos gerados")
    confidence_score: float = Field(description="Pontuação de confiança (0-1)")
    processing_time_ms: int = Field(description="Tempo de processamento em ms")
    recommendations: List[str] = Field(description="Recomendações baseadas nos resultados")


class AnalysisResponse(BaseResponse):
    """Resposta de análise."""
    result: AnalysisResult = Field(description="Resultado da análise")


class FraudDetectionRequest(BaseModel):
    """Requisição específica para detecção de fraudes."""
    file_id: str = Field(description="ID do arquivo CSV")
    amount_column: str = Field(description="Nome da coluna de valores")
    user_column: Optional[str] = Field(None, description="Coluna de identificação do usuário")
    timestamp_column: Optional[str] = Field(None, description="Coluna de timestamp")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Limiar de detecção (0-1)")
    session_id: Optional[str] = Field(None, description="ID da sessão")


class FraudDetectionResult(BaseModel):
    """Resultado da detecção de fraudes."""
    total_transactions: int = Field(description="Total de transações analisadas")
    fraud_count: int = Field(description="Número de fraudes detectadas")
    fraud_percentage: float = Field(description="Porcentagem de fraudes")
    suspicious_patterns: List[Dict[str, Any]] = Field(description="Padrões suspeitos encontrados")
    risk_analysis: Dict[str, Any] = Field(description="Análise de risco detalhada")
    fraud_transactions: List[Dict[str, Any]] = Field(description="Transações fraudulentas")
    recommendations: List[str] = Field(description="Recomendações de segurança")


class FraudDetectionResponse(BaseResponse):
    """Resposta da detecção de fraudes."""
    result: FraudDetectionResult = Field(description="Resultado da detecção")


# ============================================================================
# SCHEMAS RAG E CHAT
# ============================================================================

class RAGQuery(BaseModel):
    """Consulta para sistema RAG."""
    query: str = Field(description="Pergunta ou consulta do usuário")
    query_type: QueryType = Field(QueryType.SEMANTIC_SEARCH, description="Tipo de consulta")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    session_id: Optional[str] = Field(None, description="ID da sessão para histórico")
    max_results: int = Field(5, ge=1, le=20, description="Máximo de resultados")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Limiar de similaridade")
    include_sources: bool = Field(True, description="Incluir fontes na resposta")


class DocumentChunk(BaseModel):
    """Fragmento de documento encontrado."""
    chunk_id: str = Field(description="ID do fragmento")
    content: str = Field(description="Conteúdo do fragmento")
    source: str = Field(description="Fonte do documento")
    similarity_score: float = Field(description="Pontuação de similaridade")
    metadata: Dict[str, Any] = Field(description="Metadados do fragmento")


class RAGResponse(BaseResponse):
    """Resposta do sistema RAG."""
    answer: str = Field(description="Resposta gerada pelo LLM")
    sources: List[DocumentChunk] = Field(description="Fontes consultadas")
    confidence_score: float = Field(description="Confiança na resposta")
    processing_time_ms: int = Field(description="Tempo de processamento")
    query_type: QueryType = Field(description="Tipo de consulta processada")


class ChatMessage(BaseModel):
    """Mensagem do chat."""
    role: str = Field(description="Papel (user, assistant, system)")
    content: str = Field(description="Conteúdo da mensagem")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da mensagem")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados da mensagem")


class ChatRequest(BaseModel):
    """Requisição de chat."""
    message: str = Field(description="Mensagem do usuário")
    session_id: str = Field(description="ID da sessão do chat")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    include_memory: bool = Field(True, description="Usar memória da sessão")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperatura do LLM")


class ChatResponse(BaseResponse):
    """Resposta do chat."""
    message: str = Field(description="Resposta do assistente")
    session_id: str = Field(description="ID da sessão")
    message_id: str = Field(description="ID único da mensagem")
    sources: Optional[List[DocumentChunk]] = Field(None, description="Fontes consultadas")
    confidence_score: float = Field(description="Confiança na resposta")
    processing_time_ms: int = Field(description="Tempo de processamento")


# ============================================================================
# SCHEMAS DE SISTEMA
# ============================================================================

class HealthCheck(BaseModel):
    """Status de saúde da API."""
    status: str = Field(description="Status geral da API")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da verificação")
    version: str = Field(description="Versão da API")
    uptime_seconds: float = Field(description="Tempo de funcionamento em segundos")
    
    # Status dos componentes
    database: Dict[str, Any] = Field(description="Status do banco de dados")
    vectorstore: Dict[str, Any] = Field(description="Status do banco vetorial") 
    llm_services: Dict[str, Any] = Field(description="Status dos serviços LLM")
    memory_usage: Dict[str, Any] = Field(description="Uso de memória")
    
    # Métricas
    total_requests: int = Field(description="Total de requisições processadas")
    error_rate: float = Field(description="Taxa de erro das últimas 24h")
    avg_response_time: float = Field(description="Tempo médio de resposta")


class SystemStats(BaseModel):
    """Estatísticas do sistema."""
    total_files_processed: int = Field(description="Total de arquivos processados")
    total_analyses_performed: int = Field(description="Total de análises realizadas")
    total_queries_answered: int = Field(description="Total de consultas respondidas")
    active_sessions: int = Field(description="Sessões ativas")
    database_size_mb: float = Field(description="Tamanho do banco em MB")
    vectorstore_embeddings: int = Field(description="Total de embeddings armazenados")


class APIKeyRequest(BaseModel):
    """Requisição para criar/renovar API key."""
    name: str = Field(description="Nome identificador da chave")
    permissions: List[str] = Field(description="Permissões da chave")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")


class APIKeyResponse(BaseResponse):
    """Resposta com informações da API key."""
    key_id: str = Field(description="ID da chave")
    api_key: str = Field(description="Chave de API gerada")
    name: str = Field(description="Nome da chave")
    permissions: List[str] = Field(description="Permissões")
    created_at: datetime = Field(description="Data de criação")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")


# ============================================================================
# VALIDADORES CUSTOMIZADOS
# ============================================================================

class CSVUploadRequest(BaseModel):
    """Parâmetros para upload de CSV."""
    filename: str = Field(description="Nome do arquivo")
    delimiter: str = Field(",", description="Delimitador do CSV")
    encoding: str = Field("utf-8", description="Codificação do arquivo")
    has_header: bool = Field(True, description="Se o arquivo tem cabeçalho")
    preview_rows: int = Field(5, ge=1, le=20, description="Linhas de preview")
    
    @validator('delimiter')
    def validate_delimiter(cls, v):
        """Valida delimitador do CSV."""
        valid_delimiters = [',', ';', '\t', '|']
        if v not in valid_delimiters:
            raise ValueError(f'Delimitador deve ser um de: {valid_delimiters}')
        return v
    
    @validator('encoding')
    def validate_encoding(cls, v):
        """Valida codificação do arquivo."""
        valid_encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        if v.lower() not in valid_encodings:
            raise ValueError(f'Codificação deve ser uma de: {valid_encodings}')
        return v.lower()


# ============================================================================
# EXEMPLOS PARA DOCUMENTAÇÃO
# ============================================================================

# Exemplos para documentação automática do Swagger
class SchemaExamples:
    """Exemplos para documentação OpenAPI."""
    
    csv_upload_response = {
        "success": True,
        "message": "Arquivo CSV carregado com sucesso",
        "timestamp": 1635724800.0,
        "file_id": "csv_123456789",
        "filename": "transactions.csv",
        "file_size": 1048576,
        "rows_count": 10000,
        "columns_count": 8,
        "columns": ["id", "amount", "user_id", "timestamp", "merchant", "category"],
        "preview": [
            {"id": 1, "amount": 150.50, "user_id": "user123", "timestamp": "2023-01-01 10:00:00"},
            {"id": 2, "amount": 75.25, "user_id": "user456", "timestamp": "2023-01-01 10:01:00"}
        ],
        "data_types": {
            "id": "int64",
            "amount": "float64", 
            "user_id": "object",
            "timestamp": "datetime64",
            "merchant": "object",
            "category": "object"
        }
    }
    
    analysis_response = {
        "success": True,
        "message": "Análise concluída com sucesso",
        "timestamp": 1635724800.0,
        "result": {
            "analysis_id": "analysis_123456789",
            "analysis_type": "fraud_detection",
            "summary": "Detectadas 127 transações suspeitas de um total de 10.000 analisadas",
            "insights": [
                "Padrão suspeito: múltiplas transações pequenas em sequência",
                "Aumento de 300% em transações noturnas",
                "Concentração de fraudes em determinados merchants"
            ],
            "statistics": {
                "fraud_rate": 0.0127,
                "avg_fraud_amount": 89.45,
                "peak_fraud_hour": 23
            },
            "confidence_score": 0.92,
            "processing_time_ms": 1500,
            "recommendations": [
                "Implementar limite de transações noturnas",
                "Monitorar merchants com alta taxa de fraude",
                "Revisar transações acima de R$ 200 após 22h"
            ]
        }
    }
    
    rag_response = {
        "success": True,
        "message": "Consulta processada com sucesso",
        "timestamp": 1635724800.0,
        "answer": "Para detectar fraudes em cartão de crédito, recomenda-se...",
        "sources": [
            {
                "chunk_id": "chunk_001",
                "content": "Métodos de detecção de fraude incluem análise de padrões...",
                "source": "fraud_detection_guide.pdf",
                "similarity_score": 0.92,
                "metadata": {"page": 15, "section": "Metodologias"}
            }
        ],
        "confidence_score": 0.89,
        "processing_time_ms": 800,
        "query_type": "semantic_search"
    }