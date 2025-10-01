"""Exemplo de uso do sistema de visualização gráfica.

Este script demonstra as capacidades de visualização automática
do sistema EDA AI Minds, incluindo:
- Histogramas com estatísticas
- Scatter plots com correlação
- Boxplots com detecção de outliers
- Gráficos de barras
- Heatmaps de correlação

Utiliza dados de fraude de cartão de crédito do Kaggle.
"""
import sys
from pathlib import Path

# Adiciona root ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pandas as pd
import numpy as np
from src.tools.graph_generator import GraphGenerator, detect_visualization_need
from src.utils.logging_config import get_logger

logger = get_logger("examples.visualizacao")


def exemplo_histograma():
    """Demonstra criação de histograma com estatísticas."""
    print("\n" + "="*80)
    print("📊 EXEMPLO 1: HISTOGRAMA")
    print("="*80 + "\n")
    
    # Carregar dados
    data_path = root_dir / "data" / "creditcard_test_500.csv"
    
    if not data_path.exists():
        print(f"❌ Arquivo não encontrado: {data_path}")
        print("💡 Certifique-se de ter o arquivo creditcard_test_500.csv em data/")
        return
    
    df = pd.read_csv(data_path)
    
    # Criar gerador
    generator = GraphGenerator(output_dir=root_dir / "temp" / "visualizations")
    
    # Gerar histograma da coluna Amount
    print("Gerando histograma da coluna 'Amount'...")
    img, stats = generator.histogram(
        data=df,
        column="Amount",
        bins=50,
        title="Distribuição de Valores de Transações",
        xlabel="Valor da Transação (€)",
        kde=True,
        return_base64=False  # Salvar em arquivo
    )
    
    print("\n✅ Histograma gerado com sucesso!")
    print(f"\n📈 Estatísticas:")
    print(f"  • Contagem: {stats['count']}")
    print(f"  • Média: €{stats['mean']:.2f}")
    print(f"  • Mediana: €{stats['median']:.2f}")
    print(f"  • Desvio Padrão: €{stats['std']:.2f}")
    print(f"  • Mínimo: €{stats['min']:.2f}")
    print(f"  • Máximo: €{stats['max']:.2f}")
    print(f"  • Q1 (25%): €{stats['q25']:.2f}")
    print(f"  • Q3 (75%): €{stats['q75']:.2f}")
    
    if img.startswith("data:image"):
        print(f"\n🖼️ Imagem em base64 (primeiros 100 caracteres): {img[:100]}...")
    else:
        print(f"\n🖼️ Imagem salva em: {img}")


