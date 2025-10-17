"""
Teste rápido: Verificar se limite de memória está ativo em produção
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from security.sandbox import execute_in_sandbox

# Executar código simples
result = execute_in_sandbox('resultado = 42', memory_limit_mb=100)

print(f"✅ Sucesso: {result['success']}")
print(f"✅ Resultado: {result['result']}")

# Verificar logs de memória
memory_logs = [log for log in result['logs'] if 'Limite' in log or 'memory' in log.lower() or 'memória' in log.lower()]
print(f"\n📊 Logs de Memória/Limite:")
for log in memory_logs:
    print(f"  {log}")

print(f"\n🔒 Limite de memória ATIVO em produção: {len(memory_logs) > 0}")
