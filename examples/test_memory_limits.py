"""
🔒 SPRINT 3 P0-3 COMPLETO: Testes de Limite de Memória para Sandbox Seguro

Este módulo testa o limite de memória implementado no sandbox seguro,
validando comportamento em Unix/Linux (hard limit) e Windows (soft limit).

Cenários Testados:
1. Código seguro com baixo uso de memória (< 10MB) → EXECUTADO ✅
2. Código com uso moderado de memória (< limite) → EXECUTADO ✅
3. Código que tenta alocar memória excessiva (> limite) → BLOQUEADO ❌
4. Verificação de estatísticas de memória (delta, pico)
5. Fallback Windows vs Hard limit Unix

Autor: GitHub Copilot Sonnet 4.5 (Sprint 3 P0-3)
Data: 2025-10-17
"""

import sys
import os
import platform
import time

# Adicionar src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from security.sandbox import (
    execute_in_sandbox,
    get_memory_usage_mb,
    RESOURCE_AVAILABLE,
    PSUTIL_AVAILABLE
)


def print_header(text):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_result(test_name, result, expected_success=True):
    """Imprime resultado de teste formatado."""
    success = result.get('success')
    status_icon = "✅" if success == expected_success else "❌"
    status_text = "SUCESSO" if success == expected_success else "FALHOU"
    
    print(f"\n{status_icon} {status_text} - {test_name}")
    print(f"  Tempo: {result.get('execution_time_ms', 0):.2f}ms")
    
    if success:
        print(f"  Resultado: {result.get('result')}")
    else:
        print(f"  Erro: {result.get('error')}")
        print(f"  Tipo: {result.get('error_type')}")
    
    # Mostrar logs de memória
    logs = result.get('logs', [])
    memory_logs = [log for log in logs if 'memória' in log.lower() or 'memory' in log.lower()]
    if memory_logs:
        print(f"\n  📊 Logs de Memória:")
        for log in memory_logs:
            print(f"     {log}")
    
    return success == expected_success


