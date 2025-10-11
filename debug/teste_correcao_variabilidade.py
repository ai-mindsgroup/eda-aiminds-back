"""
Script de teste rápido para validar correção de variabilidade
"""
import sys
sys.path.insert(0, '.')

from src.agent.orchestrator_agent import OrchestratorAgent

print("="*80)
print("🧪 TESTE: Correção de Variabilidade")
print("="*80)

# Inicializar orquestrador
print("\n🤖 Inicializando orquestrador...")
orchestrator = OrchestratorAgent()

# Teste 1: Pergunta sobre variabilidade
print("\n" + "="*80)
print("📊 TESTE 1: Pergunta sobre VARIABILIDADE (desvio padrão, variância)")
print("="*80)

query = "Qual a variabilidade dos dados (desvio padrão, variância)?"
print(f"\n❓ Pergunta: {query}")
print("\n🔄 Processando...\n")

response = orchestrator.process(query)
print(response.get('response', 'Sem resposta'))

# Validação
if 'Desvio Padrão' in response.get('response', '') or 'desvio' in response.get('response', '').lower():
    print("\n✅ SUCESSO: Resposta contém 'Desvio Padrão'")
else:
    print("\n❌ FALHA: Resposta NÃO contém 'Desvio Padrão'")

if 'Variância' in response.get('response', '') or 'variancia' in response.get('response', '').lower():
    print("✅ SUCESSO: Resposta contém 'Variância'")
else:
    print("❌ FALHA: Resposta NÃO contém 'Variância'")

if 'Mínimo' not in response.get('response', '') and 'Máximo' not in response.get('response', ''):
    print("✅ SUCESSO: Resposta NÃO contém 'Mínimo/Máximo' (correto!)")
else:
    print("❌ FALHA: Resposta ainda contém 'Mínimo/Máximo' (incorreto!)")

# Teste 2: Pergunta sobre intervalo (para confirmar que não foi quebrado)
print("\n" + "="*80)
print("📊 TESTE 2: Pergunta sobre INTERVALO (mínimo, máximo)")
print("="*80)

query2 = "Qual o intervalo de cada variável (mínimo e máximo)?"
print(f"\n❓ Pergunta: {query2}")
print("\n🔄 Processando...\n")

response2 = orchestrator.process(query2)
print(response2.get('response', 'Sem resposta')[:500] + "...")

# Validação
if 'Mínimo' in response2.get('response', '') or 'minimo' in response2.get('response', '').lower():
    print("\n✅ SUCESSO: Resposta contém 'Mínimo'")
else:
    print("\n❌ FALHA: Resposta NÃO contém 'Mínimo'")

print("\n" + "="*80)
print("🎯 TESTE CONCLUÍDO")
print("="*80)
