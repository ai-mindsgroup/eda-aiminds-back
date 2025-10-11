"""
Teste completo RAG: Verifica se a pergunta sobre intervalos é respondida corretamente
"""
from src.agent.rag_agent import RAGAgent
import pandas as pd

print("="*70)
print("🔍 TESTE COMPLETO RAG - PERGUNTA 03: INTERVALOS")
print("="*70)

# Carregar CSV
print("\n📂 Carregando CSV...")
df = pd.read_csv("data/creditcard.csv")
print(f"✅ CSV carregado: {len(df)} linhas\n")

# Criar agente RAG
print("🤖 Inicializando RAGAgent...")
rag_agent = RAGAgent()
print("✅ RAGAgent inicializado\n")

# Pergunta do usuário
pergunta = "Qual o intervalo de cada variável (mínimo, máximo)?"
print(f"❓ PERGUNTA: {pergunta}\n")

# Processar pergunta com RAG
print("🔍 Processando pergunta com RAG...")
print("-" * 70)
resultado = rag_agent.process(pergunta)
print("-" * 70)

print(f"\n💬 RESPOSTA:\n")
print(resultado.get('content', 'Sem resposta'))

print("\n" + "="*70)
print("✅ TESTE CONCLUÍDO")
print("="*70)
