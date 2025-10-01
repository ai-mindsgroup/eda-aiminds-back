#!/usr/bin/env python3
"""Teste específico para detectar novo CSV e calcular estatísticas"""

import sys
from pathlib import Path
import pandas as pd

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.tools.python_analyzer import python_analyzer

def test_with_new_csv():
    """Testa detecção e análise de novo CSV"""
    
    print("🧪 Teste de Detecção de Novo CSV")
    print("=" * 50)
    
    # Criar um CSV completamente diferente
    data = {
        'employee_id': range(1, 501),
        'nome': [f'Funcionario_{i}' for i in range(1, 501)],
        'departamento': ['TI', 'RH', 'Vendas', 'Marketing', 'Financeiro'] * 100,
        'salario': [3000 + (i * 100) for i in range(500)],
        'anos_experiencia': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 50,
        'home_office': ['Sim', 'Não'] * 250
    }
    
    df = pd.DataFrame(data)
    csv_path = Path("data/funcionarios.csv")
    csv_path.parent.mkdir(exist_ok=True)
    df.to_csv(csv_path, index=False)
    
    print(f"📊 CSV criado: {csv_path}")
    print(f"   - {len(df)} registros")
    print(f"   - Colunas: {list(df.columns)}")
    
    # Simular chunk_text que menciona este novo arquivo
    chunk_text = """
    Os dados dos funcionários mostram:
    - Total de 500 funcionários
    - Arquivo: funcionarios.csv
    - Departamentos: TI, RH, Vendas, Marketing, Financeiro
    """
    
    # Calcular estatísticas
    print(f"\n🔍 Calculando estatísticas...")
    stats = python_analyzer.calculate_real_statistics("all")
    
    print(f"\n📊 Resultados:")
    if "error" not in stats:
        print(f"   ✅ Registros detectados: {stats.get('total_records', 'N/A')}")
        print(f"   ✅ Colunas detectadas: {stats.get('total_columns', 'N/A')}")
        
        # Verificar se detectou o arquivo correto
        if stats.get('total_records') == 500:
            print("   🎯 Sistema detectou o arquivo funcionarios.csv!")
        elif stats.get('total_records') == 284807:
            print("   ⚠️ Sistema ainda está usando creditcard.csv")
        else:
            print(f"   ❓ Sistema detectou arquivo com {stats.get('total_records')} registros")
        
        # Mostrar algumas estatísticas
        estatisticas = stats.get('estatisticas', {})
        if 'salario' in estatisticas:
            salario_stats = estatisticas['salario']
            print(f"   💰 Salário médio: R$ {salario_stats.get('mean', 0):.2f}")
            print(f"   💰 Salário máximo: R$ {salario_stats.get('max', 0):.2f}")
        
    else:
        print(f"   ❌ Erro: {stats['error']}")
    
    # Limpeza
    try:
        csv_path.unlink()
        print(f"\n🧹 Arquivo removido: {csv_path}")
    except:
        pass
    
    return stats

if __name__ == "__main__":
    result = test_with_new_csv()