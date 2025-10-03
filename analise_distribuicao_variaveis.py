#!/usr/bin/env python3
"""
Análise de Distribuição de Variáveis
Acessa Supabase, lê chunk_text e gera histogramas/distribuições
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.tools.python_analyzer import PythonDataAnalyzer
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Configurar estilo dos gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def gerar_histogramas(df, output_dir='outputs/histogramas'):
    """Gera histogramas para todas as variáveis numéricas"""
    
    # Criar diretório de saída
    os.makedirs(output_dir, exist_ok=True)
    
    # Separar variáveis numéricas e categóricas
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    logger.info(f"📊 Gerando histogramas para {len(numeric_cols)} variáveis numéricas")
    logger.info(f"📊 Gerando gráficos de barras para {len(categorical_cols)} variáveis categóricas")
    
    resultados = {
        'numeric_cols': numeric_cols,
        'categorical_cols': categorical_cols,
        'graficos_gerados': [],
        'estatisticas': {}
    }
    
    # Histogramas para variáveis numéricas
    for col in numeric_cols:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Histograma
            ax.hist(df[col].dropna(), bins=50, alpha=0.7, color='steelblue', edgecolor='black')
            
            # Estatísticas
            mean_val = df[col].mean()
            median_val = df[col].median()
            std_val = df[col].std()
            
            # Linhas de referência
            ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Média: {mean_val:.2f}')
            ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Mediana: {median_val:.2f}')
            
            ax.set_xlabel(col, fontsize=12)
            ax.set_ylabel('Frequência', fontsize=12)
            ax.set_title(f'Distribuição de {col}', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Salvar
            filename = f'{output_dir}/hist_{col}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            resultados['graficos_gerados'].append(filename)
            resultados['estatisticas'][col] = {
                'mean': mean_val,
                'median': median_val,
                'std': std_val,
                'min': df[col].min(),
                'max': df[col].max(),
                'count': df[col].count(),
                'missing': df[col].isna().sum()
            }
            
            logger.info(f"✅ Histograma gerado: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar histograma para {col}: {e}")
    
    # Gráficos de barras para variáveis categóricas
    for col in categorical_cols:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Contagem de valores
            value_counts = df[col].value_counts()
            
            # Gráfico de barras
            value_counts.plot(kind='bar', ax=ax, color='coral', edgecolor='black', alpha=0.7)
            
            ax.set_xlabel(col, fontsize=12)
            ax.set_ylabel('Frequência', fontsize=12)
            ax.set_title(f'Distribuição de {col}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Rotacionar labels se necessário
            plt.xticks(rotation=45, ha='right')
            
            # Salvar
            filename = f'{output_dir}/bar_{col}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            resultados['graficos_gerados'].append(filename)
            resultados['estatisticas'][col] = {
                'unique_values': df[col].nunique(),
                'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
                'most_common_count': value_counts.values[0] if len(value_counts) > 0 else 0,
                'count': df[col].count(),
                'missing': df[col].isna().sum()
            }
            
            logger.info(f"✅ Gráfico de barras gerado: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico para {col}: {e}")
    
    return resultados

def gerar_relatorio(df, resultados):
    """Gera relatório textual sobre as distribuições"""
    
    relatorio = []
    relatorio.append("=" * 80)
    relatorio.append("ANÁLISE DE DISTRIBUIÇÃO DAS VARIÁVEIS")
    relatorio.append("=" * 80)
    relatorio.append("")
    relatorio.append(f"📊 Dataset: {df.shape[0]} registros, {df.shape[1]} colunas")
    relatorio.append("")
    
    # Variáveis numéricas
    relatorio.append("🔢 VARIÁVEIS NUMÉRICAS:")
    relatorio.append("-" * 80)
    for col in resultados['numeric_cols']:
        if col in resultados['estatisticas']:
            stats = resultados['estatisticas'][col]
            relatorio.append(f"\n{col}:")
            relatorio.append(f"  - Média: {stats['mean']:.4f}")
            relatorio.append(f"  - Mediana: {stats['median']:.4f}")
            relatorio.append(f"  - Desvio Padrão: {stats['std']:.4f}")
            relatorio.append(f"  - Min: {stats['min']:.4f}")
            relatorio.append(f"  - Max: {stats['max']:.4f}")
            relatorio.append(f"  - Valores válidos: {stats['count']}")
            relatorio.append(f"  - Valores faltantes: {stats['missing']}")
    
    relatorio.append("")
    relatorio.append("")
    
    # Variáveis categóricas
    relatorio.append("📑 VARIÁVEIS CATEGÓRICAS:")
    relatorio.append("-" * 80)
    for col in resultados['categorical_cols']:
        if col in resultados['estatisticas']:
            stats = resultados['estatisticas'][col]
            relatorio.append(f"\n{col}:")
            relatorio.append(f"  - Valores únicos: {stats['unique_values']}")
            relatorio.append(f"  - Valor mais comum: {stats['most_common']}")
            relatorio.append(f"  - Frequência do mais comum: {stats['most_common_count']}")
            relatorio.append(f"  - Valores válidos: {stats['count']}")
            relatorio.append(f"  - Valores faltantes: {stats['missing']}")
    
    relatorio.append("")
    relatorio.append("")
    relatorio.append("📁 GRÁFICOS GERADOS:")
    relatorio.append("-" * 80)
    for grafico in resultados['graficos_gerados']:
        relatorio.append(f"  - {grafico}")
    
    relatorio.append("")
    relatorio.append("=" * 80)
    
    return "\n".join(relatorio)

def main():
    """Função principal"""
    
    logger.info("🚀 Iniciando análise de distribuição de variáveis")
    logger.info("📊 Acessando Supabase e reconstruindo DataFrame...")
    
    # Inicializar analyzer
    analyzer = PythonDataAnalyzer(caller_agent='test_system')
    
    # Reconstruir dados originais do Supabase
    df = analyzer.reconstruct_original_data()
    
    if df is None:
        logger.error("❌ Falha ao reconstruir DataFrame da tabela embeddings")
        return
    
    logger.info(f"✅ DataFrame reconstruído: {df.shape[0]} linhas, {df.shape[1]} colunas")
    logger.info(f"📋 Colunas: {list(df.columns)}")
    
    # Gerar histogramas
    logger.info("📊 Gerando histogramas e gráficos de distribuição...")
    resultados = gerar_histogramas(df)
    
    # Gerar relatório
    relatorio = gerar_relatorio(df, resultados)
    
    # Exibir relatório
    print("\n")
    print(relatorio)
    
    # Salvar relatório
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/relatorio_distribuicao.txt', 'w', encoding='utf-8') as f:
        f.write(relatorio)
    
    logger.info("✅ Relatório salvo em: outputs/relatorio_distribuicao.txt")
    logger.info(f"✅ Total de gráficos gerados: {len(resultados['graficos_gerados'])}")
    logger.info("🎉 Análise concluída com sucesso!")

if __name__ == "__main__":
    main()
