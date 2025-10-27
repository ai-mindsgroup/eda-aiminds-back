"""Sistema de armazenamento vetorial usando Supabase PostgreSQL + pgvector.

Este módulo gerencia o armazenamento e busca de embeddings no banco de dados,
implementando funcionalidades de RAG (Retrieval Augmented Generation).

IMPORTANTE: PostgREST/Supabase API retorna vetores (tipo VECTOR do PostgreSQL) 
como strings ao invés de arrays. Este módulo implementa parsing defensivo para 
garantir que todos os embeddings sejam listas de floats antes de operações vetoriais.
"""
from __future__ import annotations
import uuid
import json
import ast
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import time

from src.embeddings.chunker import TextChunk, ChunkMetadata
from src.embeddings.generator import EmbeddingResult
from src.vectorstore.supabase_client import supabase
from src.settings import EMBEDDINGS_INSERT_BATCH_SIZE
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

VECTOR_DIMENSIONS = 384


def parse_embedding_from_api(embedding: Any, expected_dim: int = VECTOR_DIMENSIONS) -> List[float]:
    """Converte embedding da API Supabase para lista de floats.
    
    PostgREST/Supabase API retorna colunas do tipo VECTOR(n) como strings
    ao invés de arrays nativos. Esta função garante parsing defensivo.
    
    Args:
        embedding: Embedding retornado da API (pode ser string, lista ou None)
        expected_dim: Dimensões esperadas do vetor (default: 384)
    
    Returns:
        Lista de floats com o embedding
    
    Raises:
        ValueError: Se o embedding não puder ser convertido ou tiver dimensões incorretas
    
    Exemplos:
        >>> parse_embedding_from_api("[0.1, 0.2, 0.3]")
        [0.1, 0.2, 0.3]
        >>> parse_embedding_from_api([0.1, 0.2, 0.3])
        [0.1, 0.2, 0.3]
    """
    if embedding is None:
        raise ValueError("Embedding é None")
    
    # Caso 1: Já é uma lista
    if isinstance(embedding, list):
        parsed = embedding
    
    # Caso 2: É uma string (comportamento padrão do PostgREST com tipo VECTOR)
    elif isinstance(embedding, str):
        try:
            # Tentar ast.literal_eval (mais seguro que eval)
            parsed = ast.literal_eval(embedding)
        except (ValueError, SyntaxError):
            try:
                # Fallback: json.loads
                parsed = json.loads(embedding)
            except json.JSONDecodeError as e:
                raise ValueError(f"Não foi possível parsear embedding string: {str(e)}")
    
    else:
        raise ValueError(f"Tipo de embedding não suportado: {type(embedding)}")
    
    # Validar que é uma lista
    if not isinstance(parsed, list):
        raise ValueError(f"Embedding parseado não é lista: {type(parsed)}")
    
    # Converter todos os elementos para float
    try:
        parsed_floats = [float(x) for x in parsed]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Não foi possível converter elementos para float: {str(e)}")
    
    # Validar dimensões
    if len(parsed_floats) != expected_dim:
        raise ValueError(
            f"Embedding tem {len(parsed_floats)} dimensões, esperado {expected_dim}"
        )
    
    return parsed_floats


@dataclass
class VectorSearchResult:
    """Resultado de uma busca vetorial."""
    chunk_text: str
    similarity_score: float
    metadata: Dict[str, Any]
    embedding_id: str
    source: str
    chunk_index: int
    embedding: Optional[List[float]] = None  # Campo para armazenar embedding parseado


@dataclass
class StoredEmbedding:
    """Representa um embedding armazenado no banco."""
    id: str
    chunk_text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime


