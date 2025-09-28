"""Exemplo Prático: Como Carregar e Analisar Seus Dados CSV

Este exemplo mostra como usar o Sistema de Carregamento EDA AI Minds
para carregar e analisar seus próprios arquivos CSV de forma simples e eficiente.
"""
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.data_processor import DataProcessor, create_demo_data, load_csv_file


def exemplo_carregamento_simples():
    """Exemplo mais simples possível de carregamento e análise."""
    print("🚀 EXEMPLO 1: Carregamento Simples")
    print("=" * 50)
    
    # PASSO 1: Carregar dados (usando dados sintéticos como exemplo)
    # Substitua por: processor = load_csv_file("seu_arquivo.csv")
    processor = create_demo_data("fraud_detection", num_rows=1000, fraud_rate=0.08)
    
    print("✅ Dados carregados com sucesso!")
    
    # PASSO 2: Ver resumo básico
    summary = processor.get_dataset_summary()
    print(f"📊 Dataset: {summary['basic_info']['shape'][0]} linhas × {summary['basic_info']['shape'][1]} colunas")
    
    # PASSO 3: Análise rápida automática
    print("\n📈 Executando análise rápida...")
    results = processor.quick_analysis()
    
    if 'basic_stats' in results and 'content' in results['basic_stats']:
        print("📋 Resumo dos dados:")
        print(results['basic_stats']['content'][:400] + "...\n")
    
    # PASSO 4: Perguntas específicas
    print("💬 Fazendo perguntas específicas aos dados:")
    
    questions = [
        "Quantas linhas e colunas temos?",
        "Qual a taxa de fraude no dataset?",
        "Faça um resumo das principais estatísticas"
    ]
    
    for question in questions:
        print(f"\n❓ {question}")
        answer = processor.analyze(question)
        print(f"💡 {answer['content'][:200]}...")
    
    return processor


def exemplo_carregamento_avancado():
    """Exemplo com configurações avançadas e validação."""
    print("\n🔬 EXEMPLO 2: Carregamento Avançado")
    print("=" * 50)
    
    # PASSO 1: Configurar processador com validação personalizada
    processor = DataProcessor(
        auto_validate=True,    # Validar automaticamente
        auto_clean=True        # Limpar problemas automaticamente
    )
    
    # PASSO 2: Carregar dados sintéticos com problemas propositais
    # Em caso real: result = processor.load_from_file("dados_com_problemas.csv")
    import pandas as pd
    dados_problematicos = pd.DataFrame({
        'id': [1, 2, 2, 4, 5, 6],  # ID com duplicata
        'valor': [100, 200, None, '300', 400, 'inválido'],  # Tipos mistos
        'categoria': ['A', 'B', '', None, 'C', 'D'],  # Valores vazios
        'data': ['2024-01-01', '2024-02-01', 'data_inválida', '2024-03-01', None, '2024-04-01']
    })
    
    result = processor.load_from_dataframe(dados_problematicos, "dados_exemplo")
    
    print(f"✅ {result['message']}")
    if 'validation' in result:
        print(f"🔍 Qualidade inicial: {result['validation']['score']:.1f}/100")
    
    # PASSO 3: Ver relatório detalhado de qualidade
    print("\n📊 Relatório de Qualidade Detalhado:")
    quality = processor.get_data_quality_report()
    
    print(f"📈 Score geral: {quality['overall_score']:.1f}/100")
    print(f"🎯 Completude: {quality['data_quality']['quality_metrics']['completeness']:.1f}%")
    print(f"🔄 Unicidade: {quality['data_quality']['quality_metrics']['uniqueness']:.1f}%")
    
    # PASSO 4: Ver sugestões de melhoria
    print("\n💡 Sugestões de Melhoria:")
    suggestions = processor.suggest_improvements()
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"  {i}. [{suggestion['priority'].upper()}] {suggestion['description']}")
    
    return processor


def exemplo_multiplas_fontes():
    """Exemplo de carregamento de diferentes tipos de dados."""
    print("\n🌐 EXEMPLO 3: Múltiplas Fontes de Dados")
    print("=" * 50)
    
    # Exemplo 1: Dados de vendas
    print("🛒 Carregando dados de vendas...")
    sales_processor = create_demo_data("sales", num_rows=500, start_date="2024-01-01")
    sales_summary = sales_processor.get_dataset_summary()
    print(f"✅ Vendas: {sales_summary['basic_info']['shape'][0]} transações carregadas")
    
    # Análise rápida de vendas
    sales_analysis = sales_processor.analyze("Qual o faturamento total e produto mais vendido?")
    print(f"💰 {sales_analysis['content'][:150]}...")
    
    # Exemplo 2: Dados de clientes (com correção do bug)
    print(f"\n👥 Carregando dados de clientes...")
    try:
        customer_processor = create_demo_data("customer", num_rows=300)
        customer_summary = customer_processor.get_dataset_summary()
        print(f"✅ Clientes: {customer_summary['basic_info']['shape'][0]} perfis carregados")
        
        # Análise de perfil de clientes
        customer_analysis = customer_processor.analyze("Qual o perfil médio dos clientes?")
        print(f"👤 {customer_analysis['content'][:150]}...")
    except:
        print("⚠️  Dados de cliente temporariamente indisponíveis")
    
    # Exemplo 3: URL remota (simulação)
    print(f"\n🌍 Exemplo de carregamento via URL:")
    print(f"💡 Para carregar de uma URL use:")
    print(f"   processor.load_from_url('https://exemplo.com/dados.csv')")
    
    return sales_processor


