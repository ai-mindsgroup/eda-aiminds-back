"""
Análise de Clustering Modular - Agrupamentos e Segmentação

Módulo especializado em análise de clustering, detecção de
agrupamentos naturais nos dados.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 3.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import logging
from datetime import datetime


@dataclass
class ClusteringAnalysisResult:
    """
    Resultado de análise de clustering.
    
    Attributes:
        n_clusters: Número de clusters identificados
        cluster_labels: Labels de cluster para cada ponto
        cluster_distribution: Distribuição de pontos por cluster
        cluster_centers: Centros dos clusters
        cluster_stats: Estatísticas por cluster
        quality_metrics: Métricas de qualidade (silhouette, etc)
        interpretation: Interpretação contextual
        recommendations: Próximos passos sugeridos
        metadata: Metadados adicionais
    """
    n_clusters: int = 0
    cluster_labels: Optional[np.ndarray] = None
    cluster_distribution: Dict[int, int] = field(default_factory=dict)
    cluster_centers: Optional[np.ndarray] = None
    cluster_stats: Dict[int, Dict] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Gera relatório formatado em Markdown."""
        md = f"# Análise de Clustering ({self.n_clusters} Clusters)\n\n"
        
        if self.cluster_distribution:
            md += "## Distribuição de Pontos por Cluster\n\n"
            total = sum(self.cluster_distribution.values())
            for cluster_id in sorted(self.cluster_distribution.keys()):
                count = self.cluster_distribution[cluster_id]
                percentage = count / total * 100
                md += f"- **Cluster {cluster_id}:** {count:,} pontos ({percentage:.1f}%)\n"
            md += "\n"
        
        if self.quality_metrics:
            md += "## Métricas de Qualidade\n\n"
            for metric, value in self.quality_metrics.items():
                md += f"- **{metric}:** {value:.4f}\n"
            md += "\n"
        
        if self.cluster_stats:
            md += "## Estatísticas por Cluster\n\n"
            for cluster_id in sorted(self.cluster_stats.keys()):
                stats = self.cluster_stats[cluster_id]
                md += f"### Cluster {cluster_id}\n\n"
                for stat_name, stat_value in stats.items():
                    md += f"- **{stat_name}:** {stat_value}\n"
                md += "\n"
        
        if self.interpretation:
            md += "## Interpretação\n\n"
            md += self.interpretation + "\n\n"
        
        if self.recommendations:
            md += "## Próximos Passos Recomendados\n\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
        
        return md


