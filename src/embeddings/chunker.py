"""Sistema de chunking inteligente para processamento de texto.

Este módulo implementa diferentes estratégias de divisão de texto em chunks
otimizados para geração de embeddings e busca vetorial.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ChunkStrategy(Enum):
    """Estratégias de chunking disponíveis."""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    CSV_ROW = "csv_row"


@dataclass
class ChunkMetadata:
    """Metadados de um chunk."""
    source: str
    chunk_index: int
    strategy: ChunkStrategy
    char_count: int
    word_count: int
    start_position: int
    end_position: int
    overlap_with_previous: int = 0
    additional_info: Dict[str, Any] = None


@dataclass
class TextChunk:
    """Representa um pedaço de texto com metadados."""
    content: str
    metadata: ChunkMetadata
    
    def __len__(self) -> int:
        return len(self.content)
    
    def word_count(self) -> int:
        return len(self.content.split())


class TextChunker:
    """Sistema de chunking inteligente para diferentes tipos de conteúdo."""
    
    def __init__(self, 
                 chunk_size: int = 512,
                 overlap_size: int = 50,
                 min_chunk_size: int = 50,
                 csv_chunk_size_rows: int = 20,
                 csv_overlap_rows: int = 4):
        """Inicializa o sistema de chunking.
        
        Args:
            chunk_size: Tamanho alvo de cada chunk em caracteres
            overlap_size: Sobreposição entre chunks consecutivos
            min_chunk_size: Tamanho mínimo para considerar um chunk válido
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.csv_chunk_size_rows = max(1, csv_chunk_size_rows)
        # Garantir que o overlap não exceda o tamanho do chunk em linhas
        if csv_overlap_rows >= csv_chunk_size_rows:
            logger.warning(
                "CSV overlap (%s) maior/igual ao chunk_size_rows (%s). Ajustando para chunk_size_rows - 1.",
                csv_overlap_rows,
                csv_chunk_size_rows
            )
        self.csv_overlap_rows = max(0, min(csv_overlap_rows, self.csv_chunk_size_rows - 1))
        self.logger = logger
        
    def chunk_text(self, 
                   text: str,
                   source_id: str,
                   strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE) -> List[TextChunk]:
        """Divide texto em chunks usando a estratégia especificada.
        
        Args:
            text: Texto a ser dividido
            source_id: Identificador da fonte do texto
            strategy: Estratégia de chunking a utilizar
        
        Returns:
            Lista de chunks com metadados
        """
        if not text.strip():
            logger.warning(f"Texto vazio para source_id: {source_id}")
            return []
            
        logger.info(f"Iniciando chunking: {len(text)} chars, estratégia: {strategy.value}")
        
        if strategy == ChunkStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, source_id)
        elif strategy == ChunkStrategy.SENTENCE:
            return self._chunk_by_sentence(text, source_id)
        elif strategy == ChunkStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, source_id)
        elif strategy == ChunkStrategy.CSV_ROW:
            return self._chunk_csv_data(text, source_id)
        else:
            logger.warning(f"Estratégia não implementada: {strategy}, usando FIXED_SIZE")
            return self._chunk_fixed_size(text, source_id)
    
    def _chunk_fixed_size(self, text: str, source_id: str) -> List[TextChunk]:
        """Chunking por tamanho fixo com sobreposição."""
        chunks = []
        start_pos = 0
        chunk_index = 0
        
        while start_pos < len(text):
            # Calcular fim do chunk
            end_pos = min(start_pos + self.chunk_size, len(text))
            
            # Tentar quebrar em palavra completa
            if end_pos < len(text):
                # Procurar último espaço antes do limite
                last_space = text.rfind(' ', start_pos, end_pos)
                if last_space > start_pos + self.min_chunk_size:
                    end_pos = last_space
            
            # Extrair conteúdo
            content = text[start_pos:end_pos].strip()
            
            if len(content) >= self.min_chunk_size:
                # Calcular sobreposição com chunk anterior
                overlap = 0
                if chunk_index > 0 and start_pos > 0:
                    overlap = self.overlap_size
                
                metadata = ChunkMetadata(
                    source=source_id,
                    chunk_index=chunk_index,
                    strategy=ChunkStrategy.FIXED_SIZE,
                    char_count=len(content),
                    word_count=len(content.split()),
                    start_position=start_pos,
                    end_position=end_pos,
                    overlap_with_previous=overlap
                )
                
                chunks.append(TextChunk(content=content, metadata=metadata))
                chunk_index += 1
            
            # Próximo chunk com sobreposição
            start_pos = max(end_pos - self.overlap_size, start_pos + 1)
            
            # Evitar loop infinito
            if start_pos >= end_pos:
                start_pos = end_pos
        
        logger.info(f"Criados {len(chunks)} chunks por tamanho fixo")
        return chunks
    
    def _chunk_by_sentence(self, text: str, source_id: str) -> List[TextChunk]:
        """Chunking por sentença."""
        # Regex para detectar fim de sentença
        sentence_endings = re.compile(r'[.!?]+\s+')
        sentences = sentence_endings.split(text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        start_pos = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Verificar se adicionar esta sentença ultrapassaria o limite
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Salvar chunk atual
                if len(current_chunk) >= self.min_chunk_size:
                    metadata = ChunkMetadata(
                        source=source_id,
                        chunk_index=chunk_index,
                        strategy=ChunkStrategy.SENTENCE,
                        char_count=len(current_chunk),
                        word_count=len(current_chunk.split()),
                        start_position=start_pos,
                        end_position=start_pos + len(current_chunk)
                    )
                    
                    chunks.append(TextChunk(content=current_chunk.strip(), metadata=metadata))
                    chunk_index += 1
                
                # Iniciar novo chunk
                current_chunk = sentence
                start_pos += len(current_chunk) + 1
            else:
                current_chunk = potential_chunk
        
        # Adicionar último chunk se existir
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            metadata = ChunkMetadata(
                source=source_id,
                chunk_index=chunk_index,
                strategy=ChunkStrategy.SENTENCE,
                char_count=len(current_chunk),
                word_count=len(current_chunk.split()),
                start_position=start_pos,
                end_position=start_pos + len(current_chunk)
            )
            chunks.append(TextChunk(content=current_chunk.strip(), metadata=metadata))
        
        logger.info(f"Criados {len(chunks)} chunks por sentença")
        return chunks
    
    def _chunk_by_paragraph(self, text: str, source_id: str) -> List[TextChunk]:
        """Chunking por parágrafo."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        char_position = 0
        
        for paragraph in paragraphs:
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Salvar chunk atual
                if len(current_chunk) >= self.min_chunk_size:
                    metadata = ChunkMetadata(
                        source=source_id,
                        chunk_index=chunk_index,
                        strategy=ChunkStrategy.PARAGRAPH,
                        char_count=len(current_chunk),
                        word_count=len(current_chunk.split()),
                        start_position=char_position,
                        end_position=char_position + len(current_chunk)
                    )
                    
                    chunks.append(TextChunk(content=current_chunk.strip(), metadata=metadata))
                    chunk_index += 1
                    char_position += len(current_chunk) + 2  # +2 para \n\n
                
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk
        
        # Último chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            metadata = ChunkMetadata(
                source=source_id,
                chunk_index=chunk_index,
                strategy=ChunkStrategy.PARAGRAPH,
                char_count=len(current_chunk),
                word_count=len(current_chunk.split()),
                start_position=char_position,
                end_position=char_position + len(current_chunk)
            )
            chunks.append(TextChunk(content=current_chunk.strip(), metadata=metadata))
        
        logger.info(f"Criados {len(chunks)} chunks por parágrafo")
        return chunks
    
    def _chunk_csv_data(self, csv_text: str, source_id: str) -> List[TextChunk]:
        """Chunking especializado para dados CSV baseado em linhas com overlap."""
        raw_lines = csv_text.splitlines()

        if not raw_lines:
            logger.warning("Arquivo CSV vazio para source_id: %s", source_id)
            return []

        header = raw_lines[0].strip()
        if not header:
            logger.warning("CSV sem header detectado para source_id: %s", source_id)

        data_lines = [line.strip() for line in raw_lines[1:] if line.strip()]
        total_rows = len(data_lines)

        if total_rows == 0:
            logger.warning("CSV sem linhas de dados para source_id: %s", source_id)
            return []

        chunk_size_rows = max(1, self.csv_chunk_size_rows)
        overlap_rows = max(0, min(self.csv_overlap_rows, chunk_size_rows - 1))
        step = chunk_size_rows - overlap_rows if chunk_size_rows > overlap_rows else chunk_size_rows

        chunks: List[TextChunk] = []
        chunk_index = 0
        start_row = 0

        while start_row < total_rows:
            end_row = min(start_row + chunk_size_rows, total_rows)
            chunk_lines = data_lines[start_row:end_row]

            if not chunk_lines:
                break

            chunk_content_lines = [header] + chunk_lines
            chunk_content = '\n'.join(chunk_content_lines)

            overlap_with_previous = overlap_rows if chunk_index > 0 else 0
            chunk_metadata = ChunkMetadata(
                source=source_id,
                chunk_index=chunk_index,
                strategy=ChunkStrategy.CSV_ROW,
                char_count=len(chunk_content),
                word_count=len(chunk_content.split()),
                start_position=start_row,
                end_position=end_row,
                overlap_with_previous=overlap_with_previous,
                additional_info={
                    "csv_rows": len(chunk_lines),
                    "overlap_rows": overlap_with_previous,
                    "start_row": start_row + 1,  # human-friendly (1-based)
                    "end_row": end_row,
                },
            )

            chunks.append(TextChunk(content=chunk_content, metadata=chunk_metadata))
            chunk_index += 1
            start_row += step

        total_chunk_rows = sum(c.metadata.additional_info.get("csv_rows", 0) for c in chunks if c.metadata.additional_info)
        logger.info(
            "Criados %s chunks CSV (linhas por chunk=%s, overlap=%s) totalizando %s linhas", 
            len(chunks),
            chunk_size_rows,
            overlap_rows,
            total_chunk_rows,
        )
        return chunks
    
    def get_stats(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Retorna estatísticas dos chunks criados."""
        if not chunks:
            return {"total_chunks": 0}
        
        stats = {
            "total_chunks": len(chunks),
            "total_chars": sum(c.metadata.char_count for c in chunks),
            "total_words": sum(c.metadata.word_count for c in chunks),
            "avg_chunk_size": sum(c.metadata.char_count for c in chunks) / len(chunks),
            "min_chunk_size": min(c.metadata.char_count for c in chunks),
            "max_chunk_size": max(c.metadata.char_count for c in chunks),
            "strategy": chunks[0].metadata.strategy.value,
            "overlap_total": sum(c.metadata.overlap_with_previous for c in chunks)
        }

        csv_rows_values = [
            c.metadata.additional_info.get("csv_rows")
            for c in chunks
            if c.metadata.additional_info and c.metadata.additional_info.get("csv_rows") is not None
        ]
        if csv_rows_values:
            total_csv_rows = sum(csv_rows_values)
            total_overlap_rows = sum(
                c.metadata.additional_info.get("overlap_rows", 0)
                for c in chunks
                if c.metadata.additional_info
            )
            stats["total_csv_rows"] = total_csv_rows
            stats["avg_csv_rows"] = total_csv_rows / len(csv_rows_values)
            stats["total_csv_overlap_rows"] = total_overlap_rows
            if len(csv_rows_values) > 1:
                stats["avg_csv_overlap_rows"] = total_overlap_rows / (len(csv_rows_values) - 1)
        
        return stats