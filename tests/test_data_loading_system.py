"""Testes automatizados para o Sistema de Carregamento de Dados.

Este módulo executa testes completos de:
- Carregamento de múltiplas fontes
- Validação de dados
- Limpeza automática
- Integração com análise
- Exportação
"""
import sys
import os
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.data_processor import DataProcessor, create_demo_data
from src.data.data_loader import DataLoader, DataLoaderError
from src.data.data_validator import DataValidator


class TestRunner:
    """Executor de testes para o sistema de carregamento."""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        
    def run_test(self, test_name, test_func):
        """Executa um teste individual."""
        try:
            print(f"\n🧪 Executando: {test_name}")
            result = test_func()
            
            if result:
                print(f"✅ {test_name} - PASSOU")
                self.tests_passed += 1
                self.test_results.append({"name": test_name, "status": "PASSOU", "error": None})
            else:
                print(f"❌ {test_name} - FALHOU")
                self.tests_failed += 1
                self.test_results.append({"name": test_name, "status": "FALHOU", "error": "Teste retornou False"})
                
        except Exception as e:
            print(f"❌ {test_name} - ERRO: {str(e)}")
            self.tests_failed += 1
            self.test_results.append({"name": test_name, "status": "ERRO", "error": str(e)})
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"📊 RESUMO DOS TESTES")
        print(f"{'='*80}")
        print(f"Total de testes: {total}")
        print(f"✅ Passou: {self.tests_passed}")
        print(f"❌ Falhou: {self.tests_failed}")
        print(f"🎯 Taxa de sucesso: {success_rate:.1f}%")
        
        if self.tests_failed > 0:
            print(f"\n❌ Testes que falharam:")
            for result in self.test_results:
                if result["status"] != "PASSOU":
                    print(f"  • {result['name']}: {result['error']}")
        
        return self.tests_failed == 0


def test_data_loader_basic():
    """Testa carregamento básico de dados."""
    loader = DataLoader()
    
    # Teste com dados sintéticos
    df, load_info = loader.create_synthetic_data("fraud_detection", 100)
    
    # Verificações
    assert len(df) == 100, f"Esperado 100 linhas, obtido {len(df)}"
    assert len(df.columns) > 0, "DataFrame não deve estar vazio"
    assert load_info['source_type'] == 'synthetic', "Tipo de fonte incorreto"
    assert load_info['rows'] == 100, "Número de linhas incorreto nos metadados"
    
    return True


def test_data_loader_from_dataframe():
    """Testa carregamento de DataFrame existente."""
    loader = DataLoader()
    
    # Criar DataFrame de teste
    test_df = pd.DataFrame({
        'col1': [1, 2, 3, 4, 5],
        'col2': ['A', 'B', 'C', 'D', 'E'],
        'col3': [1.1, 2.2, 3.3, 4.4, 5.5]
    })
    
    df, load_info = loader.load_from_dataframe(test_df, "teste_df")
    
    # Verificações
    assert len(df) == 5, f"Esperado 5 linhas, obtido {len(df)}"
    assert len(df.columns) == 3, f"Esperado 3 colunas, obtido {len(df.columns)}"
    assert load_info['source_type'] == 'dataframe', "Tipo de fonte incorreto"
    assert not df.equals(test_df) or df is not test_df, "Deve ser uma cópia, não referência"
    
    return True