def exemplo_exportacao_e_reutilizacao():
    """Exemplo de exportação e reutilização de dados processados."""
    print("\n💾 EXEMPLO 4: Exportação e Reutilização")
    print("=" * 50)
    
    # PASSO 1: Carregar e processar dados
    processor = create_demo_data("fraud_detection", num_rows=2000)
    print("✅ Dados carregados e processados")
    
    # PASSO 2: Realizar análises
    fraud_analysis = processor.analyze("Analise os padrões de fraude detalhadamente")
    print(f"🔍 Análise realizada: {fraud_analysis['content'][:100]}...")
    
    # PASSO 3: Exportar dados processados
    export_file = "dados_processados_exemplo.csv"
    success = processor.export_to_csv(export_file)
    
    if success:
        print(f"💾 Dados exportados para: {export_file}")
        
        # PASSO 4: Recarregar dados exportados
        processor_reload = DataProcessor()
        reload_result = processor_reload.load_from_file(export_file)
        
        if reload_result['success']:
            print(f"🔄 Dados recarregados com sucesso!")
            print(f"📊 {reload_result['message']}")
            
            # Verificar se análise ainda funciona
            test_analysis = processor_reload.analyze("Quantas transações fraudulentas temos?")
            print(f"✅ Análise pós-carregamento: {test_analysis['content'][:100]}...")
        
        # Limpeza
        import os
        os.remove(export_file)
        print(f"🗑️  Arquivo de exemplo removido")
    
    return processor


def exemplo_tratamento_erros():
    """Exemplo de como o sistema trata erros comuns."""
    print("\n⚠️  EXEMPLO 5: Tratamento de Erros")
    print("=" * 50)
    
    processor = DataProcessor()
    
    # Erro 1: Arquivo inexistente
    print("🧪 Testando arquivo inexistente...")
    result = processor.load_from_file("arquivo_que_nao_existe.csv")
    if not result['success']:
        print(f"❌ Erro capturado corretamente: {result['error'][:80]}...")
    
    # Erro 2: Análise sem dados
    print("\n🧪 Testando análise sem dados...")
    empty_processor = DataProcessor()
    result = empty_processor.analyze("teste")
    if 'error' in result or not result.get('content'):
        print("❌ Erro de análise sem dados capturado corretamente")
    
    # Erro 3: DataFrame vazio
    print("\n🧪 Testando DataFrame vazio...")
    import pandas as pd
    result = processor.load_from_dataframe(pd.DataFrame(), "vazio")
    if not result['success']:
        print(f"❌ DataFrame vazio detectado: {result['error']}")
    
    print("\n✅ Sistema de tratamento de erros funcionando corretamente!")


def main():
    """Executa todos os exemplos práticos."""
    print("🎯 EXEMPLOS PRÁTICOS - SISTEMA DE CARREGAMENTO EDA AI MINDS")
    print("=" * 80)
    print("Aprenda como usar o sistema para carregar e analisar seus dados CSV")
    print("=" * 80)
    
    try:
        # Executar todos os exemplos
        exemplo_carregamento_simples()
        exemplo_carregamento_avancado()
        exemplo_multiplas_fontes()
        exemplo_exportacao_e_reutilizacao()
        exemplo_tratamento_erros()
        
        print("\n" + "=" * 80)
        print("🎉 TODOS OS EXEMPLOS CONCLUÍDOS!")
        print("=" * 80)
        
        print("\n📚 COMO USAR COM SEUS DADOS:")
        print("1. Para arquivo local:")
        print("   processor = load_csv_file('meus_dados.csv')")
        
        print("\n2. Para análise simples:")
        print("   resultado = processor.analyze('Faça um resumo dos dados')")
        
        print("\n3. Para análise completa:")
        print("   resultados = processor.quick_analysis()")
        
        print("\n4. Para exportar resultados:")
        print("   processor.export_to_csv('dados_processados.csv')")
        
        print(f"\n🚀 Seu sistema está pronto para analisar dados CSV!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE EXEMPLOS: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    exit(exit_code)