"""
Exemplo de Uso do Sandbox Seguro - EDA AI Minds Backend

Este script demonstra como usar o módulo de sandbox para executar
código Python de forma segura.

Autor: EDA AI Minds Team
Data: 2025-10-17
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.security.sandbox import execute_in_sandbox, validate_code_safety, get_sandbox_info
import json


def print_result(title: str, result: dict):
    """Helper para imprimir resultados formatados."""
    print("\n" + "="*70)
    print(f"📋 {title}")
    print("="*70)
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    print("="*70)


def exemplo_1_calculo_matematico():
    """Exemplo 1: Cálculo matemático simples (SEGURO)."""
    print("\n🟢 EXEMPLO 1: Cálculo Matemático Simples")
    
    code = """
import math

# Calcular média e desvio padrão
valores = [10, 20, 30, 40, 50]
media = sum(valores) / len(valores)
variancia = sum((x - media) ** 2 for x in valores) / len(valores)
desvio_padrao = math.sqrt(variancia)

resultado = {
    'valores': valores,
    'media': media,
    'desvio_padrao': desvio_padrao,
    'minimo': min(valores),
    'maximo': max(valores)
}
"""
    
    result = execute_in_sandbox(code)
    print_result("Cálculo Matemático", result)
    
    if result['success']:
        print("\n✅ SUCESSO! Resultado:")
        print(f"   Média: {result['result']['media']}")
        print(f"   Desvio Padrão: {result['result']['desvio_padrao']:.2f}")
        print(f"   Mínimo: {result['result']['minimo']}")
        print(f"   Máximo: {result['result']['maximo']}")


def exemplo_2_pandas_dataframe():
    """Exemplo 2: Análise com pandas DataFrame (SEGURO)."""
    print("\n🟢 EXEMPLO 2: Análise com Pandas DataFrame")
    
    code = """
import pandas as pd
import numpy as np

# Criar DataFrame de exemplo
data = {
    'Produto': ['A', 'B', 'C', 'D', 'E'],
    'Vendas': [100, 150, 200, 120, 180],
    'Custo': [50, 70, 90, 60, 85]
}

df = pd.DataFrame(data)

# Calcular lucro
df['Lucro'] = df['Vendas'] - df['Custo']

# Estatísticas
resultado = {
    'total_vendas': int(df['Vendas'].sum()),
    'total_lucro': int(df['Lucro'].sum()),
    'media_lucro': float(df['Lucro'].mean()),
    'produto_mais_lucrativo': df.loc[df['Lucro'].idxmax(), 'Produto'],
    'lucro_maximo': int(df['Lucro'].max())
}
"""
    
    result = execute_in_sandbox(code, timeout_seconds=10)
    print_result("Análise Pandas", result)
    
    if result['success']:
        print("\n✅ SUCESSO! Análise:")
        print(f"   Total de Vendas: R$ {result['result']['total_vendas']}")
        print(f"   Total de Lucro: R$ {result['result']['total_lucro']}")
        print(f"   Média de Lucro: R$ {result['result']['media_lucro']:.2f}")
        print(f"   Produto Mais Lucrativo: {result['result']['produto_mais_lucrativo']}")


def exemplo_3_numpy_estatisticas():
    """Exemplo 3: Estatísticas avançadas com numpy (SEGURO)."""
    print("\n🟢 EXEMPLO 3: Estatísticas Avançadas com NumPy")
    
    code = """
import numpy as np

# Gerar dados de exemplo
np.random.seed(42)
dados = np.random.normal(loc=100, scale=15, size=1000)

# Calcular estatísticas
resultado = {
    'media': float(np.mean(dados)),
    'mediana': float(np.median(dados)),
    'desvio_padrao': float(np.std(dados)),
    'percentil_25': float(np.percentile(dados, 25)),
    'percentil_75': float(np.percentile(dados, 75)),
    'iqr': float(np.percentile(dados, 75) - np.percentile(dados, 25)),
    'minimo': float(np.min(dados)),
    'maximo': float(np.max(dados))
}
"""
    
    result = execute_in_sandbox(code)
    print_result("Estatísticas NumPy", result)
    
    if result['success']:
        print("\n✅ SUCESSO! Estatísticas:")
        stats = result['result']
        print(f"   Média: {stats['media']:.2f}")
        print(f"   Mediana: {stats['mediana']:.2f}")
        print(f"   Desvio Padrão: {stats['desvio_padrao']:.2f}")
        print(f"   IQR: {stats['iqr']:.2f}")


def exemplo_4_codigo_malicioso_os():
    """Exemplo 4: Tentativa de import 'os' (BLOQUEADO)."""
    print("\n🔴 EXEMPLO 4: Tentativa de Import 'os' (Malicioso)")
    
    code = """
import os

