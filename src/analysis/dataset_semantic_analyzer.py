"""
Módulo de Identificação Semântica de Datasets.

Este módulo infere o contexto e tema do dataset baseado em:
- Nomes de colunas
- Metadados existentes
- Padrões de dados

Autor: EDA AI Minds Team
Data: 2025-10-23
Versão: 1.0.0
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import pandas as pd
import logging

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DatasetDomain(Enum):
    """Domínios conhecidos de datasets."""
    CREDIT_CARD_FRAUD = "credit_card_fraud"
    FINANCIAL_TRANSACTIONS = "financial_transactions"
    E_COMMERCE = "e_commerce"
    INVOICE_NFE = "invoice_nfe"
    CUSTOMER_DATA = "customer_data"
    SALES = "sales"
    HEALTHCARE = "healthcare"
    IOT_SENSORS = "iot_sensors"
    TIME_SERIES = "time_series"
    GENERIC = "generic"
    UNKNOWN = "unknown"


@dataclass
class DomainSignature:
    """Assinatura de um domínio de dataset com palavras-chave e padrões."""
    domain: DatasetDomain
    keywords: Set[str]
    required_columns: List[str] = field(default_factory=list)
    optional_columns: List[str] = field(default_factory=list)
    column_patterns: List[str] = field(default_factory=list)  # regex patterns
    confidence_threshold: float = 0.6
    description: str = ""


# ═══════════════════════════════════════════════════════════════
# ASSINATURAS DE DOMÍNIOS CONHECIDOS
# ═══════════════════════════════════════════════════════════════

DOMAIN_SIGNATURES = [
    DomainSignature(
        domain=DatasetDomain.CREDIT_CARD_FRAUD,
        keywords={
            'time', 'amount', 'class', 'fraud', 'transaction', 'credit', 'card',
            'v1', 'v2', 'v3', 'v4', 'v5'  # PCA components típicos
        },
        required_columns=['Time', 'Amount', 'Class'],
        optional_columns=['V1', 'V2', 'V3', 'V4', 'V5'],
        column_patterns=[r'^V\d+$'],  # V1, V2, ... V28
        confidence_threshold=0.7,
        description="Dataset de fraude em cartão de crédito (ex: Kaggle Credit Card Fraud)"
    ),
    DomainSignature(
        domain=DatasetDomain.FINANCIAL_TRANSACTIONS,
        keywords={
            'transaction', 'amount', 'balance', 'account', 'payment', 'transfer',
            'date', 'timestamp', 'merchant', 'currency', 'status'
        },
        required_columns=[],
        optional_columns=['transaction_id', 'amount', 'date', 'account'],
        confidence_threshold=0.5,
        description="Transações financeiras gerais"
    ),
    DomainSignature(
        domain=DatasetDomain.INVOICE_NFE,
        keywords={
            'nota', 'fiscal', 'nfe', 'invoice', 'cfop', 'ncm', 'icms', 'ipi',
            'valor', 'produto', 'emitente', 'destinatario', 'chave'
        },
        required_columns=[],
        optional_columns=['numero_nf', 'data_emissao', 'valor_total', 'cnpj'],
        confidence_threshold=0.6,
        description="Notas Fiscais Eletrônicas (NF-e)"
    ),
    DomainSignature(
        domain=DatasetDomain.E_COMMERCE,
        keywords={
            'product', 'price', 'quantity', 'order', 'customer', 'cart',
            'category', 'rating', 'review', 'shipping', 'discount'
        },
        required_columns=[],
        optional_columns=['product_id', 'customer_id', 'order_date', 'price'],
        confidence_threshold=0.5,
        description="Dados de e-commerce (produtos, pedidos, clientes)"
    ),
    DomainSignature(
        domain=DatasetDomain.CUSTOMER_DATA,
        keywords={
            'customer', 'name', 'email', 'phone', 'address', 'age', 'gender',
            'city', 'state', 'zipcode', 'country', 'registration'
        },
        required_columns=[],
        optional_columns=['customer_id', 'name', 'email'],
        confidence_threshold=0.5,
        description="Dados cadastrais de clientes"
    ),
    DomainSignature(
        domain=DatasetDomain.SALES,
        keywords={
            'sales', 'revenue', 'profit', 'quantity', 'product', 'region',
            'salesperson', 'commission', 'target', 'forecast'
        },
        required_columns=[],
        optional_columns=['date', 'product', 'sales_amount'],
        confidence_threshold=0.5,
        description="Dados de vendas e receita"
    ),
    DomainSignature(
        domain=DatasetDomain.IOT_SENSORS,
        keywords={
            'sensor', 'temperature', 'humidity', 'pressure', 'device',
            'reading', 'measurement', 'voltage', 'current', 'signal'
        },
        required_columns=[],
        optional_columns=['timestamp', 'sensor_id', 'value'],
        confidence_threshold=0.5,
        description="Dados de sensores IoT"
    ),
    DomainSignature(
        domain=DatasetDomain.TIME_SERIES,
        keywords={
            'date', 'time', 'timestamp', 'year', 'month', 'day',
            'value', 'metric', 'measurement', 'observation'
        },
        required_columns=[],
        optional_columns=['date', 'value'],
        confidence_threshold=0.4,
        description="Séries temporais gerais"
    )
]


@dataclass
class SemanticAnalysisResult:
    """Resultado da análise semântica do dataset."""
    primary_domain: DatasetDomain
    confidence: float
    secondary_domains: List[tuple[DatasetDomain, float]] = field(default_factory=list)
    matched_keywords: Set[str] = field(default_factory=set)
    matched_columns: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict = field(default_factory=dict)


class DatasetSemanticAnalyzer:
    """
    Analisador semântico de datasets.
    
    Identifica o contexto e tema do dataset baseado em padrões conhecidos.
    
    Exemplo:
        >>> analyzer = DatasetSemanticAnalyzer()
        >>> result = analyzer.analyze(df)
        >>> print(f"Domínio: {result.primary_domain.value}")
        >>> print(f"Confiança: {result.confidence:.2%}")
    """
    
    def __init__(self, custom_signatures: Optional[List[DomainSignature]] = None):
        """
        Inicializa o analisador semântico.
        
        Args:
            custom_signatures: Assinaturas customizadas adicionais
        """
        self.signatures = DOMAIN_SIGNATURES.copy()
        if custom_signatures:
            self.signatures.extend(custom_signatures)
        
        self.logger = logger
        
    def analyze(self, df: pd.DataFrame, metadata: Optional[Dict] = None) -> SemanticAnalysisResult:
        """
        Analisa semanticamente um dataset para identificar seu domínio.
        
        Args:
            df: DataFrame a analisar
            metadata: Metadados adicionais do dataset (opcional)
        
        Returns:
            Resultado da análise semântica
        """
        self.logger.info({
            'event': 'semantic_analysis_started',
            'shape': df.shape,
            'columns': len(df.columns)
        })
        
        # Coletar informações do dataset
        column_names = [col.lower() for col in df.columns]
        column_names_set = set(column_names)
        
        # Pontuar cada domínio
        domain_scores = []
        
        for signature in self.signatures:
            score, matched_keywords, matched_columns = self._score_signature(
                signature, column_names_set, df.columns.tolist()
            )
            
            if score >= signature.confidence_threshold:
                domain_scores.append((signature, score, matched_keywords, matched_columns))
        
        # Ordenar por score
        domain_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Determinar domínio primário
        if domain_scores:
            primary_sig, primary_score, keywords, columns = domain_scores[0]
            primary_domain = primary_sig.domain
            confidence = primary_score
            description = primary_sig.description
            
            # Domínios secundários
            secondary = [(sig.domain, score) for sig, score, _, _ in domain_scores[1:3]]
        else:
            # Sem matches, classificar como GENERIC ou UNKNOWN
            primary_domain = DatasetDomain.GENERIC if len(df.columns) > 0 else DatasetDomain.UNKNOWN
            confidence = 0.0
            description = "Dataset genérico sem padrões reconhecidos"
            keywords = set()
            columns = []
            secondary = []
        
        result = SemanticAnalysisResult(
            primary_domain=primary_domain,
            confidence=confidence,
            secondary_domains=secondary,
            matched_keywords=keywords,
            matched_columns=columns,
            description=description,
            metadata={
                'total_columns': len(df.columns),
                'total_rows': len(df),
                'analyzed_signatures': len(self.signatures),
                'matched_signatures': len(domain_scores)
            }
        )
        
        self.logger.info({
            'event': 'semantic_analysis_completed',
            'primary_domain': primary_domain.value,
            'confidence': confidence,
            'matched_keywords_count': len(keywords)
        })
        
        return result
    
    def _score_signature(
        self,
        signature: DomainSignature,
        column_names_set: Set[str],
        original_columns: List[str]
    ) -> tuple[float, Set[str], List[str]]:
        """
        Calcula score de match entre dataset e assinatura.
        
        Returns:
            (score, matched_keywords, matched_columns)
        """
        score = 0.0
        matched_keywords = set()
        matched_columns = []
        
        # 1. Keywords nas colunas (peso: 50%)
        keyword_matches = 0
        for col in column_names_set:
            for keyword in signature.keywords:
                if keyword in col:
                    keyword_matches += 1
                    matched_keywords.add(keyword)
                    break
        
        if signature.keywords:
            keyword_score = keyword_matches / len(signature.keywords)
            score += keyword_score * 0.5
        
        # 2. Colunas obrigatórias presentes (peso: 30%)
        if signature.required_columns:
            required_matches = sum(
                1 for req in signature.required_columns
                if req.lower() in column_names_set
            )
            matched_columns.extend([
                col for col in original_columns
                if col.lower() in [r.lower() for r in signature.required_columns]
            ])
            
            required_score = required_matches / len(signature.required_columns)
            score += required_score * 0.3
        
        # 3. Colunas opcionais presentes (peso: 20%)
        if signature.optional_columns:
            optional_matches = sum(
                1 for opt in signature.optional_columns
                if opt.lower() in column_names_set
            )
            matched_columns.extend([
                col for col in original_columns
                if col.lower() in [o.lower() for o in signature.optional_columns]
            ])
            
            optional_score = optional_matches / len(signature.optional_columns)
            score += optional_score * 0.2
        
        # 4. Padrões de regex (bônus se houver)
        if signature.column_patterns:
            import re
            pattern_matches = 0
            for col in original_columns:
                for pattern in signature.column_patterns:
                    if re.match(pattern, col):
                        pattern_matches += 1
                        break
            
            if pattern_matches > 0:
                score += 0.1  # Bônus de 10%
        
        return score, matched_keywords, list(set(matched_columns))


def analyze_dataset_semantics(df: pd.DataFrame, metadata: Optional[Dict] = None) -> SemanticAnalysisResult:
    """
    Função de conveniência para análise semântica de dataset.
    
    Args:
        df: DataFrame a analisar
        metadata: Metadados adicionais (opcional)
    
    Returns:
        Resultado da análise semântica
    """
    analyzer = DatasetSemanticAnalyzer()
    return analyzer.analyze(df, metadata)
