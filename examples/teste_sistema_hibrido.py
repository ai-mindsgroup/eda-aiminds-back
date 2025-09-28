#!/usr/bin/env python3
"""
Teste Sistema Híbrido LLM + RAG - Cache Inteligente
==================================================

Testa se o GoogleLLMAgent agora:
1. Primeira consulta → chama Google Gemini + salva no banco
2. Segunda consulta similar → usa cache (não chama Gemini)
3. Consulta diferente → chama Gemini novamente
"""

import sys
from pathlib import Path
import time

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.agent.orchestrator_agent import OrchestratorAgent
from src.vectorstore.supabase_client import supabase

def contar_embeddings():
    """Conta embeddings no banco."""
    try:
        result = supabase.table('embeddings').select('id').execute()
        return len(result.data)
    except Exception as e:
        print(f"Erro ao contar embeddings: {e}")
        return 0

def main():
    print("🧪 TESTE SISTEMA HÍBRIDO LLM + RAG")
    print("=" * 60)
    
    # Limpar banco para teste limpo (opcional)
    try:
        supabase.table('embeddings').delete().neq('id', 'dummy').execute()
        print("🧹 Banco vetorial limpo para teste")
    except:
        pass
    
    # Contar embeddings iniciais
    embeddings_initial = contar_embeddings()
    print(f"📊 Embeddings iniciais: {embeddings_initial}")
    
    # Inicializar sistema
    print("\n🤖 Inicializando orquestrador...")
    orchestrator = OrchestratorAgent()
    print()
    
    # TESTE 1: Primeira consulta (deve ir para LLM + salvar)
    print("🔍 TESTE 1: Primeira consulta - deve usar LLM")
    print("=" * 50)
    query1 = "explique os principais padrões de fraude financeira"
    
    print(f"❓ Query: '{query1}'")
    start_time = time.time()
    
    result1 = orchestrator.process(query1)
    
    duration1 = time.time() - start_time
    metadata1 = result1.get('metadata', {})
    orchestrator_meta1 = metadata1.get('orchestrator', {})
    
    print(f"⏱️ Tempo: {duration1:.2f}s")
    print(f"🤖 Agentes: {orchestrator_meta1.get('agents_used', [])}")
    print(f"🧠 LLM usado: {metadata1.get('llm_used', False)}")
    print(f"💾 Cache usado: {metadata1.get('cache_used', False)}")
    print(f"📝 Resposta: {len(result1.get('content', ''))} caracteres")
    
    # Verificar se foi salvo no banco
    embeddings_after_1 = contar_embeddings()
    novos_embeddings_1 = embeddings_after_1 - embeddings_initial
    print(f"📊 Novos embeddings: {novos_embeddings_1}")
    print()
    
    # TESTE 2: Consulta similar (deve usar cache)
    print("🔍 TESTE 2: Consulta similar - deve usar CACHE")
    print("=" * 50)
    query2 = "quais são os padrões de fraude em transações financeiras"  # Similar
    
    print(f"❓ Query: '{query2}'")
    start_time = time.time()
    
    result2 = orchestrator.process(query2)
    
    duration2 = time.time() - start_time
    metadata2 = result2.get('metadata', {})
    orchestrator_meta2 = metadata2.get('orchestrator', {})
    
    print(f"⏱️ Tempo: {duration2:.2f}s")
    print(f"🤖 Agentes: {orchestrator_meta2.get('agents_used', [])}")
    print(f"🧠 LLM usado: {metadata2.get('llm_used', False)}")
    print(f"💾 Cache usado: {metadata2.get('cache_used', False)}")
    
    if metadata2.get('cache_used'):
        similarity = metadata2.get('similarity_score', 0)
        print(f"🎯 Similaridade: {similarity:.3f}")
    
    print(f"📝 Resposta: {len(result2.get('content', ''))} caracteres")
    
    # Verificar se NÃO criou novos embeddings
    embeddings_after_2 = contar_embeddings()
    novos_embeddings_2 = embeddings_after_2 - embeddings_after_1
    print(f"📊 Novos embeddings: {novos_embeddings_2}")
    print()
    
    # TESTE 3: Consulta diferente (deve ir para LLM novamente)
    print("🔍 TESTE 3: Consulta diferente - deve usar LLM")
    print("=" * 50)
    query3 = "como analisar correlações em datasets de vendas"  # Diferente
    
    print(f"❓ Query: '{query3}'")
    start_time = time.time()
    
    result3 = orchestrator.process(query3)
    
    duration3 = time.time() - start_time
    metadata3 = result3.get('metadata', {})
    orchestrator_meta3 = metadata3.get('orchestrator', {})
    
    print(f"⏱️ Tempo: {duration3:.2f}s")
    print(f"🤖 Agentes: {orchestrator_meta3.get('agents_used', [])}")
    print(f"🧠 LLM usado: {metadata3.get('llm_used', False)}")
    print(f"💾 Cache usado: {metadata3.get('cache_used', False)}")
    print(f"📝 Resposta: {len(result3.get('content', ''))} caracteres")
    
    # Verificar se criou novos embeddings
    embeddings_final = contar_embeddings()
    novos_embeddings_3 = embeddings_final - embeddings_after_2
    print(f"📊 Novos embeddings: {novos_embeddings_3}")
    print()
    
    # RESULTADOS FINAIS
    print("🏁 RESULTADOS DO TESTE")
    print("=" * 60)
    print(f"📊 Total embeddings criados: {embeddings_final - embeddings_initial}")
    print()
    
    # Análise dos resultados
    success_count = 0
    
    print("📋 Análise dos resultados:")
    
    # Teste 1: Deve usar LLM e criar embedding
    if metadata1.get('llm_used') and not metadata1.get('cache_used') and novos_embeddings_1 > 0:
        print("✅ Teste 1: SUCESSO - LLM usado + embedding salvo")
        success_count += 1
    else:
        print("❌ Teste 1: FALHOU - deveria usar LLM e salvar")
    
    # Teste 2: Deve usar cache e não criar embedding
    if metadata2.get('cache_used') and not metadata2.get('llm_used') and novos_embeddings_2 == 0:
        print("✅ Teste 2: SUCESSO - Cache usado + sem novos embeddings")
        success_count += 1
    else:
        print("❌ Teste 2: FALHOU - deveria usar cache")
    
    # Teste 3: Deve usar LLM e criar embedding
    if metadata3.get('llm_used') and not metadata3.get('cache_used') and novos_embeddings_3 > 0:
        print("✅ Teste 3: SUCESSO - LLM usado + embedding salvo")
        success_count += 1
    else:
        print("❌ Teste 3: FALHOU - deveria usar LLM e salvar")
    
    print()
    print(f"🎯 Sucessos: {success_count}/3")
    
    if success_count == 3:
        print("🎉 SISTEMA HÍBRIDO FUNCIONANDO PERFEITAMENTE!")
        print("   ✅ Cache inteligente operacional")
        print("   ✅ Fallback para LLM funcionando")
        print("   ✅ Persistência no banco vetorial")
    elif success_count >= 2:
        print("⚠️ Sistema funcionando com algumas falhas")
    else:
        print("❌ Sistema híbrido com problemas sérios")

if __name__ == "__main__":
    main()