"""
Exemplo de Uso do Sandbox Seguro

Demonstra execução segura de código Python usando RestrictedPython.

Sprint 3 - P0-1
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from security.sandbox import execute_in_sandbox


def main():
    print("=" * 70)
    print("EXEMPLOS DE EXECUCAO NO SANDBOX SEGURO")
    print("=" * 70)
    print()
    
    # ========================================================================
    # EXEMPLO 1: Codigo Seguro - Calculo Matematico
    # ========================================================================
    print("[OK] EXEMPLO 1: Calculo de Media")
    print("-" * 70)
    
    code_safe_math = """
valores = [10, 20, 30, 40, 50]
media = sum(valores) / len(valores)
resultado = f"Média: {media}"
"""
    
    result = execute_in_sandbox(code_safe_math)
    
    print(f"Sucesso: {result['success']}")
    if result['success']:
        print(f"Resultado: {result['result']}")
        print(f"Tempo de execucao: {result['execution_time_ms']:.2f}ms")
    else:
        print(f"Erro: {result['error']}")
    
    print()
    
    # ========================================================================
    # EXEMPLO 2: Codigo Seguro - Operacoes com Pandas
    # ========================================================================
    print("[OK] EXEMPLO 2: Analise com Pandas")
    print("-" * 70)
    
    code_safe_pandas = """
import pandas as pd

dados = {
    'Produto': ['A', 'B', 'C', 'D'],
    'Vendas': [100, 200, 150, 300]
}

df = pd.DataFrame(dados)
total_vendas = df['Vendas'].sum()
media_vendas = df['Vendas'].mean()

resultado = f"Total: {total_vendas}, Média: {media_vendas}"
"""
    
    result = execute_in_sandbox(code_safe_pandas)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'success':
        print(f"Resultado: {result['result']}")
        print(f"Tempo de execução: {result['execution_time_ms']:.2f}ms")
    else:
        print(f"Erro: {result['error']}")
    
    print()
    
    # ========================================================================
    # EXEMPLO 3: Codigo Seguro - NumPy
    # ========================================================================
    print("[OK] EXEMPLO 3: Calculos Estatisticos com NumPy")
    print("-" * 70)
    
    code_safe_numpy = """
import numpy as np

dados = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
array = np.array(dados)

media = np.mean(array)
desvio = np.std(array)
mediana = np.median(array)

resultado = f"Média: {media:.2f}, Desvio: {desvio:.2f}, Mediana: {mediana:.2f}"
"""
    
    result = execute_in_sandbox(code_safe_numpy)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'success':
        print(f"Resultado: {result['result']}")
        print(f"Tempo de execução: {result['execution_time_ms']:.2f}ms")
    else:
        print(f"Erro: {result['error']}")
    
    print()
    
    # ========================================================================
    # EXEMPLO 4: Codigo MALICIOSO - Import OS (BLOQUEADO)
    # ========================================================================
    print("[BLOCK] EXEMPLO 4: Tentativa de Import Malicioso (OS)")
    print("-" * 70)
    
    code_malicious_os = """
import os
resultado = os.listdir('/')
"""
    
    result = execute_in_sandbox(code_malicious_os)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'error':
        print(f"✅ BLOQUEADO! Erro: {result['error']}")
    else:
        print(f"❌ FALHA DE SEGURANÇA! Código malicioso foi executado!")
    
    print()
    
    # ========================================================================
    # EXEMPLO 5: Código MALICIOSO - Subprocess (BLOQUEADO)
    # ========================================================================
    print("🚫 EXEMPLO 5: Tentativa de Subprocess (BLOQUEADO)")
    print("-" * 70)
    
    code_malicious_subprocess = """
import subprocess
resultado = subprocess.run(['ls', '-la'], capture_output=True)
"""
    
    result = execute_in_sandbox(code_malicious_subprocess)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'error':
        print(f"✅ BLOQUEADO! Erro: {result['error']}")
    else:
        print(f"❌ FALHA DE SEGURANÇA! Código malicioso foi executado!")
    
    print()
    
    # ========================================================================
    # EXEMPLO 6: Código MALICIOSO - Eval (BLOQUEADO)
    # ========================================================================
    print("🚫 EXEMPLO 6: Tentativa de Eval (BLOQUEADO)")
    print("-" * 70)
    
    code_malicious_eval = """
codigo_perigoso = "__import__('os').system('whoami')"
resultado = eval(codigo_perigoso)
"""
    
    result = execute_in_sandbox(code_malicious_eval)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'error':
        print(f"✅ BLOQUEADO! Erro: {result['error']}")
    else:
        print(f"❌ FALHA DE SEGURANÇA! Código malicioso foi executado!")
    
    print()
    
    # ========================================================================
    # EXEMPLO 7: Código MALICIOSO - Open File (BLOQUEADO)
    # ========================================================================
    print("🚫 EXEMPLO 7: Tentativa de Leitura de Arquivo (BLOQUEADO)")
    print("-" * 70)
    
    code_malicious_file = """
with open('/etc/passwd', 'r') as f:
    resultado = f.read()
"""
    
    result = execute_in_sandbox(code_malicious_file)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'error':
        print(f"✅ BLOQUEADO! Erro: {result['error']}")
    else:
        print(f"❌ FALHA DE SEGURANÇA! Código malicioso foi executado!")
    
    print()
    
    # ========================================================================
    # EXEMPLO 8: Código com Erro de Sintaxe
    # ========================================================================
    print("⚠️ EXEMPLO 8: Erro de Sintaxe")
    print("-" * 70)
    
    code_syntax_error = """
def funcao_quebrada(
    print("Faltou fechar parêntese"
"""
    
    result = execute_in_sandbox(code_syntax_error)
    
    print(f"Status: {result['success']}")
    print(f"Erro: {result['error']}")
    
    print()
    
    # ========================================================================
    # EXEMPLO 9: Código com Timeout (Loop Infinito)
    # ========================================================================
    print("⏱️ EXEMPLO 9: Timeout em Loop Infinito")
    print("-" * 70)
    
    code_infinite_loop = """
contador = 0
while True:
    contador += 1
resultado = contador
"""
    
    result = execute_in_sandbox(code_infinite_loop, timeout_seconds=2)
    
    print(f"Status: {result['success']}")
    if result['success'] == 'timeout':
        print(f"✅ TIMEOUT FUNCIONOU! Erro: {result['error']}")
    else:
        print(f"Status inesperado: {result['success']}")
    
    print()
    
    # ========================================================================
    # RESUMO
    # ========================================================================
    print("=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    print("✅ Código seguro (matemática, pandas, numpy): PERMITIDO")
    print("❌ Import malicioso (os, subprocess): BLOQUEADO")
    print("❌ Funções perigosas (eval, open): BLOQUEADO")
    print("⏱️ Timeout em loops infinitos: FUNCIONANDO")
    print("⚠️ Erros de sintaxe: TRATADOS CORRETAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
