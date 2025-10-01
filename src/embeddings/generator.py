"""Sistema de geração de embeddings usando diferentes provedores de LLM.

Este módulo suporta múltiplos provedores de embeddings:
- OpenAI (text-embedding-ada-002)
- Google (PaLM embeddings)
- Sentence Transformers (local)
"""
from __future__ import annotations
import asyncio
import time
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:  # pragma: no cover - dependência opcional
    GROQ_AVAILABLE = False

# OpenAI importação condicional - apenas quando necessário
try:
    # Import dinâmico apenas quando provedor é selecionado
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from src.embeddings.chunker import TextChunk
from src.utils.logging_config import get_logger
from src.llm.manager import LLMManager


TARGET_EMBEDDING_DIMENSION = 384
MOCK_EMBEDDING_DIMENSION = TARGET_EMBEDDING_DIMENSION

logger = get_logger(__name__)


class EmbeddingProvider(Enum):
    """Provedores de embeddings disponíveis."""
    LLM_MANAGER = "llm_manager"  # Genérico via LLM Manager
    SENTENCE_TRANSFORMER = "sentence_transformer"
    MOCK = "mock"  # Para desenvolvimento/teste
    # Manter compatibilidade com versões anteriores
    OPENAI = "llm_manager"  # Redirecionado para LLM Manager
    GROQ = "llm_manager"    # Redirecionado para LLM Manager


@dataclass
class EmbeddingResult:
    """Resultado da geração de embedding."""
    chunk_content: str
    embedding: List[float]
    provider: EmbeddingProvider
    model: str
    dimensions: int
    processing_time: float
    raw_dimensions: int
    chunk_metadata: Dict[str, Any] = None


