"""Script para testar as correções implementadas.

Este script valida:
1. Nome do agente correto na saída (embeddings_analyzer)
2. Exibição completa de todas as variáveis (31 no total)
"""
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Forçar recarga dos módulos modificados
import importlib
if 'src.agent.orchestrator_agent' in sys.modules:
    del sys.modules['src.agent.orchestrator_agent']
if 'src.agent.csv_analysis_agent' in sys.modules:
    del sys.modules['src.agent.csv_analysis_agent']

from src.agent.orchestrator_agent import OrchestratorAgent

def test_central_tendency_full():
    """Testa se todas as variáveis são exibidas."""
    
    print("="*80)
    print("TESTE: Medidas de Tendência Central - Exibição Completa")
    print("="*80)
    print()
    
    # Criar nova instância do agente
    print("🔄 Criando nova instância do OrchestratorAgent...")
    agent = OrchestratorAgent()
    print("✅ Agente inicializado")
    print()
    
    # Fazer pergunta sobre medidas de tendência central
    query = "Quais são as medidas de tendência central (média, mediana)?"
    
    print(f"❓ Pergunta: {query}")
    print()
    print("🔄 Processando...")
    print()
    
    # Processar consulta
    response = agent.process(query)
    
    # Exibir resposta
    print("="*80)
    print("RESPOSTA DO AGENTE:")
    print("="*80)
    print()
    
    content = response.get('content', response)
    print(content)
    print()
    
    # Verificar metadados
    metadata = response.get('metadata', {})
    print("="*80)
    print("VERIFICAÇÃO:")
    print("="*80)
    print()
    
    # 1. Verificar nome do agente
    agents_used = metadata.get('agents_used', [])
    agent_name = agents_used[0] if agents_used else 'N/A'
    
    if agent_name == 'embeddings_analyzer':
        print("✅ CORRETO: Nome do agente = 'embeddings_analyzer'")
    else:
        print(f"❌ INCORRETO: Nome do agente = '{agent_name}' (esperado: 'embeddings_analyzer')")
    
    # 2. Verificar se todas as variáveis estão sendo exibidas
    if '... e mais' in content:
        print("❌ INCORRETO: Ainda há variáveis ocultas (mensagem '... e mais')")
    else:
        # Contar quantas linhas de variáveis existem na tabela
        lines = content.split('\n')
        table_lines = [l for l in lines if l.startswith('| ') and not l.startswith('| Variável')]
        
        if len(table_lines) >= 31:
            print(f"✅ CORRETO: Todas as variáveis exibidas ({len(table_lines)} linhas na tabela)")
        else:
            print(f"⚠️  PARCIAL: {len(table_lines)} variáveis exibidas (esperado: 31)")
    
    # 3. Verificar conformidade
    if 'embeddings_only' in str(metadata.get('conformidade', '')):
        print("✅ CORRETO: Conformidade mantida (embeddings_only)")
    
    # 4. Verificar query type
    if metadata.get('query_type') == 'central_tendency':
        print("✅ CORRETO: Query type = 'central_tendency'")
    
    print()
    print("="*80)
    print("METADADOS COMPLETOS:")
    print("="*80)
    print()
    print(f"• Agentes usados: {agents_used}")
    print(f"• Total de registros: {metadata.get('total_records', 'N/A')}")
    print(f"• Colunas numéricas: {metadata.get('total_numeric_columns', 'N/A')}")
    print(f"• Query type: {metadata.get('query_type', 'N/A')}")
    print(f"• Conformidade: {metadata.get('conformidade', 'N/A')}")
    print()

if __name__ == "__main__":
    test_central_tendency_full()
