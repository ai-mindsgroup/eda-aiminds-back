"""Teste direto do fallback de visualização sem interface."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from src.agent.orchestrator_agent import OrchestratorAgent

async def test_visualization_fallback():
    """Testa o fallback de visualização diretamente."""
    print("=" * 70)
    print("TESTE: Fallback de Visualização com EmbeddingsAnalysisAgent")
    print("=" * 70)
    
    # Inicializar orquestrador
    print("\n1. Inicializando OrchestratorAgent...")
    orchestrator = OrchestratorAgent()
    print("   ✅ Orquestrador inicializado")
    
    # Query de visualização
    query = "Qual a distribuição de cada variável (histogramas, distribuições)?"
    print(f"\n2. Enviando query: '{query}'")
    
    # Processar com memória persistente
    print("\n3. Processando query...")
    try:
        response = await orchestrator.process_with_persistent_memory(query)
        print("\n4. Resposta recebida:")
        print(f"   Tipo: {response.get('query_type')}")
        print(f"   Agentes: {response.get('agents_used')}")
        print(f"   Resposta: {response.get('response', '')[:200]}...")
        
        # Verificar metadados
        metadata = response.get('metadata', {})
        if 'fallback_used' in metadata:
            print(f"\n5. ✅ FALLBACK ACIONADO")
            print(f"   Chunks amostrados: {metadata.get('sampled_chunks')}")
            print(f"   Linhas reconstruídas: {metadata.get('reconstructed_rows')}")
        
        # Verificar gráficos gerados
        print("\n6. Verificando arquivos gerados...")
        histogramas_dir = "outputs/histogramas"
        if os.path.exists(histogramas_dir):
            files = os.listdir(histogramas_dir)
            png_files = [f for f in files if f.endswith('.png')]
            print(f"   Arquivos PNG encontrados: {len(png_files)}")
            for png in png_files[:5]:  # Mostrar primeiros 5
                print(f"   - {png}")
        else:
            print(f"   ⚠️  Diretório {histogramas_dir} não encontrado")
        
        print("\n✅ TESTE CONCLUÍDO")
        
    except Exception as e:
        print(f"\n❌ ERRO: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_visualization_fallback())