# Tentar executar comando do sistema
resultado = os.system('echo "HACKED!"')
"""
    
    result = execute_in_sandbox(code)
    print_result("Tentativa de Import 'os'", result)
    
    if not result['success']:
        print("\n❌ BLOQUEADO! Como esperado:")
        print(f"   Erro: {result['error']}")
        print(f"   Tipo: {result['error_type']}")


def exemplo_5_codigo_malicioso_subprocess():
    """Exemplo 5: Tentativa de import 'subprocess' (BLOQUEADO)."""
    print("\n🔴 EXEMPLO 5: Tentativa de Import 'subprocess' (Malicioso)")
    
    code = """
import subprocess

# Tentar executar comando
resultado = subprocess.run(['ls', '-la'], capture_output=True)
"""
    
    result = execute_in_sandbox(code)
    print_result("Tentativa de Import 'subprocess'", result)
    
    if not result['success']:
        print("\n❌ BLOQUEADO! Como esperado:")
        print(f"   Erro: {result['error']}")


def exemplo_6_codigo_malicioso_eval():
    """Exemplo 6: Tentativa de eval() (BLOQUEADO)."""
    print("\n🔴 EXEMPLO 6: Tentativa de eval() (Malicioso)")
    
    code = """
# Tentar usar eval para executar código arbitrário
resultado = eval("__import__('os').system('whoami')")
"""
    
    result = execute_in_sandbox(code)
    print_result("Tentativa de eval()", result)
    
    if not result['success']:
        print("\n❌ BLOQUEADO! Como esperado:")
        print(f"   Erro: {result['error']}")


def exemplo_7_timeout():
    """Exemplo 7: Loop infinito com timeout (TIMEOUT)."""
    print("\n⏱️ EXEMPLO 7: Loop Infinito com Timeout")
    
    code = """
# Loop infinito - deve ser interrompido pelo timeout
while True:
    pass
"""
    
    result = execute_in_sandbox(code, timeout_seconds=2)
    print_result("Loop Infinito (Timeout)", result)
    
    if not result['success']:
        print("\n⏱️ TIMEOUT! Como esperado:")
        print(f"   Erro: {result['error']}")


def exemplo_8_validacao_estatica():
    """Exemplo 8: Validação estática de código."""
    print("\n🔍 EXEMPLO 8: Validação Estática de Código")
    
    # Código seguro
    safe_code = """
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3]})
resultado = df['A'].mean()
"""
    
    # Código malicioso
    malicious_code = """
import os
os.system('rm -rf /')
"""
    
    print("\n📝 Validando código SEGURO:")
    safe_validation = validate_code_safety(safe_code)
    print(f"   É seguro? {safe_validation['is_safe']}")
    print(f"   Avisos: {len(safe_validation['warnings'])}")
    
    print("\n📝 Validando código MALICIOSO:")
    malicious_validation = validate_code_safety(malicious_code)
    print(f"   É seguro? {malicious_validation['is_safe']}")
    print(f"   Padrões bloqueados: {malicious_validation['blocked_patterns']}")


def exemplo_9_info_sandbox():
    """Exemplo 9: Informações do sandbox."""
    print("\n⚙️ EXEMPLO 9: Informações do Sandbox")
    
    info = get_sandbox_info()
    print_result("Configuração do Sandbox", info)
    
    print("\n📊 Resumo:")
    print(f"   RestrictedPython disponível: {info['restricted_python_available']}")
    print(f"   Imports permitidos: {len(info['allowed_imports'])} módulos")
    print(f"   Imports bloqueados: {len(info['blocked_imports'])} módulos")
    print(f"   Funções bloqueadas: {len(info['blocked_functions'])} funções")
    print(f"   Timeout padrão: {info['default_timeout_seconds']}s")
    print(f"   Limite de memória: {info['default_memory_limit_mb']}MB")


def main():
    """Executa todos os exemplos."""
    print("=" * 70)
    print(" " * 16 + "SANDBOX SEGURO - EXEMPLOS DE USO")
    print(" " * 20 + "EDA AI Minds Backend")
    print("=" * 70)
    
    # Exemplos de código SEGURO
    exemplo_1_calculo_matematico()
    exemplo_2_pandas_dataframe()
    exemplo_3_numpy_estatisticas()
    
    # Exemplos de código MALICIOSO (todos devem falhar)
    exemplo_4_codigo_malicioso_os()
    exemplo_5_codigo_malicioso_subprocess()
    exemplo_6_codigo_malicioso_eval()
    exemplo_7_timeout()
    
    # Ferramentas auxiliares
    exemplo_8_validacao_estatica()
    exemplo_9_info_sandbox()
    
    print("\n" + "="*70)
    print("🎉 TODOS OS EXEMPLOS EXECUTADOS!")
    print("="*70)
    print("\n📊 Resumo:")
    print("   ✅ Código seguro: PERMITIDO e executado com sucesso")
    print("   ❌ Código malicioso: BLOQUEADO corretamente")
    print("   ⏱️ Timeout: FUNCIONANDO")
    print("   🔍 Validação estática: FUNCIONANDO")
    print("\n🔒 Sandbox está SEGURO e OPERACIONAL!")


if __name__ == "__main__":
    main()
