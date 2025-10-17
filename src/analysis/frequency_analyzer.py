"""
Análise de Frequência Modular - Distribuições e Contagens

Módulo especializado em análises de frequência, valores mais/menos
comuns, distribuições e contagens.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 3.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import logging
from datetime import datetime


@dataclass
class FrequencyAnalysisResult:
    """
    Resultado de análise de frequência.
    
    Attributes:
        frequency_tables: Tabelas de frequência por coluna
        mode_stats: Estatísticas de moda
        value_counts: Contagens de valores únicos
        rarity_analysis: Análise de valores raros vs comuns
        interpretation: Interpretação contextual
        recommendations: Próximos passos sugeridos
        metadata: Metadados adicionais
    """
    frequency_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    mode_stats: Dict[str, Any] = field(default_factory=dict)
    value_counts: Dict[str, Dict] = field(default_factory=dict)
    rarity_analysis: Dict[str, Dict] = field(default_factory=dict)
    interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Gera relatório formatado em Markdown."""
        md = "# Análise de Frequência e Distribuição\n\n"
        
        if self.mode_stats:
            md += "## Valores Mais Frequentes (Moda)\n\n"
            for col, stats in self.mode_stats.items():
                md += f"### {col}\n\n"
                md += f"- **Valor mais frequente:** {stats['mode_value']}\n"
                md += f"- **Frequência:** {stats['mode_count']:,} ocorrências ({stats['mode_percentage']:.1f}%)\n"
                if stats.get('second_mode_value'):
                    md += f"- **Segundo mais frequente:** {stats['second_mode_value']} "
                    md += f"({stats['second_mode_count']:,} ocorrências)\n"
                md += "\n"
        
        if self.rarity_analysis:
            md += "## Análise de Raridade\n\n"
            for col, stats in self.rarity_analysis.items():
                md += f"### {col}\n\n"
                md += f"- **Valores únicos:** {stats['unique_values']:,}\n"
                md += f"- **Valores raros (< 1%):** {stats['rare_values_count']:,}\n"
                md += f"- **Concentração:** {stats['concentration_top10']:.1f}% nos top 10 valores\n\n"
        
        if self.interpretation:
            md += "## Interpretação\n\n"
            md += self.interpretation + "\n\n"
        
        if self.recommendations:
            md += "## Próximos Passos Recomendados\n\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
        
        return md


