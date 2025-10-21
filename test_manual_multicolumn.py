"""Teste manual rápido para validar chunking multi-coluna."""

import sys
from pathlib import Path

# Adicionar src ao path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Imports
from src.embeddings.chunker import TextChunker, ChunkStrategy

# CSV de teste
SAMPLE_CSV = """Time,V1,V2,V3,Amount,Class
1000.0,1.5,2.3,3.1,100.50,0
2000.0,-0.8,1.2,-1.5,250.00,0
3000.0,0.5,0.9,0.3,75.25,1
4000.0,2.1,-1.3,1.8,500.00,0
5000.0,-1.2,0.4,-0.6,150.00,1
"""

def test_csv_column_chunking():
    """Testa chunking por coluna."""
    print("=" * 80)
    print("TESTE: Chunking por COLUNA (CSV_COLUMN)")
    print("=" * 80)
    
    chunker = TextChunker(chunk_size=500, overlap_size=50, min_chunk_size=50)
    
    try:
        chunks = chunker.chunk_text(
            text=SAMPLE_CSV,
            source_id="test_creditcard.csv",
            strategy=ChunkStrategy.CSV_COLUMN
        )
        
        print(f"\n✅ SUCCESS: {len(chunks)} chunks gerados\n")
        
        # Mostrar resumo dos chunks
        for i, chunk in enumerate(chunks):
            info = chunk.metadata.additional_info
            chunk_type = info.get('chunk_type', 'unknown')
            column_name = info.get('column_name', 'N/A')
            is_numeric = info.get('is_numeric', 'N/A')
            
            print(f"Chunk {i}:")
            print(f"  - Type: {chunk_type}")
            print(f"  - Column: {column_name}")
            print(f"  - Is Numeric: {is_numeric}")
            print(f"  - Content Length: {len(chunk.content)} chars")
            
            # Mostrar primeiras 3 linhas do conteúdo
            lines = chunk.content.split('\n')[:3]
            print(f"  - Preview:")
            for line in lines:
                print(f"    {line}")
            print()
        
        # Validações
        assert len(chunks) >= 7, f"Esperado pelo menos 7 chunks (1 metadata + 6 colunas), obteve {len(chunks)}"
        
        # Verificar metadata chunk
        metadata_chunk = chunks[0]
        assert metadata_chunk.metadata.additional_info.get('chunk_type') == 'metadata'
        print("✅ Metadata chunk validado")
        
        # Verificar column chunks
        column_chunks = chunks[1:]
        expected_columns = ['Time', 'V1', 'V2', 'V3', 'Amount', 'Class']
        found_columns = [c.metadata.additional_info.get('column_name') for c in column_chunks]
        
        for col in expected_columns:
            assert col in found_columns, f"Coluna {col} não encontrada"
        print(f"✅ Todas as {len(expected_columns)} colunas encontradas")
        
        # Verificar estatísticas em colunas numéricas
        amount_chunk = next((c for c in chunks if c.metadata.additional_info.get('column_name') == 'Amount'), None)
        assert amount_chunk is not None
        assert "Média:" in amount_chunk.content
        assert "Desvio Padrão:" in amount_chunk.content
        print("✅ Estatísticas numéricas validadas")
        
        print("\n" + "=" * 80)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_csv_column_chunking()
    sys.exit(0 if success else 1)
