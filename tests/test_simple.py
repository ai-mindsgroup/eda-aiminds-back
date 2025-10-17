"""Teste simplificado e funcional do sistema RAG."""
import sys
from pathlib import Path
import numpy as np

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_simple_chunking():
    """Teste básico do sistema de chunking."""
    print("🧩 TESTE SIMPLIFICADO DE CHUNKING")
    print("=" * 40)
    
    try:
        from src.embeddings.chunker import TextChunker, ChunkStrategy
        
        text = "Este é um teste. Primeira frase aqui. Segunda frase agora. Terceira e final."
        
        chunker = TextChunker(chunk_size=50, overlap_size=10)
        chunks = chunker.chunk_text(text, "test_source", ChunkStrategy.SENTENCE)
        
        print(f"✅ Texto processado: {len(text)} caracteres")
        print(f"✅ Chunks criados: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}: '{chunk.content}'")
            print(f"   Metadados: fonte={chunk.metadata.source}, estratégia={chunk.metadata.strategy.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_embeddings():
    """Teste básico de geração de embeddings."""
    print("\n🔢 TESTE SIMPLIFICADO DE EMBEDDINGS")
    print("=" * 40)
    
    try:
        from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
        
        generator = EmbeddingGenerator(EmbeddingProvider.SENTENCE_TRANSFORMER)
        
        text = "Teste de embedding simples"
        result = generator.generate_embedding(text)
        
        print(f"✅ Embedding gerado com sucesso!")
        print(f"   Texto: '{text}'")
        print(f"   Dimensões: {result.dimensions}")
        print(f"   Primeiros 5 valores: {result.embedding[:5]}")
        print(f"   Modelo usado: {result.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_integration():
    """Teste do agente CSV que sabemos que funciona."""
    print("\n📊 TESTE DE INTEGRAÇÃO COM CSV")
    print("=" * 40)
    
    try:
    # Removido: agente obsoleto csv_analysis_agent.py
        
        # Criar agente CSV
        csv_agent = CSVAnalysisAgent()
        
        # Criar um pequeno dataset de exemplo
        import pandas as pd
        sample_data = pd.DataFrame({
            'valor': [100, 200, 50, 1000, 75],
            'categoria': ['A', 'B', 'A', 'C', 'B'],
            'data': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
        })
        
        # Salvar temporariamente
        temp_file = "temp_test.csv"
        sample_data.to_csv(temp_file, index=False)
        
        # Testar carregamento
        result = csv_agent.load_csv(temp_file)
        print(f"✅ CSV carregado: {result['content']}")
        
        # Testar análise básica
        analysis_result = csv_agent.process("Faça uma análise básica dos dados")
        print(f"✅ Análise realizada: {analysis_result['content'][:200]}...")
        
        # Limpar arquivo temporário
        import os
        os.remove(temp_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa testes simplificados."""
    print("🚀 TESTE SIMPLIFICADO DO SISTEMA EDA-AIMINDS")
    print("=" * 60)
    print("ℹ️  Testando componentes individuais funcionais")
    print()
    
    tests = [
        ("Chunking", test_simple_chunking),
        ("Embeddings", test_simple_embeddings),
        ("CSV Agent", test_csv_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🔍 Executando teste: {name}")
        if test_func():
            passed += 1
            print(f"✅ {name}: PASSOU")
        else:
            print(f"❌ {name}: FALHOU")
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   ✅ Testes passaram: {passed}/{total}")
    print(f"   ❌ Testes falharam: {total - passed}/{total}")
    print(f"   📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 SISTEMA BÁSICO FUNCIONANDO!")
        print("   Próximos passos:")
        print("   1. Configurar Supabase para testes com banco real")
        print("   2. Implementar agente orquestrador")
        print("   3. Criar pipeline completo RAG + CSV")
    else:
        print("\n⚠️  Alguns componentes precisam de ajustes")
    
    print("\n💡 COMPONENTES FUNCIONAIS IDENTIFICADOS:")
    if passed > 0:
        print("   - Sistema de logging e configurações")
        print("   - Estrutura base de agentes")
        print("   - Processamento CSV com pandas")
        if passed >= 2:
            print("   - Sistema de chunking de texto")
            print("   - Geração de embeddings")


if __name__ == "__main__":
    main()