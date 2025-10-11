"""
Script para testar pergunta sobre intervalos com instância NOVA do agente.
Garante que as alterações de código sejam aplicadas.
"""

import sys
from pathlib import Path

# Garantir que o módulo seja recarregado
if 'src.agent.orchestrator_agent' in sys.modules:
    del sys.modules['src.agent.orchestrator_agent']
if 'src.agent.csv_analysis_agent' in sys.modules:
    del sys.modules['src.agent.csv_analysis_agent']

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.orchestrator_agent import OrchestratorAgent


def main():
    print("\n" + "="*80)
    print("🧪 TESTE COM INSTÂNCIA NOVA DO AGENTE")
    print("="*80 + "\n")
    
    print("🔄 Criando nova instância do OrchestratorAgent...")
    orchestrator = OrchestratorAgent()
    print("✅ Agente criado\n")
    
    # Fazer a pergunta
    query = "Qual o intervalo de cada variável (mínimo, máximo)?"
    print(f"❓ Pergunta: {query}\n")
    print("🔄 Processando...\n")
    print("-"*80 + "\n")
    
    # Processar
    result = orchestrator.process(query)
    
    # Exibir resultado
    print("\n" + "="*80)
    print("📊 RESPOSTA DO AGENTE:")
    print("="*80)
    print(result.get('content', 'Sem resposta'))
    
    # Exibir metadados
    print("\n" + "="*80)
    print("📋 METADADOS:")
    print("="*80)
    metadata = result.get('metadata', {})
    print(f"✓ Agentes utilizados: {metadata.get('agents_used', [])}")
    print(f"✓ Tipo de query: {metadata.get('query_type', 'N/A')}")
    print(f"✓ Conformidade: {metadata.get('conformidade', 'N/A')}")
    
    if metadata.get('error'):
        print(f"✗ Erro: {metadata.get('error')}")
        return False
    else:
        if 'total_records' in metadata:
            print(f"✓ Total de registros: {metadata['total_records']:,}")
        if 'total_numeric_columns' in metadata:
            print(f"✓ Colunas numéricas: {metadata['total_numeric_columns']}")
        if 'statistics' in metadata and len(metadata['statistics']) > 0:
            print(f"✓ Estatísticas calculadas: {len(metadata['statistics'])} variáveis")
            # Mostrar algumas estatísticas
            print("\n📊 Primeiras variáveis:")
            for stat in metadata['statistics'][:5]:
                var = stat['variavel']
                vmin = stat['minimo']
                vmax = stat['maximo']
                print(f"   • {var}: min={vmin:.2f}, max={vmax:.2f}")
    
    print("="*80 + "\n")
    
    # Validar resposta
    content = result.get('content', '')
    if 'Mínimo' in content and 'Máximo' in content and 'embeddings' in content.lower():
        print("✅ SUCESSO: Resposta contém estatísticas reais dos dados da tabela embeddings!")
        return True
    else:
        print("❌ FALHA: Resposta não contém estatísticas esperadas ou não consultou embeddings")
        return False


if __name__ == "__main__":
    try:
        sucesso = main()
        exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
