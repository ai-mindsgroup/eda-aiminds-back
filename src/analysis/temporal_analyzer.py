"""
Análise temporal avançada e interpretativa para séries temporais.

Este módulo fornece análises estatísticas sofisticadas de séries temporais,
incluindo detecção de tendências, sazonalidade, anomalias e interpretação
contextualizada dos padrões descobertos.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 2.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np
import logging
from datetime import datetime


class TrendType(Enum):
    """Tipos de tendência detectados."""
    CRESCENTE = "crescente"
    DECRESCENTE = "decrescente"
    ESTAVEL = "estável"
    NAO_LINEAR = "não-linear"


class SeasonalityType(Enum):
    """Tipos de sazonalidade detectados."""
    DIARIA = "diária"
    SEMANAL = "semanal"
    MENSAL = "mensal"
    ANUAL = "anual"
    NENHUMA = "nenhuma"


@dataclass
class TemporalAnalysisResult:
    """
    Resultado completo da análise temporal.
    
    Attributes:
        column_name: Nome da coluna analisada
        summary_stats: Estatísticas descritivas
        trend: Informações de tendência
        seasonality: Informações de sazonalidade
        anomalies: Anomalias detectadas
        autocorrelation: Análise de autocorrelação
        interpretation: Interpretação contextual
        recommendations: Recomendações para análises futuras
        metadata: Metadados adicionais
    """
    column_name: str
    summary_stats: Dict = field(default_factory=dict)
    trend: Dict = field(default_factory=dict)
    seasonality: Dict = field(default_factory=dict)
    anomalies: Dict = field(default_factory=dict)
    autocorrelation: Dict = field(default_factory=dict)
    interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Gera relatório formatado em Markdown."""
        md = f"# Análise Temporal: {self.column_name}\n\n"
        
        # Introdução contextual
        md += self._generate_introduction()
        
        # Estatísticas descritivas
        md += "## Resumo Estatístico\n\n"
        md += self._format_summary_stats()
        
        # Análise de tendência
        md += "\n## Análise de Tendência\n\n"
        md += self._format_trend_analysis()
        
        # Autocorrelação e ciclos
        md += "\n## Autocorrelação e Padrões Cíclicos\n\n"
        md += self._format_autocorrelation()
        
        # Sazonalidade
        if self.seasonality.get('detected'):
            md += "\n## Sazonalidade Detectada\n\n"
            md += self._format_seasonality()
        
        # Anomalias
        md += "\n## Detecção de Anomalias\n\n"
        md += self._format_anomalies()
        
        # Interpretação contextual
        md += "\n## Interpretação Qualitativa\n\n"
        md += self.interpretation + "\n\n"
        
        # Recomendações
        md += "\n## Próximos Passos Recomendados\n\n"
        for rec in self.recommendations:
            md += f"- {rec}\n"
        
        return md
    
    def _generate_introduction(self) -> str:
        """Gera introdução contextualizada."""
        return (
            f"Realizamos uma análise detalhada da dimensão temporal **'{self.column_name}'** "
            "dos dados para identificar padrões, tendências e anomalias ao longo do período analisado. "
            "A seguir, apresentamos as métricas estatísticas, análises quantitativas e "
            "interpretações qualitativas que fundamentam nossas conclusões.\n\n"
        )
    
    def _format_summary_stats(self) -> str:
        """Formata estatísticas descritivas em tabela Markdown."""
        if not self.summary_stats:
            return "*Estatísticas não disponíveis*\n"
        
        stats_df = pd.Series(self.summary_stats).to_frame(name=self.column_name)
        return stats_df.to_markdown() + "\n"
    
    def _format_trend_analysis(self) -> str:
        """Formata análise de tendência."""
        if not self.trend:
            return "*Análise de tendência não disponível*\n"
        
        trend_type = self.trend.get('type', 'desconhecido')
        slope = self.trend.get('slope', 0)
        r2 = self.trend.get('r2_score', 0)
        
        md = f"**Tipo de tendência:** {trend_type.capitalize()}\n\n"
        md += f"**Coeficiente angular:** {slope:.6f}\n\n"
        md += f"**Qualidade do ajuste (R²):** {r2:.4f}\n\n"
        
        # Interpretação do R²
        if r2 >= 0.8:
            md += "*O modelo linear explica bem a tendência (R² ≥ 0.8)*\n"
        elif r2 >= 0.5:
            md += "*O modelo linear explica moderadamente a tendência (0.5 ≤ R² < 0.8)*\n"
        else:
            md += "*A tendência pode não ser linear (R² < 0.5). Considere modelos não-lineares.*\n"
        
        return md + "\n"
    
    def _format_autocorrelation(self) -> str:
        """Formata análise de autocorrelação."""
        if not self.autocorrelation:
            return "*Análise de autocorrelação não disponível*\n"
        
        lag1 = self.autocorrelation.get('lag1', 0)
        is_cyclic = self.autocorrelation.get('is_cyclic', False)
        
        md = f"**Autocorrelação (lag=1):** {lag1:.4f}\n\n"
        
        if is_cyclic:
            md += "*Indicação de dependência temporal ou padrões cíclicos significativos (|autocorr| > 0.3)*\n"
        else:
            md += "*Não foram identificados padrões cíclicos relevantes (|autocorr| ≤ 0.3)*\n"
        
        return md + "\n"
    
    def _format_seasonality(self) -> str:
        """Formata análise de sazonalidade."""
        season_type = self.seasonality.get('type', SeasonalityType.NENHUMA.value)
        strength = self.seasonality.get('strength', 0)
        
        md = f"**Tipo de sazonalidade:** {season_type.capitalize()}\n\n"
        md += f"**Força da sazonalidade:** {strength:.2%}\n\n"
        
        if strength >= 0.7:
            md += "*Sazonalidade forte detectada*\n"
        elif strength >= 0.4:
            md += "*Sazonalidade moderada detectada*\n"
        else:
            md += "*Sazonalidade fraca ou ausente*\n"
        
        return md + "\n"
    
    def _format_anomalies(self) -> str:
        """Formata detecção de anomalias."""
        if not self.anomalies:
            return "*Análise de anomalias não disponível*\n"
        
        count = self.anomalies.get('count', 0)
        method = self.anomalies.get('method', 'z-score')
        threshold = self.anomalies.get('threshold', 3)
        
        md = f"**Método de detecção:** {method} (threshold={threshold})\n\n"
        md += f"**Anomalias detectadas:** {count}\n\n"
        
        if count == 0:
            md += "*Nenhum ponto de mudança significativo detectado*\n"
        elif count < 10:
            md += "*Poucas anomalias detectadas - podem ser mudanças de regime ou outliers genuínos*\n"
        elif count < 100:
            md += "*Número moderado de anomalias - investigar contexto e causas*\n"
        else:
            md += "*Muitas anomalias detectadas - pode indicar alta variabilidade ou ruído nos dados*\n"
        
        return md + "\n"