class FrequencyAnalyzer:
    """
    Analisador modular de frequência e distribuição.
    
    Fornece análises detalhadas de valores mais/menos frequentes,
    distribuições e concentrações de dados.
    
    Exemplo:
        >>> analyzer = FrequencyAnalyzer()
        >>> result = analyzer.analyze(df, columns=['Class', 'V1'])
        >>> print(result.to_markdown())
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa analisador de frequência.
        
        Args:
            logger: Logger opcional
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        top_n: int = 10,
        rare_threshold: float = 0.01  # 1%
    ) -> FrequencyAnalysisResult:
        """
        Executa análise de frequência completa.
        
        Args:
            df: DataFrame a analisar
            columns: Colunas específicas (None = todas)
            top_n: Número de valores mais frequentes a retornar
            rare_threshold: Threshold para classificar valor como raro (0.01 = 1%)
            
        Returns:
            Resultado completo da análise
        """
        try:
            self.logger.info("Iniciando análise de frequência...")
            
            # Selecionar colunas
            if columns is None:
                columns = df.columns.tolist()
            
            # Validar colunas
            columns = [col for col in columns if col in df.columns]
            if not columns:
                raise ValueError("Nenhuma coluna encontrada")
            
            result = FrequencyAnalysisResult()
            
            # Tabelas de frequência
            result.frequency_tables = self._compute_frequency_tables(df, columns, top_n)
            
            # Estatísticas de moda
            result.mode_stats = self._compute_mode_stats(df, columns)
            
            # Contagens de valores
            result.value_counts = self._compute_value_counts(df, columns)
            
            # Análise de raridade
            result.rarity_analysis = self._compute_rarity_analysis(
                df, columns, rare_threshold
            )
            
            # Interpretação
            result.interpretation = self._generate_interpretation(result)
            
            # Recomendações
            result.recommendations = self._generate_recommendations(result)
            
            # Metadados
            result.metadata = {
                "columns_analyzed": columns,
                "total_columns": len(columns),
                "total_rows": len(df),
                "top_n": top_n,
                "rare_threshold": rare_threshold,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Análise de frequência concluída: {len(columns)} colunas")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na análise de frequência: {e}", exc_info=True)
            raise
    
    def _compute_frequency_tables(
        self,
        df: pd.DataFrame,
        columns: List[str],
        top_n: int
    ) -> Dict[str, pd.DataFrame]:
        """Calcula tabelas de frequência."""
        tables = {}
        
        for col in columns:
            # Value counts
            value_counts = df[col].value_counts().head(top_n)
            
            # Criar DataFrame
            freq_table = pd.DataFrame({
                'Valor': value_counts.index,
                'Frequência': value_counts.values,
                'Percentual (%)': (value_counts.values / len(df) * 100).round(2)
            })
            
            tables[col] = freq_table
        
        return tables
    
    def _compute_mode_stats(self, df: pd.DataFrame, columns: List[str]) -> Dict:
        """Calcula estatísticas de moda."""
        stats = {}
        
        for col in columns:
            value_counts = df[col].value_counts()
            
            if len(value_counts) == 0:
                continue
            
            # Valor mais frequente (moda)
            mode_value = value_counts.index[0]
            mode_count = value_counts.iloc[0]
            mode_percentage = mode_count / len(df) * 100
            
            # Segundo mais frequente (se houver)
            second_mode = None
            second_count = None
            if len(value_counts) > 1:
                second_mode = value_counts.index[1]
                second_count = value_counts.iloc[1]
            
            stats[col] = {
                'mode_value': mode_value,
                'mode_count': int(mode_count),
                'mode_percentage': float(mode_percentage),
                'second_mode_value': second_mode,
                'second_mode_count': int(second_count) if second_count else None
            }
        
        return stats
    
    def _compute_value_counts(self, df: pd.DataFrame, columns: List[str]) -> Dict:
        """Calcula contagens completas de valores."""
        counts = {}
        
        for col in columns:
            unique_values = df[col].nunique()
            null_count = df[col].isnull().sum()
            
            counts[col] = {
                'unique_values': int(unique_values),
                'null_count': int(null_count),
                'null_percentage': float(null_count / len(df) * 100)
            }
        
        return counts
    
    def _compute_rarity_analysis(
        self,
        df: pd.DataFrame,
        columns: List[str],
        threshold: float
    ) -> Dict:
        """Analisa valores raros vs comuns."""
        analysis = {}
        
        for col in columns:
            value_counts = df[col].value_counts()
            total = len(df)
            
            # Valores raros (frequência < threshold)
            rare_mask = (value_counts / total) < threshold
            rare_values_count = rare_mask.sum()
            
            # Concentração nos top 10
            top10_sum = value_counts.head(10).sum()
            concentration_top10 = top10_sum / total * 100
            
            analysis[col] = {
                'unique_values': int(value_counts.count()),
                'rare_values_count': int(rare_values_count),
                'rare_percentage': float(rare_values_count / value_counts.count() * 100),
                'concentration_top10': float(concentration_top10)
            }
        
        return analysis
    
    def _generate_interpretation(self, result: FrequencyAnalysisResult) -> str:
        """Gera interpretação contextual."""
        interpretation = []
        
        # Análise de concentração
        if result.rarity_analysis:
            highly_concentrated = [
                col for col, stats in result.rarity_analysis.items()
                if stats['concentration_top10'] > 80
            ]
            
            if highly_concentrated:
                interpretation.append(
                    f"As variáveis {', '.join(highly_concentrated[:3])} apresentam alta concentração "
                    "(>80% nos top 10 valores), indicando distribuição dominada por poucos valores."
                )
            
            many_unique = [
                col for col, stats in result.rarity_analysis.items()
                if stats['unique_values'] > 1000
            ]
            
            if many_unique:
                interpretation.append(
                    f"As variáveis {', '.join(many_unique[:3])} possuem muitos valores únicos (>1000), "
                    "sugerindo natureza contínua ou alta cardinalidade."
                )
        
        return " ".join(interpretation) if interpretation else \
            "As variáveis apresentam distribuição de frequência típica."
    
    def _generate_recommendations(self, result: FrequencyAnalysisResult) -> List[str]:
        """Gera recomendações de próximos passos."""
        recommendations = []
        
        # Recomendações baseadas em raridade
        if result.rarity_analysis:
            has_rare = any(
                stats['rare_values_count'] > 0
                for stats in result.rarity_analysis.values()
            )
            if has_rare:
                recommendations.append(
                    "Investigue valores raros para identificar possíveis outliers ou casos especiais"
                )
            
            high_concentration = any(
                stats['concentration_top10'] > 90
                for stats in result.rarity_analysis.values()
            )
            if high_concentration:
                recommendations.append(
                    "Considere agrupar valores menos frequentes em categoria 'outros' para simplificar análises"
                )
        
        # Recomendação padrão
        if not recommendations:
            recommendations.append(
                "Visualize histogramas para melhor compreensão das distribuições"
            )
        
        return recommendations