class VectorStore:
    def invalidate_embedding_cache(self):
        """Invalida cache/memória de embeddings após nova ingestão."""
        # Exemplo: se usar cache local/global, limpe aqui
        if hasattr(self, 'embedding_cache'):
            self.embedding_cache = None
        self.logger.info("Cache de embeddings invalidado após nova ingestão.")

    def refresh_embeddings(self, ingestion_id: str):
        """Atualiza memória/contexto para o ingestion_id atual."""
        self.invalidate_embedding_cache()
        # Busca todos os embeddings do ingestion_id atual
        embeddings = self.search_similar([0.0]*384, similarity_threshold=0.0, limit=1000, filters={'ingestion_id': ingestion_id})
        # Atualize contexto/memória conforme necessário
        self.logger.info(f"Memória/contexto atualizado para ingestion_id={ingestion_id} com {len(embeddings)} embeddings.")
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
        """Armazena embeddings no banco de dados com retry robusto e backoff exponencial.
        
        Implementa mecanismo resiliente para lidar com timeouts do Supabase (erro 57014):
        - Retry com backoff exponencial (2^attempt segundos)
        - Divisão recursiva de lotes ao detectar timeout
        - Fallback para inserção individual após 3 tentativas falhadas
        - Logging estruturado de todas as operações
        
        Args:
            embedding_results: Lista de resultados de embeddings
            source_type: Tipo da fonte (text, csv, document, etc.)
        
        Returns:
            Lista de IDs dos embeddings inseridos com sucesso
        """
        if not embedding_results:
            self.logger.warning("Nenhum embedding para armazenar")
            return []
        
        self.logger.info(f"🚀 Iniciando armazenamento de {len(embedding_results)} embeddings")
        
        # Validar dimensões antes de preparar dados para inserção
        for result in embedding_results:
            actual_dims = len(result.embedding)
            if actual_dims != VECTOR_DIMENSIONS:
                chunk_idx = None
                if result.chunk_metadata:
                    chunk_idx = result.chunk_metadata.get("chunk_index")
                message = (
                    f"Dimensão do embedding incompatível: {actual_dims}D"
                    f" (esperado {VECTOR_DIMENSIONS}D)"
                    f" no chunk {chunk_idx if chunk_idx is not None else 'desconhecido'}. "
                    "Ajuste o provedor de embeddings ou atualize o schema do Supabase."
                )
                self.logger.error(message)
                raise ValueError(message)

        # Preparar dados para inserção
        insert_data = []
        for result in embedding_results:
            # Criar metadados consolidados
            metadata = {
                "provider": result.provider.value,
                "model": result.model,
                "dimensions": result.dimensions,
                "raw_dimensions": result.raw_dimensions,
                "processing_time": result.processing_time,
                "source_type": source_type,
                "created_at": datetime.now().isoformat()
            }
            
            # Adicionar metadados do chunk se disponíveis
            if result.chunk_metadata:
                metadata.update(result.chunk_metadata)
            
            # Converter embedding para formato PostgreSQL vector
            # O client Supabase requer string no formato "[1.0,2.0,3.0]"
            embedding_str = "[" + ",".join(str(float(x)) for x in result.embedding) + "]"
            
            insert_data.append({
                "chunk_text": result.chunk_content,
                "embedding": embedding_str,
                "metadata": metadata
            })
        
        total = len(insert_data)
        batch_size = EMBEDDINGS_INSERT_BATCH_SIZE  # Configurável via .env para evitar timeouts
        inserted_ids: List[str] = []
        total_batches = (total + batch_size - 1) // batch_size
        
        # Contadores para estatísticas
        retry_stats = {
            'total_retries': 0,
            'splits_performed': 0,
            'individual_fallbacks': 0,
            'failed_embeddings': 0
        }
        
        def _is_timeout_error(error: Exception) -> bool:
            """Detecta se erro é timeout do PostgreSQL/Supabase."""
            err_str = str(error)
            return ('57014' in err_str) or ('statement timeout' in err_str.lower())
        
        def _insert_with_retry(
            payload: List[Dict[str, Any]], 
            batch_label: str,
            depth: int = 0,
            max_depth: int = 10
        ) -> List[str]:
            """Insere payload com retry exponencial e divisão recursiva.
            
            Args:
                payload: Dados a inserir
                batch_label: Identificação do lote para logging
                depth: Profundidade da recursão (controla backoff)
                max_depth: Profundidade máxima para evitar recursão infinita
                
            Returns:
                Lista de IDs inseridos com sucesso
            """
            payload_size = len(payload)
            
            # Proteção contra recursão infinita
            if depth > max_depth:
                self.logger.error(
                    f"⚠️ Profundidade máxima atingida ({max_depth}) para {batch_label}. "
                    f"Pulando {payload_size} embeddings."
                )
                retry_stats['failed_embeddings'] += payload_size
                return []
            
            # Tentativa de inserção direta
            try:
                self.logger.debug(f"📤 Tentando inserir {batch_label}: {payload_size} registros (depth={depth})")
                response = self.supabase.table('embeddings').insert(payload).execute()
                
                # Verificar erro explícito
                if getattr(response, 'error', None):
                    raise RuntimeError(response.error)
                
                # Verificar resposta vazia
                if not response.data:
                    raise RuntimeError("Resposta vazia do Supabase")
                
                # Sucesso imediato
                ids = [row['id'] for row in response.data]
                self.logger.debug(f"✅ {batch_label} inserido com sucesso: {len(ids)} registros")
                return ids
                
            except Exception as e:
                # Detectar se é timeout
                if not _is_timeout_error(e):
                    # Erro não-timeout: propaga imediatamente
                    self.logger.error(f"❌ Erro não-timeout em {batch_label}: {str(e)[:200]}")
                    raise
                
                # TIMEOUT DETECTADO
                retry_stats['total_retries'] += 1
                self.logger.warning(
                    f"⏱️ TIMEOUT detectado em {batch_label} "
                    f"({payload_size} registros, depth={depth})"
                )
                
                # Estratégia 1: Dividir lote ao meio se possível
                if payload_size > 1:
                    retry_stats['splits_performed'] += 1
                    mid = payload_size // 2
                    
                    self.logger.info(
                        f"🔀 Dividindo {batch_label}: {payload_size} → "
                        f"{mid} + {payload_size - mid} registros"
                    )
                    
                    # Recursão em ambas as metades
                    left_label = f"{batch_label}.L"
                    right_label = f"{batch_label}.R"
                    
                    left_ids = _insert_with_retry(payload[:mid], left_label, depth + 1, max_depth)
                    right_ids = _insert_with_retry(payload[mid:], right_label, depth + 1, max_depth)
                    
                    return left_ids + right_ids
                
                # Estratégia 2: Lote unitário → Retry com backoff exponencial
                retry_stats['individual_fallbacks'] += 1
                max_attempts = 3
                backoff_seconds = min(8.0, 0.5 * (2 ** depth))
                
                self.logger.info(
                    f"🔄 Fallback individual para {batch_label}: "
                    f"backoff inicial={backoff_seconds:.2f}s, max_attempts={max_attempts}"
                )
                
                for attempt in range(1, max_attempts + 1):
                    self.logger.debug(
                        f"   Tentativa {attempt}/{max_attempts} após {backoff_seconds:.2f}s..."
                    )
                    time.sleep(backoff_seconds)
                    
                    try:
                        response = self.supabase.table('embeddings').insert(payload).execute()
                        
                        if getattr(response, 'error', None):
                            raise RuntimeError(response.error)
                        if not response.data:
                            raise RuntimeError("Resposta vazia")
                        
                        # Sucesso no retry
                        embedding_id = response.data[0]['id']
                        self.logger.info(
                            f"✅ {batch_label} inserido após {attempt} tentativas "
                            f"(total backoff: {backoff_seconds * (2**(attempt-1)):.2f}s)"
                        )
                        return [embedding_id]
                        
                    except Exception as retry_error:
                        if attempt < max_attempts:
                            # Ainda há tentativas: aumenta backoff exponencialmente
                            backoff_seconds = min(8.0, backoff_seconds * 2)
                            self.logger.warning(
                                f"   ⚠️ Tentativa {attempt} falhou: {str(retry_error)[:100]}"
                            )
                        else:
                            # Última tentativa esgotada
                            self.logger.error(
                                f"   ❌ {batch_label} falhou após {max_attempts} tentativas: "
                                f"{str(retry_error)[:200]}"
                            )
                            retry_stats['failed_embeddings'] += 1
                            return []
                
                # Não deveria chegar aqui, mas garantir retorno vazio
                return []
        
        # Processar batches com retry robusto
        try:
            start_time = time.time()
            
            for batch_index in range(total_batches):
                start_idx = batch_index * batch_size
                end_idx = min(start_idx + batch_size, total)
                batch_payload = insert_data[start_idx:end_idx]
                batch_label = f"Batch-{batch_index + 1}/{total_batches}"
                
                self.logger.info(
                    f"📦 Processando {batch_label}: "
                    f"{len(batch_payload)} embeddings (índices {start_idx}-{end_idx-1})"
                )
                
                # Inserir com retry
                ids = _insert_with_retry(batch_payload, batch_label, depth=0)
                inserted_ids.extend(ids)
                
                self.logger.info(
                    f"✅ {batch_label} concluído: {len(ids)}/{len(batch_payload)} inseridos "
                    f"({len(inserted_ids)}/{total} total)"
                )
            
            elapsed_time = time.time() - start_time
            
            # Relatório final
            success_count = len(inserted_ids)
            failed_count = total - success_count
            success_rate = (success_count / total * 100) if total > 0 else 0
            
            self.logger.info(
                f"\n{'='*70}\n"
                f"📊 ARMAZENAMENTO CONCLUÍDO\n"
                f"{'='*70}\n"
                f"   Total embeddings: {total}\n"
                f"   ✅ Sucesso: {success_count} ({success_rate:.1f}%)\n"
                f"   ❌ Falhas: {failed_count}\n"
                f"   🔄 Retries aplicados: {retry_stats['total_retries']}\n"
                f"   🔀 Divisões de lote: {retry_stats['splits_performed']}\n"
                f"   🔄 Fallbacks individuais: {retry_stats['individual_fallbacks']}\n"
                f"   ⏱️ Tempo total: {elapsed_time:.2f}s\n"
                f"   ⚡ Taxa: {total / elapsed_time:.2f} embeddings/s\n"
                f"{'='*70}"
            )
            
            if failed_count > 0:
                self.logger.warning(
                    f"⚠️ ATENÇÃO: {failed_count} embeddings não foram armazenados. "
                    f"Considere aumentar EMBEDDINGS_INSERT_BATCH_SIZE ou verificar conectividade."
                )
            
            return inserted_ids
            
        except Exception as e:
            error_details = getattr(e, 'args', None)
            self.logger.error(
                f"❌ Erro crítico no armazenamento: {str(e)[:200]} | detalhes: {error_details}"
            )
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
                embedding_parsed = parse_embedding_from_api(row['embedding'])
                metadata = row.get('metadata') or {}
                result = VectorSearchResult(
                    chunk_text=row['chunk_text'],
                    similarity_score=float(row['similarity']),
                    metadata=metadata,
                    embedding_id=row['id'],
                    source=metadata.get('source', 'unknown'),
                    chunk_index=metadata.get('chunk_index', 0)
                )
                result.embedding = embedding_parsed
                results.append(result)

            # Aplicar filtros de metadata no cliente se fornecidos (ex: {'ingestion_id': id})
            if filters:
                def _matches_filters(meta: dict, flt: dict) -> bool:
                    for k, v in flt.items():
                        # metadata pode conter valores aninhados ou strings; comparar como string/valor direto
                        if meta is None:
                            return False
                        meta_val = meta.get(k)
                        if meta_val != v:
                            return False
                    return True

                filtered = [r for r in results if _matches_filters(r.metadata, filters)]
                self.logger.info(f"Encontrados {len(filtered)} resultados após aplicar filtros {filters}")
                return filtered

            self.logger.info(f"Encontrados {len(results)} resultados similares")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na busca vetorial: {str(e)}")
            # Fallback para busca simples por texto se busca vetorial falhar
            for row in response.data:
                # Similaridade mock baseada no comprimento do texto (apenas para fallback)
                mock_similarity = min(0.9, len(row['chunk_text']) / 1000)
                embedding_parsed = parse_embedding_from_api(row['embedding'])
                
                result = VectorSearchResult(
                    chunk_text=row['chunk_text'],
                    similarity_score=mock_similarity,
                    metadata=row['metadata'] or {},
                    embedding_id=row['id'],
                    source=row['metadata'].get('source', 'unknown'),
                    chunk_index=row['metadata'].get('chunk_index', 0)
                )
                result.embedding = embedding_parsed
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
            embedding_parsed = parse_embedding_from_api(row['embedding'])
            return StoredEmbedding(
                id=row['id'],
                chunk_text=row['chunk_text'],
                embedding=embedding_parsed,
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
        rpc_function_sql = f"""
        CREATE OR REPLACE FUNCTION match_embeddings(
            query_embedding vector({VECTOR_DIMENSIONS}),
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