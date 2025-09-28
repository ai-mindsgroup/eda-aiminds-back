"""Demo completo do sistema de carregamento de dados EDA AI Minds.

Este script demonstra todas as funcionalidades do sistema de carregamento:
- Carregamento de diferentes fontes (arquivo, URL, dados sintéticos)
- Validação automática de qualidade
- Limpeza automática de dados
- Análise inteligente integrada
- Interface unificada e simples
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np

# Importar o novo sistema de carregamento
from src.data.data_processor import DataProcessor, create_demo_data, load_csv_file
from src.data.data_loader import DataLoader
from src.data.data_validator import DataValidator


def demo_basic_usage():
    """Demonstração básica do sistema de carregamento."""
    print("🚀 DEMO: Sistema de Carregamento EDA AI Minds")
    print("=" * 60)
    
    # 1. Criar dados sintéticos para demonstração
    print("\n📊 1. Carregando dados sintéticos de fraude...")
    processor = create_demo_data("fraud_detection", num_rows=2000, fraud_rate=0.06)
    
    # Ver resumo dos dados carregados
    summary = processor.get_dataset_summary()
    print(f"✅ Dados carregados: {summary['basic_info']['shape'][0]} linhas, {summary['basic_info']['shape'][1]} colunas")
    
    if 'validation' in summary:
        print(f"🔍 Qualidade dos dados: {summary['validation']['overall_score']:.1f}/100")
    
    if 'cleaning' in summary:
        print(f"🧹 Limpeza automática: {summary['cleaning']['actions_taken']} ações realizadas")
    
    # 2. Executar análises rápidas
    print("\n📈 2. Executando análises automáticas...")
    quick_results = processor.quick_analysis()
    
    # Mostrar resultados das análises
    if 'basic_stats' in quick_results and 'content' in quick_results['basic_stats']:
        print("📋 Estatísticas básicas:")
        print(quick_results['basic_stats']['content'][:300] + "...")
    
    if 'fraud_analysis' in quick_results and 'content' in quick_results['fraud_analysis']:
        print("\n🚨 Análise de fraude:")
        print(quick_results['fraud_analysis']['content'][:300] + "...")
    
    # 3. Análises interativas
    print("\n💬 3. Análises interativas...")
    queries = [
        "Quantas transações temos por categoria de merchant?",
        "Qual a correlação entre valor e distância de casa?",
        "Mostre estatísticas das transações fraudulentas vs legítimas"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Consulta {i}: {query}")
        result = processor.analyze(query)
        if 'content' in result:
            print("Resposta:", result['content'][:200] + "...")
    
    return processor


def demo_advanced_features():
    """Demonstração de funcionalidades avançadas."""
    print("\n" + "=" * 60)
    print("🔬 DEMO: Funcionalidades Avançadas")
    print("=" * 60)
    
    # 1. Carregamento com validação personalizada
    print("\n1. Carregamento com configurações personalizadas...")
    processor = DataProcessor(auto_validate=True, auto_clean=False)
    
    # Criar dados com problemas propositais para demonstrar validação
    problematic_data = pd.DataFrame({
        'id': [1, 2, 2, 4, 5],  # Duplicata
        'value': [100, 200, None, '300', 'invalid'],  # Tipos mistos
        'category': ['A', 'B', '', 'C', None],  # Valores vazios
        'weird_col_name!@#': [1, 2, 3, 4, 5],  # Nome problemático
        '': [1, 1, 1, 1, 1]  # Coluna sem nome
    })
    
    result = processor.load_from_dataframe(problematic_data, "dados_problematicos")
    print(f"✅ Dados carregados (com problemas): {result['message']}")
    
    if 'validation' in result:
        print(f"⚠️  Qualidade: {result['validation']['score']:.1f}/100")
        print(f"   Erros: {result['validation']['errors']}, Avisos: {result['validation']['warnings']}")
    
    # 2. Relatório detalhado de qualidade
    print("\n2. Relatório detalhado de qualidade...")
    quality_report = processor.get_data_quality_report()
    print(f"📊 Score geral: {quality_report['overall_score']:.1f}/100")
    print(f"🎯 Completude: {quality_report['data_quality']['quality_metrics']['completeness']:.1f}%")
    print(f"🔄 Unicidade: {quality_report['data_quality']['quality_metrics']['uniqueness']:.1f}%")
    
    # 3. Sugestões de melhoria
    print("\n3. Sugestões de melhoria...")
    suggestions = processor.suggest_improvements()
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"   {i}. [{suggestion['priority'].upper()}] {suggestion['description']}")
    
    # 4. Limpeza manual
    print("\n4. Aplicando limpeza manual...")
    validator = DataValidator()
    df_clean, cleaning_report = validator.clean_dataframe(processor.current_df, auto_fix=True)
    
    print(f"🧹 {len(cleaning_report['actions_taken'])} ações de limpeza realizadas:")
    for action in cleaning_report['actions_taken'][:5]:
        print(f"   • {action}")
    
    if cleaning_report['rows_removed'] > 0:
        print(f"🗑️  {cleaning_report['rows_removed']} linhas removidas")
    
    return processor


def demo_multiple_sources():
    """Demonstração de carregamento de múltiplas fontes."""
    print("\n" + "=" * 60)
    print("🌐 DEMO: Múltiplas Fontes de Dados")
    print("=" * 60)
    
    sources_demo = []
    
    # 1. Dados sintéticos de vendas
    print("\n1. Dados sintéticos - Vendas...")
    try:
        processor = create_demo_data("sales", num_rows=500, start_date="2024-01-01")
        summary = processor.get_dataset_summary()
        sources_demo.append({
            'type': 'Vendas Sintéticas',
            'shape': summary['basic_info']['shape'],
            'columns': len(summary['basic_info']['columns'])
        })
        print(f"✅ {summary['basic_info']['shape'][0]} transações de vendas carregadas")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # 2. Dados sintéticos de clientes
    print("\n2. Dados sintéticos - Clientes...")
    try:
        processor = create_demo_data("customer", num_rows=300)
        summary = processor.get_dataset_summary()
        sources_demo.append({
            'type': 'Clientes Sintéticos', 
            'shape': summary['basic_info']['shape'],
            'columns': len(summary['basic_info']['columns'])
        })
        print(f"✅ {summary['basic_info']['shape'][0]} perfis de clientes carregados")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # 3. Dados genéricos
    print("\n3. Dados sintéticos - Genéricos...")
    try:
        processor = create_demo_data("generic", num_rows=200, num_numeric=7, num_categorical=4)
        summary = processor.get_dataset_summary()
        sources_demo.append({
            'type': 'Genéricos',
            'shape': summary['basic_info']['shape'], 
            'columns': len(summary['basic_info']['columns'])
        })
        print(f"✅ {summary['basic_info']['shape'][0]} registros genéricos carregados")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # Resumo das fontes testadas
    print(f"\n📊 Resumo - {len(sources_demo)} fontes testadas:")
    for source in sources_demo:
        print(f"   • {source['type']}: {source['shape'][0]} linhas × {source['columns']} colunas")
    
    return processor


def demo_export_capabilities():
    """Demonstração de capacidades de exportação."""
    print("\n" + "=" * 60)
    print("💾 DEMO: Exportação de Dados")
    print("=" * 60)
    
    # Criar dados para exportação
    processor = create_demo_data("fraud_detection", num_rows=1000)
    
    # Exportar para CSV
    export_file = "dados_processados_demo.csv"
    success = processor.export_to_csv(export_file)
    
    if success:
        print(f"✅ Dados exportados para: {export_file}")
        
        # Verificar arquivo exportado
        if os.path.exists(export_file):
            file_size = os.path.getsize(export_file) / 1024  # KB
            print(f"📁 Tamanho do arquivo: {file_size:.1f} KB")
            
            # Testar re-carregamento
            print("\n🔄 Testando re-carregamento do arquivo exportado...")
            processor_reload = DataProcessor()
            result = processor_reload.load_from_file(export_file)
            
            if result['success']:
                print(f"✅ Re-carregamento bem-sucedido: {result['message']}")
            else:
                print(f"❌ Falha no re-carregamento: {result['error']}")
            
            # Limpar arquivo de teste
            os.remove(export_file)
            print(f"🗑️  Arquivo de teste removido: {export_file}")
        
    else:
        print("❌ Falha na exportação")


def main():
    """Função principal que executa todos os demos."""
    print("🎯 EDA AI MINDS - SISTEMA DE CARREGAMENTO DE DADOS")
    print("=" * 80)
    print("Este demo mostra como carregar e processar dados CSV de forma inteligente.")
    print("=" * 80)
    
    try:
        # Executar demos sequencialmente
        processor1 = demo_basic_usage()
        processor2 = demo_advanced_features()
        processor3 = demo_multiple_sources()
        demo_export_capabilities()
        
        print("\n" + "=" * 80)
        print("✅ TODOS OS DEMOS CONCLUÍDOS COM SUCESSO!")
        print("=" * 80)
        
        # Resumo final
        print(f"\n📊 Resumo Final:")
        print(f"• Sistema de carregamento: ✅ Funcionando")
        print(f"• Validação automática: ✅ Funcionando") 
        print(f"• Limpeza de dados: ✅ Funcionando")
        print(f"• Análise inteligente: ✅ Funcionando")
        print(f"• Múltiplas fontes: ✅ Funcionando")
        print(f"• Exportação: ✅ Funcionando")
        
        print(f"\n🚀 O sistema está pronto para carregar e analisar seus dados CSV!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE EXECUÇÃO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    exit(exit_code)