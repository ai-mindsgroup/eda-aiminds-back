"""Agente RAG (Retrieval Augmented Generation) para consultas inteligentes.

⚠️ CONFORMIDADE: Este agente funciona como AGENTE DE INGESTÃO autorizado.
Pode ler CSV diretamente para indexação na tabela embeddings.

Este agente combina:
- Chunking de texto/dados
- Geração de embeddings  
- Busca vetorial
- Geração de respostas contextualizadas via LLM
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Union, Tuple
import time
import io
from pathlib import Path

import pandas as pd

from src.agent.base_agent import BaseAgent, AgentError
from src.embeddings.chunker import TextChunker, ChunkStrategy, TextChunk
from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider
from src.embeddings.vector_store import VectorStore, VectorSearchResult
from src.api.sonar_client import send_sonar_query


class RAGAgent(BaseAgent):
    """Agente RAG para consultas inteligentes com contexto vetorial.
    
    ⚠️ CONFORMIDADE: Este agente é o AGENTE DE INGESTÃO AUTORIZADO do sistema.
    Tem permissão para ler CSV diretamente e indexar na tabela embeddings.
    """
    
    def __init__(self, 
                 embedding_provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMER,
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 csv_chunk_size_rows: int = 20,
                 csv_overlap_rows: int = 4):
        """Inicializa o agente RAG.
        
        Args:
            embedding_provider: Provedor de embeddings
            chunk_size: Tamanho dos chunks em caracteres
            chunk_overlap: Sobreposição entre chunks
        """
        super().__init__(
            name="rag_agent",
            description="Agente RAG para consultas contextualizadas com busca vetorial",
            enable_memory=True  # Habilita sistema de memória
        )
        # Cache de buscas em memória local (otimização)
        self._search_cache: Dict[str, Any] = {}
        self._relevance_scores: Dict[str, float] = {}
        
        # Inicializar componentes
        try:
            self.chunker = TextChunker(
                chunk_size=chunk_size,
                overlap_size=chunk_overlap,
                min_chunk_size=50,
                csv_chunk_size_rows=csv_chunk_size_rows,
                csv_overlap_rows=csv_overlap_rows
            )
            
            self.embedding_generator = EmbeddingGenerator(
                provider=embedding_provider
            )
            
            self.vector_store = VectorStore()
            
            self.logger.info("Agente RAG inicializado com sucesso e sistema de memória")
            
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

            # OTIMIZAÇÃO BALANCEADA: Enriquecimento leve para manter precisão sem comprometer velocidade
            if chunk_strategy == ChunkStrategy.CSV_ROW:
                chunks = self._enrich_csv_chunks_light(chunks)
            
            chunk_stats = self.chunker.get_stats(chunks)
            self.logger.info(f"Criados {len(chunks)} chunks")
            
            # 2. Geração de embeddings (MODO ASSÍNCRONO para performance)
            self.logger.info("Gerando embeddings com processamento assíncrono...")
            
            # Usar geração assíncrona se disponível
            try:
                from src.embeddings.async_generator import run_async_embeddings
                embedding_results = run_async_embeddings(
                    chunks=chunks,
                    provider=self.embedding_generator.provider,
                    max_workers=4  # 4 workers paralelos
                )
                self.logger.info("✅ Embeddings gerados com processamento assíncrono")
            except ImportError:
                # Fallback para processamento síncrono
                self.logger.warning("Processamento assíncrono não disponível, usando síncrono")
                embedding_results = self.embedding_generator.generate_embeddings_batch(chunks)
            except Exception as e:
                self.logger.error(f"Erro no processamento assíncrono: {e}, fallback para síncrono")
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
        """Ingesta dados CSV (conteúdo bruto) usando estratégia especializada.
        
        ⚠️ CONFORMIDADE: RAGAgent é o AGENTE DE INGESTÃO AUTORIZADO.
        Este método tem permissão para processar CSV diretamente.
        """
        self.logger.info(f"✅ INGESTÃO AUTORIZADA: RAGAgent processando CSV: {source_id}")
        self.logger.info("✅ CONFORMIDADE: Agente de ingestão tem permissão para ler CSV")
        
        return self.ingest_text(
            text=csv_text,
            source_id=source_id,
            source_type="csv",
            chunk_strategy=ChunkStrategy.CSV_ROW
        )

    def _enrich_csv_chunks_light(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """VERSÃO BALANCEADA - Enriquecimento leve que mantém precisão sem comprometer velocidade."""
        enriched_chunks: List[TextChunk] = []

        for chunk in chunks:
            info = chunk.metadata.additional_info or {}
            start_row = info.get("start_row")
            end_row = info.get("end_row")
            row_span = f"linhas {start_row} a {end_row}" if start_row and end_row else "intervalo não identificado"
            
            # Análise rápida sem pandas
            lines = chunk.content.split('\n')
            header_line = lines[0] if lines else ""
            data_lines = [line for line in lines[1:] if line.strip()]
            
            # Extrair nome do arquivo CSV do metadata ou do chunk
            csv_filename = metadata.get('source_file', 'dataset.csv')
            if not csv_filename.endswith('.csv'):
                # Tentar extrair do chunk_text
                import re
                csv_match = re.search(r'([\w-]+\.csv)', chunk_text)
                if csv_match:
                    csv_filename = csv_match.group(1)
            
            # Detectar automaticamente colunas do header (genérico para qualquer CSV)
            detected_columns = []
            if header_line:
                # Parsear header (com ou sem aspas)
                detected_columns = [col.strip().strip('"') for col in header_line.split(',')]
                detected_columns = [col for col in detected_columns if col and not col.startswith('#')]
            
            # Análise genérica: detectar possíveis colunas de classificação/target (última coluna)
            target_column = None
            binary_class_count = 0
            if detected_columns and len(detected_columns) > 0:
                target_column = detected_columns[-1]  # Última coluna geralmente é o target
                # Verificar se é binária (0 ou 1)
                for line in data_lines[:100]:  # Amostra
                    parts = line.split(',')
                    if parts and parts[-1].strip() in ['0', '1', '"0"', '"1"']:
                        binary_class_count += 1
            
            # Construir descrição contextual genérica e otimizada
            summary_lines = [
                f"Chunk do dataset {csv_filename} ({row_span}) - {len(data_lines)} registros",
            ]
            
            # Adicionar informações sobre colunas detectadas
            if detected_columns:
                num_cols = len(detected_columns)
                col_sample = ', '.join(detected_columns[:3])
                if num_cols > 3:
                    col_sample += f", ... ({num_cols} colunas no total)"
                summary_lines.append(f"Colunas: {col_sample}")
            
            # Se detectar possível classificação binária
            if binary_class_count > 0:
                binary_ratio = (binary_class_count / min(len(data_lines), 100)) * 100
                if binary_ratio > 50:  # Se >50% das linhas são binárias na última coluna
                    if target_column:
                        summary_lines.append(f"Coluna '{target_column}': Variável binária detectada (~{binary_ratio:.1f}% de valores binários na amostra)")
                    else:
                        summary_lines.append(f"Classificação binária detectada (~{binary_ratio:.1f}% na amostra)")
            
            # Adicionar informação sobre tipo de dados
            if len(detected_columns) > 5:
                summary_lines.append(f"Dataset com {len(detected_columns)} features para análise")
            
            # Amostra das primeiras linhas para contexto
            if len(data_lines) >= 2:
                sample_line = data_lines[0][:150] + "..." if len(data_lines[0]) > 150 else data_lines[0]
                summary_lines.append(f"Exemplo de registro: {sample_line}")
            
            # Incluir cabeçalho para referência
            summary_lines.append(f"Colunas: {header_line}")

            # CORREÇÃO CRÍTICA: Manter dados originais + adicionar contexto enriquecido
            context_summary = "\n".join(summary_lines)
            enriched_content = f"{context_summary}\n\n=== DADOS ORIGINAIS ===\n{chunk.content}"
            
            enriched_chunks.append(TextChunk(content=enriched_content, metadata=chunk.metadata))

        return enriched_chunks

    def ingest_csv_file(self,
                        file_path: str,
                        source_id: Optional[str] = None,
                        encoding: str = "utf-8",
                        errors: str = "ignore") -> Dict[str, Any]:
        """Lê um arquivo CSV do disco e ingesta utilizando a estratégia CSV_ROW.

        ⚠️ CONFORMIDADE: RAGAgent é o AGENTE DE INGESTÃO AUTORIZADO.
        Este método tem permissão para ler arquivos CSV diretamente.

        Args:
            file_path: Caminho absoluto ou relativo para o arquivo CSV.
            source_id: Identificador opcional para a fonte; usa o nome do arquivo se não fornecido.
            encoding: Codificação utilizada para leitura do arquivo.
            errors: Política de tratamento de erros de decodificação.

        Returns:
            Resposta padrão do agente com estatísticas do processamento.
        """
        path = Path(file_path)
        if not path.exists():
            message = f"Arquivo CSV não encontrado: {file_path}"
            self.logger.error(message)
            return self._build_response(message, metadata={"error": True, "file_path": file_path})

        try:
            csv_text = path.read_text(encoding=encoding, errors=errors)
        except Exception as exc:
            message = f"Falha ao ler arquivo CSV '{file_path}': {exc}"
            self.logger.error(message)
            return self._build_response(
                message,
                metadata={"error": True, "file_path": file_path, "exception": str(exc)}
            )

        resolved_source_id = source_id or path.stem
        
        # ⚠️ CONFORMIDADE: Logging de acesso autorizado
        self.logger.info(f"✅ INGESTÃO AUTORIZADA: RAGAgent lendo arquivo CSV: {file_path}")
        self.logger.info("✅ CONFORMIDADE: Agente de ingestão tem permissão para ler CSV")
        
        self.logger.info(
            "Iniciando ingestão do arquivo CSV",
            extra={"file_path": str(path.resolve()), "source_id": resolved_source_id}
        )

        return self.ingest_csv_data(csv_text=csv_text, source_id=resolved_source_id)
    
    async def process_with_search_memory(self, query: str, context: Optional[Dict[str, Any]] = None,
                                       session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa consulta RAG com memória de buscas e aprendizado de relevância.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
            session_id: ID da sessão
            
        Returns:
            Resposta contextualizada com otimização baseada em histórico
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Inicializar sessão de memória se necessário
            if session_id and self.has_memory:
                if not self._current_session_id or self._current_session_id != session_id:
                    await self.init_memory_session(session_id)
            elif not self._current_session_id and self.has_memory:
                await self.init_memory_session()
            
            # 2. Verificar cache de buscas similares
            search_key = self._generate_search_cache_key(query, context)
            cached_search = await self.recall_cached_search(search_key)
            
            if cached_search:
                self.logger.info(f"🔍 Busca recuperada do cache: {search_key}")
                cached_search['metadata']['from_search_cache'] = True
                return cached_search
            
            # 3. Recuperar histórico de relevância
            relevance_history = await self.recall_relevance_history()
            if relevance_history:
                self.logger.debug(f"📊 Aplicando histórico de relevância: {len(relevance_history)} registros")
                context = context or {}
                context['relevance_history'] = relevance_history
            
            # 4. Ajustar threshold baseado em aprendizado
            similarity_threshold = self._adaptive_similarity_threshold(query, context)
            if context:
                context['similarity_threshold'] = similarity_threshold
            else:
                context = {'similarity_threshold': similarity_threshold}
            
            # 5. Processar consulta com otimizações
            result = self.process(query, context)
            
            # 6. Calcular tempo de processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            result.setdefault('metadata', {})['processing_time_ms'] = processing_time_ms
            
            # 7. Aprender relevância dos resultados
            await self.learn_search_relevance(query, result)
            
            # 8. Cachear busca se significativa
            if self._should_cache_search(result, processing_time_ms):
                await self.cache_search_result(search_key, result, expiry_hours=6)
                self.logger.debug(f"💾 Busca salva no cache: {search_key}")
            
            # 9. Salvar interação na memória
            if self.has_memory and self._current_session_id:
                await self.remember_interaction(
                    query=query,
                    response=result.get('content', str(result)),
                    processing_time_ms=processing_time_ms,
                    metadata=result.get('metadata', {})
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento RAG com memória: {e}")
            # Fallback para processamento sem memória
            return self.process(query, context)

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
            # 3. Construir contexto a partir dos resultados
            context_pieces = []
            source_info = {}
            for idx, result in enumerate(search_results, 1):
                chunk_content = result.chunk_text
                context_pieces.append(f"[Fonte: {result.source}, Similaridade: {result.similarity_score:.3f}]\n{chunk_content}")
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
                # 📋 LOG DE AUDITORIA: Contexto completo enviado ao LLM
                self.logger.info(f"📤 Enviando {len(context_pieces)} chunks ao LLM para interpretação semântica")
                self.logger.debug(f"\n{'='*80}\n🤖 CONTEXTO COMPLETO ENVIADO AO LLM:\n{'='*80}\n{context_text[:1000]}...\n{'='*80}")

                # Recuperar estatísticas do chunker para explicar diferença entre chunks e linhas do CSV
                # CORREÇÃO: search_results são objetos VectorSearchResult, não TextChunk
                # Não podemos usar get_stats() diretamente, precisamos calcular manualmente
                total_chunks = len(search_results)
                total_csv_rows = None
                
                # Tentar extrair total de linhas dos metadados dos chunks
                for result in search_results:
                    if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
                        if 'total_csv_rows' in result.metadata:
                            total_csv_rows = result.metadata.get('total_csv_rows')
                            break
                
                explain_chunk_vs_row = ""
                if total_csv_rows is not None:
                    explain_chunk_vs_row = (
                        f"\n\n🟦 **Nota Importante:** O sistema divide o arquivo CSV em chunks para análise semântica. "
                        f"O número de chunks ({total_chunks}) não corresponde ao total de linhas do CSV original. "
                        f"O total de linhas processadas foi {total_csv_rows}. "
                        f"Cada chunk pode conter múltiplas linhas, conforme configuração de chunking. "
                        f"Para estatísticas precisas, sempre consulte o campo 'total_csv_rows' nas estatísticas."
                    )

                rag_prompt = f"""Você é um assistente especializado em análise de dados e datasets. Sua função é interpretar SEMANTICAMENTE o conteúdo textual dos chunks fornecidos abaixo para responder à pergunta do usuário.

