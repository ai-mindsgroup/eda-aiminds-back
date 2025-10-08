"""Módulo para geração de visualizações gráficas para análise de dados.

Este módulo fornece ferramentas para criar gráficos e visualizações
usando Matplotlib, Seaborn e Plotly para enriquecer respostas dos agentes.
"""
import io
import base64
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px

from src.utils.logging_config import get_logger

logger = get_logger("tools.graph_generator")

# Configuração de estilo padrão
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 100


class GraphGeneratorError(Exception):
    """Exceção para erros na geração de gráficos."""
    pass


class GraphGenerator:
    """
    Gerador de visualizações gráficas para análise exploratória de dados.
    
    Suporta:
    - Histogramas
    - Gráficos de dispersão (scatter plots)
    - Boxplots
    - Gráficos de barras
    - Gráficos de linhas
    - Heatmaps de correlação
    - E mais...
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa o gerador de gráficos.
        Args:
            output_dir: Diretório para salvar gráficos (None = usa settings.HISTOGRAMS_DIR)
        """
        if output_dir is None:
            try:
                from src.settings import HISTOGRAMS_DIR
                output_dir = Path(HISTOGRAMS_DIR)
            except Exception:
                output_dir = Path("outputs/histogramas")
        self.output_dir = output_dir
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger("graph_generator")
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def _save_or_encode(self, fig, filename: Optional[str] = None,
                       return_base64: bool = True) -> Optional[str]:
        """
        Salva gráfico em arquivo ou retorna como base64.
        
        Args:
            fig: Figura do matplotlib
            filename: Nome do arquivo (se None, gera timestamp)
            return_base64: Se True, retorna string base64
            
        Returns:
            String base64 da imagem ou caminho do arquivo
        """
        try:
            if return_base64:
                # Converte para base64
                buf = io.BytesIO()
                fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                buf.seek(0)
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()
                plt.close(fig)
                return f"data:image/png;base64,{img_base64}"
            
            # Salva em arquivo
            if not filename:
                filename = f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            filepath = self.output_dir / filename if self.output_dir else Path(filename)
            fig.savefig(filepath, bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            self.logger.info(f"Gráfico salvo: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar gráfico: {e}")
            plt.close(fig)
            raise GraphGeneratorError(f"Falha ao salvar gráfico: {e}")
    
    def _validate_data(self, data: Union[pd.DataFrame, pd.Series, np.ndarray],
                      columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Valida e converte dados para DataFrame.
        
        Args:
            data: Dados de entrada
            columns: Colunas esperadas
            
        Returns:
            DataFrame validado
        """
        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, pd.Series):
            df = data.to_frame()
        elif isinstance(data, np.ndarray):
            df = pd.DataFrame(data, columns=columns)
        else:
            raise GraphGeneratorError(f"Tipo de dados não suportado: {type(data)}")
        
        if columns:
            missing = [col for col in columns if col not in df.columns]
            if missing:
                raise GraphGeneratorError(f"Colunas ausentes: {missing}")
        
        return df
    
    # ========================================================================
    # HISTOGRAMAS
    # ========================================================================
    
    def histogram(self, data: Union[pd.DataFrame, pd.Series, np.ndarray],
                 column: Optional[str] = None,
                 bins: int = 30,
                 title: Optional[str] = None,
                 xlabel: Optional[str] = None,
                 ylabel: str = "Frequência",
                 color: str = "skyblue",
                 kde: bool = True,
                 return_base64: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Cria um histograma da distribuição de dados.
        
        Args:
            data: Dados para plotar
            column: Nome da coluna (se DataFrame)
            bins: Número de bins
            title: Título do gráfico
            xlabel: Rótulo do eixo X
            ylabel: Rótulo do eixo Y
            color: Cor das barras
            kde: Se True, adiciona curva KDE
            return_base64: Se True, retorna base64
            
        Returns:
            Tuple (imagem/caminho, estatísticas)
        """
        try:
            df = self._validate_data(data, [column] if column else None)
            
            if column:
                values = df[column].dropna()
            else:
                values = df.iloc[:, 0].dropna()
            
            # Calcula estatísticas
            stats = {
                "count": len(values),
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
                "q25": float(values.quantile(0.25)),
                "q75": float(values.quantile(0.75))
            }
            
            # Cria gráfico
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if kde:
                sns.histplot(values, bins=bins, kde=True, color=color, ax=ax)
            else:
                ax.hist(values, bins=bins, color=color, edgecolor='black', alpha=0.7)
            
            ax.set_title(title or f"Distribuição de {column or 'Dados'}", fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel or (column if column else "Valor"), fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            
            # Adiciona linha de média
            ax.axvline(stats['mean'], color='red', linestyle='--', linewidth=2, label=f"Média: {stats['mean']:.2f}")
            ax.axvline(stats['median'], color='green', linestyle='--', linewidth=2, label=f"Mediana: {stats['median']:.2f}")
            ax.legend()
            
            plt.tight_layout()
            
            img = self._save_or_encode(fig, return_base64=return_base64)
            
            self.logger.info(f"Histograma criado: {column or 'dados'}")
            return img, stats
            
        except Exception as e:
            self.logger.error(f"Erro ao criar histograma: {e}")
            raise GraphGeneratorError(f"Falha ao criar histograma: {e}")
    
    # ========================================================================
    # SCATTER PLOTS
    # ========================================================================
    
    def scatter_plot(self, data: pd.DataFrame,
                    x_column: str,
                    y_column: str,
                    hue_column: Optional[str] = None,
                    title: Optional[str] = None,
                    xlabel: Optional[str] = None,
                    ylabel: Optional[str] = None,
                    size: int = 50,
                    alpha: float = 0.6,
                    return_base64: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Cria gráfico de dispersão (scatter plot).
        
        Args:
            data: DataFrame com os dados
            x_column: Coluna para eixo X
            y_column: Coluna para eixo Y
            hue_column: Coluna para colorir pontos
            title: Título do gráfico
            xlabel: Rótulo do eixo X
            ylabel: Rótulo do eixo Y
            size: Tamanho dos pontos
            alpha: Transparência
            return_base64: Se True, retorna base64
            
        Returns:
            Tuple (imagem/caminho, estatísticas)
        """
        try:
            df = self._validate_data(data, [x_column, y_column])
            
            # Remove NaN
            plot_data = df[[x_column, y_column]].dropna()
            
            # Calcula correlação
            correlation = plot_data[x_column].corr(plot_data[y_column])
            
            stats = {
                "correlation": float(correlation),
                "n_points": len(plot_data),
                "x_mean": float(plot_data[x_column].mean()),
                "y_mean": float(plot_data[y_column].mean())
            }
            
            # Cria gráfico
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if hue_column and hue_column in df.columns:
                sns.scatterplot(data=df, x=x_column, y=y_column, hue=hue_column,
                              s=size, alpha=alpha, ax=ax)
            else:
                ax.scatter(plot_data[x_column], plot_data[y_column],
                          s=size, alpha=alpha, color='steelblue')
            
            ax.set_title(title or f"{y_column} vs {x_column}", fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel or x_column, fontsize=12)
            ax.set_ylabel(ylabel or y_column, fontsize=12)
            
            # Adiciona linha de tendência
            z = np.polyfit(plot_data[x_column], plot_data[y_column], 1)
            p = np.poly1d(z)
            ax.plot(plot_data[x_column], p(plot_data[x_column]), "r--", alpha=0.8,
                   label=f"Correlação: {correlation:.3f}")
            ax.legend()
            
            plt.tight_layout()
            
            img = self._save_or_encode(fig, return_base64=return_base64)
            
            self.logger.info(f"Scatter plot criado: {y_column} vs {x_column}")
            return img, stats
            
        except Exception as e:
            self.logger.error(f"Erro ao criar scatter plot: {e}")
            raise GraphGeneratorError(f"Falha ao criar scatter plot: {e}")
    
    # ========================================================================
    # BOXPLOTS
    # ========================================================================
    
    def boxplot(self, data: Union[pd.DataFrame, pd.Series],
               column: Optional[str] = None,
               group_by: Optional[str] = None,
               title: Optional[str] = None,
               xlabel: Optional[str] = None,
               ylabel: Optional[str] = None,
               return_base64: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Cria boxplot para visualizar distribuição e outliers.
        
        Args:
            data: Dados para plotar
            column: Nome da coluna (se DataFrame)
            group_by: Coluna para agrupar
            title: Título do gráfico
            xlabel: Rótulo do eixo X
            ylabel: Rótulo do eixo Y
            return_base64: Se True, retorna base64
            
        Returns:
            Tuple (imagem/caminho, estatísticas)
        """
        try:
            df = self._validate_data(data, [column, group_by] if column and group_by else [column] if column else None)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if group_by and group_by in df.columns:
                sns.boxplot(data=df, x=group_by, y=column, ax=ax)
            else:
                col_data = df[column] if column else df.iloc[:, 0]
                sns.boxplot(y=col_data, ax=ax)
            
            ax.set_title(title or f"Boxplot de {column or 'Dados'}", fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel or (group_by if group_by else ""), fontsize=12)
            ax.set_ylabel(ylabel or (column if column else "Valor"), fontsize=12)
            
            plt.tight_layout()
            
            # Calcula estatísticas
            col_data = df[column] if column else df.iloc[:, 0]
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1
            outliers = col_data[(col_data < q1 - 1.5 * iqr) | (col_data > q3 + 1.5 * iqr)]
            
            stats = {
                "q1": float(q1),
                "median": float(col_data.median()),
                "q3": float(q3),
                "iqr": float(iqr),
                "outliers_count": len(outliers),
                "outliers_percentage": float(len(outliers) / len(col_data) * 100)
            }
            
            img = self._save_or_encode(fig, return_base64=return_base64)
            
            self.logger.info(f"Boxplot criado: {column or 'dados'}")
            return img, stats
            
        except Exception as e:
            self.logger.error(f"Erro ao criar boxplot: {e}")
            raise GraphGeneratorError(f"Falha ao criar boxplot: {e}")
    
    # ========================================================================
    # GRÁFICOS DE BARRAS
    # ========================================================================
    
    def bar_chart(self, data: Union[pd.DataFrame, Dict[str, Any]],
                 x_column: Optional[str] = None,
                 y_column: Optional[str] = None,
                 title: Optional[str] = None,
                 xlabel: Optional[str] = None,
                 ylabel: Optional[str] = None,
                 color: str = "steelblue",
                 horizontal: bool = False,
                 return_base64: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Cria gráfico de barras.
        
        Args:
            data: DataFrame ou dicionário
            x_column: Coluna para eixo X
            y_column: Coluna para eixo Y
            title: Título do gráfico
            xlabel: Rótulo do eixo X
            ylabel: Rótulo do eixo Y
            color: Cor das barras
            horizontal: Se True, cria barras horizontais
            return_base64: Se True, retorna base64
            
        Returns:
            Tuple (imagem/caminho, estatísticas)
        """
        try:
            if isinstance(data, dict):
                df = pd.DataFrame(list(data.items()), columns=['category', 'value'])
                x_column = 'category'
                y_column = 'value'
            else:
                df = self._validate_data(data, [x_column, y_column] if x_column and y_column else None)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if horizontal:
                ax.barh(df[x_column], df[y_column], color=color, edgecolor='black', alpha=0.7)
            else:
                ax.bar(df[x_column], df[y_column], color=color, edgecolor='black', alpha=0.7)
            
            ax.set_title(title or f"{y_column} por {x_column}", fontsize=14, fontweight='bold')
            ax.set_xlabel(xlabel or (y_column if horizontal else x_column), fontsize=12)
            ax.set_ylabel(ylabel or (x_column if horizontal else y_column), fontsize=12)
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            stats = {
                "total": float(df[y_column].sum()),
                "mean": float(df[y_column].mean()),
                "max": float(df[y_column].max()),
                "max_category": str(df.loc[df[y_column].idxmax(), x_column])
            }
            
            img = self._save_or_encode(fig, return_base64=return_base64)
            
            self.logger.info(f"Gráfico de barras criado")
            return img, stats
            
        except Exception as e:
            self.logger.error(f"Erro ao criar gráfico de barras: {e}")
            raise GraphGeneratorError(f"Falha ao criar gráfico de barras: {e}")
    
    # ========================================================================
    # HEATMAP DE CORRELAÇÃO
    # ========================================================================
    
    def correlation_heatmap(self, data: pd.DataFrame,
                          columns: Optional[List[str]] = None,
                          title: Optional[str] = None,
                          annot: bool = True,
                          cmap: str = "coolwarm",
                          return_base64: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Cria heatmap de correlação entre variáveis.
        
        Args:
            data: DataFrame com os dados
            columns: Colunas para incluir (None = todas numéricas)
            title: Título do gráfico
            annot: Se True, mostra valores
            cmap: Paleta de cores
            return_base64: Se True, retorna base64
            
        Returns:
            Tuple (imagem/caminho, estatísticas)
        """
        try:
            df = self._validate_data(data)
            
            # Seleciona apenas colunas numéricas
            if columns:
                numeric_df = df[columns].select_dtypes(include=[np.number])
            else:
                numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                raise GraphGeneratorError("Nenhuma coluna numérica encontrada")
            
            # Calcula correlação
            corr_matrix = numeric_df.corr()
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            sns.heatmap(corr_matrix, annot=annot, cmap=cmap, center=0,
                       square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
            
            ax.set_title(title or "Matriz de Correlação", fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            # Encontra correlações mais fortes
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_pairs.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': float(corr_matrix.iloc[i, j])
                    })
            
            corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            stats = {
                "n_variables": len(corr_matrix),
                "strongest_positive": corr_pairs[0] if corr_pairs else None,
                "strongest_negative": min(corr_pairs, key=lambda x: x['correlation']) if corr_pairs else None,
                "mean_correlation": float(corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean())
            }
            
            img = self._save_or_encode(fig, return_base64=return_base64)
            
            self.logger.info(f"Heatmap de correlação criado")
            return img, stats
            
        except Exception as e:
            self.logger.error(f"Erro ao criar heatmap: {e}")
            raise GraphGeneratorError(f"Falha ao criar heatmap: {e}")


def detect_visualization_need(query: str) -> Optional[str]:
    """
    Detecta se a query do usuário requer visualização gráfica.
    
    Args:
        query: Pergunta do usuário
        
    Returns:
        Tipo de gráfico necessário ou None
    """
    query_lower = query.lower()
    
    keywords_map = {
        'histogram': ['histograma', 'distribuição', 'frequência', 'histogram'],
        'scatter': ['dispersão', 'scatter', 'correlação', 'relação entre'],
        'boxplot': ['boxplot', 'outliers', 'quartis', 'box plot'],
        'bar': ['barras', 'bar chart', 'gráfico de barras', 'comparação'],
        'heatmap': ['heatmap', 'mapa de calor', 'correlações', 'matriz de correlação']
    }
    
    for graph_type, keywords in keywords_map.items():
        if any(keyword in query_lower for keyword in keywords):
            return graph_type
    
    # Palavras genéricas que indicam necessidade de visualização
    viz_keywords = ['mostre', 'visualize', 'gráfico', 'plote', 'desenhe', 'exiba']
    if any(keyword in query_lower for keyword in viz_keywords):
        return 'auto'  # Detectar automaticamente baseado nos dados
    
    return None
