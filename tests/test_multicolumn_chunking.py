"""Teste automatizado para validar chunking multi-coluna (CSV_ROW + CSV_COLUMN).

Este teste verifica se:
1. Chunker gera corretamente chunks por linha (CSV_ROW)
2. Chunker gera corretamente chunks por coluna (CSV_COLUMN)
3. Cada coluna numérica possui estatísticas completas
4. Cada coluna categórica possui distribuição de frequência
5. Chunks têm metadados corretos (chunk_type, column_name, etc.)
"""

import pytest
import sys
from pathlib import Path

# Adicionar src ao path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.embeddings.chunker import TextChunker, ChunkStrategy, TextChunk
import pandas as pd

# CSV de teste simulando dataset multi-coluna
SAMPLE_CSV = """Time,V1,V2,V3,Amount,Class
1000.0,1.5,2.3,3.1,100.50,0
2000.0,-0.8,1.2,-1.5,250.00,0
3000.0,0.5,0.9,0.3,75.25,1
4000.0,2.1,-1.3,1.8,500.00,0
5000.0,-1.2,0.4,-0.6,150.00,1
"""

class TestMultiColumnChunking:
    """Testes para validar chunking multi-coluna."""
    
    @pytest.fixture
    def chunker(self):
        """Cria instância do TextChunker."""
        return TextChunker(chunk_size=500, overlap_size=50, min_chunk_size=50)
    
    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Cria arquivo CSV temporário para testes."""
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(SAMPLE_CSV)
        return str(csv_file)
    
    def test_csv_row_chunking_generates_chunks(self, chunker):
        """Teste 1: Chunking por LINHA gera chunks corretamente."""
        chunks = chunker.chunk_text(
            text=SAMPLE_CSV,
            source_id="test_creditcard.csv",
            strategy=ChunkStrategy.CSV_ROW
        )
        
        # Validações
        assert len(chunks) > 0, "Nenhum chunk por linha foi gerado"
        
        # Verificar que chunks contêm dados CSV
        for chunk in chunks:
            assert isinstance(chunk, TextChunk), "Chunk deve ser instância de TextChunk"
            assert len(chunk.content) > 0, "Chunk não pode estar vazio"
            assert chunk.metadata.strategy == ChunkStrategy.CSV_ROW
            
        print(f"✅ TESTE 1 PASSOU: {len(chunks)} chunks por LINHA gerados")
    
    def test_csv_column_chunking_generates_chunks(self, chunker):
        """Teste 2: Chunking por COLUNA gera chunks corretamente."""
        chunks = chunker.chunk_text(
            text=SAMPLE_CSV,
            source_id="test_creditcard.csv",
            strategy=ChunkStrategy.CSV_COLUMN
        )
        
        # Validações
        assert len(chunks) > 0, "Nenhum chunk por coluna foi gerado"
        
        # Deve ter: 1 chunk de metadata + 6 chunks de colunas (Time, V1, V2, V3, Amount, Class)
        expected_min_chunks = 7  # 1 metadata + 6 colunas
        assert len(chunks) >= expected_min_chunks, f"Esperado pelo menos {expected_min_chunks} chunks (1 metadata + 6 colunas), obteve {len(chunks)}"
        
        # Verificar chunk de metadata
        metadata_chunk = chunks[0]
        assert "Dataset:" in metadata_chunk.content or "Total de Linhas:" in metadata_chunk.content
        assert metadata_chunk.metadata.additional_info.get('chunk_type') == 'metadata'
        
        # Verificar chunks de colunas
        column_chunks = chunks[1:]
        column_names_found = []
        
        for chunk in column_chunks:
            assert chunk.metadata.additional_info.get('chunk_type') == 'column_analysis'
            column_name = chunk.metadata.additional_info.get('column_name')
            assert column_name is not None, "chunk_type=column_analysis deve ter column_name"
            column_names_found.append(column_name)
            assert f"Coluna: {column_name}" in chunk.content, f"Chunk deve conter 'Coluna: {column_name}'"
        
        # Verificar que todas as colunas esperadas foram processadas
        expected_columns = ['Time', 'V1', 'V2', 'V3', 'Amount', 'Class']
        for col in expected_columns:
            assert col in column_names_found, f"Coluna {col} não foi encontrada nos chunks"
        
        print(f"✅ TESTE 2 PASSOU: {len(chunks)} chunks por COLUNA gerados (1 metadata + {len(column_chunks)} colunas)")
        print(f"   Colunas encontradas: {', '.join(column_names_found)}")
    
    def test_numeric_columns_have_statistics(self, chunker):
        """Teste 3: Colunas NUMÉRICAS possuem estatísticas completas."""
        chunks = chunker.chunk_text(
            text=SAMPLE_CSV,
            source_id="test_creditcard.csv",
            strategy=ChunkStrategy.CSV_COLUMN
        )
        
        numeric_columns = ['Time', 'V1', 'V2', 'V3', 'Amount']
        
        for col_name in numeric_columns:
            # Encontrar chunk dessa coluna
            col_chunk = next(
                (c for c in chunks if c.metadata.additional_info.get('column_name') == col_name),
                None
            )
            
            assert col_chunk is not None, f"Chunk da coluna {col_name} não encontrado"
            
            # Verificar presença de estatísticas essenciais
            content = col_chunk.content
            assert "Tipo: numérico" in content or "Tipo: numeric" in content, f"{col_name}: deve ser identificada como numérica"
            assert "MEDIDAS DE TENDÊNCIA CENTRAL" in content, f"{col_name}: faltam medidas de tendência central"
            assert "Mínimo:" in content, f"{col_name}: falta mínimo"
            assert "Máximo:" in content, f"{col_name}: falta máximo"
            assert "Média:" in content, f"{col_name}: falta média"
            assert "Mediana:" in content, f"{col_name}: falta mediana"
            assert "MEDIDAS DE DISPERSÃO" in content, f"{col_name}: faltam medidas de dispersão"
            assert "Desvio Padrão:" in content, f"{col_name}: falta desvio padrão"
            assert "Variância:" in content, f"{col_name}: falta variância"
            
            # Verificar metadados
            assert col_chunk.metadata.additional_info.get('is_numeric') == True, f"{col_name}: is_numeric deve ser True"
        
        print(f"✅ TESTE 3 PASSOU: {len(numeric_columns)} colunas numéricas com estatísticas completas")
    
    def test_categorical_columns_have_frequencies(self, chunker):
        """Teste 4: Colunas CATEGÓRICAS possuem distribuição de frequência."""
        chunks = chunker.chunk_text(
            text=SAMPLE_CSV,
            source_id="test_creditcard.csv",
            strategy=ChunkStrategy.CSV_COLUMN
        )
        
        categorical_columns = ['Class']  # Class é binária (0 ou 1)
        
        for col_name in categorical_columns:
            # Encontrar chunk dessa coluna
            col_chunk = next(
                (c for c in chunks if c.metadata.additional_info.get('column_name') == col_name),
                None
            )
            
            assert col_chunk is not None, f"Chunk da coluna {col_name} não encontrado"
            
            # Verificar presença de distribuição de frequência
            content = col_chunk.content
            assert "Tipo: categórico" in content or "Tipo: categorical" in content, f"{col_name}: deve ser identificada como categórica"
            assert "DISTRIBUIÇÃO DE FREQUÊNCIA" in content, f"{col_name}: falta distribuição de frequência"
            assert "VALORES MAIS FREQUENTES" in content, f"{col_name}: faltam valores mais frequentes"
            assert "Valores Únicos:" in content, f"{col_name}: falta contagem de valores únicos"
            
            # Verificar metadados
            assert col_chunk.metadata.additional_info.get('is_numeric') == False, f"{col_name}: is_numeric deve ser False"
        
        print(f"✅ TESTE 4 PASSOU: {len(categorical_columns)} colunas categóricas com distribuição de frequência")
    
    def test_chunks_have_correct_metadata(self, chunker):
        """Teste 5: Chunks possuem metadados corretos."""
        chunks = chunker.chunk_text(
            text=SAMPLE_CSV,
            source_id="test_creditcard.csv",
            strategy=ChunkStrategy.CSV_COLUMN
        )
        
        # Validar metadata chunk
        metadata_chunk = chunks[0]
        assert metadata_chunk.metadata.additional_info.get('chunk_type') == 'metadata'
        assert metadata_chunk.metadata.additional_info.get('columns_count') == 6
        assert metadata_chunk.metadata.additional_info.get('rows_count') == 5
        
        # Validar column chunks
        column_chunks = chunks[1:]
        for chunk in column_chunks:
            info = chunk.metadata.additional_info
            assert info.get('chunk_type') == 'column_analysis'
            assert info.get('column_name') is not None
            assert info.get('column_dtype') is not None
            assert 'is_numeric' in info
            assert 'null_count' in info
            assert 'unique_count' in info
        
        print(f"✅ TESTE 5 PASSOU: Todos os {len(chunks)} chunks possuem metadados corretos")
    
    def test_dual_chunking_generates_both_strategies(self, chunker):
        """Teste 6: RAGAgent deve gerar chunks ROW + COLUMN simultaneamente."""
        from src.agent.rag_agent import RAGAgent
        from src.settings import SUPABASE_URL, SUPABASE_KEY
        
        # Inicializar RAGAgent
        rag_agent = RAGAgent(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY
        )
        
        # Ingerir CSV (deve gerar chunks metadata + ROW + COLUMN)
        result = rag_agent.ingest_csv_data(
            csv_text=SAMPLE_CSV,
            source_id="test_dual_chunking.csv"
        )
        
        # Validar resposta
        assert result is not None
        assert 'metadata' in result
        
        stats = result['metadata']
        assert 'metadata_chunks_created' in stats
        assert 'row_chunks_created' in stats
        assert 'column_chunks_created' in stats
        assert 'total_chunks_created' in stats
        
        # Validar que TODOS os tipos de chunks foram gerados
        assert stats['metadata_chunks_created'] > 0, "Nenhum chunk de metadata foi criado"
        assert stats['row_chunks_created'] > 0, "Nenhum chunk por linha foi criado"
        assert stats['column_chunks_created'] > 0, "Nenhum chunk por coluna foi criado"
        
        # Total deve ser a soma
        expected_total = stats['metadata_chunks_created'] + stats['row_chunks_created'] + stats['column_chunks_created']
        assert stats['total_chunks_created'] == expected_total, f"Total incorreto: esperado {expected_total}, obteve {stats['total_chunks_created']}"
        
        print(f"✅ TESTE 6 PASSOU: Ingestão DUAL completa")
        print(f"   Metadata: {stats['metadata_chunks_created']} chunks")
        print(f"   Linhas: {stats['row_chunks_created']} chunks")
        print(f"   Colunas: {stats['column_chunks_created']} chunks")
        print(f"   TOTAL: {stats['total_chunks_created']} chunks")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
