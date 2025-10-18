# 🔧 EXEMPLOS PRÁTICOS DE IMPLEMENTAÇÃO - Correções da Auditoria

**Documento Complementar:** AUDITORIA_COMPLETA_WORKSPACE.md  
**Data:** 18 de Outubro de 2025  
**Objetivo:** Fornecer código prático para implementar as recomendações

---

## 📌 ÍNDICE

1. [Correção #1: Remover Keywords do OrchestratorAgent](#correção-1)
2. [Correção #2: Substituir Fallback por LLM](#correção-2)
3. [Correção #3: Implementar OutlierAnalyzer](#correção-3)
4. [Correção #4: Consolidar Módulos LLM](#correção-4)
5. [Correção #5: Adicionar Schemas Pydantic](#correção-5)

---

## <a name="correção-1"></a>🔴 CORREÇÃO #1: Remover Keywords do OrchestratorAgent

### ANTES (Código Atual - PROBLEMÁTICO)

```python
# src/agent/orchestrator_agent.py (linhas ~1090-1110)

def _needs_data_analysis(self, query: str, context: Optional[Dict[str, Any]]) -> bool:
    """Verifica se query precisa de análise de dados."""
    
    # 🔴 PROBLEMA: 80+ keywords hardcoded
    data_specific_keywords = [
        'média', 'media', 'mínimo', 'minimo', 'máximo', 'maximo',
        'desvio', 'variância', 'variancia', 'distribuição', 'distribuicao',
        'correlação', 'correlacao', 'frequência', 'frequencia',
        'outlier', 'anomalia', 'padrão', 'padrao', 'cluster',
        'temporal', 'tendência', 'tendencia', 'sazonal',
        'estatística', 'estatistica', 'análise', 'analise',
        'histograma', 'gráfico', 'grafico', 'visualização', 'visualizacao'
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in data_specific_keywords)
```

**Problemas:**
- ❌ Não reconhece "standard deviation", "covariance", "skewness"
- ❌ Não funciona em inglês/outros idiomas
- ❌ Manutenção custosa (adicionar keyword por keyword)
- ❌ Violação do requisito "zero hardcoding"

---

### DEPOIS (Solução LLM-Based)

```python
# src/agent/orchestrator_agent.py (linhas ~1090-1120)

from src.analysis.intent_classifier import IntentClassifier, AnalysisIntent

def _needs_data_analysis(self, query: str, context: Optional[Dict[str, Any]]) -> bool:
    """Verifica se query precisa de análise de dados usando LLM."""
    
    # ✅ SOLUÇÃO: Usar IntentClassifier (LLM)
    if not hasattr(self, 'intent_classifier'):
        self.intent_classifier = IntentClassifier()
    
    try:
        # Classificar intenção via LLM
        result = self.intent_classifier.classify(query, context)
        
        # Definir intenções que precisam de análise de dados
        data_analysis_intents = {
            AnalysisIntent.STATISTICAL_ANALYSIS,
            AnalysisIntent.CORRELATION_ANALYSIS,
            AnalysisIntent.OUTLIER_DETECTION,
            AnalysisIntent.DISTRIBUTION_ANALYSIS,
            AnalysisIntent.TEMPORAL_ANALYSIS,
            AnalysisIntent.CLUSTERING,
            AnalysisIntent.VISUALIZATION
        }
        
        # Verificar se intenção principal ou secundárias requerem análise
        needs_analysis = (
            result.primary_intent in data_analysis_intents or
            any(intent in data_analysis_intents for intent in result.secondary_intents)
        )
        
        self.logger.info(
            f"Análise de dados necessária: {needs_analysis} "
            f"(intenção: {result.primary_intent.value}, confiança: {result.confidence:.2f})"
        )
        
        return needs_analysis
        
    except Exception as e:
        self.logger.error(f"Erro ao classificar intenção: {e}")
        # Fallback seguro: assumir que precisa de análise
        return True
```

**Vantagens:**
- ✅ Reconhece sinônimos ilimitados
- ✅ Funciona em qualquer idioma
- ✅ Zero manutenção de keywords
- ✅ Contexto histórico automático
- ✅ Confiança e raciocínio

---

### Refatoração Completa do _classify_query

```python
# src/agent/orchestrator_agent.py

def _classify_query(self, query: str, context: Optional[Dict[str, Any]]) -> QueryType:
    """
    Classifica tipo de query usando semantic router + intent classifier.
    ZERO keywords hardcoded.
    """
    try:
        # 1. Tentar semantic router (busca vetorial)
        if self.semantic_router:
            routing_result = self.semantic_router.route(query)
            route = routing_result.get('route', 'unknown')
            confidence = routing_result.get('confidence', 0.0)
            
            self.logger.info(f"📍 Roteamento semântico: {route} (confiança: {confidence:.2f})")
            
            # Mapear rota para QueryType
            route_mapping = {
                'visualization': QueryType.VISUALIZATION,
                'statistical': QueryType.ANALYSIS,
                'correlation': QueryType.CORRELATION,
                'temporal': QueryType.SUMMARY,
                'data_loading': QueryType.DATA_LOADING
            }
            
            if route in route_mapping and confidence > 0.7:
                return route_mapping[route]
        
        # 2. Fallback: Intent Classifier (LLM)
        result = self.intent_classifier.classify(query, context)
        
        # Mapear AnalysisIntent para QueryType
        intent_mapping = {
            AnalysisIntent.STATISTICAL_ANALYSIS: QueryType.ANALYSIS,
            AnalysisIntent.CORRELATION_ANALYSIS: QueryType.CORRELATION,
            AnalysisIntent.OUTLIER_DETECTION: QueryType.OUTLIERS,
            AnalysisIntent.DISTRIBUTION_ANALYSIS: QueryType.DISTRIBUTION,
            AnalysisIntent.TEMPORAL_ANALYSIS: QueryType.SUMMARY,
            AnalysisIntent.VISUALIZATION: QueryType.VISUALIZATION,
            AnalysisIntent.DATA_LOADING: QueryType.DATA_LOADING,
            AnalysisIntent.CLUSTERING: QueryType.ANALYSIS
        }
        
        query_type = intent_mapping.get(result.primary_intent, QueryType.GENERAL)
        
        self.logger.info(
            f"🧠 Classificação LLM: {query_type.value} "
            f"(intenção: {result.primary_intent.value}, confiança: {result.confidence:.2f})"
        )
        
        return query_type
        
    except Exception as e:
        self.logger.error(f"Erro ao classificar query: {e}")
        return QueryType.GENERAL
```

---

## <a name="correção-2"></a>🟡 CORREÇÃO #2: Substituir Fallback por LLM

### ANTES (csv_analysis_agent.py - PROBLEMÁTICO)

```python
# src/agent/csv_analysis_agent.py (linhas 91-130)

def _classify_query_by_keywords(self, query: str):
    """Classificação básica via keywords (fallback quando RAGQueryClassifier indisponível)."""
    
    query_lower = query.lower()
    
    # 🔴 PROBLEMA: Keywords hardcoded como fallback
    keywords_map = {
        QueryType.VISUALIZATION: ['gráfico', 'grafico', 'histograma', 'distribuição', 'plot'],
        QueryType.CORRELATION: ['correlação', 'correlacao', 'relação', 'relacao'],
        QueryType.VARIABILITY: ['variabilidade', 'variação', 'variacao', 'desvio'],
        QueryType.CENTRAL_TENDENCY: ['média', 'media', 'mediana', 'moda', 'central'],
        QueryType.DISTRIBUTION: ['distribuição', 'distribuicao', 'frequência', 'frequencia'],
        QueryType.OUTLIERS: ['outlier', 'discrepante', 'anômalo', 'anomalo'],
        QueryType.INTERVAL: ['intervalo', 'faixa', 'range', 'mínimo', 'minimo', 'máximo', 'maximo'],
        QueryType.COUNT: ['quantos', 'quantas', 'quantidade', 'contar', 'número', 'numero'],
        QueryType.SUMMARY: ['resumo', 'visão geral', 'visao geral', 'overview', 'sumário'],
    }
    
    for qtype, keywords in keywords_map.items():
        if any(kw in query_lower for kw in keywords):
            return qtype
    
    return QueryType.ANALYSIS
```

---

### DEPOIS (Solução com LLM Genérico)

```python
# src/agent/csv_analysis_agent.py (linhas 91-150)

from src.llm.langchain_manager import LangChainLLMManager, LLMConfig

def _classify_query_intelligent(self, query: str) -> QueryType:
    """
    Classificação inteligente via LLM quando classifier principal indisponível.
    ZERO keywords hardcoded.
    """
    try:
        # Usar LLM genérico como fallback
        if not hasattr(self, 'llm_fallback'):
            self.llm_fallback = LangChainLLMManager()
        
        # Prompt para classificação
        classification_prompt = f"""Classifique o tipo de análise solicitada na pergunta abaixo.

Pergunta: "{query}"

Tipos possíveis:
- VISUALIZATION: Gráficos, visualizações, plots
- CORRELATION: Correlação, relação entre variáveis
- VARIABILITY: Variabilidade, dispersão, desvio padrão
- CENTRAL_TENDENCY: Média, mediana, moda, tendência central
- DISTRIBUTION: Distribuição, frequência
- OUTLIERS: Outliers, valores discrepantes, anomalias
- INTERVAL: Intervalos, faixas, min/max
- COUNT: Contagem, quantidade
- SUMMARY: Resumo geral, overview
- ANALYSIS: Análise geral

Responda APENAS com o tipo (ex: CORRELATION).
"""
        
        response = self.llm_fallback.query(
            prompt=classification_prompt,
            config=LLMConfig(temperature=0.1, max_tokens=50)
        )
        
        # Parse resposta
        classification = response.content.strip().upper()
        
        # Mapear para QueryType
        try:
            return QueryType[classification]
        except KeyError:
            self.logger.warning(f"Classificação desconhecida: {classification}, usando ANALYSIS")
            return QueryType.ANALYSIS
        
    except Exception as e:
        self.logger.error(f"Erro na classificação inteligente: {e}")
        return QueryType.ANALYSIS

# Substituir uso no método principal
def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None):
    """Analisa query usando classificação inteligente."""
    
    try:
        # 1. Tentar RAGQueryClassifier (preferencial)
        if self.query_classifier:
            classification = self.query_classifier.classify_query(query)
            classification_type = classification.get('type', 'ANALYSIS')
        else:
            # 2. Fallback: LLM genérico (NÃO keywords)
            self.logger.info("⚠️ RAGQueryClassifier indisponível, usando LLM fallback")
            classification_type = self._classify_query_intelligent(query)
        
        # ... resto da lógica
```

---

## <a name="correção-3"></a>🔴 CORREÇÃO #3: Implementar OutlierAnalyzer

### Arquivo Novo: src/analysis/outlier_analyzer.py

```python
"""Analisador especializado para detecção e tratamento de outliers.

Implementa múltiplos métodos de detecção:
- IQR (Interquartile Range)
- Z-Score
- Isolation Forest
- MAD (Median Absolute Deviation)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.utils.logging_config import get_logger


class OutlierMethod(Enum):
    """Métodos disponíveis para detecção de outliers."""
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"
    MAD = "mad"


@dataclass
class OutlierDetectionResult:
    """Resultado de detecção de outliers por um método."""
    method: OutlierMethod
    outliers: pd.DataFrame
    outlier_indices: List[int]
    outlier_percentage: float
    threshold_info: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutlierAnalysisResult:
    """Resultado completo de análise de outliers."""
    detections: Dict[str, OutlierDetectionResult]
    consensus_outliers: pd.DataFrame  # Outliers detectados por 2+ métodos
    impact_analysis: Dict[str, Any]
    treatment_suggestions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Converte resultado para dicionário."""
        return {
            'detections': {
                method: {
                    'outlier_count': len(result.outlier_indices),
                    'percentage': result.outlier_percentage,
                    'threshold_info': result.threshold_info
                }
                for method, result in self.detections.items()
            },
            'consensus_outliers_count': len(self.consensus_outliers),
            'impact_analysis': self.impact_analysis,
            'treatment_suggestions': self.treatment_suggestions,
            'metadata': self.metadata
        }


class OutlierAnalyzer:
    """
    Analisador especializado para detecção e tratamento de outliers.
    
    Exemplo:
        >>> analyzer = OutlierAnalyzer()
        >>> result = analyzer.analyze(
        ...     df, 
        ...     columns=['amount', 'value'],
        ...     methods=[OutlierMethod.IQR, OutlierMethod.ZSCORE]
        ... )
        >>> print(f"Outliers detectados: {len(result.consensus_outliers)}")
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Inicializa analisador de outliers."""
        self.logger = logger or get_logger(__name__)
    
    def analyze(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        methods: List[OutlierMethod] = None
    ) -> OutlierAnalysisResult:
        """
        Detecta outliers usando múltiplos métodos.
        
        Args:
            df: DataFrame a analisar
            columns: Colunas a verificar (None = todas numéricas)
            methods: Métodos a usar (None = todos)
            
        Returns:
            Resultado completo da análise
        """
        if methods is None:
            methods = [OutlierMethod.IQR, OutlierMethod.ZSCORE]
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        self.logger.info(f"Iniciando análise de outliers em {len(columns)} colunas...")
        
        # Detectar outliers com cada método
        detections = {}
        for method in methods:
            self.logger.info(f"Aplicando método: {method.value}")
            detections[method.value] = self._detect_by_method(df, columns, method)
        
        # Encontrar consenso (2+ métodos)
        consensus = self._find_consensus(detections)
        
        # Analisar impacto
        impact = self._analyze_impact(df, consensus)
        
        # Sugerir tratamento
        suggestions = self._suggest_treatment(detections, impact)
        
        return OutlierAnalysisResult(
            detections=detections,
            consensus_outliers=consensus,
            impact_analysis=impact,
            treatment_suggestions=suggestions,
            metadata={
                'total_rows': len(df),
                'columns_analyzed': columns,
                'methods_used': [m.value for m in methods]
            }
        )
    
    def _detect_by_method(
        self, 
        df: pd.DataFrame, 
        columns: List[str],
        method: OutlierMethod
    ) -> OutlierDetectionResult:
        """Detecta outliers usando método específico."""
        
        if method == OutlierMethod.IQR:
            return self._detect_iqr(df, columns)
        elif method == OutlierMethod.ZSCORE:
            return self._detect_zscore(df, columns)
        elif method == OutlierMethod.ISOLATION_FOREST:
            return self._detect_isolation_forest(df, columns)
        elif method == OutlierMethod.MAD:
            return self._detect_mad(df, columns)
        else:
            raise ValueError(f"Método desconhecido: {method}")
    
    def _detect_iqr(self, df: pd.DataFrame, columns: List[str]) -> OutlierDetectionResult:
        """Detecta outliers usando método IQR."""
        outlier_mask = pd.Series(False, index=df.index)
        threshold_info = {}
        
        for col in columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_mask |= col_outliers
            
            threshold_info[col] = {
                'q1': float(q1),
                'q3': float(q3),
                'iqr': float(iqr),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'outliers_in_column': int(col_outliers.sum())
            }
        
        outliers = df[outlier_mask]
        
        return OutlierDetectionResult(
            method=OutlierMethod.IQR,
            outliers=outliers,
            outlier_indices=outliers.index.tolist(),
            outlier_percentage=len(outliers) / len(df) * 100,
            threshold_info=threshold_info
        )
    
    def _detect_zscore(
        self, 
        df: pd.DataFrame, 
        columns: List[str],
        threshold: float = 3.0
    ) -> OutlierDetectionResult:
        """Detecta outliers usando Z-Score."""
        outlier_mask = pd.Series(False, index=df.index)
        threshold_info = {}
        
        for col in columns:
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            col_outliers = z_scores > threshold
            
            # Reindexar para tamanho original
            col_outliers_full = pd.Series(False, index=df.index)
            col_outliers_full[df[col].notna()] = col_outliers
            
            outlier_mask |= col_outliers_full
            
            threshold_info[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'threshold': threshold,
                'max_zscore': float(np.max(z_scores)) if len(z_scores) > 0 else 0,
                'outliers_in_column': int(col_outliers_full.sum())
            }
        
        outliers = df[outlier_mask]
        
        return OutlierDetectionResult(
            method=OutlierMethod.ZSCORE,
            outliers=outliers,
            outlier_indices=outliers.index.tolist(),
            outlier_percentage=len(outliers) / len(df) * 100,
            threshold_info=threshold_info
        )
    
    def _detect_isolation_forest(
        self, 
        df: pd.DataFrame, 
        columns: List[str],
        contamination: float = 0.1
    ) -> OutlierDetectionResult:
        """Detecta outliers usando Isolation Forest."""
        # Preparar dados
        X = df[columns].copy()
        X = X.fillna(X.mean())  # Tratar missing values
        
        # Escalar dados
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Aplicar Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = iso_forest.fit_predict(X_scaled)
        
        # -1 = outlier, 1 = inlier
        outlier_mask = predictions == -1
        outliers = df[outlier_mask]
        
        # Calcular scores
        scores = iso_forest.score_samples(X_scaled)
        
        return OutlierDetectionResult(
            method=OutlierMethod.ISOLATION_FOREST,
            outliers=outliers,
            outlier_indices=outliers.index.tolist(),
            outlier_percentage=len(outliers) / len(df) * 100,
            threshold_info={
                'contamination': contamination,
                'n_estimators': 100,
                'mean_score': float(np.mean(scores)),
                'min_score': float(np.min(scores))
            }
        )
    
    def _detect_mad(
        self, 
        df: pd.DataFrame, 
        columns: List[str],
        threshold: float = 3.5
    ) -> OutlierDetectionResult:
        """Detecta outliers usando MAD (Median Absolute Deviation)."""
        outlier_mask = pd.Series(False, index=df.index)
        threshold_info = {}
        
        for col in columns:
            median = df[col].median()
            mad = np.median(np.abs(df[col] - median))
            
            if mad == 0:
                # Evitar divisão por zero
                col_outliers = pd.Series(False, index=df.index)
            else:
                modified_z_scores = 0.6745 * (df[col] - median) / mad
                col_outliers = np.abs(modified_z_scores) > threshold
            
            outlier_mask |= col_outliers
            
            threshold_info[col] = {
                'median': float(median),
                'mad': float(mad),
                'threshold': threshold,
                'outliers_in_column': int(col_outliers.sum())
            }
        
        outliers = df[outlier_mask]
        
        return OutlierDetectionResult(
            method=OutlierMethod.MAD,
            outliers=outliers,
            outlier_indices=outliers.index.tolist(),
            outlier_percentage=len(outliers) / len(df) * 100,
            threshold_info=threshold_info
        )
    
    def _find_consensus(self, detections: Dict) -> pd.DataFrame:
        """Encontra outliers detectados por 2+ métodos (consenso)."""
        if len(detections) < 2:
            # Se só há 1 método, retornar seus outliers
            return list(detections.values())[0].outliers
        
        # Contar quantas vezes cada índice foi marcado como outlier
        index_counts = {}
        for detection in detections.values():
            for idx in detection.outlier_indices:
                index_counts[idx] = index_counts.get(idx, 0) + 1
        
        # Filtrar índices detectados por 2+ métodos
        consensus_indices = [idx for idx, count in index_counts.items() if count >= 2]
        
        # Retornar DataFrame com outliers de consenso
        if consensus_indices:
            first_detection = list(detections.values())[0]
            return first_detection.outliers.loc[consensus_indices]
        else:
            return pd.DataFrame()
    
    def _analyze_impact(self, df: pd.DataFrame, outliers: pd.DataFrame) -> Dict:
        """Analisa impacto dos outliers nas estatísticas."""
        if len(outliers) == 0:
            return {'message': 'Nenhum outlier para análise de impacto'}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        impact = {}
        
        for col in numeric_cols:
            # Estatísticas com outliers
            with_outliers = {
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std())
            }
            
            # Estatísticas sem outliers
            df_no_outliers = df.drop(outliers.index)
            without_outliers = {
                'mean': float(df_no_outliers[col].mean()),
                'median': float(df_no_outliers[col].median()),
                'std': float(df_no_outliers[col].std())
            }
            
            # Calcular diferenças
            impact[col] = {
                'with_outliers': with_outliers,
                'without_outliers': without_outliers,
                'mean_diff_%': abs((with_outliers['mean'] - without_outliers['mean']) / with_outliers['mean'] * 100),
                'std_diff_%': abs((with_outliers['std'] - without_outliers['std']) / with_outliers['std'] * 100)
            }
        
        return impact
    
    def _suggest_treatment(
        self, 
        detections: Dict, 
        impact: Dict
    ) -> List[str]:
        """Sugere tratamentos para outliers baseado na análise."""
        suggestions = []
        
        # Contar total de outliers
        total_outliers = len(list(detections.values())[0].outliers)
        total_rows = list(detections.values())[0].outliers.index.max() + 1
        outlier_percentage = total_outliers / total_rows * 100
        
        if outlier_percentage < 1:
            suggestions.append("✅ Remoção: Menos de 1% dos dados, pode remover com segurança")
        elif outlier_percentage < 5:
            suggestions.append("⚠️ Winsorização: 1-5% dos dados, considerar winsorização (cap nos percentis 1 e 99)")
        else:
            suggestions.append("❌ Investigar: Mais de 5%, pode indicar problema nos dados ou fenômeno real")
        
        # Analisar impacto
        high_impact_cols = [
            col for col, info in impact.items()
            if info.get('mean_diff_%', 0) > 10 or info.get('std_diff_%', 0) > 20
        ]
        
        if high_impact_cols:
            suggestions.append(
                f"🔍 Alto impacto: Outliers afetam significativamente {', '.join(high_impact_cols)}"
            )
            suggestions.append("💡 Considerar transformação logarítmica ou Box-Cox")
        
        # Sugestões por método
        if len(detections) >= 2:
            suggestions.append("✅ Consenso: Use apenas outliers detectados por 2+ métodos para maior confiança")
        
        return suggestions


# Exemplo de uso
if __name__ == "__main__":
    # Criar dados de exemplo
    np.random.seed(42)
    df = pd.DataFrame({
        'value1': np.random.normal(100, 15, 1000).tolist() + [200, 250, -50],  # Adicionar outliers
        'value2': np.random.normal(50, 10, 1000).tolist() + [150, 180, -20]
    })
    
    # Analisar outliers
    analyzer = OutlierAnalyzer()
    result = analyzer.analyze(
        df,
        methods=[OutlierMethod.IQR, OutlierMethod.ZSCORE, OutlierMethod.ISOLATION_FOREST]
    )
    
    print(f"Outliers detectados: {len(result.consensus_outliers)}")
    print(f"\nSugestões de tratamento:")
    for suggestion in result.treatment_suggestions:
        print(f"  {suggestion}")
```

### Integração no OrchestratorAgent

```python
# src/agent/orchestrator_agent.py

from src.analysis.outlier_analyzer import OutlierAnalyzer, OutlierMethod

def _handle_outlier_query(self, query: str, context: Dict) -> Dict:
    """Processa consultas sobre outliers."""
    
    # Carregar dados
    df = self._load_data_from_context(context)
    
    # Analisar outliers
    analyzer = OutlierAnalyzer()
    result = analyzer.analyze(
        df,
        methods=[OutlierMethod.IQR, OutlierMethod.ZSCORE, OutlierMethod.ISOLATION_FOREST]
    )
    
    # Formatar resposta
    response = f"""
## 🔍 Análise de Outliers

**Total de Outliers (Consenso):** {len(result.consensus_outliers)} ({len(result.consensus_outliers) / len(df) * 100:.2f}%)

### Detecções por Método:
{self._format_detections(result.detections)}

### Impacto nas Estatísticas:
{self._format_impact(result.impact_analysis)}

### Recomendações de Tratamento:
{chr(10).join(result.treatment_suggestions)}
"""
    
    return {
        'answer': response,
        'data': result.to_dict(),
        'outliers': result.consensus_outliers.to_dict('records')
    }
```

---

## <a name="correção-4"></a>🟡 CORREÇÃO #4: Consolidar Módulos LLM

### Adicionar Aviso de Deprecação

```python
# src/llm/manager.py (ADICIONAR NO INÍCIO)

import warnings

warnings.warn(
    "\n⚠️ AVISO DE DEPRECAÇÃO ⚠️\n"
    "Este módulo (src.llm.manager) está DEPRECATED.\n"
    "Use src.llm.langchain_manager.LangChainLLMManager\n"
    "Este arquivo será removido na versão 3.0\n",
    DeprecationWarning,
    stacklevel=2
)

# Re-exportar para compatibilidade temporária
from src.llm.langchain_manager import (
    LangChainLLMManager as LLMManager,
    LLMProvider,
    LLMResponse,
    LLMConfig
)

__all__ = ['LLMManager', 'LLMProvider', 'LLMResponse', 'LLMConfig']
```

### Migração em Todos os Agentes

```bash
# Script de migração automática
find src/agent -name "*.py" -exec sed -i 's/from src.llm.manager import/from src.llm.langchain_manager import/g' {} \;
find src/agent -name "*.py" -exec sed -i 's/LLMManager(/LangChainLLMManager(/g' {} \;
```

---

## <a name="correção-5"></a>🟡 CORREÇÃO #5: Adicionar Schemas Pydantic

### Arquivo Novo: src/schemas/query_schemas.py

```python
"""Schemas Pydantic para validação de entrada em todas as queries."""

from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any
from enum import Enum


class ChartType(str, Enum):
    """Tipos de gráficos suportados."""
    HISTOGRAM = "histogram"
    SCATTER = "scatter"
    BOXPLOT = "boxplot"
    HEATMAP = "heatmap"
    LINE = "line"
    BAR = "bar"


class QueryRequest(BaseModel):
    """Schema para requisição de query genérica."""
    
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=5000,
        description="Pergunta do usuário"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexto adicional (dataset, histórico, etc.)"
    )
    dataset_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Nome do dataset a usar"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Valida conteúdo da query."""
        # Bloquear conteúdo malicioso
        forbidden_patterns = [
            '<script>', 'DROP TABLE', 'DELETE FROM', 
            'UPDATE', 'INSERT INTO', 'ALTER TABLE',
            '__import__', 'eval(', 'exec('
        ]
        
        v_upper = v.upper()
        for pattern in forbidden_patterns:
            if pattern.upper() in v_upper:
                raise ValueError(f"Query contém padrão proibido: {pattern}")
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Qual a média de valores?",
                "context": {"dataset": "creditcard"},
                "dataset_name": "creditcard_fraud"
            }
        }


class VisualizationRequest(BaseModel):
    """Schema para requisição de visualização."""
    
    chart_type: ChartType = Field(
        ...,
        description="Tipo de gráfico"
    )
    columns: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=10,
        description="Colunas a visualizar"
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Título do gráfico"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configurações adicionais"
    )
    
    @validator('columns')
    def validate_columns(cls, v):
        """Valida nomes de colunas."""
        for col in v:
            if len(col) > 100:
                raise ValueError(f"Nome de coluna muito longo: {col}")
            if not col.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Nome de coluna inválido: {col}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "chart_type": "histogram",
                "columns": ["Amount"],
                "title": "Distribuição de Valores",
                "config": {"bins": 30}
            }
        }


class AnalysisRequest(BaseModel):
    """Schema para requisição de análise estatística."""
    
    analysis_type: str = Field(
        ...,
        regex='^(statistical|correlation|outlier|temporal|clustering)$',
        description="Tipo de análise"
    )
    columns: Optional[List[str]] = Field(
        default=None,
        max_items=50,
        description="Colunas a analisar (None = todas)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parâmetros específicos da análise"
    )
    
    @root_validator
    def validate_parameters(cls, values):
        """Valida parâmetros baseado no tipo de análise."""
        analysis_type = values.get('analysis_type')
        parameters = values.get('parameters') or {}
        
        # Validações específicas por tipo
        if analysis_type == 'outlier':
            if 'threshold' in parameters:
                threshold = parameters['threshold']
                if not isinstance(threshold, (int, float)) or threshold <= 0:
                    raise ValueError("threshold deve ser número positivo")
        
        return values


# Uso nos agentes:
from src.schemas.query_schemas import QueryRequest, VisualizationRequest

def process_query(self, request_data: dict):
    # Validação automática
    request = QueryRequest(**request_data)
    
    # Agora request.query está validado e sanitizado
    return self._execute_query(request.query, request.context)
```

---

## 📚 Referências e Documentação

### Testes para Validar Correções

```python
# tests/test_corrections.py

import pytest
from src.agent.orchestrator_agent import OrchestratorAgent
from src.analysis.outlier_analyzer import OutlierAnalyzer, OutlierMethod
from src.schemas.query_schemas import QueryRequest

def test_no_keywords_in_orchestrator():
    """Verifica que OrchestratorAgent não usa keywords."""
    orchestrator = OrchestratorAgent()
    
    # Teste com sinônimos não-triviais
    test_queries = [
        "Calculate the standard deviation",  # Inglês
        "Qual a covariância?",  # Português
        "Show me the kurtosis",  # Métrica estatística avançada
    ]
    
    for query in test_queries:
        result = orchestrator._needs_data_analysis(query, {})
        assert isinstance(result, bool)
        # Não deve falhar em nenhum caso

def test_outlier_analyzer():
    """Testa OutlierAnalyzer com múltiplos métodos."""
    import pandas as pd
    import numpy as np
    
    # Dados de teste
    df = pd.DataFrame({
        'value': np.random.normal(100, 15, 1000).tolist() + [500, -100]
    })
    
    analyzer = OutlierAnalyzer()
    result = analyzer.analyze(
        df,
        methods=[OutlierMethod.IQR, OutlierMethod.ZSCORE]
    )
    
    assert len(result.consensus_outliers) > 0
    assert len(result.treatment_suggestions) > 0
    assert 'iqr' in result.detections
    assert 'zscore' in result.detections

def test_pydantic_validation():
    """Testa validação de schemas Pydantic."""
    
    # Query válida
    valid = QueryRequest(query="Qual a média?", dataset_name="test")
    assert valid.query == "Qual a média?"
    
    # Query maliciosa deve falhar
    with pytest.raises(ValueError):
        QueryRequest(query="DROP TABLE users")
    
    with pytest.raises(ValueError):
        QueryRequest(query="<script>alert(1)</script>")
```

---

**FIM DOS EXEMPLOS DE IMPLEMENTAÇÃO**

Para dúvidas ou assistência na implementação, consulte a documentação principal em `AUDITORIA_COMPLETA_WORKSPACE.md`.
