"""Gerador de embeddings assíncrono para máxima performance mantendo qualidade.

VANTAGENS DO PROCESSAMENTO ASSÍNCRONO:
- Paraleliza geração de embeddings em lotes
- Mantém ordem dos chunks (importante para qualidade)
- Processa múltiplos batches simultaneamente
- Não impacta a qualidade dos embeddings individuais
"""
from __future__ import annotations
import asyncio
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider, EmbeddingResult
from src.embeddings.chunker import TextChunk
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AsyncEmbeddingGenerator:
    """Gerador de embeddings assíncrono para alta performance."""
    
    def __init__(self, 
                 provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMER,
                 max_workers: int = 4,
                 batch_size: int = 25):
        """Inicializa gerador assíncrono.
        
        Args:
            provider: Provedor de embeddings
            max_workers: Número máximo de workers paralelos
            batch_size: Tamanho do batch por worker
        """
        self.provider = provider
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.logger = logger
        
        # Cache de geradores por thread para thread-safety
        self._generators: Dict[int, EmbeddingGenerator] = {}
        self._lock = threading.Lock()
    
    def _get_generator(self) -> EmbeddingGenerator:
        """Obtém gerador thread-safe para thread atual."""
        thread_id = threading.get_ident()
        
        if thread_id not in self._generators:
            with self._lock:
                if thread_id not in self._generators:
                    self._generators[thread_id] = EmbeddingGenerator(provider=self.provider)
                    self.logger.debug(f"Criado gerador para thread {thread_id}")
        
        return self._generators[thread_id]
    
    def _process_batch_sync(self, chunks_batch: List[TextChunk]) -> List[EmbeddingResult]:
        """Processa um batch de forma síncrona (executado em thread separada)."""
        generator = self._get_generator()
        results = []
        
        for chunk in chunks_batch:
            try:
                result = generator.generate_embedding(chunk.content)
                # Preservar metadados do chunk
                result.chunk_metadata = {
                    "source": chunk.metadata.source,
                    "chunk_index": chunk.metadata.chunk_index,
                    "strategy": chunk.metadata.strategy.value,
                    "char_count": chunk.metadata.char_count,
                    "word_count": chunk.metadata.word_count
                }
                results.append(result)
            except Exception as e:
                self.logger.error(f"Erro no chunk {chunk.metadata.chunk_index}: {e}")
                continue
        
        return results
    
    async def generate_embeddings_async(self, chunks: List[TextChunk]) -> List[EmbeddingResult]:
        """Gera embeddings de forma assíncrona mantendo ordem e qualidade.
        
        Args:
            chunks: Lista de chunks para processar
            
        Returns:
            Lista de resultados ordenados (mesma ordem dos chunks)
        """
        if not chunks:
            return []
        
        total_chunks = len(chunks)
        self.logger.info(f"Iniciando processamento assíncrono de {total_chunks} chunks")
        start_time = time.perf_counter()
        
        # Dividir chunks em batches mantendo ordem
        batches = []
        for i in range(0, total_chunks, self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batches.append((i, batch))  # (index_inicial, chunks)
        
        self.logger.info(f"Criados {len(batches)} batches para {self.max_workers} workers")
        
        # Processar batches em paralelo
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submeter tarefas
            futures = []
            for batch_index, chunks_batch in batches:
                future = loop.run_in_executor(
                    executor, 
                    self._process_batch_sync, 
                    chunks_batch
                )
                futures.append((batch_index, future))
            
            # Aguardar resultados
            batch_results = []
            for batch_index, future in futures:
                try:
                    results = await future
                    batch_results.append((batch_index, results))
                    self.logger.info(f"Batch {batch_index // self.batch_size + 1}/{len(batches)} concluído: {len(results)} embeddings")
                except Exception as e:
                    self.logger.error(f"Erro no batch {batch_index}: {e}")
                    batch_results.append((batch_index, []))
        
        # Reordenar resultados mantendo ordem original
        batch_results.sort(key=lambda x: x[0])  # Ordenar por índice
        
        final_results = []
        for _, results in batch_results:
            final_results.extend(results)
        
        processing_time = time.perf_counter() - start_time
        success_rate = len(final_results) / total_chunks * 100
        speed = len(final_results) / processing_time if processing_time > 0 else 0
        
        self.logger.info(
            f"Processamento assíncrono concluído: "
            f"{len(final_results)}/{total_chunks} embeddings ({success_rate:.1f}%) "
            f"em {processing_time:.2f}s ({speed:.1f} emb/s)"
        )
        
        return final_results
    
    def get_stats(self, results: List[EmbeddingResult]) -> Dict[str, Any]:
        """Calcula estatísticas dos embeddings gerados."""
        if not results:
            return {"total_embeddings": 0}
        
        processing_times = [r.processing_time for r in results]
        
        return {
            "total_embeddings": len(results),
            "provider": self.provider.value,
            "async_processing": True,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "total_processing_time": sum(processing_times),
            "dimensions": results[0].dimensions if results else 0,
        }


def run_async_embeddings(chunks: List[TextChunk], 
                        provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMER,
                        max_workers: int = 4) -> List[EmbeddingResult]:
    """Função helper para executar geração assíncrona em ambiente síncrono."""
    generator = AsyncEmbeddingGenerator(provider=provider, max_workers=max_workers)
    
    # Executar em loop assíncrono
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(generator.generate_embeddings_async(chunks))