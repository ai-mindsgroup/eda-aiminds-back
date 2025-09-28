"""Agente RAG (Retrieval Augmented Generation) para consultas inteligentes.

Este agente combina:
- Chunking de texto/dados
- Geração de embeddings  
- Busca vetorial
- Geração de respostas contextualizadas via LLM
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Union, Tuple
import time

from src.agent.base_agent import BaseAgent, AgentError
from src.embeddings.chunker import TextChunker, ChunkStrategy, TextChunk
from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
from src.embeddings.vector_store import VectorStore, VectorSearchResult
from src.api.sonar_client import send_sonar_query


class RAGAgent(BaseAgent):
    """Agente RAG para consultas inteligentes com contexto vetorial."""
    
    def __init__(self, 
                 embedding_provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMER,
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """Inicializa o agente RAG.
        
        Args:
            embedding_provider: Provedor de embeddings
            chunk_size: Tamanho dos chunks em caracteres
            chunk_overlap: Sobreposição entre chunks
        """
        super().__init__(
            name="rag_agent",
            description="Agente RAG para consultas contextualizadas com busca vetorial"
        )
        
        # Inicializar componentes
        try:
            self.chunker = TextChunker(
                chunk_size=chunk_size,
                overlap_size=chunk_overlap,
                min_chunk_size=50
            )
            
            self.embedding_generator = EmbeddingGenerator(
                provider=embedding_provider
            )
            
            self.vector_store = VectorStore()
            
            self.logger.info("Agente RAG inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do RAG: {str(e)}")
            raise AgentError(self.name, f"Falha na inicialização: {str(e)}")
    
    def ingest_text(self, 
                   text: str, 
                   source_id: str,
                   source_type: str = "text",
                   chunk_strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE) -> Dict[str, Any]:
        """Ingesta texto no sistema RAG (chunking + embeddings + armazenamento).
        
        Args:
            text: Texto para processar
            source_id: Identificador único da fonte
            source_type: Tipo da fonte (text, csv, document)
            chunk_strategy: Estratégia de chunking
        
        Returns:
            Resultado do processamento com estatísticas
        """
        self.logger.info(f"Iniciando ingestão: {len(text)} chars, fonte: {source_id}")
        start_time = time.perf_counter()
        
        try:
            # 1. Chunking
            self.logger.info("Executando chunking...")
            chunks = self.chunker.chunk_text(text, source_id, chunk_strategy)
            
            if not chunks:
                return self._build_response(
                    "Nenhum chunk válido foi criado a partir do texto",
                    metadata={"error": True}
                )
            
            chunk_stats = self.chunker.get_stats(chunks)
            self.logger.info(f"Criados {len(chunks)} chunks")
            
            # 2. Geração de embeddings
            self.logger.info("Gerando embeddings...")
            embedding_results = self.embedding_generator.generate_embeddings_batch(chunks)
            
            if not embedding_results:
                return self._build_response(
                    "Falha na geração de embeddings",
                    metadata={"error": True, "chunk_stats": chunk_stats}
                )
            
            embedding_stats = self.embedding_generator.get_embedding_stats(embedding_results)
            self.logger.info(f"Gerados {len(embedding_results)} embeddings")
            
            # 3. Armazenamento
            self.logger.info("Armazenando no vector store...")
            stored_ids = self.vector_store.store_embeddings(embedding_results, source_type)
            
            processing_time = time.perf_counter() - start_time
            
            # Estatísticas consolidadas
            stats = {
                "source_id": source_id,
                "source_type": source_type,
                "processing_time": processing_time,
                "chunks_created": len(chunks),
                "embeddings_generated": len(embedding_results),
                "embeddings_stored": len(stored_ids),
                "chunk_strategy": chunk_strategy.value,
                "chunk_stats": chunk_stats,
                "embedding_stats": embedding_stats,
                "success_rate": len(stored_ids) / len(chunks) * 100 if chunks else 0
            }
            
            response = f"✅ Ingestão concluída para '{source_id}'\n" \
                      f"📊 {len(chunks)} chunks → {len(embedding_results)} embeddings → {len(stored_ids)} armazenados\n" \
                      f"⏱️ Processado em {processing_time:.2f}s"
            
            self.logger.info(f"Ingestão concluída: {stats['success_rate']:.1f}% sucesso")
            
            return self._build_response(response, metadata=stats)
            
        except Exception as e:
            self.logger.error(f"Erro na ingestão: {str(e)}")
            return self._build_response(
                f"Erro na ingestão: {str(e)}",
                metadata={"error": True}
            )
    
    def ingest_csv_data(self, 
                       csv_text: str, 
                       source_id: str,
                       include_headers: bool = True) -> Dict[str, Any]:
        """Ingesta dados CSV usando estratégia especializada."""
        return self.ingest_text(
            text=csv_text,
            source_id=source_id,
            source_type="csv",
            chunk_strategy=ChunkStrategy.CSV_ROW
        )
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta RAG com busca vetorial e geração contextualizada.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional (filtros, configurações)
        
        Returns:
            Resposta contextualizada baseada na busca vetorial
        """
        self.logger.info(f"Processando consulta RAG: '{query[:50]}...'")
        start_time = time.perf_counter()
        
        try:
            # Configurações da busca
            config = context or {}
            similarity_threshold = config.get('similarity_threshold', 0.7)
            max_results = config.get('max_results', 5)
            include_context = config.get('include_context', True)
            
            # 1. Gerar embedding da query
            self.logger.debug("Gerando embedding da consulta...")
            query_embedding_result = self.embedding_generator.generate_embedding(query)
            query_embedding = query_embedding_result.embedding
            
            # 2. Busca vetorial
            self.logger.debug(f"Executando busca vetorial (threshold={similarity_threshold})")
            search_results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                similarity_threshold=similarity_threshold,
                limit=max_results
            )
            
            if not search_results:
                return self._build_response(
                    "❌ Nenhum contexto relevante encontrado na base de conhecimento.",
                    metadata={
                        "query": query,
                        "search_results_count": 0,
                        "similarity_threshold": similarity_threshold
                    }
                )
            
            # 3. Construir contexto a partir dos resultados
            context_pieces = []
            source_info = {}
            
            for result in search_results:
                context_pieces.append(f"[Fonte: {result.source}, Similaridade: {result.similarity_score:.3f}]\n{result.chunk_text}")
                
                source = result.source
                if source not in source_info:
                    source_info[source] = {
                        "chunks": 0,
                        "avg_similarity": 0,
                        "max_similarity": 0
                    }
                
                source_info[source]["chunks"] += 1
                source_info[source]["max_similarity"] = max(source_info[source]["max_similarity"], result.similarity_score)
            
            # Calcular médias de similaridade
            for source in source_info:
                source_results = [r for r in search_results if r.source == source]
                source_info[source]["avg_similarity"] = sum(r.similarity_score for r in source_results) / len(source_results)
            
            # 4. Gerar resposta contextualizada via LLM
            if include_context:
                context_text = "\n\n---\n\n".join(context_pieces)
                
                rag_prompt = f"""Você é um assistente especializado em análise de dados. Baseando-se EXCLUSIVAMENTE no contexto fornecido abaixo, responda à pergunta do usuário de forma clara e objetiva.

CONTEXTO RELEVANTE:
{context_text}

PERGUNTA DO USUÁRIO: {query}

INSTRUÇÕES:
- Use APENAS as informações do contexto fornecido
- Se não houver informação suficiente no contexto, diga claramente
- Cite as fontes quando apropriado
- Seja preciso e objetivo na resposta
- Se encontrar dados numéricos, inclua-os na resposta

RESPOSTA:"""
                
                self.logger.debug("Gerando resposta via LLM...")
                llm_response = self._call_llm(rag_prompt, context)
                
                # Extrair conteúdo da resposta
                if llm_response and 'choices' in llm_response:
                    content = llm_response['choices'][0]['message']['content']
                else:
                    content = "Erro ao gerar resposta contextualizada."
            
            else:
                # Apenas retornar informações dos resultados da busca
                content = f"📄 Encontrados {len(search_results)} resultados relevantes na base de conhecimento.\n\n"
                
                for i, result in enumerate(search_results, 1):
                    content += f"**Resultado {i}** (Similaridade: {result.similarity_score:.3f})\n"
                    content += f"Fonte: {result.source}\n"
                    content += f"Texto: {result.chunk_text[:200]}...\n\n"
            
            processing_time = time.perf_counter() - start_time
            
            # Metadados da resposta
            metadata = {
                "query": query,
                "processing_time": processing_time,
                "search_results_count": len(search_results),
                "sources_found": list(source_info.keys()),
                "source_stats": source_info,
                "similarity_threshold": similarity_threshold,
                "embedding_provider": query_embedding_result.provider.value,
                "embedding_model": query_embedding_result.model,
                "rag_mode": "contextual" if include_context else "search_only"
            }
            
            self.logger.info(f"Consulta RAG concluída: {len(search_results)} resultados em {processing_time:.2f}s")
            
            return self._build_response(content, metadata=metadata)
            
        except Exception as e:
            self.logger.error(f"Erro no processamento RAG: {str(e)}")
            return self._build_response(
                f"Erro no processamento RAG: {str(e)}",
                metadata={"error": True, "query": query}
            )
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da base de conhecimento."""
        try:
            stats = self.vector_store.get_collection_stats()
            
            response = f"""📊 **Estatísticas da Base de Conhecimento**