def main():
    print_header("🔒 TESTES DE LIMITE DE MEMÓRIA - SANDBOX SEGURO")
    
    # Informações do sistema
    print(f"\n📊 Informações do Sistema:")
    print(f"   Sistema Operacional: {platform.system()} {platform.release()}")
    print(f"   Arquitetura: {platform.machine()}")
    print(f"   Versão Python: {platform.python_version()}")
    print(f"   resource disponível: {'✅ SIM' if RESOURCE_AVAILABLE else '❌ NÃO'}")
    print(f"   psutil disponível: {'✅ SIM' if PSUTIL_AVAILABLE else '❌ NÃO'}")
    
    # Detecção de estratégia de limite
    if platform.system() in ('Linux', 'Darwin') and RESOURCE_AVAILABLE:
        strategy = "HARD LIMIT via resource.setrlimit() (Unix/Linux)"
    elif PSUTIL_AVAILABLE:
        strategy = "SOFT LIMIT via psutil monitoring (Windows/Fallback)"
    else:
        strategy = "SEM LIMITE DE MEMÓRIA (psutil não instalado)"
    
    print(f"\n🔧 Estratégia de Limite: {strategy}")
    
    # Memória inicial do processo
    initial_memory = get_memory_usage_mb()
    if initial_memory > 0:
        print(f"   Memória inicial do processo: {initial_memory:.2f}MB")
    
    # ═══════════════════════════════════════════════════════════════
    # TESTE 1: Código Leve (< 10MB) - Deve Executar
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 1: Código Leve com Baixo Uso de Memória")
    
    code_test1 = """
import pandas as pd
import numpy as np

# Criar DataFrame pequeno (~1MB)
df = pd.DataFrame({
    'A': list(range(1000)),
    'B': list(range(1000, 2000)),
    'C': list(range(2000, 3000))
})

# Cálculos simples
mean_A = df['A'].mean()
sum_B = df['B'].sum()
max_C = df['C'].max()

resultado = {
    'mean_A': mean_A,
    'sum_B': sum_B,
    'max_C': max_C,
    'rows': len(df)
}
"""
    
    result1 = execute_in_sandbox(
        code=code_test1,
        timeout_seconds=10,
        memory_limit_mb=50  # Limite generoso
    )
    
    test1_passed = print_result("Código leve (< 10MB)", result1, expected_success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TESTE 2: Código Moderado (20-30MB) - Deve Executar
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 2: Código com Uso Moderado de Memória")
    
    code_test2 = """
import pandas as pd
import numpy as np

# Criar DataFrame maior (~20MB)
# 100k linhas x 20 colunas de float64 = 100k * 20 * 8 bytes ≈ 16MB
data = {}
for i in range(20):
    data[f'col_{i}'] = np.random.rand(100000)

df = pd.DataFrame(data)

# Operações estatísticas
stats = df.describe()
corr_matrix = df.corr()

resultado = {
    'shape': df.shape,
    'memory_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
    'mean_col_0': df['col_0'].mean(),
    'corr_shape': corr_matrix.shape
}
"""
    
    result2 = execute_in_sandbox(
        code=code_test2,
        timeout_seconds=15,
        memory_limit_mb=100  # Limite de 100MB
    )
    
    test2_passed = print_result("Código moderado (20-30MB)", result2, expected_success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TESTE 3: Código com Alocação Excessiva - Deve Bloquear
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 3: Código Tentando Alocar Memória Excessiva")
    
    code_test3 = """
import numpy as np

# Tentar alocar array gigante e FORÇAR alocação real
# 5 milhões de elementos x 20 colunas x 8 bytes = 800MB
huge_array = np.random.rand(5_000_000, 20)  # random.rand FORÇA alocação imediata
resultado = f"Array criado: {huge_array.shape} (NÃO DEVERIA ACONTECER!)"
"""
    
    result3 = execute_in_sandbox(
        code=code_test3,
        timeout_seconds=10,
        memory_limit_mb=50  # Limite baixo (50MB)
    )
    
    # Esperamos falha (success=False) devido ao limite de memória
    test3_passed = print_result("Alocação excessiva (> limite)", result3, expected_success=False)
    
    # Verificar se erro é de memória
    if not result3.get('success'):
        error_type = result3.get('error_type')
        if error_type in ('MemoryLimitError', 'MemoryError', 'ExecutionError'):
            print(f"  ✅ Bloqueio de memória funcionou corretamente ({error_type})")
        else:
            print(f"  ⚠️ Erro inesperado: {error_type}")
    
    # ═══════════════════════════════════════════════════════════════
    # TESTE 4: Crescimento Gradual de Memória
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 4: Crescimento Gradual de Memória")
    
    code_test4 = """
import numpy as np

# Crescer memória gradualmente até atingir limite
arrays = []
total_mb = 0

for i in range(10):
    # Alocar ~5MB por iteração
    arr = np.zeros((625000,))  # 625k floats x 8 bytes = 5MB
    arrays.append(arr)
    total_mb += 5
    
resultado = {
    'arrays_allocated': len(arrays),
    'total_mb_attempted': total_mb,
    'status': 'completou sem erro'
}
"""
    
    result4 = execute_in_sandbox(
        code=code_test4,
        timeout_seconds=15,
        memory_limit_mb=40  # Limite de 40MB (deve permitir ~8 arrays)
    )
    
    test4_passed = print_result("Crescimento gradual de memória", result4, expected_success=False)
    
    # ═══════════════════════════════════════════════════════════════
    # TESTE 5: Lista Gigante (Memory Bomb)
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 5: Memory Bomb - Lista Gigante")
    
    code_test5 = """
# Tentar criar lista enorme
lista = []
for i in range(10_000_000):  # 10 milhões de elementos
    lista.append(i)
    
resultado = f"Lista criada com {len(lista)} elementos (NÃO DEVERIA ACONTECER!)"
"""
    
    result5 = execute_in_sandbox(
        code=code_test5,
        timeout_seconds=10,
        memory_limit_mb=30  # Limite baixo
    )
    
    test5_passed = print_result("Memory bomb (lista gigante)", result5, expected_success=False)
    
    # ═══════════════════════════════════════════════════════════════
    # TESTE 6: Loop Infinito + Alocação Gradual
    # ═══════════════════════════════════════════════════════════════
    print_header("TESTE 6: Loop Infinito com Alocação Gradual (Timeout + Memory)")
    
    code_test6 = """
import time

# Loop que aloca memória gradualmente
data = []
iteration = 0

while True:
    # Alocar ~1MB por iteração
    data.append([0] * 125000)  # 125k ints x 8 bytes ≈ 1MB
    iteration += 1
    time.sleep(0.01)  # 10ms por iteração
    
resultado = f"Iterações: {iteration}"
"""
    
    result6 = execute_in_sandbox(
        code=code_test6,
        timeout_seconds=3,  # Timeout curto
        memory_limit_mb=30  # Limite de memória
    )
    
    # Esperamos falha por timeout OU memória
    test6_passed = print_result("Loop infinito + alocação", result6, expected_success=False)
    
    if not result6.get('success'):
        error_type = result6.get('error_type')
        if error_type == 'TimeoutError':
            print(f"  ⏱️ Bloqueado por timeout (esperado)")
        elif error_type in ('MemoryLimitError', 'MemoryError'):
            print(f"  💾 Bloqueado por memória (esperado)")
    
    # ═══════════════════════════════════════════════════════════════
    # SUMÁRIO FINAL
    # ═══════════════════════════════════════════════════════════════
    print_header("📊 SUMÁRIO DOS TESTES DE MEMÓRIA")
    
    tests_results = {
        "Teste 1 - Código Leve": test1_passed,
        "Teste 2 - Código Moderado": test2_passed,
        "Teste 3 - Alocação Excessiva": test3_passed,
        "Teste 4 - Crescimento Gradual": test4_passed,
        "Teste 5 - Memory Bomb": test5_passed,
        "Teste 6 - Loop + Alocação": test6_passed
    }
    
    passed_count = sum(1 for passed in tests_results.values() if passed)
    total_count = len(tests_results)
    
    print(f"\n📊 Resultados:")
    for test_name, passed in tests_results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status} - {test_name}")
    
    print(f"\n🎯 RESULTADO GERAL: {passed_count}/{total_count} testes passaram ({passed_count/total_count*100:.1f}%)")
    
    # Memória final do processo
    final_memory = get_memory_usage_mb()
    if final_memory > 0 and initial_memory > 0:
        delta = final_memory - initial_memory
        print(f"\n📊 Memória do Processo:")
        print(f"   Inicial: {initial_memory:.2f}MB")
        print(f"   Final: {final_memory:.2f}MB")
        print(f"   Delta: {delta:+.2f}MB")
    
    # Validação da estratégia
    print(f"\n🔧 Validação da Estratégia:")
    if platform.system() in ('Linux', 'Darwin') and RESOURCE_AVAILABLE:
        print(f"   ✅ Unix/Linux detectado → Hard limit via resource.setrlimit()")
        print(f"   ✅ Limite de memória aplicado pelo kernel")
    elif PSUTIL_AVAILABLE:
        print(f"   ✅ Windows/Fallback detectado → Soft limit via psutil")
        print(f"   ⚠️ Monitoramento ativo (não é hard limit)")
    else:
        print(f"   ❌ ATENÇÃO: Nenhuma estratégia de limite disponível!")
        print(f"   ⚠️ Instale psutil: pip install psutil")
    
    if passed_count == total_count:
        print("\n🎉 SUCESSO TOTAL! Limite de memória funcionando perfeitamente!")
        print("✅ Sprint 3 P0-3 validado com sucesso")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} teste(s) falharam")
        print("❌ Revisar implementação do limite de memória")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
