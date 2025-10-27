"""
Detecção inteligente e robusta de colunas temporais em DataFrames.

Este módulo implementa heurísticas flexíveis e extensíveis para identificar
colunas que representam dimensões temporais, suportando múltiplos formatos,
tipos de dados e convenções de nomenclatura.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 2.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
import pandas as pd
import numpy as np
import logging
from datetime import datetime


class DetectionMethod(Enum):
    """Métodos de detecção de colunas temporais."""
    OVERRIDE_MANUAL = "override_manual"
    NATIVE_DATETIME = "native_datetime"
    COMMON_NAME = "common_name"
    STRING_CONVERSION = "string_conversion"
    NUMERIC_SEQUENCE = "numeric_sequence"


@dataclass
class TemporalDetectionConfig:
    """
    Configuração parametrizável para detecção de colunas temporais.
    
    Attributes:
        common_names: Lista de nomes comuns para colunas temporais (case-insensitive)
        conversion_threshold: Percentual mínimo de valores válidos após conversão (0.0-1.0)
        min_unique_ratio: Razão mínima valores_únicos/total para considerar temporal
        numeric_sequence_threshold: Threshold para detectar sequências numéricas temporais
        enable_aggressive_detection: Ativa heurísticas mais agressivas de detecção
        excluded_patterns: Padrões de nomes a excluir da detecção
    """
    common_names: List[str] = field(default_factory=lambda: [
        "time", "date", "datetime", "timestamp", "data", "hora",
        "created_at", "updated_at", "dt", "ts", "period", "periodo"
    ])
    conversion_threshold: float = 0.80
    min_unique_ratio: float = 0.01
    numeric_sequence_threshold: float = 0.95
    # Parâmetros contextualizados para nomes temporais em colunas numéricas
    context_unique_ratio_threshold: float = 0.30  # >= 30% valores únicos → provável temporal
    low_cardinality_threshold: float = 0.10       # < 10% valores únicos → improvável temporal
    enable_aggressive_detection: bool = False
    excluded_patterns: Set[str] = field(default_factory=lambda: {
        "id", "class", "label", "target", "amount", "value", "v1", "v2", "v3"
    })
    # LLM fallback opcional para casos ambíguos
    use_llm_fallback: bool = False
    llm_temperature: float = 0.2
    llm_max_tokens: int = 256


@dataclass
class DetectionResult:
    """
    Resultado detalhado da detecção de uma coluna temporal.
    
    Attributes:
        column_name: Nome da coluna
        detected: Se foi detectada como temporal
        method: Método que detectou a coluna
        confidence: Confiança da detecção (0.0-1.0)
        metadata: Metadados adicionais da detecção
        conversion_stats: Estatísticas de conversão (se aplicável)
    """
    column_name: str
    detected: bool
    method: Optional[DetectionMethod] = None
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)
    conversion_stats: Dict = field(default_factory=dict)


class TemporalColumnDetector:
    """
    Detector inteligente de colunas temporais com heurísticas extensíveis.
    
    Implementa múltiplas estratégias de detecção em ordem de prioridade:
    1. Override manual (confiança: 1.0)
    2. Tipo datetime nativo (confiança: 0.95)
    3. Conversão de strings com validação (confiança: 0.75)
    4. Sequências numéricas temporais (confiança: 0.60, modo agressivo)
    5. Nomes comuns parametrizáveis (confiança: 0.85) — somente quando não-string
    
    Exemplo:
        >>> config = TemporalDetectionConfig(conversion_threshold=0.85)
        >>> detector = TemporalColumnDetector(config)
        >>> results = detector.detect(df)
        >>> temporal_cols = detector.get_detected_columns(results)
    """
    
    def __init__(self, config: Optional[TemporalDetectionConfig] = None):
        """
        Inicializa o detector com configuração customizável.
        
        Args:
            config: Configuração de detecção (usa defaults se None)
        """
        self.config = config or TemporalDetectionConfig()
        self.logger = logging.getLogger(__name__)
        
    def detect(
        self,
        df: pd.DataFrame,
        override_column: Optional[str] = None
    ) -> List[DetectionResult]:
        """
        Executa detecção completa de colunas temporais no DataFrame.
        
        Args:
            df: DataFrame a analisar
            override_column: Coluna específica a forçar como temporal
            
        Returns:
            Lista de resultados de detecção para cada coluna analisada
            
        Raises:
            ValueError: Se override_column não existir no DataFrame
        """
        self.logger.info({
            'event': 'detection_started',
            'shape': df.shape,
            'columns': len(df.columns),
            'override': override_column
        })
        
        results: List[DetectionResult] = []
        
        # 1. Override manual (prioridade máxima)
        if override_column:
            if override_column not in df.columns:
                raise ValueError(f"Coluna override '{override_column}' não encontrada no DataFrame")
            
            result = DetectionResult(
                column_name=override_column,
                detected=True,
                method=DetectionMethod.OVERRIDE_MANUAL,
                confidence=1.0,
                metadata={'source': 'manual_override'}
            )
            results.append(result)
            self.logger.info({
                'event': 'override_detected',
                'column': override_column
            })
            return results
        
        # 2-5. Detecção automática para todas as colunas
        for col in df.columns:
            result = self._detect_single_column(df, col)
            results.append(result)
            
            if result.detected:
                self.logger.info({
                    'event': 'temporal_column_detected',
                    'column': col,
                    'method': result.method.value if result.method else 'unknown',
                    'confidence': result.confidence
                })
        
        detected_count = sum(1 for r in results if r.detected)
        self.logger.info({
            'event': 'detection_completed',
            'total_columns': len(df.columns),
            'detected': detected_count
        })
        
        return results
    
    def _detect_single_column(self, df: pd.DataFrame, col: str) -> DetectionResult:
        """
        Detecta se uma única coluna é temporal usando heurísticas em cascata.
        
        Args:
            df: DataFrame contendo a coluna
            col: Nome da coluna a analisar
            
        Returns:
            Resultado da detecção
        """
        # Exclusão preventiva: padrões conhecidos como não-temporais
        if self._should_exclude(col):
            return DetectionResult(
                column_name=col,
                detected=False,
                metadata={'reason': 'excluded_pattern'}
            )
        
        # Heurística 1: Tipo datetime nativo
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return DetectionResult(
                column_name=col,
                detected=True,
                method=DetectionMethod.NATIVE_DATETIME,
                confidence=0.95,
                metadata={'dtype': str(df[col].dtype)}
            )
        
        # Heurística 2: Conversão de string para datetime
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            conversion_result = self._try_datetime_conversion(df[col])
            if conversion_result['success']:
                return DetectionResult(
                    column_name=col,
                    detected=True,
                    method=DetectionMethod.STRING_CONVERSION,
                    confidence=conversion_result['confidence'],
                    conversion_stats=conversion_result
                )
        
        # Heurística 3: Sequência numérica temporal (modo agressivo)
        if self.config.enable_aggressive_detection:
            if pd.api.types.is_numeric_dtype(df[col]):
                sequence_result = self._analyze_numeric_sequence(df[col])
                if sequence_result['is_temporal']:
                    return DetectionResult(
                        column_name=col,
                        detected=True,
                        method=DetectionMethod.NUMERIC_SEQUENCE,
                        confidence=sequence_result['confidence'],
                        metadata=sequence_result
                    )

        # Heurística 4: Nome comum (case-insensitive)
        # Regras:
        # - Não aplicar COMMON_NAME para colunas string/objeto (exigem conversão válida)
        # - Evitar detectar nomes que contenham 'unix' via COMMON_NAME (reservado para sequência numérica)
        # - ✅ CORREÇÃO (2025-10-23): Para colunas numéricas com nomes temporais, verificar contexto
        #   * Se alta cardinalidade (>30% valores únicos) + nome temporal → PROVÁVEL elapsed time/segundos
        #   * Se baixa cardinalidade (<10% valores únicos) + nome temporal → IMPROVÁVEL temporal
        if self._matches_common_name(col):
            col_lower = col.lower()
            if 'unix' in col_lower:
                return DetectionResult(
                    column_name=col,
                    detected=False,
                    metadata={'reason': 'unix_reserved_for_numeric_sequence'}
                )
            # Se for string/objeto, não considere apenas pelo nome (já tentamos conversão antes)
            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                return DetectionResult(
                    column_name=col,
                    detected=False,
                    metadata={'reason': 'common_name_requires_conversion_for_strings'}
                )
            
            # ✅ ANÁLISE CONTEXTUAL para numéricos com nomes temporais
            if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
                unique_count = df[col].nunique(dropna=True)
                total_count = len(df[col].dropna())
                unique_ratio = unique_count / total_count if total_count > 0 else 0
                
                # Heurística: Alta cardinalidade indica elapsed time/seconds (ex: Time no creditcard)
                # Baixa cardinalidade indica ID ou categórico disfarçado
                if unique_ratio >= self.config.context_unique_ratio_threshold:
                    self.logger.info({
                        'event': 'numeric_temporal_detected_by_context',
                        'column': col,
                        'dtype': str(df[col].dtype),
                        'unique_ratio': unique_ratio,
                        'reason': 'High cardinality + temporal name suggests elapsed time/seconds'
                    })
                    return DetectionResult(
                        column_name=col,
                        detected=True,
                        method=DetectionMethod.COMMON_NAME,
                        confidence=0.75,  # Confiança média-alta (contexto inferido)
                        metadata={
                            'matched_pattern': col_lower,
                            'dtype': str(df[col].dtype),
                            'unique_ratio': unique_ratio,
                            'interpretation': 'elapsed_time_seconds'
                        }
                    )
                else:
                    # Faixa baixa ou ambígua: decidir por thresholds ou LLM fallback
                    if unique_ratio < self.config.low_cardinality_threshold:
                        # Baixa cardinalidade: provavelmente não temporal
                        self.logger.warning({
                            'event': 'temporal_name_rejected_low_cardinality',
                            'column': col,
                            'dtype': str(df[col].dtype),
                            'unique_ratio': unique_ratio,
                            'reason': 'Low cardinality suggests non-temporal despite name'
                        })
                        return DetectionResult(
                            column_name=col,
                            detected=False,
                            metadata={
                                'reason': 'temporal_name_but_low_cardinality',
                                'unique_ratio': unique_ratio
                            }
                        )
                    # Zona cinza: tentar LLM fallback se habilitado
                    if self.config.use_llm_fallback:
                        llm_vote = self._llm_assess_temporal(col, df[col])
                        if llm_vote.get('decide') is True:
                            return DetectionResult(
                                column_name=col,
                                detected=True,
                                method=DetectionMethod.COMMON_NAME,
                                confidence=llm_vote.get('confidence', 0.7),
                                metadata={
                                    'matched_pattern': col_lower,
                                    'dtype': str(df[col].dtype),
                                    'unique_ratio': unique_ratio,
                                    'llm_reason': llm_vote.get('reason', 'llm_fallback')
                                }
                            )
                        elif llm_vote.get('decide') is False:
                            return DetectionResult(
                                column_name=col,
                                detected=False,
                                metadata={
                                    'reason': 'llm_rejected_temporal',
                                    'unique_ratio': unique_ratio,
                                    'llm_reason': llm_vote.get('reason', 'llm_fallback')
                                }
                            )
                        # Se LLM não decidir, cair para não detectar para segurança
                    return DetectionResult(
                        column_name=col,
                        detected=False,
                        metadata={
                            'reason': 'ambiguous_temporal_name_without_llm',
                            'unique_ratio': unique_ratio
                        }
                    )
            
            # Para dtypes válidos (datetime, timedelta), aceitar COMMON_NAME
            return DetectionResult(
                column_name=col,
                detected=True,
                method=DetectionMethod.COMMON_NAME,
                confidence=0.85,
                metadata={'matched_pattern': col_lower}
            )
        
        # Não detectado
        return DetectionResult(
            column_name=col,
            detected=False,
            metadata={'reason': 'no_match'}
        )

    def _llm_assess_temporal(self, col_name: str, series: pd.Series) -> Dict:
        """Consulta opcional ao LLM Manager para decidir casos ambíguos.

        Retorna um dicionário com chaves:
        - decide: True/False se conseguiu decidir; ausente se não aplicável
        - confidence: 0.0-1.0
        - reason: string curta explicando a decisão
        """
        try:
            # Import tardio para não criar dependência dura
            from src.llm.manager import get_llm_manager, LLMConfig
            llm = get_llm_manager()

            # Amostra pequena e segura da coluna
            sample = series.dropna().astype(str).head(10).tolist()
            prompt = (
                "Você é um assistente de dados. Dada uma coluna de um DataFrame e seu nome, "
                "decida se a coluna representa TEMPO (data/hora, timestamp, elapsed time).\n"
                f"Nome da coluna: {col_name}\n"
                f"Amostra de valores: {sample}\n"
                "Responda apenas com uma das opções: 'temporal', 'nao_temporal' e uma razão breve."
            )
            cfg = LLMConfig(temperature=self.config.llm_temperature, max_tokens=self.config.llm_max_tokens)
            resp = llm.chat(prompt, cfg)
            if not resp.success:
                return {}
            text = (resp.content or '').lower()
            if 'temporal' in text and 'nao_temporal' not in text:
                return {'decide': True, 'confidence': 0.7, 'reason': text[:200]}
            if 'nao_temporal' in text or 'não_temporal' in text or 'nao temporal' in text:
                return {'decide': False, 'confidence': 0.7, 'reason': text[:200]}
            return {}
        except Exception as e:
            # Falha no LLM: não decide
            self.logger.debug(f"LLM fallback indisponível: {e}")
            return {}
    
    def _should_exclude(self, col: str) -> bool:
        """Verifica se a coluna deve ser excluída da detecção."""
        col_lower = col.lower()
        
        # Exclusão por padrão exato
        if col_lower in self.config.excluded_patterns:
            return True
        
        # Exclusão por substring (ex: v1, v2, v3... v28)
        for pattern in self.config.excluded_patterns:
            if pattern in col_lower:
                return True
        
        return False
    
    def _matches_common_name(self, col: str) -> bool:
        """Verifica se o nome da coluna corresponde a padrões temporais comuns."""
        col_lower = col.lower()
        return any(name.lower() in col_lower for name in self.config.common_names)
    
    def _try_datetime_conversion(self, series: pd.Series) -> Dict:
        """
        Tenta converter série para datetime e retorna estatísticas.
        
        Args:
            series: Série pandas a converter
            
        Returns:
            Dicionário com resultado da conversão e estatísticas
        """
        try:
            # infer_datetime_format está deprecado; comportamento estrito é default
            converted = pd.to_datetime(series, errors='coerce')
            valid_ratio = converted.notna().mean()
            unique_ratio = converted.nunique() / len(converted)
            
            success = (
                valid_ratio >= self.config.conversion_threshold and
                unique_ratio >= self.config.min_unique_ratio
            )
            
            # Confiança proporcional à taxa de conversão
            confidence = 0.75 * valid_ratio if success else 0.0
            
            return {
                'success': success,
                'valid_ratio': valid_ratio,
                'unique_ratio': unique_ratio,
                'confidence': confidence,
                'total_values': len(series),
                'valid_values': int(converted.notna().sum()),
                'unique_values': converted.nunique()
            }
        except Exception as e:
            self.logger.debug(f"Conversão datetime falhou para coluna: {e}")
            return {
                'success': False,
                'error': str(e),
                'confidence': 0.0
            }
    
    def _analyze_numeric_sequence(self, series: pd.Series) -> Dict:
        """
        Analisa se uma série numérica representa uma sequência temporal.
        
        Detecta padrões como: timestamps Unix, índices sequenciais, etc.
        
        Args:
            series: Série numérica a analisar
            
        Returns:
            Análise da sequência com flag is_temporal
        """
        try:
            # Verificar monotonicidade
            is_monotonic = series.is_monotonic_increasing or series.is_monotonic_decreasing
            
            # Verificar espaçamento regular (diferenças)
            if len(series) > 2:
                diffs = series.diff().dropna()
                diff_std = diffs.std()
                diff_mean = diffs.mean()
                regularity = 1.0 - (diff_std / abs(diff_mean)) if diff_mean != 0 else 0.0
            else:
                regularity = 0.0
            
            # Timestamp Unix (1970-2100)
            min_val, max_val = series.min(), series.max()
            is_unix_timestamp = (
                min_val >= 0 and
                max_val <= 4102444800  # 2100-01-01 em Unix timestamp
            )
            
            # Decisão temporal
            is_temporal = (
                is_monotonic and
                regularity >= self.config.numeric_sequence_threshold and
                is_unix_timestamp
            )
            
            confidence = 0.60 * regularity if is_temporal else 0.0
            
            return {
                'is_temporal': is_temporal,
                'confidence': confidence,
                'is_monotonic': is_monotonic,
                'regularity': regularity,
                'is_unix_timestamp': is_unix_timestamp,
                'min_value': min_val,
                'max_value': max_val
            }
        except Exception as e:
            self.logger.debug(f"Análise de sequência numérica falhou: {e}")
            return {
                'is_temporal': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    @staticmethod
    def get_detected_columns(results: List[DetectionResult]) -> List[str]:
        """
        Extrai lista de nomes de colunas detectadas como temporais.
        
        Args:
            results: Lista de resultados de detecção
            
        Returns:
            Lista de nomes de colunas temporais detectadas
        """
        return [r.column_name for r in results if r.detected]
    
    @staticmethod
    def get_detection_summary(results: List[DetectionResult]) -> Dict:
        """
        Gera resumo estatístico da detecção.
        
        Args:
            results: Lista de resultados de detecção
            
        Returns:
            Dicionário com estatísticas da detecção
        """
        detected = [r for r in results if r.detected]
        
        methods_count = {}
        for result in detected:
            method = result.method.value if result.method else 'unknown'
            methods_count[method] = methods_count.get(method, 0) + 1
        
        return {
            'total_columns': len(results),
            'detected_count': len(detected),
            'detection_rate': len(detected) / len(results) if results else 0.0,
            'avg_confidence': np.mean([r.confidence for r in detected]) if detected else 0.0,
            'methods_used': methods_count,
            'detected_columns': [r.column_name for r in detected]
        }
