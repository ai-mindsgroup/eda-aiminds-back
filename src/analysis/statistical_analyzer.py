"""
Análise Estatística Modular - Estatísticas Descritivas

Módulo especializado em análises estatísticas descritivas gerais,
desacoplado e reutilizável.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 3.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import logging
from datetime import datetime


@dataclass
class StatisticalAnalysisResult:
    """
    Resultado de análise estatística.
    
    Attributes:
        summary_stats: Estatísticas descritivas gerais
        distribution_stats: Estatísticas de distribuição
        variability_stats: Métricas de variabilidade
        position_stats: Métricas de posição
        interpretation: Interpretação contextual
        recommendations: Próximos passos sugeridos
        metadata: Metadados adicionais
    """
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    distribution_stats: Dict[str, Any] = field(default_factory=dict)
    variability_stats: Dict[str, Any] = field(default_factory=dict)
    position_stats: Dict[str, Any] = field(default_factory=dict)
    interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Gera relatório formatado em Markdown."""
        md = "# Análise Estatística Descritiva\n\n"
        
        if self.summary_stats:
            md += "## Resumo Estatístico\n\n"
            md += self._format_dict_as_table(self.summary_stats)
        
        if self.variability_stats:
            md += "\n## Métricas de Variabilidade\n\n"
            md += self._format_dict_as_table(self.variability_stats)
        
        if self.position_stats:
            md += "\n## Métricas de Posição\n\n"
            md += self._format_dict_as_table(self.position_stats)
        
        if self.distribution_stats:
            md += "\n## Características de Distribuição\n\n"
            md += self._format_dict_as_table(self.distribution_stats)
        
        if self.interpretation:
            md += "\n## Interpretação\n\n"
            md += self.interpretation + "\n\n"
        
        if self.recommendations:
            md += "\n## Próximos Passos Recomendados\n\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
        
        return md
    
    def _format_dict_as_table(self, data: Dict) -> str:
        """Formata dicionário como tabela Markdown."""
        if not data:
            return "*Sem dados*\n"
        
        df = pd.DataFrame.from_dict(data, orient='index', columns=['Valor'])
        return df.to_markdown() + "\n"