def exemplo_scatter():
    """Demonstra criação de scatter plot com correlação."""
    print("\n" + "="*80)
    print("📊 EXEMPLO 2: SCATTER PLOT")
    print("="*80 + "\n")
    
    data_path = root_dir / "data" / "creditcard_test_500.csv"
    
    if not data_path.exists():
        print(f"❌ Arquivo não encontrado: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    generator = GraphGenerator(output_dir=root_dir / "temp" / "visualizations")
    
    # Gerar scatter plot entre V1 e V2
    print("Gerando scatter plot entre 'V1' e 'V2'...")
    img, stats = generator.scatter_plot(
        data=df,
        x_column="V1",
        y_column="V2",
        hue_column="Class",
        title="Relação entre V1 e V2 (Colorido por Classe)",
        size=30,
        return_base64=False  # Salvar em arquivo
    )
    
    print("\n✅ Scatter plot gerado com sucesso!")
    print(f"\n📈 Estatísticas:")
    print(f"  • Correlação: {stats['correlation']:.4f}")
    print(f"  • Número de pontos: {stats['n_points']}")
    print(f"  • Média X (V1): {stats['x_mean']:.4f}")
    print(f"  • Média Y (V2): {stats['y_mean']:.4f}")
    
    if img.startswith("data:image"):
        print(f"\n🖼️ Imagem em base64 gerada")
    else:
        print(f"\n🖼️ Imagem salva em: {img}")


def exemplo_boxplot():
    """Demonstra criação de boxplot com detecção de outliers."""
    print("\n" + "="*80)
    print("📊 EXEMPLO 3: BOXPLOT")
    print("="*80 + "\n")
    
    data_path = root_dir / "data" / "creditcard_test_500.csv"
    
    if not data_path.exists():
        print(f"❌ Arquivo não encontrado: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    generator = GraphGenerator(output_dir=root_dir / "temp" / "visualizations")
    
    # Gerar boxplot da coluna Time
    print("Gerando boxplot da coluna 'Time'...")
    img, stats = generator.boxplot(
        data=df,
        column="Time",
        title="Boxplot: Distribuição de Tempo das Transações",
        return_base64=False  # Salvar em arquivo
    )
    
    print("\n✅ Boxplot gerado com sucesso!")
    print(f"\n📈 Estatísticas:")
    print(f"  • Q1 (25%): {stats['q1']:.2f}")
    print(f"  • Mediana (50%): {stats['median']:.2f}")
    print(f"  • Q3 (75%): {stats['q3']:.2f}")
    print(f"  • IQR (Intervalo Interquartil): {stats['iqr']:.2f}")
    print(f"  • Outliers detectados: {stats['outliers_count']} ({stats['outliers_percentage']:.2f}%)")
    
    if img.startswith("data:image"):
        print(f"\n🖼️ Imagem em base64 gerada")
    else:
        print(f"\n🖼️ Imagem salva em: {img}")


def exemplo_bar_chart():
    """Demonstra criação de gráfico de barras."""
    print("\n" + "="*80)
    print("📊 EXEMPLO 4: GRÁFICO DE BARRAS")
    print("="*80 + "\n")
    
    data_path = root_dir / "data" / "creditcard_test_500.csv"
    
    if not data_path.exists():
        print(f"❌ Arquivo não encontrado: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    generator = GraphGenerator(output_dir=root_dir / "temp" / "visualizations")
    
    # Contar transações por classe
    class_counts = df['Class'].value_counts().to_dict()
    class_labels = {0: 'Legítima', 1: 'Fraude'}
    class_counts_labeled = {class_labels[k]: v for k, v in class_counts.items()}
    
    print("Gerando gráfico de barras de transações por classe...")
    img, stats = generator.bar_chart(
        data=class_counts_labeled,
        title="Distribuição de Transações por Classe",
        xlabel="Classe",
        ylabel="Quantidade de Transações",
        color="steelblue",
        return_base64=False  # Salvar em arquivo
    )
    
    print("\n✅ Gráfico de barras gerado com sucesso!")
    print(f"\n📈 Estatísticas:")
    print(f"  • Total: {stats['total']}")
    print(f"  • Média: {stats['mean']:.2f}")
    print(f"  • Máximo: {stats['max']}")
    print(f"  • Categoria com mais transações: {stats['max_category']}")
    
    if img.startswith("data:image"):
        print(f"\n🖼️ Imagem em base64 gerada")
    else:
        print(f"\n🖼️ Imagem salva em: {img}")


def exemplo_heatmap():
    """Demonstra criação de heatmap de correlação."""
    print("\n" + "="*80)
    print("📊 EXEMPLO 5: HEATMAP DE CORRELAÇÃO")
    print("="*80 + "\n")
    
    data_path = root_dir / "data" / "creditcard_test_500.csv"
    
    if not data_path.exists():
        print(f"❌ Arquivo não encontrado: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    generator = GraphGenerator(output_dir=root_dir / "temp" / "visualizations")
    
    # Selecionar apenas algumas colunas para visualização
    columns_to_plot = ['Time', 'Amount', 'V1', 'V2', 'V3', 'V4', 'V5']
    
    print("Gerando heatmap de correlação...")
    img, stats = generator.correlation_heatmap(
        data=df,
        columns=columns_to_plot,
        title="Matriz de Correlação (Features Selecionadas)",
        return_base64=False  # Salvar em arquivo
    )
    
    print("\n✅ Heatmap gerado com sucesso!")
    print(f"\n📈 Estatísticas:")
    print(f"  • Número de variáveis: {stats['n_variables']}")
    print(f"  • Correlação média: {stats['mean_correlation']:.4f}")
    
    if stats['strongest_positive']:
        print(f"  • Correlação positiva mais forte: {stats['strongest_positive']['var1']} ↔ {stats['strongest_positive']['var2']} ({stats['strongest_positive']['correlation']:.4f})")
    
    if stats['strongest_negative']:
        print(f"  • Correlação negativa mais forte: {stats['strongest_negative']['var1']} ↔ {stats['strongest_negative']['var2']} ({stats['strongest_negative']['correlation']:.4f})")
    
    if img.startswith("data:image"):
        print(f"\n🖼️ Imagem em base64 gerada")
    else:
        print(f"\n🖼️ Imagem salva em: {img}")


def exemplo_deteccao_automatica():
    """Demonstra detecção automática de necessidade de visualização."""
    print("\n" + "="*80)
    print("📊 EXEMPLO 6: DETECÇÃO AUTOMÁTICA DE VISUALIZAÇÃO")
    print("="*80 + "\n")
    
    queries = [
        "Mostre um histograma da distribuição de valores",
        "Gere um gráfico de dispersão entre V1 e V2",
        "Faça um boxplot para detectar outliers",
        "Crie um gráfico de barras comparando as classes",
        "Exiba um heatmap de correlação",
        "Qual é a média de Amount?",  # Não requer visualização
        "Analise os dados de fraude"  # Genérico
    ]
    
    for query in queries:
        viz_type = detect_visualization_need(query)
        status = f"✅ {viz_type}" if viz_type else "❌ Nenhuma"
        print(f"Query: '{query}'")
        print(f"  → Visualização detectada: {status}\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🎨 EXEMPLOS DE USO: SISTEMA DE VISUALIZAÇÃO GRÁFICA")
    print("="*80)
    
    try:
        # Executar todos os exemplos
        exemplo_histograma()
        exemplo_scatter()
        exemplo_boxplot()
        exemplo_bar_chart()
        exemplo_heatmap()
        exemplo_deteccao_automatica()
        
        print("\n" + "="*80)
        print("✅ TODOS OS EXEMPLOS CONCLUÍDOS COM SUCESSO!")
        print("="*80 + "\n")
        
        # Verificar se diretório de saída foi criado
        output_dir = root_dir / "temp" / "visualizations"
        if output_dir.exists():
            files = list(output_dir.glob("*.png"))
            print(f"📁 {len(files)} imagens salvas em: {output_dir}")
            for f in files:
                print(f"  • {f.name}")
        
    except Exception as e:
        logger.error(f"Erro durante execução dos exemplos: {e}", exc_info=True)
        print(f"\n❌ Erro: {e}")
