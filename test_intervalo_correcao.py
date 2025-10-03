"""
Script de teste para validar correção da pergunta sobre intervalos (min/max).
Testa se o sistema agora consulta corretamente os dados da tabela embeddings.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.orchestrator_agent import OrchestratorAgent


def test_intervalo_query():
    """Testa a pergunta sobre intervalos das variáveis."""
    print("\n" + "="*80)
    print("🧪 TESTE: Pergunta sobre intervalos (mínimo/máximo)")
    print("="*80 + "\n")
    
    # Criar orquestrador
    orchestrator = OrchestratorAgent()
    
    # Fazer a pergunta
    query = "Qual o intervalo de cada variável (mínimo, máximo)?"
    print(f"❓ Pergunta: {query}\n")
    print("🔄 Processando...\n")
    
    # Processar
    result = orchestrator.process(query)
    
    # Exibir resultado
    print("="*80)
    print("📊 RESULTADO:")
    print("="*80)
    print(result.get('content', 'Sem resposta'))
    print("\n" + "="*80)
    
    # Exibir metadados
    metadata = result.get('metadata', {})
    print("\n📋 METADADOS:")
    print(f"   • Agentes utilizados: {metadata.get('agents_used', [])}")
    print(f"   • Tipo de query: {metadata.get('query_type', 'N/A')}")
    print(f"   • Conformidade: {metadata.get('conformidade', 'N/A')}")
    
    if metadata.get('error'):
        print(f"   ⚠️ Erro: {metadata.get('error')}")
    else:
        print(f"   ✅ Sucesso!")
        if 'total_records' in metadata:
            print(f"   • Total de registros: {metadata['total_records']:,}")
        if 'total_numeric_columns' in metadata:
            print(f"   • Colunas numéricas: {metadata['total_numeric_columns']}")
    
    print("="*80 + "\n")
    
    return result


if __name__ == "__main__":
    try:
        result = test_intervalo_query()
        
        # Validar se a resposta está correta
        if 'Mínimo' in result.get('content', '') and 'Máximo' in result.get('content', ''):
            print("✅ TESTE PASSOU: Resposta contém estatísticas de mínimo e máximo")
            exit(0)
        else:
            print("❌ TESTE FALHOU: Resposta não contém estatísticas esperadas")
            exit(1)
            
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