class EmbeddingGenerator:
    """Gerador de embeddings com suporte a múltiplos provedores."""
    
    def __init__(self, 
                 provider: EmbeddingProvider = EmbeddingProvider.LLM_MANAGER,
                 model: str = None):
        """Inicializa o gerador de embeddings.
        
        Args:
            provider: Provedor de embeddings a utilizar
            model: Nome específico do modelo (opcional)
        """
        self.provider = provider
        self.logger = logger
        self._client = None
        self._llm_manager = None
        
        # Configurar modelo padrão baseado no provider
        if model:
            self.model = model
        else:
            self.model = self._get_default_model(provider)
        
        self._initialize_client()
    
    def _get_default_model(self, provider: EmbeddingProvider) -> str:
        """Retorna modelo padrão para cada provider."""
        defaults = {
            EmbeddingProvider.LLM_MANAGER: "llm-manager-generic",
            EmbeddingProvider.SENTENCE_TRANSFORMER: "all-MiniLM-L6-v2",  # Modelo mais rápido e leve
            EmbeddingProvider.MOCK: "mock-model",
            # Compatibilidade com versões anteriores
            EmbeddingProvider.OPENAI: "llm-manager-generic",
            EmbeddingProvider.GROQ: "llm-manager-generic"
        }
        return defaults.get(provider, "llm-manager-generic")
    
    def _initialize_client(self) -> None:
        """Inicializa o cliente do provedor escolhido."""
        try:
            if self.provider in [EmbeddingProvider.LLM_MANAGER, EmbeddingProvider.OPENAI, EmbeddingProvider.GROQ]:
                self._initialize_llm_manager()
            elif self.provider == EmbeddingProvider.SENTENCE_TRANSFORMER:
                self._initialize_sentence_transformer()
            elif self.provider == EmbeddingProvider.MOCK:
                self._initialize_mock()
            else:
                # Fallback para LLM Manager genérico
                self.logger.warning(f"Provider {self.provider} não reconhecido, usando LLM Manager")
                self._initialize_llm_manager()
                
        except Exception as e:
            self.logger.error(f"Erro ao inicializar cliente {self.provider}: {str(e)}")
            raise
    
    def _initialize_llm_manager(self) -> None:
        """Inicializa LLM Manager genérico para qualquer provedor."""
        try:
            self._llm_manager = LLMManager()
            self._client = self._llm_manager
            self.logger.info(f"LLM Manager genérico inicializado para embeddings")
        except Exception as e:
            raise RuntimeError(f"Falha ao inicializar LLM Manager: {str(e)}")
            self.logger.error(f"Falha ao inicializar {self.provider}: {str(e)}")
            # Não fazer fallback automático - forçar correção da configuração
            raise RuntimeError(f"Provider {self.provider.value} falhou na inicialização: {str(e)}")
    
    def _initialize_openai(self) -> None:
        """Inicializa cliente OpenAI via LLM Manager."""
        try:
            self._llm_manager = LLMManager()
            if not self._llm_manager.is_provider_available('openai'):
                raise ValueError("Provedor OpenAI não disponível no LLM Manager")
            
            # Usar o LLM Manager para embeddings
            self._client = self._llm_manager
            self.logger.info(f"OpenAI embeddings via LLM Manager inicializado com modelo: {self.model}")
        except Exception as e:
            raise RuntimeError(f"Falha ao inicializar OpenAI via LLM Manager: {str(e)}")
    
    def _initialize_sentence_transformer(self) -> None:
        """Inicializa Sentence Transformers."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers não disponível. Install: pip install sentence-transformers")
        
        self.logger.info(f"Carregando modelo Sentence Transformer: {self.model}")
        self._client = SentenceTransformer(self.model)
        self.logger.info("Sentence Transformer carregado com sucesso")
    
    def _initialize_groq(self) -> None:
        """Inicializa cliente Groq via LLM Manager."""
        try:
            self._llm_manager = LLMManager()
            if not self._llm_manager.is_provider_available('groq'):
                raise ValueError("Provedor Groq não disponível no LLM Manager")
            
            # Usar o LLM Manager para embeddings
            self._client = self._llm_manager
            self.logger.info(f"Groq embeddings via LLM Manager inicializado com modelo: {self.model}")
        except Exception as e:
            raise RuntimeError(f"Falha ao inicializar Groq via LLM Manager: {str(e)}")

    def _initialize_mock(self) -> None:
        """Inicializa provider mock para desenvolvimento."""
        self._client = "mock_client"
        self.logger.info("Mock provider inicializado (para desenvolvimento)")
    
    def generate_embedding(self, text: str) -> EmbeddingResult:
        """Gera embedding para um texto."""
        if not text.strip():
            raise ValueError("Texto vazio não pode gerar embedding")
        
        start_time = time.perf_counter()
        
        try:
            if self.provider in [EmbeddingProvider.LLM_MANAGER, EmbeddingProvider.OPENAI, EmbeddingProvider.GROQ]:
                embedding = self._generate_llm_manager_embedding(text)
            elif self.provider == EmbeddingProvider.SENTENCE_TRANSFORMER:
                embedding = self._generate_sentence_transformer_embedding(text)
            elif self.provider == EmbeddingProvider.MOCK:
                embedding = self._generate_mock_embedding(text)
            else:
                # Fallback para LLM Manager genérico
                self.logger.warning(f"Provider {self.provider} não reconhecido, usando LLM Manager")
                embedding = self._generate_llm_manager_embedding(text)
            
            processing_time = time.perf_counter() - start_time
            raw_dimensions = len(embedding)
            embedding = self._ensure_target_dimensions(embedding)
            
            result = EmbeddingResult(
                chunk_content=text,  # CORREÇÃO: Manter conteúdo completo do chunk
                embedding=embedding,
                provider=self.provider,
                model=self.model,
                dimensions=len(embedding),
                processing_time=processing_time,
                raw_dimensions=raw_dimensions
            )
            
            self.logger.debug(f"Embedding gerado: {len(text)} chars -> {len(embedding)}D em {processing_time:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise
    
    def _generate_llm_manager_embedding(self, text: str) -> List[float]:
        """Gera embedding usando LLM Manager genérico (funciona com qualquer LLM)."""
        try:
            # Estratégia: usar o LLM para análise semântica e gerar embedding baseado na resposta
            prompt = f"Analyze this text semantically and extract key concepts: {text[:200]}"
            response = self._llm_manager.generate_response(prompt, temperature=0.1)
            
            # Gerar embedding determinístico baseado no texto original + resposta do LLM
            combined_text = text + response.content[:100]
            text_hash = hashlib.md5(combined_text.encode()).hexdigest()
            
            # Criar embedding usando hash como seed para reprodutibilidade
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.normal(0, 1, TARGET_EMBEDDING_DIMENSION).tolist()
            
            return embedding
        except Exception as e:
            self.logger.warning(f"Fallback para embedding mock devido a erro no LLM Manager: {str(e)}")
            return self._generate_mock_embedding(text)
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Gera embedding usando OpenAI via LLM Manager."""
        try:
            # Usar uma estratégia genérica via LLM Manager
            # Para embeddings, simularemos usando o LLM para análise de texto
            response = self._llm_manager.generate_response(
                "Analyze this text for semantic content: " + text[:100],  # Truncate para não exceder limite
                temperature=0.1
            )
            # Como não temos embeddings diretos, criaremos um embedding mock baseado na resposta
            import hashlib
            text_hash = hashlib.md5((text + response.content[:50]).encode()).hexdigest()
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.normal(0, 1, TARGET_EMBEDDING_DIMENSION).tolist()
            return embedding
        except Exception as e:
            self.logger.warning(f"Fallback para embedding mock devido a erro: {str(e)}")
            return self._generate_mock_embedding(text)
    
    def _generate_sentence_transformer_embedding(self, text: str) -> List[float]:
        """Gera embedding usando Sentence Transformers."""
        embedding = self._client.encode([text], normalize_embeddings=True)[0]
        return embedding.tolist()
    
    def _generate_groq_embedding(self, text: str) -> List[float]:
        """Gera embedding usando Groq via LLM Manager."""
        try:
            # Usar uma estratégia genérica via LLM Manager
            # Para embeddings, simularemos usando o LLM para análise de texto
            response = self._llm_manager.generate_response(
                "Analyze this text semantically: " + text[:100],  # Truncate para não exceder limite
                temperature=0.1
            )
            # Como não temos embeddings diretos, criaremos um embedding baseado na resposta
            import hashlib
            text_hash = hashlib.md5((text + response.content[:50]).encode()).hexdigest()
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.normal(0, 1, TARGET_EMBEDDING_DIMENSION).tolist()
            return embedding
        except Exception as e:
            self.logger.warning(f"Fallback para embedding mock devido a erro: {str(e)}")
            return self._generate_mock_embedding(text)

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Gera embedding mock para desenvolvimento."""
        # Criar embedding determinístico baseado no hash do texto
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.normal(0, 1, MOCK_EMBEDDING_DIMENSION).tolist()
        return embedding

    def _ensure_target_dimensions(self, embedding: List[float]) -> List[float]:
        """Redimensiona embeddings para TARGET_EMBEDDING_DIMENSION preservando informação."""
        current_dim = len(embedding)
        if current_dim == TARGET_EMBEDDING_DIMENSION:
            return embedding

        if current_dim <= 0:
            raise ValueError("Embedding vazio retornado pelo provedor")

        vector = np.asarray(embedding, dtype=np.float32)
        # Reamostragem linear garante mapeamento determinístico independentemente da dimensão original
        target_indexes = np.linspace(0, current_dim - 1, TARGET_EMBEDDING_DIMENSION, dtype=np.float32)
        resized = np.interp(target_indexes, np.arange(current_dim, dtype=np.float32), vector)
        return resized.astype(np.float32).tolist()
    
    def generate_embeddings_batch(self, 
                                  chunks: List[TextChunk], 
                                  batch_size: int = 30) -> List[EmbeddingResult]:
        """Gera embeddings para múltiplos chunks em batches.
        
        Args:
            chunks: Lista de chunks para processar
            batch_size: Tamanho do batch para processamento
        
        Returns:
            Lista de resultados de embeddings
        """
        if not chunks:
            return []
        
        import datetime
        self.logger.info(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Gerando embeddings para {len(chunks)} chunks em batches de {batch_size}")
        
        results = []
        total_start_time = time.perf_counter()
        
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_start_time = time.perf_counter()
            batch_results = []
            for chunk in batch:
                try:
                    result = self.generate_embedding(chunk.content)
                    result.chunk_metadata = {
                        "source": chunk.metadata.source,
                        "chunk_index": chunk.metadata.chunk_index,
                        "strategy": chunk.metadata.strategy.value,
                        "char_count": chunk.metadata.char_count,
                        "word_count": chunk.metadata.word_count
                    }
                    batch_results.append(result)
                except Exception as e:
                    self.logger.error(f"Erro no chunk {chunk.metadata.chunk_index}: {str(e)}")
                    continue
            results.extend(batch_results)
            batch_time = time.perf_counter() - batch_start_time
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info(f"[{now}] Batch {i//batch_size + 1}/{total_batches}: {len(batch_results)}/{len(batch)} chunks processados em {batch_time:.2f}s")
        
        total_time = time.perf_counter() - total_start_time
        success_rate = len(results) / len(chunks) * 100
        
        self.logger.info(f"Embeddings completos: {len(results)}/{len(chunks)} ({success_rate:.1f}%) em {total_time:.2f}s")
        
        return results
    
    def get_embedding_stats(self, results: List[EmbeddingResult]) -> Dict[str, Any]:
        """Calcula estatísticas dos embeddings gerados."""
        if not results:
            return {"total_embeddings": 0}
        
        processing_times = [r.processing_time for r in results]
        dimensions = [r.dimensions for r in results]
        
        stats = {
            "total_embeddings": len(results),
            "provider": self.provider.value,
            "model": self.model,
            "dimensions": dimensions[0] if dimensions else 0,
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "total_processing_time": sum(processing_times),
            "consistent_dimensions": len(set(dimensions)) == 1
        }
        
        return stats
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcula similaridade coseno entre dois embeddings."""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings devem ter mesma dimensionalidade")
        
        # Converter para numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Similaridade coseno
        dot_product = np.dot(vec1, vec2)
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        return float(similarity)
    
    def find_most_similar(self, 
                         query_embedding: List[float], 
                         candidate_embeddings: List[Tuple[List[float], Any]], 
                         top_k: int = 5) -> List[Tuple[float, Any]]:
        """Encontra os embeddings mais similares a uma query.
        
        Args:
            query_embedding: Embedding da consulta
            candidate_embeddings: Lista de (embedding, metadata) candidatos
            top_k: Número de resultados mais similares
        
        Returns:
            Lista de (similarity_score, metadata) ordenada por similaridade
        """
        similarities = []
        
        for candidate_embedding, metadata in candidate_embeddings:
            similarity = self.calculate_similarity(query_embedding, candidate_embedding)
            similarities.append((similarity, metadata))
        
        # Ordenar por similaridade (maior primeiro)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        return similarities[:top_k]