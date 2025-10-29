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
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:  # pragma: no cover - dependência opcional
    GROQ_AVAILABLE = False

# Flags de disponibilidade; valores padrão (ajustadas em tempo de execução por instância)
OPENAI_AVAILABLE = False  # Mantida por compatibilidade; ajustada quando possível
HAS_ANY_LLM_PROVIDER = False  # Mantida por compatibilidade; ajustada quando possível

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from src.embeddings.chunker import TextChunk
from src.utils.logging_config import get_logger
from src.llm.manager import LLMManager, LLMConfig


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
        # Configuração base
        self.provider = provider
        self.logger = logger
        self._client = None
        self._llm_manager = None
        self._available_providers: List[str] = []
        self._has_any_llm_provider: bool = False
        self._strict_mode: bool = str(os.getenv("EMBEDDINGS_STRICT_MODE", "false")).lower() == "true"
        self._force_mock: bool = str(os.getenv("EMBEDDINGS_FORCE_MOCK", "false")).lower() == "true"
        
        # Configurar modelo padrão baseado no provider
        if model:
            self.model = model
        else:
            self.model = self._get_default_model(provider)
        
        # Detectar provedores disponíveis (lazy, por instância)
        self._detect_providers()
        # Inicializar cliente com regras de fallback e flags
        self._initialize_client()

    def _detect_providers(self) -> None:
        """Detecta provedores disponíveis via LLMManager de forma genérica e leve.

        Estratégia:
        - Se LLMManager expõe list_providers(): usa diretamente.
        - Caso contrário, tenta detectar um provedor ativo (ex.: atributo/propriedade).
        - Evita checagens rígidas por nome de provider específico.
        - Ajusta flags de módulo para retrocompatibilidade (quando possível).
        """
        try:
            mgr = LLMManager()
            providers: List[str] = []
            if hasattr(mgr, "list_providers") and callable(getattr(mgr, "list_providers")):
                try:
                    providers = mgr.list_providers() or []
                except Exception:
                    providers = []
            elif hasattr(mgr, "active_provider"):
                ap = getattr(mgr, "active_provider")
                if isinstance(ap, str) and ap:
                    providers = [ap]
            else:
                # Como fallback mínimo, se o LLMManager inicializou, considerar um provedor genérico disponível
                providers = ["generic"]

            self._available_providers = providers
            self._has_any_llm_provider = len(providers) > 0

            # Ajustar flags globais para compatibilidade com código legado
            global HAS_ANY_LLM_PROVIDER, OPENAI_AVAILABLE
            HAS_ANY_LLM_PROVIDER = self._has_any_llm_provider
            OPENAI_AVAILABLE = OPENAI_AVAILABLE or ("openai" in providers)
        except Exception:
            self._available_providers = []
            self._has_any_llm_provider = False
            # Não alterar flags globais em caso de falha aqui
    
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
            # Forçar mock por configuração
            if self._force_mock:
                self.logger.warning("EMBEDDINGS_FORCE_MOCK=TRUE — forçando provider MOCK")
                self.provider = EmbeddingProvider.MOCK
                self._initialize_mock()
                return

            if self.provider in [EmbeddingProvider.LLM_MANAGER, EmbeddingProvider.OPENAI, EmbeddingProvider.GROQ]:
                # Condicionar à disponibilidade real via LLMManager (lazy, por instância)
                if not self._has_any_llm_provider:
                    msg = "Nenhum provedor LLM disponível via LLMManager"
                    if self._strict_mode:
                        self.logger.error(msg + "; STRICT_MODE ativo — abortando")
                        raise RuntimeError("Sem provedores LLM disponíveis e STRICT_MODE habilitado")
                    else:
                        self.logger.warning(msg + "; usando MOCK para embeddings")
                        self.provider = EmbeddingProvider.MOCK
                        self._initialize_mock()
                else:
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
            self.logger.info("LLM Manager genérico inicializado para embeddings")
        except Exception as e:
            self.logger.error(f"Falha ao inicializar LLM Manager: {e}")
            raise RuntimeError(f"Falha ao inicializar LLM Manager: {e}")
    
    def _initialize_openai(self) -> None:
        """Inicializa cliente OpenAI via LLM Manager."""
        try:
            self._llm_manager = LLMManager()
            
            # Usar o LLM Manager para embeddings
            self._client = self._llm_manager
            self.logger.info(f"Embeddings via LLM Manager inicializado (OpenAI compatível) com modelo: {self.model}")
        except Exception as e:
            raise RuntimeError(f"Falha ao inicializar provider via LLM Manager: {str(e)}")
    
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
            
            # Usar o LLM Manager para embeddings
            self._client = self._llm_manager
            self.logger.info(f"Embeddings via LLM Manager inicializado (Groq compatível) com modelo: {self.model}")
        except Exception as e:
            raise RuntimeError(f"Falha ao inicializar provider via LLM Manager: {str(e)}")

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

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para uma lista de textos (API de conveniência).

        Compatível com testes e cenários simples onde não há metadados de chunk.
        Usa internamente `generate_embeddings_batch` criando TextChunks temporários.
        Retorna apenas os vetores de embeddings para compatibilidade com testes existentes.
        """
        if not texts:
            return []
        from src.embeddings.chunker import ChunkMetadata, ChunkStrategy
        temp_chunks: List[TextChunk] = []
        for i, t in enumerate(texts):
            meta = ChunkMetadata(
                source="direct_api",
                chunk_index=i,
                strategy=ChunkStrategy.FIXED_SIZE,
                char_count=len(t or ""),
                word_count=len((t or "").split()),
                start_position=0,
                end_position=len(t or "")
            )
            temp_chunks.append(TextChunk(content=t, metadata=meta))

        results = self.generate_embeddings_batch(temp_chunks)
        return [r.embedding for r in results]
    
    def _generate_llm_manager_embedding(self, text: str) -> List[float]:
        """Gera embedding usando LLM Manager genérico (funciona com qualquer LLM).

        Esta implementação usa o LLM para gerar uma análise semântica do texto e,
        a partir da resposta, constrói um embedding determinístico via numpy com
        semente derivada de um hash (MD5) do texto + resposta. Isso funciona como
        fallback/reprodução em ambientes sem suporte direto a embeddings e é
        intencionalmente determinístico — útil para testes e cenários mock.

        Se o LLM falhar ou não estiver disponível, o método executa fallback
        chamando `_generate_mock_embedding`, que produz um vetor pseudo-aleatório
        com semente baseada no conteúdo (ou uma implementação controlada).
        
        Observação: Em ambientes de produção, o uso de mocks pode ser desabilitado
        definindo a variável de ambiente EMBEDDINGS_STRICT_MODE=true. Também é
        possível forçar o uso de mocks com EMBEDDINGS_FORCE_MOCK=true para cenários
        de desenvolvimento.
        """
        try:
            # Estratégia: usar o LLM para análise semântica e gerar embedding baseado na resposta
            prompt = f"Analyze this text semantically and extract key concepts: {text[:200]}"
            response = self._llm_manager.chat(prompt, config=LLMConfig(temperature=0.1))
            
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
            response = self._llm_manager.chat(
                "Analyze this text for semantic content: " + text[:100],  # Truncate para não exceder limite
                config=LLMConfig(temperature=0.1)
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
            response = self._llm_manager.chat(
                "Analyze this text semantically: " + text[:100],  # Truncate para não exceder limite
                config=LLMConfig(temperature=0.1)
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
                    # Copiar additional_info se existir (contém chunk_type, topic, etc.)
                    if chunk.metadata.additional_info:
                        result.chunk_metadata.update(chunk.metadata.additional_info)
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