class ClusteringAnalyzer:
    """
    Analisador modular de clustering.
    
    Fornece análises de agrupamentos usando algoritmos como KMeans,
    DBSCAN, etc.
    
    Exemplo:
        >>> analyzer = ClusteringAnalyzer()
        >>> result = analyzer.analyze(df, n_clusters=3, method='kmeans')
        >>> print(result.to_markdown())
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa analisador de clustering.
        
        Args:
            logger: Logger opcional
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(
        self,
        df: pd.DataFrame,
        n_clusters: int = 3,
        method: str = 'kmeans',
        features: Optional[List[str]] = None,
        scale_features: bool = True
    ) -> ClusteringAnalysisResult:
        """
        Executa análise de clustering.
        
        Args:
            df: DataFrame a analisar
            n_clusters: Número de clusters (para KMeans)
            method: Método de clustering ('kmeans', 'dbscan', 'hierarchical')
            features: Features específicas (None = todas numéricas)
            scale_features: Se deve escalar features antes do clustering
            
        Returns:
            Resultado completo da análise
        """
        try:
            self.logger.info(f"Iniciando análise de clustering (método: {method})...")
            
            # Selecionar features
            if features is None:
                features = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Validar features
            features = [f for f in features if f in df.columns]
            if not features:
                raise ValueError("Nenhuma feature numérica encontrada")
            
            # Preparar dados
            X = df[features].copy()
            
            # Remover NaNs
            X = X.dropna()
            
            if len(X) == 0:
                raise ValueError("Nenhum dado válido após remoção de NaNs")
            
            # Escalar features
            if scale_features:
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
            else:
                X_scaled = X.values
            
            # Executar clustering
            if method.lower() == 'kmeans':
                labels, centers = self._kmeans_clustering(X_scaled, n_clusters)
            elif method.lower() == 'dbscan':
                labels, centers = self._dbscan_clustering(X_scaled)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            elif method.lower() == 'hierarchical':
                labels, centers = self._hierarchical_clustering(X_scaled, n_clusters)
            else:
                raise ValueError(f"Método desconhecido: {method}")
            
            # Construir resultado
            result = ClusteringAnalysisResult()
            result.n_clusters = n_clusters
            result.cluster_labels = labels
            result.cluster_centers = centers
            
            # Distribuição
            unique, counts = np.unique(labels, return_counts=True)
            result.cluster_distribution = dict(zip(unique.tolist(), counts.tolist()))
            
            # Estatísticas por cluster
            result.cluster_stats = self._compute_cluster_stats(X, labels, features)
            
            # Métricas de qualidade
            result.quality_metrics = self._compute_quality_metrics(X_scaled, labels)
            
            # Interpretação
            result.interpretation = self._generate_interpretation(result)
            
            # Recomendações
            result.recommendations = self._generate_recommendations(result)
            
            # Metadados
            result.metadata = {
                "method": method,
                "features_used": features,
                "total_features": len(features),
                "total_points": len(X),
                "scaled": scale_features,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Clustering concluído: {n_clusters} clusters identificados")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na análise de clustering: {e}", exc_info=True)
            raise
    
    def _kmeans_clustering(self, X: np.ndarray, n_clusters: int):
        """Executa KMeans clustering."""
        from sklearn.cluster import KMeans
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        centers = kmeans.cluster_centers_
        
        return labels, centers
    
    def _dbscan_clustering(self, X: np.ndarray):
        """Executa DBSCAN clustering."""
        from sklearn.cluster import DBSCAN
        
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        labels = dbscan.fit_predict(X)
        
        # DBSCAN não tem centros pré-calculados
        # Calcular centros manualmente
        unique_labels = set(labels)
        centers = []
        for label in unique_labels:
            if label != -1:  # Ignorar noise
                cluster_points = X[labels == label]
                center = cluster_points.mean(axis=0)
                centers.append(center)
        
        return labels, np.array(centers) if centers else None
    
    def _hierarchical_clustering(self, X: np.ndarray, n_clusters: int):
        """Executa clustering hierárquico."""
        from sklearn.cluster import AgglomerativeClustering
        
        hierarchical = AgglomerativeClustering(n_clusters=n_clusters)
        labels = hierarchical.fit_predict(X)
        
        # Calcular centros manualmente
        centers = []
        for label in range(n_clusters):
            cluster_points = X[labels == label]
            center = cluster_points.mean(axis=0)
            centers.append(center)
        
        return labels, np.array(centers)
    
    def _compute_cluster_stats(
        self,
        X: pd.DataFrame,
        labels: np.ndarray,
        features: List[str]
    ) -> Dict:
        """Calcula estatísticas por cluster."""
        stats = {}
        
        for cluster_id in np.unique(labels):
            if cluster_id == -1:  # Noise em DBSCAN
                continue
            
            cluster_data = X[labels == cluster_id]
            
            stats[int(cluster_id)] = {
                'size': len(cluster_data),
                'percentage': f"{len(cluster_data) / len(X) * 100:.1f}%",
                'mean_values': cluster_data[features].mean().to_dict()
            }
        
        return stats
    
    def _compute_quality_metrics(self, X: np.ndarray, labels: np.ndarray) -> Dict:
        """Calcula métricas de qualidade do clustering."""
        metrics = {}
        
        try:
            from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
            
            # Silhouette Score (quanto maior, melhor)
            if len(set(labels)) > 1:
                metrics['silhouette_score'] = float(silhouette_score(X, labels))
                
                # Davies-Bouldin Index (quanto menor, melhor)
                metrics['davies_bouldin_index'] = float(davies_bouldin_score(X, labels))
                
                # Calinski-Harabasz Index (quanto maior, melhor)
                metrics['calinski_harabasz_index'] = float(calinski_harabasz_score(X, labels))
        
        except Exception as e:
            self.logger.warning(f"Erro ao calcular métricas de qualidade: {e}")
        
        return metrics
    
    def _generate_interpretation(self, result: ClusteringAnalysisResult) -> str:
        """Gera interpretação contextual."""
        interpretation = []
        
        # Análise de balanceamento
        if result.cluster_distribution:
            total = sum(result.cluster_distribution.values())
            sizes = list(result.cluster_distribution.values())
            
            max_size = max(sizes)
            min_size = min(sizes)
            ratio = max_size / min_size if min_size > 0 else float('inf')
            
            if ratio > 5:
                interpretation.append(
                    f"Os clusters são **desbalanceados** (razão {ratio:.1f}:1 entre maior e menor). "
                    "O maior cluster domina a distribuição."
                )
            else:
                interpretation.append(
                    f"Os clusters são **balanceados** (razão {ratio:.1f}:1 entre maior e menor)."
                )
        
        # Análise de qualidade
        if result.quality_metrics.get('silhouette_score'):
            silhouette = result.quality_metrics['silhouette_score']
            
            if silhouette > 0.7:
                quality = "excelente"
            elif silhouette > 0.5:
                quality = "boa"
            elif silhouette > 0.3:
                quality = "razoável"
            else:
                quality = "fraca"
            
            interpretation.append(
                f"A qualidade da separação entre clusters é **{quality}** "
                f"(silhouette score: {silhouette:.2f})."
            )
        
        return " ".join(interpretation) if interpretation else \
            f"Foram identificados {result.n_clusters} agrupamentos distintos nos dados."
    
    def _generate_recommendations(self, result: ClusteringAnalysisResult) -> List[str]:
        """Gera recomendações de próximos passos."""
        recommendations = []
        
        # Recomendações baseadas em qualidade
        if result.quality_metrics.get('silhouette_score', 0) < 0.5:
            recommendations.append(
                "Experimente diferentes números de clusters para melhorar a separação"
            )
        
        # Recomendações baseadas em balanceamento
        if result.cluster_distribution:
            sizes = list(result.cluster_distribution.values())
            ratio = max(sizes) / min(sizes) if min(sizes) > 0 else float('inf')
            
            if ratio > 10:
                recommendations.append(
                    "Considere usar DBSCAN para identificar outliers e clusters de densidade variável"
                )
        
        # Recomendação padrão
        recommendations.append(
            "Visualize clusters em 2D/3D usando PCA para entender melhor a separação"
        )
        
        recommendations.append(
            "Analise características estatísticas de cada cluster para interpretação de perfis"
        )
        
        return recommendations
