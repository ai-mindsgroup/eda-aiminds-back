#!/usr/bin/env python3
"""Teste de parsing do chunk_text para validar correção"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.tools.python_analyzer import PythonDataAnalyzer
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_chunk_parsing():
    """Testa se o parsing do chunk_text está funcionando corretamente"""
    
    print("="*60)
    print("🧪 TESTE: Parsing de chunk_text para DataFrame original")
    print("="*60)
    
    try:
        # Inicializar analyzer
        analyzer = PythonDataAnalyzer(caller_agent='test_system')
        print("✅ PythonDataAnalyzer inicializado")
        
        # Tentar recuperar dados com parsing
        print("\n📊 Recuperando dados da tabela embeddings com parsing...")
        df = analyzer.get_data_from_embeddings(limit=None, parse_chunk_text=True)
        
        if df is None:
            print("❌ FALHA: Não foi possível recuperar dados")
            return False
        
        print(f"\n✅ Dados recuperados com sucesso!")
        print(f"📏 Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
        print(f"\n📋 Colunas identificadas:")
        for col in df.columns:
            print(f"  • {col} ({df[col].dtype})")
        
        # Verificar se as colunas esperadas estão presentes
        print("\n🔍 Verificando colunas esperadas do dataset creditcard...")
        expected_numeric = ['Time', 'Amount'] + [f'V{i}' for i in range(1, 29)]
        expected_categorical = ['Class']
        
        found_numeric = []
        found_categorical = []
        
        for col in df.columns:
            if col in expected_numeric:
                found_numeric.append(col)
            elif col in expected_categorical:
                found_categorical.append(col)
        
        print(f"\n✅ Colunas numéricas encontradas: {len(found_numeric)}/{len(expected_numeric)}")
        if len(found_numeric) < len(expected_numeric):
            missing = set(expected_numeric) - set(found_numeric)
            print(f"   ⚠️ Faltando: {', '.join(list(missing)[:5])}...")
        
        print(f"✅ Colunas categóricas encontradas: {len(found_categorical)}/{len(expected_categorical)}")
        if len(found_categorical) < len(expected_categorical):
            missing = set(expected_categorical) - set(found_categorical)
            print(f"   ⚠️ Faltando: {', '.join(missing)}")
        
        # Testar cálculo de estatísticas
        print("\n📊 Testando cálculo de estatísticas reais...")
        stats = analyzer.calculate_real_statistics("tipos_dados")
        
        if "error" in stats:
            print(f"❌ FALHA no cálculo de estatísticas: {stats['error']}")
            return False
        
        print(f"\n✅ Estatísticas calculadas com sucesso!")
        if 'tipos_dados' in stats:
            tipos = stats['tipos_dados']
            print(f"\n📈 Tipos de dados identificados:")
            print(f"  • Numéricos: {len(tipos['numericos'])} colunas")
            print(f"    {', '.join(tipos['numericos'][:5])}...")
            print(f"  • Categóricos: {len(tipos['categoricos'])} colunas")
            print(f"    {', '.join(tipos['categoricos'])}")
        
        print("\n" + "="*60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chunk_parsing()
    sys.exit(0 if success else 1)
