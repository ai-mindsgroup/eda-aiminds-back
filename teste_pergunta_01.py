"""
Teste da Pergunta 01: Quais são os tipos de dados?
"""
from src.agent.rag_agent import RAGAgent

print("="*70)
print("🧪 TESTE: PERGUNTA 01 - TIPOS DE DADOS")
print("="*70)

# Inicializar agente
agent = RAGAgent('rag_agent')

# Pergunta 01
pergunta = "Quais são os tipos de dados de cada coluna no dataset creditcard?"

print(f"\n❓ PERGUNTA:\n{pergunta}\n")
print("🔍 Buscando resposta no RAG...\n")

# Fazer query
try:
    resposta = agent.process(pergunta)  # ← Método correto é 'process'
    
    print("="*70)
    print("💬 RESPOSTA DO AGENTE:")
    print("="*70)
    print(resposta.get('response', 'Sem resposta'))
    print("\n")
    
    # Metadados
    metadata = resposta.get('metadata', {})
    print("="*70)
    print("📊 METADADOS:")
    print("="*70)
    print(f"  • Chunks recuperados: {metadata.get('chunks_retrieved', 0)}")
    print(f"  • Provedor LLM: {metadata.get('llm_provider', 'N/A')}")
    print(f"  • Modelo: {metadata.get('llm_model', 'N/A')}")
    print(f"  • Tokens usados: {metadata.get('tokens_used', 'N/A')}")
    print(f"  • Tempo de resposta: {metadata.get('response_time', 0):.2f}s")
    
    # Mostrar chunks recuperados
    if 'chunks' in metadata and metadata['chunks']:
        print("\n" + "="*70)
        print("📄 CHUNKS RECUPERADOS:")
        print("="*70)
        for i, chunk in enumerate(metadata['chunks'][:3], 1):
            chunk_type = chunk.get('metadata', {}).get('chunk_type', 'N/A')
            similarity = chunk.get('similarity', 0)
            preview = chunk.get('content', '')[:150]
            print(f"\n[{i}] Tipo: {chunk_type} | Similaridade: {similarity:.3f}")
            print(f"    {preview}...")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ TESTE CONCLUÍDO")
print("="*70)