📈 **Geral**
• Total de embeddings: {stats.get('total_embeddings', 0):,}

📁 **Por Fonte**
{self._format_stats_dict(stats.get('sources', {}))}

🔧 **Por Provider**
{self._format_stats_dict(stats.get('providers', {}))}

🤖 **Por Modelo**
{self._format_stats_dict(stats.get('models', {}))}"""
            
            return self._build_response(response, metadata=stats)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return self._build_response(
                f"Erro ao obter estatísticas: {str(e)}",
                metadata={"error": True}
            )
    
    def _format_stats_dict(self, stats_dict: Dict[str, int]) -> str:
        """Formata dicionário de estatísticas."""
        if not stats_dict:
            return "• Nenhum dado disponível"
        
        formatted = []
        for key, count in sorted(stats_dict.items(), key=lambda x: x[1], reverse=True):
            formatted.append(f"• {key}: {count:,}")
        
        return "\n".join(formatted)
    
    def clear_source(self, source_id: str) -> Dict[str, Any]:
        """Remove todos os embeddings de uma fonte específica."""
        try:
            deleted_count = self.vector_store.delete_embeddings_by_source(source_id)
            
            if deleted_count > 0:
                message = f"✅ Removidos {deleted_count:,} embeddings da fonte '{source_id}'"
            else:
                message = f"ℹ️ Nenhum embedding encontrado para a fonte '{source_id}'"
            
            return self._build_response(
                message,
                metadata={"source_id": source_id, "deleted_count": deleted_count}
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar fonte {source_id}: {str(e)}")
            return self._build_response(
                f"Erro ao limpar fonte: {str(e)}",
                metadata={"error": True, "source_id": source_id}
            )