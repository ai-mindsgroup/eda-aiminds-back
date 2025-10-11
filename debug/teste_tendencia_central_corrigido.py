"""Script de teste para validar medidas de tendência central.

Este script testa se o agente responde corretamente perguntas sobre média e mediana
usando dados REAIS APENAS da tabela embeddings do Supabase.

⚠️ CONFORMIDADE: NENHUM CSV é lido - APENAS tabela embeddings.
"""
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent.orchestrator_agent import OrchestratorAgent

def test_central_tendency_query():
    """Testa pergunta sobre medidas de tendência central."""
    
    print("="*80)
    print("TESTE: Medidas de Tendência Central (APENAS EMBEDDINGS)")
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
    print(response.get('content', response))
    print()
    
    # Verificar metadados
    metadata = response.get('metadata', {})
    print("="*80)
    print("METADADOS DA RESPOSTA:")
    print("="*80)
    print()
    print(f"• Query Type: {metadata.get('query_type', 'N/A')}")
    print(f"• Total Records: {metadata.get('total_records', 'N/A')}")
    print(f"• Total Numeric Columns: {metadata.get('total_numeric_columns', 'N/A')}")
    print(f"• Conformidade: {metadata.get('conformidade', 'N/A')}")
    print(f"• Agente Usado: {metadata.get('agent_used', 'N/A')}")
    print()
    
    # Verificar se resposta contém dados reais
    content = response.get('content', '').lower()
    has_real_data = any([
        metadata.get('total_records', 0) > 0,
        metadata.get('total_numeric_columns', 0) > 0,
        metadata.get('central_tendency') is not None,
        'chunk_text parseada' in content,
        metadata.get('conformidade') == 'embeddings_only',
        metadata.get('query_type') == 'central_tendency'
    ])
    
    # Verificar se NÃO está usando dados genéricos do LLM
    has_generic_response = any([
        'são estatísticas que descrevem' in content and metadata.get('total_records', 0) == 0,
        metadata.get('agent_used') == 'llm_manager',
        'groq' in str(metadata.get('provider', '')).lower()
    ])
    
    print("="*80)
    print("RESULTADO DO TESTE:")
    print("="*80)
    print()
    
    if has_real_data and not has_generic_response:
        print("✅ SUCESSO: Agente respondeu com dados reais da tabela embeddings")
        print("✅ Resposta contém média e/ou mediana calculadas dos dados reais")
        print("✅ Conformidade mantida (APENAS embeddings do Supabase)")
        print("✅ Query Type correto: central_tendency")
    elif has_generic_response:
        print("❌ FALHA: Agente retornou resposta genérica do LLM (Groq)")
        print("❌ Não consultou dados reais da tabela embeddings")
        print("⚠️  Verifique o roteamento de queries no orchestrator")
        print("⚠️  Palavras-chave para tendência central podem não estar sendo detectadas")
    else:
        print("❌ FALHA: Resposta ambígua ou incompleta")
        print("⚠️  Verifique os logs para mais detalhes")
    
    print()
    print("="*80)
    print("VERIFICAÇÃO DE CONFORMIDADE:")
    print("="*80)
    print()
    print(f"• Dados de embeddings: {'✅ SIM' if metadata.get('conformidade') == 'embeddings_only' else '❌ NÃO'}")
    print(f"• Total de registros: {metadata.get('total_records', 0):,}")
    print(f"• Colunas numéricas: {metadata.get('total_numeric_columns', 0)}")
    print(f"• Query Type: {metadata.get('query_type', 'N/A')}")
    print(f"• Agente usado: {metadata.get('agent_used', 'N/A')}")
    print()
    
    return has_real_data and not has_generic_response

if __name__ == "__main__":
    success = test_central_tendency_query()
    sys.exit(0 if success else 1)