⚠️ DIRETRIZES OBRIGATÓRIAS:
1. ANÁLISE SEMÂNTICA: Interprete o significado e contexto do texto nos chunks, não apenas repita informações literais
2. DADOS DO DATASET: Os chunks contêm descrições de datasets reais. Extraia informações sobre:
   - Tipos de dados (numéricos, categóricos, temporais)
   - Estrutura das colunas e features
   - Características dos dados (valores, distribuições, padrões)
   - Exemplos e amostras presentes no texto
3. FUNDAMENTAÇÃO: Base sua resposta EXCLUSIVAMENTE nas informações presentes nos chunks
4. PRECISÃO: Se os chunks mencionam colunas, valores ou estatísticas, inclua-os explicitamente na resposta
5. CONTEXTO: Considere que cada chunk pode conter descrições textuais, metadados e amostras de dados
6. CLAREZA: Responda de forma estruturada, citando as informações específicas encontradas nos chunks

{explain_chunk_vs_row}

CONTEXTO RECUPERADO DA BASE DE DADOS (chunk_text da tabela embeddings):
{context_text}

PERGUNTA DO USUÁRIO: {query}

INSTRUÇÕES DE RESPOSTA:
- Leia e interprete SEMANTICAMENTE cada chunk fornecido
- Extraia informações relevantes sobre o dataset descrito nos chunks
- Se encontrar menções a tipos de dados, colunas ou features, liste-os explicitamente
- Se houver exemplos de dados nos chunks, use-os para fundamentar sua resposta
- Seja específico e detalhado, evitando respostas genéricas
- Se não houver informação suficiente nos chunks, informe claramente

