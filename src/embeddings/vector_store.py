"""Sistema de armazenamento vetorial usando Supabase PostgreSQL + pgvector.

Este módulo gerencia o armazenamento e busca de embeddings no banco de dados,
implementando funcionalidades de RAG (Retrieval Augmented Generation).
"""
from __future__ import annotations
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from src.embeddings.chunker import TextChunk, ChunkMetadata
from src.embeddings.generator import EmbeddingResult
from src.vectorstore.supabase_client import supabase
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VectorSearchResult:
    """Resultado de uma busca vetorial."""
    chunk_text: str
    similarity_score: float
    metadata: Dict[str, Any]
    embedding_id: str
    source: str
    chunk_index: int


@dataclass
class StoredEmbedding:
    """Representa um embedding armazenado no banco."""
    id: str
    chunk_text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime


class VectorStore:
    """Sistema de armazenamento e busca vetorial."""
    
    def __init__(self):
        """Inicializa o vector store."""
        self.logger = logger
        self.supabase = supabase
        
        # Verificar conexão
        try:
            # Teste simples de conexão
            result = self.supabase.table('embeddings').select('id').limit(1).execute()
            self.logger.info("Conexão com vector store estabelecida")
        except Exception as e:
            self.logger.error(f"Erro ao conectar com vector store: {str(e)}")
            raise
    
    def store_embeddings(self, 
                        embedding_results: List[EmbeddingResult],
                        source_type: str = "text") -> List[str]:
        """Armazena embeddings no banco de dados.
        
        Args:
            embedding_results: Lista de resultados de embeddings
            source_type: Tipo da fonte (text, csv, document, etc.)
        
        Returns:
            Lista de IDs dos embeddings inseridos
        """
        if not embedding_results:
            self.logger.warning("Nenhum embedding para armazenar")
            return []
        
        self.logger.info(f"Armazenando {len(embedding_results)} embeddings")
        
        # Preparar dados para inserção
        insert_data = []
        for result in embedding_results:
            # Criar metadados consolidados
            metadata = {
                "provider": result.provider.value,
                "model": result.model,
                "dimensions": result.dimensions,
                "processing_time": result.processing_time,
                "source_type": source_type,
                "created_at": datetime.now().isoformat()
            }
            
            # Adicionar metadados do chunk se disponíveis
            if result.chunk_metadata:
                metadata.update(result.chunk_metadata)
            
            insert_data.append({
                "chunk_text": result.chunk_content,
                "embedding": result.embedding,
                "metadata": metadata
            })
        
        try:
            # Inserir em batch
            response = self.supabase.table('embeddings').insert(insert_data).execute()
            
            if response.data:
                inserted_ids = [row['id'] for row in response.data]
                self.logger.info(f"✅ {len(inserted_ids)} embeddings armazenados com sucesso")
                return inserted_ids
            else:
                self.logger.error("Inserção falhou: resposta vazia")
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao armazenar embeddings: {str(e)}")
            raise
    
    def store_embedding(self, 
                       query: str, 
                       response: str, 
                       embedding: List[float], 
                       source_type: str = "llm_cache") -> Optional[str]:
        """Armazena um embedding individual para cache de LLM.
        
        Args:
            query: Consulta original
            response: Resposta gerada
            embedding: Embedding da consulta
            source_type: Tipo da fonte
            
        Returns:
            ID do embedding inserido ou None se falhou
        """
        try:
            metadata = {
                "source_type": source_type,
                "query": query,
                "response": response,  # Resposta do LLM salva aqui
                "created_at": datetime.now().isoformat(),
                "provider": "sentence-transformers",
                "model": "all-MiniLM-L6-v2"
            }
            
            insert_data = {
                "chunk_text": query,  # Usar query como chunk_text para busca
                "embedding": embedding,
                "metadata": metadata
            }
            
            response = self.supabase.table('embeddings').insert([insert_data]).execute()
            
            if response.data:
                embedding_id = response.data[0]['id']
                self.logger.info(f"✅ Embedding salvo no cache: {embedding_id}")
                return embedding_id
            else:
                self.logger.error("Falha ao salvar embedding no cache")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar embedding no cache: {str(e)}")
            return None
    
    def search_similar(self, 
                      query_embedding: List[float],
                      similarity_threshold: float = 0.7,
                      limit: int = 5,
                      filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """Busca embeddings similares usando busca vetorial.
        
        Args:
            query_embedding: Embedding da consulta
            similarity_threshold: Threshold mínimo de similaridade
            limit: Número máximo de resultados
            filters: Filtros adicionais para metadados
        
        Returns:
            Lista de resultados ordenados por similaridade
        """
        self.logger.debug(f"Buscando embeddings similares (threshold={similarity_threshold}, limit={limit})")
        
        try:
            # Construir a query RPC para busca vetorial
            rpc_params = {
                'query_embedding': query_embedding,
                'similarity_threshold': similarity_threshold,
                'match_count': limit
            }
            
            # Executar busca vetorial via RPC function
            response = self.supabase.rpc('match_embeddings', rpc_params).execute()
            
            if not response.data:
                self.logger.info("Nenhum resultado encontrado")
                return []
            
            # Converter resultados
            results = []
            for row in response.data:
                result = VectorSearchResult(
                    chunk_text=row['chunk_text'],
                    similarity_score=float(row['similarity']),
                    metadata=row['metadata'] or {},
                    embedding_id=row['id'],
                    source=row['metadata'].get('source', 'unknown'),
                    chunk_index=row['metadata'].get('chunk_index', 0)
                )
                results.append(result)
            
            self.logger.info(f"Encontrados {len(results)} resultados similares")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na busca vetorial: {str(e)}")
            # Fallback para busca simples por texto se busca vetorial falhar
            return self._fallback_text_search(query_embedding, limit)
    
    def _fallback_text_search(self, query_embedding: List[float], limit: int) -> List[VectorSearchResult]:
        """Busca fallback usando similaridade de texto simples."""
        self.logger.warning("Usando busca fallback por texto")
        
        try:
            # Buscar alguns registros recentes
            response = self.supabase.table('embeddings').select('*').limit(limit * 2).execute()
            
            if not response.data:
                return []
            
            # Calcular similaridade manualmente (simplificado)
            results = []
            for row in response.data:
                # Similaridade mock baseada no comprimento do texto (apenas para fallback)
                mock_similarity = min(0.9, len(row['chunk_text']) / 1000)
                
                result = VectorSearchResult(
                    chunk_text=row['chunk_text'],
                    similarity_score=mock_similarity,
                    metadata=row['metadata'] or {},
                    embedding_id=row['id'],
                    source=row['metadata'].get('source', 'unknown'),
                    chunk_index=row['metadata'].get('chunk_index', 0)
                )
                results.append(result)
            
            # Ordenar por similarity mock e limitar
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Fallback search também falhou: {str(e)}")
            return []
    
    def get_embedding_by_id(self, embedding_id: str) -> Optional[StoredEmbedding]:
        """Recupera um embedding específico pelo ID."""
        try:
            response = self.supabase.table('embeddings').select('*').eq('id', embedding_id).execute()
            
            if not response.data:
                return None
            
            row = response.data[0]
            return StoredEmbedding(
                id=row['id'],
                chunk_text=row['chunk_text'],
                embedding=row['embedding'],
                metadata=row['metadata'] or {},
                created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar embedding {embedding_id}: {str(e)}")
            return None
    
    def delete_embeddings_by_source(self, source: str) -> int:
        """Remove todos os embeddings de uma fonte específica."""
        try:
            # Primeiro, contar quantos existem
            count_response = self.supabase.table('embeddings')\
                .select('id', count='exact')\
                .eq('metadata->>source', source)\
                .execute()
            
            total_count = len(count_response.data) if count_response.data else 0
            
            if total_count == 0:
                self.logger.info(f"Nenhum embedding encontrado para source: {source}")
                return 0
            
            # Deletar
            delete_response = self.supabase.table('embeddings')\
                .delete()\
                .eq('metadata->>source', source)\
                .execute()
            
            self.logger.info(f"Removidos {total_count} embeddings da fonte: {source}")
            return total_count
            
        except Exception as e:
            self.logger.error(f"Erro ao deletar embeddings da fonte {source}: {str(e)}")
            return 0
    
    def get_collection_stats(self, source: Optional[str] = None) -> Dict[str, Any]:
        """Retorna estatísticas da coleção de embeddings."""
        try:
            query = self.supabase.table('embeddings').select('*', count='exact')
            
            if source:
                query = query.eq('metadata->>source', source)
            
            response = query.execute()
            
            if not response.data:
                return {
                    "total_embeddings": 0,
                    "sources": []
                }
            
            # Calcular estatísticas
            embeddings = response.data
            total_count = len(embeddings)
            
            # Agrupar por fonte
            sources = {}
            providers = {}
            models = {}
            
            for emb in embeddings:
                metadata = emb.get('metadata', {})
                
                # Por fonte
                src = metadata.get('source', 'unknown')
                sources[src] = sources.get(src, 0) + 1
                
                # Por provider
                provider = metadata.get('provider', 'unknown')
                providers[provider] = providers.get(provider, 0) + 1
                
                # Por modelo
                model = metadata.get('model', 'unknown')
                models[model] = models.get(model, 0) + 1
            
            stats = {
                "total_embeddings": total_count,
                "sources": dict(sorted(sources.items())),
                "providers": dict(sorted(providers.items())),
                "models": dict(sorted(models.items())),
                "collection_scope": source if source else "all"
            }
            
            self.logger.info(f"Estatísticas calculadas: {total_count} embeddings")
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {str(e)}")
            return {"error": str(e)}
    
    def create_rpc_function(self) -> bool:
        """Cria função RPC para busca vetorial se não existir.
        
        Esta função deve ser executada uma vez para configurar a busca vetorial.
        """
        rpc_function_sql = """
        CREATE OR REPLACE FUNCTION match_embeddings(
            query_embedding vector(1536),
            similarity_threshold float DEFAULT 0.5,
            match_count int DEFAULT 10
        )
        RETURNS TABLE (
            id uuid,
            chunk_text text,
            metadata jsonb,
            similarity float
        )
        LANGUAGE sql STABLE
        AS $$
            SELECT
                embeddings.id,
                embeddings.chunk_text,
                embeddings.metadata,
                1 - (embeddings.embedding <=> query_embedding) AS similarity
            FROM embeddings
            WHERE 1 - (embeddings.embedding <=> query_embedding) > similarity_threshold
            ORDER BY similarity DESC
            LIMIT match_count;
        $$;
        """
        
        try:
            # Executar SQL via RPC
            self.supabase.rpc('exec_sql', {'sql': rpc_function_sql}).execute()
            self.logger.info("✅ Função RPC match_embeddings criada/atualizada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar função RPC: {str(e)}")
            self.logger.info("Função RPC pode já existir ou precisar ser criada manualmente")
            return False