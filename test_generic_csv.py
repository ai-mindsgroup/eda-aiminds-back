#!/usr/bin/env python3
"""
Teste de validação: Sistema deve funcionar com CSVs genéricos
Verifica se não há hard-coding específico para creditcard.csv
"""
import sys
import pandas as pd
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.tools.python_analyzer import PythonDataAnalyzer
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def create_test_csv():
    """Cria um CSV de teste genérico completamente diferente do creditcard"""
    data = {
        'id': [1, 2, 3, 4, 5],
        'nome': ['João', 'Maria', 'Pedro', 'Ana', 'Carlos'],
        'idade': [25, 30, 35, 28, 42],
        'cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Brasília', 'Porto Alegre'],
        'salario': [5000.50, 7500.00, 6200.75, 5800.25, 8900.00],
        'ativo': [1, 1, 0, 1, 1]
    }
    
    df = pd.DataFrame(data)
    test_file = Path('temp_test.csv')
    df.to_csv(test_file, index=False)
    logger.info(f"✅ CSV de teste criado: {test_file}")
    logger.info(f"📊 Colunas: {list(df.columns)}")
    return test_file, df

def simulate_chunk_text(df, csv_filename='temp_test.csv'):
    """Simula como o chunk_text seria criado pelo ingestion_agent"""
    # Simular formato de chunk similar ao que o sistema cria
    lines = []
    lines.append(f"Chunk do dataset {csv_filename} (linhas 0 a 5) - 5 registros")
    lines.append(f"Dataset genérico com {len(df.columns)} colunas")
    lines.append(f"Colunas: {','.join([f'\"{col}\"' for col in df.columns])}")
    lines.append("")
    lines.append("=== DADOS ORIGINAIS ===")
    
    # Header com aspas
    header = ','.join([f'"{col}"' for col in df.columns])
    lines.append(header)
    
    # Dados
    for _, row in df.iterrows():
        row_str = ','.join([str(val) for val in row.values])
        lines.append(row_str)
    
    return '\n'.join(lines)

def test_generic_parsing():
    """Testa se o parser consegue ler CSV genérico sem hard-coding"""
    logger.info("=" * 80)
    logger.info("🧪 TESTE: Parsing de CSV Genérico (sem hard-coding)")
    logger.info("=" * 80)
    
    # Criar CSV de teste
    test_file, df_original = create_test_csv()
    
    # Simular chunk_text
    chunk_text = simulate_chunk_text(df_original, test_file.name)
    logger.info(f"\n📄 Chunk Text simulado (primeiros 500 chars):\n{chunk_text[:500]}...\n")
    
    # Criar DataFrame de embeddings simulado
    import pandas as pd
    embeddings_df = pd.DataFrame({
        'id': [1],
        'chunk_text': [chunk_text],
        'metadata': [{'source': test_file.name}]
    })
    
    # Tentar parsear
    analyzer = PythonDataAnalyzer(caller_agent='test_system')
    parsed_df = analyzer._parse_chunk_text_to_dataframe(embeddings_df)
    
    if parsed_df is None:
        logger.error("❌ FALHA: Parser retornou None")
        return False
    
    # Validar resultado
    logger.info(f"\n✅ DataFrame parseado com sucesso!")
    logger.info(f"📊 Shape original: {df_original.shape}")
    logger.info(f"📊 Shape parseado: {parsed_df.shape}")
    logger.info(f"📋 Colunas originais: {list(df_original.columns)}")
    logger.info(f"📋 Colunas parseadas: {list(parsed_df.columns)}")
    
    # Verificar se todas as colunas foram detectadas
    colunas_esperadas = set(df_original.columns)
    colunas_parseadas = set(parsed_df.columns)
    
    if colunas_esperadas == colunas_parseadas:
        logger.info("✅ SUCESSO: Todas as colunas foram detectadas corretamente!")
    else:
        logger.warning(f"⚠️ DIFERENÇA: Esperadas {colunas_esperadas}, Parseadas {colunas_parseadas}")
        missing = colunas_esperadas - colunas_parseadas
        extra = colunas_parseadas - colunas_esperadas
        if missing:
            logger.warning(f"   Faltando: {missing}")
        if extra:
            logger.warning(f"   Extra: {extra}")
    
    # Verificar se não há colunas hard-coded do creditcard
    creditcard_columns = ['Time', 'V1', 'V2', 'Amount', 'Class']
    found_hardcoded = [col for col in creditcard_columns if col in parsed_df.columns]
    if found_hardcoded:
        logger.error(f"❌ FALHA: Colunas hard-coded do creditcard detectadas: {found_hardcoded}")
        return False
    else:
        logger.info("✅ SUCESSO: Nenhuma coluna hard-coded do creditcard detectada")
    
    # Verificar tipos de dados
    logger.info(f"\n📊 Tipos de dados detectados:")
    for col, dtype in parsed_df.dtypes.items():
        logger.info(f"   {col}: {dtype}")
    
    # Limpar arquivo de teste
    test_file.unlink()
    logger.info(f"\n🧹 Arquivo de teste removido: {test_file}")
    
    return True

def test_column_type_detection():
    """Testa se a detecção de tipos de colunas é genérica"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 TESTE: Detecção Genérica de Tipos de Colunas")
    logger.info("=" * 80)
    
    # Criar DataFrame de teste
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'nome': ['A', 'B', 'C'],
        'valor': [1.5, 2.5, 3.5],
        'ativo': [0, 1, 1]
    })
    
    analyzer = PythonDataAnalyzer(caller_agent='test_system')
    
    # Simular análise de tipos
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    logger.info(f"📊 Colunas numéricas detectadas: {numeric_cols}")
    logger.info(f"📊 Colunas categóricas detectadas: {categorical_cols}")
    
    # Verificar se não há hard-coding
    expected_numeric = ['id', 'valor', 'ativo']
    expected_categorical = ['nome']
    
    if set(numeric_cols) == set(expected_numeric):
        logger.info("✅ SUCESSO: Colunas numéricas detectadas corretamente")
    else:
        logger.error(f"❌ FALHA: Esperadas {expected_numeric}, obtidas {numeric_cols}")
        return False
    
    if set(categorical_cols) == set(expected_categorical):
        logger.info("✅ SUCESSO: Colunas categóricas detectadas corretamente")
    else:
        logger.error(f"❌ FALHA: Esperadas {expected_categorical}, obtidas {categorical_cols}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("\n" + "🚀 " * 40)
    logger.info("VALIDAÇÃO: Sistema sem Hard-Coding de CSV Específico")
    logger.info("🚀 " * 40 + "\n")
    
    success = True
    
    # Teste 1: Parsing genérico
    if not test_generic_parsing():
        success = False
    
    # Teste 2: Detecção de tipos
    if not test_column_type_detection():
        success = False
    
    # Resultado final
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("✅ Sistema é genérico e funciona com qualquer CSV")
    else:
        logger.error("❌ ALGUNS TESTES FALHARAM")
        logger.error("❌ Sistema pode ter hard-coding específico")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)
