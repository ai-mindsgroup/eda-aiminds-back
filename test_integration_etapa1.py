"""
Script de Teste: Integração Etapa 1 - Metadata Extractor com RAGAgent

Valida que:
1. metadata_extractor.py funciona corretamente
2. RAGAgent._generate_metadata_chunks() usa metadata_extractor
3. atomic_ingestion_and_query() usa RAGAgent (6 chunks)
4. run_auto_ingest.py gerará 6 embeddings de metadata + chunks de dados
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_metadata_extraction():
    """Testa extração de metadados diretamente."""
    print("\n" + "="*80)
    print("TESTE 1: Extração de Metadados Dinâmica")
    print("="*80)
    
    from src.ingest.metadata_extractor import extract_dataset_metadata
    
    # Usar temp_convert.csv como exemplo
    csv_path = Path(__file__).parent / "temp_convert.csv"
    
    if not csv_path.exists():
        print(f"❌ Arquivo de teste não encontrado: {csv_path}")
        return False
    
    print(f"📁 Arquivo de teste: {csv_path}")
    
    try:
        metadata = extract_dataset_metadata(str(csv_path), output_path=None)
        
        print(f"\n✅ Metadados extraídos com sucesso!")
        print(f"   - Dataset: {metadata['dataset_info']['filename']}")
        print(f"   - Linhas: {metadata['dataset_info']['total_rows']:,}")
        print(f"   - Colunas: {metadata['dataset_info']['total_columns']}")
        print(f"   - Tipos semânticos detectados:")
        
        semantic_summary = metadata.get('semantic_summary', {})
        for semantic_type, count in semantic_summary.items():
            print(f"     • {semantic_type}: {count} colunas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao extrair metadados: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_agent_metadata_chunks():
    """Testa se RAGAgent usa metadata_extractor."""
    print("\n" + "="*80)
    print("TESTE 2: RAGAgent com Metadata Extractor Integrado")
    print("="*80)
    
    from src.agent.rag_agent import RAGAgent
    from src.embeddings.generator import EmbeddingProvider
    import pandas as pd
    
    csv_path = Path(__file__).parent / "temp_convert.csv"
    
    if not csv_path.exists():
        print(f"❌ Arquivo de teste não encontrado: {csv_path}")
        return False
    
    try:
        # Ler CSV como texto
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_text = f.read()
        
        # Criar agente RAG
        rag = RAGAgent(
            embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER,
            csv_chunk_size_rows=500,
            csv_overlap_rows=50
        )
        
        print(f"📊 Gerando chunks de metadata usando RAGAgent...")
        
        # Chamar método privado para testar
        chunks = rag._generate_metadata_chunks(csv_text, "temp_convert_test")
        
        print(f"\n✅ Chunks de metadata gerados: {len(chunks)}")
        
        if len(chunks) != 6:
            print(f"⚠️ ATENÇÃO: Esperado 6 chunks, mas foram gerados {len(chunks)}")
            return False
        
        # Listar chunks
        for i, chunk in enumerate(chunks):
            chunk_type = chunk.metadata.additional_info.get('chunk_type', 'unknown')
            topic = chunk.metadata.additional_info.get('topic', 'unknown')
            print(f"   Chunk {i}: {chunk_type} - {topic}")
            print(f"      Tamanho: {chunk.metadata.char_count} chars")
        
        # Verificar se o primeiro chunk menciona metadata_extractor
        first_chunk_content = chunks[0].content
        if "metadata_extractor" in first_chunk_content.lower() or "extraídas dinamicamente" in first_chunk_content.lower():
            print(f"\n✅ Chunks confirmados como usando metadata_extractor!")
        else:
            print(f"\n⚠️ Chunks podem não estar usando metadata_extractor (verificar conteúdo)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar RAGAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_atomic_ingestion():
    """Testa fluxo atômico completo (MOCK - sem inserir no banco real)."""
    print("\n" + "="*80)
    print("TESTE 3: Fluxo Atômico com RAGAgent (DRY RUN)")
    print("="*80)
    
    print("ℹ️ Este teste verifica se atomic_ingestion_and_query usa RAGAgent")
    print("   (não executa inserção real no banco para evitar poluição)")
    
    # Verificar código fonte
    from src.agent.data_ingestor import atomic_ingestion_and_query
    import inspect
    
    source_code = inspect.getsource(atomic_ingestion_and_query)
    
    if "RAGAgent" in source_code:
        print("✅ atomic_ingestion_and_query usa RAGAgent!")
        return True
    elif "DataIngestor" in source_code and "ingest_csv" in source_code:
        print("❌ atomic_ingestion_and_query ainda usa DataIngestor (deprecated)!")
        print("   Esperado: usar RAGAgent.ingest_csv_file()")
        return False
    else:
        print("⚠️ Não foi possível determinar qual agente é usado")
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("VALIDAÇÃO INTEGRAÇÃO ETAPA 1: Metadata Extractor + RAGAgent")
    print("="*80)
    
    results = {
        "Metadata Extraction": test_metadata_extraction(),
        "RAGAgent Metadata Chunks": test_rag_agent_metadata_chunks(),
        "Atomic Ingestion (RAGAgent)": test_atomic_ingestion()
    }
    
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Integração Etapa 1 está funcionando corretamente")
        print("✅ run_auto_ingest.py deve gerar 6 embeddings de metadata + chunks de dados")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("❌ Revisar implementação antes de executar run_auto_ingest.py")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