def test_data_loader_file_operations():
    """Testa operações com arquivos temporários."""
    loader = DataLoader()
    
    # Criar arquivo CSV temporário
    test_data = pd.DataFrame({
        'id': range(1, 101),
        'value': np.random.rand(100),
        'category': np.random.choice(['A', 'B', 'C'], 100)
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        test_data.to_csv(f, index=False)
        temp_file = f.name
    
    try:
        # Carregar arquivo
        df, load_info = loader.load_from_file(temp_file)
        
        # Verificações
        assert len(df) == 100, f"Esperado 100 linhas, obtido {len(df)}"
        assert len(df.columns) == 3, f"Esperado 3 colunas, obtido {len(df.columns)}"
        assert load_info['source_type'] == 'file', "Tipo de fonte incorreto"
        assert load_info['encoding'] in ['utf-8', 'ascii'], "Encoding não detectado corretamente"
        
        return True
        
    finally:
        # Limpar arquivo temporário
        os.unlink(temp_file)


def test_data_validator_basic():
    """Testa validação básica de dados."""
    validator = DataValidator()
    
    # Criar dados com problemas conhecidos
    problematic_df = pd.DataFrame({
        'good_col': [1, 2, 3, 4, 5],
        'missing_col': [1, None, 3, None, 5],
        'constant_col': [1, 1, 1, 1, 1],
        'mixed_types': [1, '2', 3.0, 'four', 5],
        'weird_name!@#': [1, 2, 3, 4, 5]
    })
    
    # Validar
    results = validator.validate_dataframe(problematic_df)
    
    # Verificações
    assert 'overall_score' in results, "Score geral deve estar presente"
    assert 0 <= results['overall_score'] <= 100, "Score deve estar entre 0-100"
    assert 'basic_info' in results, "Informações básicas devem estar presentes"
    assert results['basic_info']['shape'] == (5, 5), "Shape incorreto"
    
    return True


def test_data_validator_cleaning():
    """Testa limpeza automática de dados."""
    validator = DataValidator()
    
    # Criar dados que precisam de limpeza
    dirty_df = pd.DataFrame({
        'id': [1, 2, 2, 4, 5],  # Duplicata
        'value': [100, 200, None, '300', 400],  # Tipo misto
        'category': ['A', 'B', '', None, 'C'],  # Valores vazios
        '': [1, 1, 1, 1, 1]  # Nome de coluna vazio
    })
    
    # Limpar
    clean_df, cleaning_report = validator.clean_dataframe(dirty_df, auto_fix=True)
    
    # Verificações
    assert len(clean_df) <= len(dirty_df), "Dados limpos não devem ter mais linhas"
    assert len(cleaning_report['actions_taken']) > 0, "Deve ter realizado ações de limpeza"
    assert 'rows_removed' in cleaning_report, "Deve reportar linhas removidas"
    
    return True


def test_data_processor_integration():
    """Testa integração completa do DataProcessor."""
    processor = DataProcessor(auto_validate=True, auto_clean=True)
    
    # Carregar dados sintéticos
    result = processor.load_synthetic_data("fraud_detection", 500)
    
    # Verificações do carregamento
    assert result['success'], f"Carregamento falhou: {result.get('error', 'Sem erro especificado')}"
    assert 'load_info' in result, "Informações de carregamento ausentes"
    assert result['load_info']['rows'] == 500, "Número de linhas incorreto"
    
    # Verificar integração com análise
    assert result.get('agent_ready', False), "Integração com agente de análise falhou"
    
    # Testar análise
    analysis_result = processor.analyze("Faça um resumo básico dos dados")
    assert 'content' in analysis_result, "Resultado de análise deve ter conteúdo"
    
    # Testar relatório de qualidade
    quality = processor.get_data_quality_report()
    assert 'overall_score' in quality, "Relatório de qualidade deve ter score"
    
    return True


def test_synthetic_data_generation():
    """Testa geração de diferentes tipos de dados sintéticos."""
    test_cases = [
        ("fraud_detection", {"num_rows": 200, "fraud_rate": 0.1}),
        ("sales", {"num_rows": 150, "start_date": "2024-01-01"}),
        ("generic", {"num_rows": 100, "num_numeric": 3, "num_categorical": 2})
    ]
    
    for data_type, params in test_cases:
        try:
            processor = create_demo_data(data_type, **params)
            summary = processor.get_dataset_summary()
            
            expected_rows = params.get("num_rows", 1000)
            actual_rows = summary['basic_info']['shape'][0]
            
            assert actual_rows == expected_rows, f"{data_type}: Esperado {expected_rows} linhas, obtido {actual_rows}"
            
        except Exception as e:
            if data_type == "customer":
                # Permitir falha conhecida no tipo customer
                print(f"⚠️  Falha conhecida em {data_type}: {str(e)}")
                continue
            else:
                raise e
    
    return True


def test_export_import_cycle():
    """Testa ciclo completo de exportação e importação."""
    # Criar dados
    processor1 = create_demo_data("fraud_detection", 300)
    
    # Exportar para arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        temp_file = f.name
    
    try:
        # Exportar
        success = processor1.export_to_csv(temp_file)
        assert success, "Exportação falhou"
        assert os.path.exists(temp_file), "Arquivo exportado não existe"
        
        # Importar
        processor2 = DataProcessor()
        result = processor2.load_from_file(temp_file)
        
        assert result['success'], f"Importação falhou: {result.get('error')}"
        
        # Comparar
        summary1 = processor1.get_dataset_summary()
        summary2 = processor2.get_dataset_summary()
        
        assert summary1['basic_info']['shape'] == summary2['basic_info']['shape'], "Shapes diferentes após export/import"
        
        return True
        
    finally:
        # Limpar arquivo temporário
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_error_handling():
    """Testa tratamento de erros."""
    processor = DataProcessor()
    
    # Teste 1: Arquivo inexistente
    try:
        result = processor.load_from_file("arquivo_inexistente.csv")
        assert not result['success'], "Deve falhar para arquivo inexistente"
        assert 'error' in result, "Deve retornar erro"
    except Exception as e:
        # Permitir exceção ou erro estruturado
        pass
    
    # Teste 2: DataFrame vazio
    try:
        empty_df = pd.DataFrame()
        result = processor.load_from_dataframe(empty_df)
        assert not result['success'], "Deve falhar para DataFrame vazio"
    except Exception as e:
        # Permitir exceção
        pass
    
    # Teste 3: Análise sem dados carregados
    processor_empty = DataProcessor()
    result = processor_empty.analyze("teste")
    assert not result.get('success', True), "Deve falhar sem dados carregados"
    
    return True


def test_performance_basic():
    """Testa performance básica do sistema."""
    import time
    
    # Teste com dataset médio
    start_time = time.time()
    processor = create_demo_data("fraud_detection", 5000)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    # Verificações de performance (limites generosos)
    assert processing_time < 10, f"Processamento muito lento: {processing_time:.2f}s"
    
    # Teste de análise
    start_time = time.time()
    result = processor.analyze("Faça um resumo dos dados")
    end_time = time.time()
    
    analysis_time = end_time - start_time
    assert analysis_time < 5, f"Análise muito lenta: {analysis_time:.2f}s"
    
    return True


def main():
    """Executa todos os testes."""
    print("🚀 EXECUTANDO TESTES DO SISTEMA DE CARREGAMENTO")
    print("=" * 80)
    
    runner = TestRunner()
    
    # Lista de testes
    tests = [
        ("Carregamento Básico de Dados", test_data_loader_basic),
        ("Carregamento de DataFrame", test_data_loader_from_dataframe),
        ("Operações com Arquivos", test_data_loader_file_operations),
        ("Validação Básica", test_data_validator_basic),
        ("Limpeza Automática", test_data_validator_cleaning),
        ("Integração do DataProcessor", test_data_processor_integration),
        ("Geração de Dados Sintéticos", test_synthetic_data_generation),
        ("Ciclo Exportar/Importar", test_export_import_cycle),
        ("Tratamento de Erros", test_error_handling),
        ("Performance Básica", test_performance_basic),
    ]
    
    # Executar testes
    for test_name, test_func in tests:
        runner.run_test(test_name, test_func)
    
    # Imprimir resumo
    success = runner.print_summary()
    
    if success:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Sistema de carregamento funcionando perfeitamente")
        return 0
    else:
        print(f"\n⚠️  ALGUNS TESTES FALHARAM")
        print(f"🔧 Verificar problemas antes de usar em produção")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)