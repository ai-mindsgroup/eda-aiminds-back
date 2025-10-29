"""
Carrega dados do CSV na tabela embeddings para testes.
"""

import sys
sys.path.insert(0, '.')

from src.agent.rag_data_agent_v4 import RAGDataAgentV4 as RAGDataAgent
from pathlib import Path

print("="*80)
print("📂 CARREGANDO DADOS DO CSV PARA EMBEDDINGS")
print("="*80)

# Verificar se arquivo CSV existe
csv_path = "data/creditcard_test_500.csv"
if not Path(csv_path).exists():
    print(f"\n❌ Arquivo não encontrado: {csv_path}")
    print("   Tentando arquivo completo...")
    csv_path = "data/creditcard.csv"
    
if not Path(csv_path).exists():
    print(f"\n❌ Arquivo não encontrado: {csv_path}")
    print("   Por favor, coloque um arquivo CSV em data/")
    sys.exit(1)

print(f"\n✅ Arquivo encontrado: {csv_path}")

# Inicializar agente
agent = RAGDataAgent()

# Carregar CSV
print("\n🔄 Iniciando carregamento...")
result = agent.load_csv_to_embeddings(
    csv_path=csv_path,
    chunk_size=50,  # Chunks menores para teste
    overlap=10
)

print("\n" + "="*80)
print("📊 RESULTADO")
print("="*80)
print(result.get('response', 'Sem resposta'))

metadata = result.get('metadata', {})
if metadata:
    print("\n📈 Estatísticas:")
    print(f"  - Linhas do CSV: {metadata.get('total_rows', 0)}")
    print(f"  - Colunas: {metadata.get('total_columns', 0)}")
    print(f"  - Chunks criados: {metadata.get('chunks_created', 0)}")
    print(f"  - Chunks inseridos: {metadata.get('chunks_inserted', 0)}")

print("="*80)