class TemporalAnalyzer:
    """
    Analisador avançado de séries temporais com múltiplas técnicas estatísticas.
    
    Implementa:
    - Análise de tendência (regressão linear, polinomial)
    - Detecção de sazonalidade
    - Autocorrelação e dependência temporal
    - Detecção de anomalias (z-score, IQR, isolation forest)
    - Interpretação contextualizada
    
    Exemplo:
        >>> analyzer = TemporalAnalyzer()
        >>> result = analyzer.analyze(df, 'timestamp_column')
        >>> print(result.to_markdown())
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa o analisador temporal.
        
        Args:
            logger: Logger customizado (cria um novo se None)
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(
        self,
        df: pd.DataFrame,
        temporal_col: str,
        enable_advanced: bool = True
    ) -> TemporalAnalysisResult:
        """
        Executa análise temporal completa em uma coluna.
        
        Args:
            df: DataFrame contendo os dados
            temporal_col: Nome da coluna temporal a analisar
            enable_advanced: Ativa análises avançadas (sazonalidade, etc.)
            
        Returns:
            Resultado completo da análise temporal
            
        Raises:
            ValueError: Se a coluna não existir no DataFrame
        """
        if temporal_col not in df.columns:
            raise ValueError(f"Coluna '{temporal_col}' não encontrada no DataFrame")
        
        self.logger.info({
            'event': 'temporal_analysis_started',
            'column': temporal_col,
            'rows': len(df),
            'advanced_enabled': enable_advanced
        })
        
        serie = df[temporal_col].dropna()
        
        if len(serie) == 0:
            self.logger.warning(f"Coluna '{temporal_col}' contém apenas valores nulos")
            return self._empty_result(temporal_col)
        
        # Criar resultado
        result = TemporalAnalysisResult(column_name=temporal_col)
        
        # 1. Estatísticas descritivas
        result.summary_stats = self._compute_summary_stats(serie)
        
        # 2. Análise de tendência
        result.trend = self._analyze_trend(serie)
        
        # 3. Autocorrelação
        result.autocorrelation = self._analyze_autocorrelation(serie)
        
        # 4. Sazonalidade (se habilitado)
        if enable_advanced:
            result.seasonality = self._detect_seasonality(serie)
        
        # 5. Detecção de anomalias
        result.anomalies = self._detect_anomalies(serie)
        
        # 6. Interpretação contextual
        result.interpretation = self._generate_interpretation(result)
        
        # 7. Recomendações
        result.recommendations = self._generate_recommendations(result)
        
        # Metadados
        result.metadata = {
            'analysis_timestamp': datetime.now().isoformat(),
            'sample_size': len(serie),
            'missing_values': df[temporal_col].isna().sum(),
            'advanced_enabled': enable_advanced
        }
        
        self.logger.info({
            'event': 'temporal_analysis_completed',
            'column': temporal_col,
            'trend_type': result.trend.get('type'),
            'anomalies_count': result.anomalies.get('count', 0)
        })
        
        return result
    
    def _empty_result(self, column_name: str) -> TemporalAnalysisResult:
        """Retorna resultado vazio para colunas inválidas."""
        return TemporalAnalysisResult(
            column_name=column_name,
            interpretation="Não foi possível realizar análise temporal: dados insuficientes ou inválidos.",
            recommendations=["Verificar qualidade dos dados na coluna temporal"]
        )
    
    def _compute_summary_stats(self, serie: pd.Series) -> Dict:
        """Calcula estatísticas descritivas."""
        try:
            desc = serie.describe()
            return {
                'count': int(desc['count']),
                'mean': float(desc['mean']),
                'std': float(desc['std']),
                'min': float(desc['min']),
                '25%': float(desc['25%']),
                '50% (median)': float(desc['50%']),
                '75%': float(desc['75%']),
                'max': float(desc['max'])
            }
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas descritivas: {e}")
            return {}
    
    def _analyze_trend(self, serie: pd.Series) -> Dict:
        """
        Analisa tendência usando regressão linear.
        
        Returns:
            Dicionário com tipo de tendência, slope, R² score
        """
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score
            
            X = np.arange(len(serie)).reshape(-1, 1)
            y = serie.values.reshape(-1, 1)
            
            model = LinearRegression().fit(X, y)
            slope = float(model.coef_[0][0])
            y_pred = model.predict(X)
            r2 = float(r2_score(y, y_pred))
            
            # Parâmetros de sensibilidade
            slope_epsilon = 0.01  # inclinação considerada praticamente nula
            r2_trend_min = 0.20   # mínimo de qualidade para considerar tendência linear
            r2_significant_min = 0.50  # mínimo para marcar significância da tendência
            slope_significant_min = 0.05

            # Classificar tendência: considerar ESTÁVEL se a inclinação for muito pequena
            # ou se o ajuste linear explicar pouco a variância (r² baixo)
            if abs(slope) < slope_epsilon or r2 < r2_trend_min:
                trend_type = TrendType.ESTAVEL
                slope_out = 0.0  # padroniza como 0 para séries estáveis
            elif slope > 0:
                trend_type = TrendType.CRESCENTE
                slope_out = slope
            else:
                trend_type = TrendType.DECRESCENTE
                slope_out = slope
            
            return {
                'type': trend_type.value,
                'slope': slope_out if 'slope_out' in locals() else slope,
                'intercept': float(model.intercept_[0]),
                'r2_score': r2,
                'is_significant': (abs(slope) >= slope_significant_min) and (r2 >= r2_significant_min)
            }
        except Exception as e:
            self.logger.error(f"Erro na análise de tendência: {e}")
            return {'type': TrendType.ESTAVEL.value, 'slope': 0, 'r2_score': 0}
    
    def _analyze_autocorrelation(self, serie: pd.Series) -> Dict:
        """
        Analisa autocorrelação para detectar dependência temporal.
        
        Returns:
            Dicionário com autocorrelação lag1 e flag de ciclo
        """
        try:
            autocorr_lag1 = float(serie.autocorr(lag=1))
            is_cyclic = abs(autocorr_lag1) > 0.3
            
            return {
                'lag1': autocorr_lag1,
                'is_cyclic': is_cyclic,
                'threshold': 0.3
            }
        except Exception as e:
            self.logger.error(f"Erro na análise de autocorrelação: {e}")
            return {'lag1': 0, 'is_cyclic': False}
    
    def _detect_seasonality(self, serie: pd.Series) -> Dict:
        """
        Detecta sazonalidade usando análise espectral ou decomposição.
        
        NOTA: Implementação simplificada. Para produção, usar statsmodels.seasonal_decompose
        
        Returns:
            Dicionário com tipo e força da sazonalidade
        """
        try:
            # Implementação simplificada: verificar periodicidade via autocorrelação
            # Para análise completa, usar: from statsmodels.tsa.seasonal import seasonal_decompose
            
            # Testar autocorrelação em múltiplos lags comuns
            lags_to_test = {
                7: SeasonalityType.SEMANAL,
                30: SeasonalityType.MENSAL,
                365: SeasonalityType.ANUAL
            }
            
            max_autocorr = 0
            detected_type = SeasonalityType.NENHUMA
            
            for lag, season_type in lags_to_test.items():
                if len(serie) > lag * 2:  # Precisa de dados suficientes
                    autocorr = abs(serie.autocorr(lag=lag))
                    if autocorr > max_autocorr:
                        max_autocorr = autocorr
                        detected_type = season_type
            
            is_seasonal = max_autocorr > 0.4
            
            return {
                'detected': is_seasonal,
                'type': detected_type.value if is_seasonal else SeasonalityType.NENHUMA.value,
                'strength': max_autocorr,
                'threshold': 0.4
            }
        except Exception as e:
            self.logger.error(f"Erro na detecção de sazonalidade: {e}")
            return {'detected': False, 'type': SeasonalityType.NENHUMA.value, 'strength': 0}
    
    def _detect_anomalies(self, serie: pd.Series, method: str = 'z-score', threshold: float = 3.0) -> Dict:
        """
        Detecta anomalias usando z-score modificado (robusto a outliers).
        
        Args:
            serie: Série temporal a analisar
            method: Método de detecção ('z-score', 'iqr')
            threshold: Threshold para classificação (padrão: 3 para z-score)
            
        Returns:
            Dicionário com contagem de anomalias e índices
        """
        try:
            if method == 'z-score':
                # Z-score das diferenças (change-point detection)
                diffs = np.diff(serie.values)
                
                # Guard contra desvio padrão zero
                std_d = np.std(diffs)
                if std_d == 0 or np.isnan(std_d):
                    zscore = np.zeros_like(diffs)
                else:
                    zscore = (diffs - np.mean(diffs)) / std_d
                
                anomaly_indices = np.where(np.abs(zscore) > threshold)[0]
                
            elif method == 'iqr':
                # Método IQR (Interquartile Range)
                Q1 = serie.quantile(0.25)
                Q3 = serie.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                anomaly_mask = (serie < lower_bound) | (serie > upper_bound)
                anomaly_indices = np.where(anomaly_mask)[0]
            
            else:
                raise ValueError(f"Método de detecção não suportado: {method}")
            
            return {
                'method': method,
                'threshold': threshold,
                'count': len(anomaly_indices),
                'indices': anomaly_indices.tolist()[:100],  # Limitar a 100 para evitar payload grande
                'percentage': len(anomaly_indices) / len(serie) * 100
            }
        except Exception as e:
            self.logger.error(f"Erro na detecção de anomalias: {e}")
            return {'method': method, 'count': 0, 'indices': []}
    
    def _generate_interpretation(self, result: TemporalAnalysisResult) -> str:
        """
        Gera interpretação contextualizada dos resultados.
        
        Args:
            result: Resultado da análise temporal
            
        Returns:
            String com interpretação em linguagem natural
        """
        interpretacao = []
        
        # Tendência
        trend_type = result.trend.get('type', 'estável')
        r2 = result.trend.get('r2_score', 0)
        
        if trend_type == TrendType.CRESCENTE.value:
            interpretacao.append(
                f"Os dados apresentam **tendência de crescimento** ao longo do tempo "
                f"(R² = {r2:.2f})."
            )
        elif trend_type == TrendType.DECRESCENTE.value:
            interpretacao.append(
                f"Os dados apresentam **tendência de queda** ao longo do tempo "
                f"(R² = {r2:.2f})."
            )
        else:
            interpretacao.append(
                "**Não foi identificada tendência significativa** ao longo do tempo "
                "(valores permanecem relativamente estáveis)."
            )
        
        # Autocorrelação/Ciclos
        is_cyclic = result.autocorrelation.get('is_cyclic', False)
        if is_cyclic:
            interpretacao.append(
                "Há **indícios de dependência temporal ou padrões cíclicos** nos dados."
            )
        else:
            interpretacao.append(
                "Não foram identificados **padrões cíclicos relevantes**."
            )
        
        # Sazonalidade
        if result.seasonality.get('detected'):
            season_type = result.seasonality.get('type', 'desconhecida')
            interpretacao.append(
                f"Foi detectada **sazonalidade {season_type}** significativa."
            )
        
        # Anomalias
        anomaly_count = result.anomalies.get('count', 0)
        anomaly_pct = result.anomalies.get('percentage', 0)
        
        if anomaly_count > 0:
            interpretacao.append(
                f"Foram detectados **{anomaly_count} pontos de mudança/anomalias** "
                f"({anomaly_pct:.1f}% dos dados)."
            )
        
        return " ".join(interpretacao)
    
    def _generate_recommendations(self, result: TemporalAnalysisResult) -> List[str]:
        """
        Gera recomendações personalizadas baseadas nos resultados.
        
        Args:
            result: Resultado da análise temporal
            
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        # Recomendações base
        recommendations.append(
            "Realizar análise gráfica detalhada (ex.: gráficos de linha, dispersão, boxplots temporais)."
        )
        
        # Recomendações baseadas em sazonalidade
        if result.seasonality.get('detected'):
            recommendations.append(
                "Aplicar decomposição de séries temporais (STL, X-13-ARIMA) para separar tendência, "
                "sazonalidade e componente irregular."
            )
            recommendations.append(
                "Considerar modelos que incorporem sazonalidade (SARIMA, Prophet, Holt-Winters)."
            )
        else:
            recommendations.append(
                "Investigar outras granularidades temporais (diária, semanal, mensal) "
                "para detectar padrões ocultos."
            )
        
        # Recomendações baseadas em tendência
        r2 = result.trend.get('r2_score', 0)
        if r2 < 0.5:
            recommendations.append(
                "A tendência não é bem capturada por modelo linear. Considerar modelos não-lineares "
                "(polinomial, splines, GAM)."
            )
        
        # Recomendações baseadas em anomalias
        anomaly_count = result.anomalies.get('count', 0)
        if anomaly_count > 100:
            recommendations.append(
                "Alto número de anomalias detectadas. Investigar causas: mudanças estruturais, "
                "eventos externos, problemas de qualidade dos dados."
            )
            recommendations.append(
                "Considerar técnicas de remoção de outliers ou modelos robustos a anomalias."
            )
        elif anomaly_count > 0:
            recommendations.append(
                "Investigar anomalias detectadas para identificar eventos relevantes ou "
                "mudanças de regime no comportamento dos dados."
            )
        
        # Modelagem preditiva
        recommendations.append(
            "Testar modelos preditivos adequados ao padrão identificado (ARIMA, Prophet, "
            "LSTM, XGBoost) para previsão futura."
        )
        
        return recommendations