RESPOSTA FUNDAMENTADA:"""

                self.logger.info("🤖 Solicitando interpretação semântica ao LLM...")
                llm_response = self._call_llm(rag_prompt, context)

                # Extrair conteúdo da resposta
                if llm_response and 'choices' in llm_response:
                    content = llm_response['choices'][0]['message']['content']
                    # 📋 LOG DE AUDITORIA: Resposta do LLM
                    self.logger.info("✅ Resposta gerada pelo LLM com sucesso")
                    self.logger.debug(f"\n{'='*80}\n📥 RESPOSTA DO LLM:\n{'='*80}\n{content[:500]}...\n{'='*80}")
                else:
                    content = "Erro ao gerar resposta contextualizada."
                    self.logger.error("❌ Falha ao obter resposta do LLM")
            
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
    
    # ========================================================================
    # MÉTODOS DE MEMÓRIA ESPECÍFICOS PARA RAG
    # ========================================================================
    
    def _generate_search_cache_key(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Gera chave única para cache de busca."""
        import hashlib
        
        # Normaliza query para cache
        normalized_query = query.lower().strip()
        
        # Adiciona parâmetros relevantes de busca
        search_params = ""
        if context:
            relevant_params = {
                'similarity_threshold': context.get('similarity_threshold', 0.7),
                'max_results': context.get('max_results', 5)
            }
            search_params = str(sorted(relevant_params.items()))
        
        # Gera hash
        cache_input = f"{normalized_query}_{search_params}"
        return f"search_{hashlib.md5(cache_input.encode()).hexdigest()[:12]}"
    
    def _should_cache_search(self, result: Dict[str, Any], processing_time_ms: int) -> bool:
        """Determina se uma busca deve ser cacheada."""
        # Cachear se:
        # 1. Busca demorada (> 1000ms)
        # 2. Encontrou resultados relevantes
        # 3. Não é erro
        
        if result.get('metadata', {}).get('error', False):
            return False
        
        if processing_time_ms > 1000:
            return True
        
        metadata = result.get('metadata', {})
        search_results_count = metadata.get('search_results_count', 0)
        
        return search_results_count > 0
    
    async def cache_search_result(self, search_key: str, result: Dict[str, Any], 
                                expiry_hours: int = 6) -> None:
        """Salva resultado de busca no cache."""
        if not self.has_memory or not self._current_session_id:
            return
        
        try:
            await self.remember_analysis_result(search_key, result, expiry_hours)
            self.logger.debug(f"Resultado de busca cacheado: {search_key}")
        except Exception as e:
            self.logger.debug(f"Erro ao cachear busca: {e}")
    
    async def recall_cached_search(self, search_key: str) -> Optional[Dict[str, Any]]:
        """Recupera resultado de busca do cache."""
        if not self.has_memory or not self._current_session_id:
            return None
        
        try:
            cached_result = await self.recall_cached_analysis(search_key)
            if cached_result:
                self.logger.debug(f"Busca recuperada do cache: {search_key}")
            return cached_result
        except Exception as e:
            self.logger.debug(f"Erro ao recuperar busca cacheada: {e}")
            return None
    
    async def learn_search_relevance(self, query: str, result: Dict[str, Any]) -> None:
        """Aprende relevância de buscas para otimização futura."""
        if not self.has_memory or not self._current_session_id:
            return
        
        try:
            metadata = result.get('metadata', {})
            search_results_count = metadata.get('search_results_count', 0)
            avg_similarity = metadata.get('avg_similarity', 0.0)
            
            # Extrai características da busca
            relevance_data = {
                'query_length': len(query),
                'query_words': len(query.split()),
                'search_results_count': search_results_count,
                'avg_similarity': avg_similarity,
                'processing_time_ms': metadata.get('processing_time_ms', 0),
                'success': search_results_count > 0,
                'timestamp': time.time()
            }
            
            # Salva dados de relevância
            relevance_key = f"relevance_{int(time.time())}"
            context_key = f"search_relevance_{relevance_key}"
            
            await self.remember_data_context(relevance_data, context_key)
            
            self.logger.debug(f"Relevância de busca aprendida: {relevance_key}")
            
        except Exception as e:
            self.logger.debug(f"Erro ao aprender relevância: {e}")
    
    async def recall_relevance_history(self) -> List[Dict[str, Any]]:
        """Recupera histórico de relevância de buscas."""
        if not self.has_memory or not self._current_session_id:
            return []
        
        try:
            # Recupera contexto de relevância
            context = await self.recall_conversation_context(hours=72)  # 3 dias
            
            relevance_history = []
            for key, data in context.get('data_context', {}).items():
                if key.startswith('search_relevance_'):
                    relevance_history.append(data)
            
            # Ordena por timestamp (mais recente primeiro)
            relevance_history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            return relevance_history[:50]  # Últimos 50 registros
            
        except Exception as e:
            self.logger.debug(f"Erro ao recuperar histórico de relevância: {e}")
            return []
    
    def _adaptive_similarity_threshold(self, query: str, context: Optional[Dict[str, Any]]) -> float:
        """Calcula threshold de similaridade adaptativo baseado no histórico."""
        base_threshold = context.get('similarity_threshold', 0.7) if context else 0.7
        
        # Se não há memória, usa base
        if not self.has_memory or not self._current_session_id:
            return base_threshold
        
        try:
            # Recupera histórico de relevância do cache local se disponível
            relevance_history = self._relevance_scores.get('recent_searches', [])
            
            if not relevance_history:
                return base_threshold
            
            # Calcula estatísticas de sucesso por threshold
            successful_searches = [r for r in relevance_history if r.get('success', False)]
            
            if not successful_searches:
                return base_threshold
            
            # Calcula threshold médio de buscas bem-sucedidas
            avg_successful_similarity = sum(r.get('avg_similarity', 0.7) for r in successful_searches) / len(successful_searches)
            
            # Ajusta threshold baseado na taxa de sucesso
            success_rate = len(successful_searches) / len(relevance_history)
            
            if success_rate > 0.8:
                # Alta taxa de sucesso - pode ser mais restritivo
                adjusted_threshold = min(base_threshold + 0.1, avg_successful_similarity + 0.05)
            elif success_rate < 0.5:
                # Baixa taxa de sucesso - ser mais permissivo
                adjusted_threshold = max(base_threshold - 0.1, 0.5)
            else:
                # Taxa média - usar média das buscas bem-sucedidas
                adjusted_threshold = (base_threshold + avg_successful_similarity) / 2
            
            self.logger.debug(f"Threshold adaptativo: {base_threshold:.3f} → {adjusted_threshold:.3f} (taxa sucesso: {success_rate:.1%})")
            
            return round(adjusted_threshold, 3)
            
        except Exception as e:
            self.logger.debug(f"Erro no threshold adaptativo: {e}")
            return base_threshold
    
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

    def _enrich_csv_chunks_simple(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Versão simplificada do enriquecimento de chunks CSV."""
        enriched_chunks: List[TextChunk] = []

        for chunk in chunks:
            try:
                lines = chunk.content.strip().split('\n')
                if len(lines) < 2:  # Precisa pelo menos do header + 1 linha
                    enriched_chunks.append(chunk)
                    continue
                
                header = lines[0]
                data_lines = lines[1:]
                
                info = chunk.metadata.additional_info or {}
                start_row = info.get("start_row", "desconhecido")
                end_row = info.get("end_row", "desconhecido")
                
                # Detectar nome do arquivo CSV do metadata
                csv_filename = chunk.metadata.source or "dataset.csv"
                if not csv_filename.endswith('.csv'):
                    csv_filename = "dataset.csv"
                
                # Criar descrição textual simples e genérica
                summary = f"Dados do dataset {csv_filename} (linhas {start_row} a {end_row})\n"
                summary += f"Total de {len(data_lines)} registros\n"
                summary += f"Colunas: {header}\n"
                summary += f"Primeiras linhas como exemplo:\n"
                
                # Incluir algumas linhas de exemplo
                for i, line in enumerate(data_lines[:3]):
                    summary += f"  Linha {i+1}: {line}\n"
                
                enriched_chunks.append(TextChunk(content=summary, metadata=chunk.metadata))
                
            except Exception as exc:
                self.logger.warning("Erro no enriquecimento simples CSV: %s", exc)
                enriched_chunks.append(chunk)
                
        return enriched_chunks

    @staticmethod
    def _format_value(value: Any) -> str:
        """Formata valores numéricos para texto compacto."""
        if isinstance(value, (float, int)):
            return f"{value:.3f}" if isinstance(value, float) else str(value)
        return str(value)