class StatisticalAnalyzer:
    """
    Analisador modular de estatísticas descritivas.
    
    Fornece análises estatísticas robustas e interpretativas sem
    depender de lógica hardcoded externa.
    
    Exemplo:
        >>> analyzer = StatisticalAnalyzer()
        >>> result = analyzer.analyze(df, columns=['Amount', 'Time'])
        >>> print(result.to_markdown())
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa analisador estatístico.
        
        Args:
            logger: Logger opcional
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        include_distribution: bool = True,
        include_variability: bool = True,
        include_position: bool = True
    ) -> StatisticalAnalysisResult:
        """
        Executa análise estatística completa.
        
        Args:
            df: DataFrame a analisar
            columns: Colunas específicas (None = todas numéricas)
            include_distribution: Incluir análise de distribuição
            include_variability: Incluir métricas de variabilidade
            include_position: Incluir métricas de posição
            
        Returns:
            Resultado completo da análise
        """
        try:
            self.logger.info("Iniciando análise estatística...")
            
            # Selecionar colunas
            if columns is None:
                columns = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validar colunas
            columns = [col for col in columns if col in df.columns]
            if not columns:
                raise ValueError("Nenhuma coluna numérica encontrada")
            
            result = StatisticalAnalysisResult()
            
            # Estatísticas gerais
            result.summary_stats = self._compute_summary_stats(df, columns)
            
            # Métricas de variabilidade
            if include_variability:
                result.variability_stats = self._compute_variability_stats(df, columns)
            
            # Métricas de posição
            if include_position:
                result.position_stats = self._compute_position_stats(df, columns)
            
            # Distribuição
            if include_distribution:
                result.distribution_stats = self._compute_distribution_stats(df, columns)
            
            # Interpretação
            result.interpretation = self._generate_interpretation(result)
            
            # Recomendações
            result.recommendations = self._generate_recommendations(result)
            
            # Metadados
            result.metadata = {
                "columns_analyzed": columns,
                "total_columns": len(columns),
                "total_rows": len(df),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Análise estatística concluída: {len(columns)} colunas")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na análise estatística: {e}", exc_info=True)
            raise
    
    def _compute_summary_stats(self, df: pd.DataFrame, columns: List[str]) -> Dict:
        """Calcula estatísticas descritivas gerais."""
        stats = {}
        
        for col in columns:
            series = df[col].dropna()
            
            stats[col] = {
                'count': int(series.count()),
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max())
            }
        
        return stats
    
    def _compute_variability_stats(self, df: pd.DataFrame, columns: List[str]) -> Dict:
        """Calcula métricas de variabilidade."""
        stats = {}
        
        for col in columns:
            series = df[col].dropna()
            mean_val = series.mean()
            std_val = series.std()
            
            # Coeficiente de variação (CV)
            cv = (std_val / mean_val * 100) if mean_val != 0 else np.inf
            
            # Intervalo interquartil (IQR)
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            
            # Range
            range_val = series.max() - series.min()
            
            stats[col] = {
                'std_dev': float(std_val),
                'variance': float(series.var()),
                'coef_variation_%': float(cv) if not np.isinf(cv) else None,
                'iqr': float(iqr),
                'range': float(range_val)
            }
        
        return stats
    
    def _compute_position_stats(self, df: pd.DataFrame, columns: List[str]) -> Dict:
        """Calcula métricas de posição."""
        stats = {}
        
        for col in columns:
            series = df[col].dropna()
            
            stats[col] = {
                'q1_25%': float(series.quantile(0.25)),
                'q2_50%_median': float(series.quantile(0.50)),
                'q3_75%': float(series.quantile(0.75)),
                'mode': float(series.mode().iloc[0]) if len(series.mode()) > 0 else None
            }
        
        return stats
    
    def _compute_distribution_stats(self, df: pd.DataFrame, columns: List[str]) -> Dict:
        """Calcula características de distribuição."""
        stats = {}
        
        for col in columns:
            series = df[col].dropna()
            
            # Skewness e Kurtosis
            from scipy import stats as scipy_stats
            
            try:
                skew = scipy_stats.skew(series)
                kurt = scipy_stats.kurtosis(series)
            except:
                skew = None
                kurt = None
            
            stats[col] = {
                'skewness': float(skew) if skew is not None else None,
                'kurtosis': float(kurt) if kurt is not None else None,
                'unique_values': int(series.nunique()),
                'unique_ratio_%': float(series.nunique() / len(series) * 100)
            }
        
        return stats
    
    def _generate_interpretation(self, result: StatisticalAnalysisResult) -> str:
        """Gera interpretação contextual."""
        interpretation = []
        
        # Análise de variabilidade
        if result.variability_stats:
            high_cv_vars = [
                col for col, stats in result.variability_stats.items()
                if stats.get('coef_variation_%') and stats['coef_variation_%'] > 50
            ]
            
            if high_cv_vars:
                interpretation.append(
                    f"As variáveis {', '.join(high_cv_vars[:3])} apresentam alta variabilidade "
                    "(CV > 50%), indicando grande dispersão dos dados em relação à média."
                )
        
        # Análise de distribuição
        if result.distribution_stats:
            skewed_vars = [
                col for col, stats in result.distribution_stats.items()
                if stats.get('skewness') and abs(stats['skewness']) > 1
            ]
            
            if skewed_vars:
                interpretation.append(
                    f"As variáveis {', '.join(skewed_vars[:3])} apresentam assimetria acentuada "
                    "(|skewness| > 1), sugerindo distribuições não-normais."
                )
        
        return " ".join(interpretation) if interpretation else \
            "As variáveis apresentam características estatísticas típicas."
    
    def _generate_recommendations(self, result: StatisticalAnalysisResult) -> List[str]:
        """Gera recomendações de próximos passos."""
        recommendations = []
        
        # Recomendações baseadas em variabilidade
        if result.variability_stats:
            high_var = any(
                stats.get('coef_variation_%', 0) > 50
                for stats in result.variability_stats.values()
            )
            if high_var:
                recommendations.append(
                    "Considere investigar outliers nas variáveis com alta variabilidade"
                )
        
        # Recomendações baseadas em distribuição
        if result.distribution_stats:
            skewed = any(
                abs(stats.get('skewness', 0)) > 1
                for stats in result.distribution_stats.values()
            )
            if skewed:
                recommendations.append(
                    "Visualize histogramas para entender melhor distribuições assimétricas"
                )
        
        # Recomendação padrão
        if not recommendations:
            recommendations.append(
                "Explore correlações entre variáveis para identificar relações"
            )
        
        return recommendations
