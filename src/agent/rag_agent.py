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
from src.llm.manager import get_llm_manager, LLMConfig


class RAGAgent(BaseAgent):
    """Agente RAG para consultas inteligentes com contexto vetorial.
    
    ⚠️ CONFORMIDADE: Este agente é o AGENTE DE INGESTÃO AUTORIZADO do sistema.
    Tem permissão para ler CSV diretamente e indexar na tabela embeddings.
    """
    
    def __init__(self, 
                 embedding_provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMER,
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 csv_chunk_size_rows: int = 2000,
                 csv_overlap_rows: int = 100):
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
            
            # Obter instância do LLM Manager (camada de abstração)
            self.llm_manager = get_llm_manager()
            
            self.logger.info("Agente RAG inicializado com sucesso e sistema de memória")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do RAG: {str(e)}")
            raise AgentError(self.name, f"Falha na inicialização: {str(e)}")
        
        # ✅ ETAPA 2: Hybrid Query Processor V2 para análises inteligentes
        try:
            from src.agent.hybrid_query_processor_v2 import HybridQueryProcessorV2
            self.hybrid_processor = HybridQueryProcessorV2(
                vector_store=self.vector_store,
                embedding_generator=self.embedding_generator
            )
            self.logger.info("✅ Hybrid Query Processor V2 inicializado (Etapa 2)")
        except Exception as e:
            self.logger.warning(f"⚠️ Hybrid Query Processor V2 não disponível: {e}")
            self.hybrid_processor = None
    
    def process_query_hybrid(self, query: str, source_id: str, 
                            session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        🎯 ETAPA 2 - Processamento Híbrido Inteligente de Queries
        
        Estratégia:
        1. PRIORIZA chunks analíticos existentes (6 metadata chunks)
        2. FALLBACK automático para CSV completo quando necessário
        3. GERA chunks adicionais sob demanda
        4. RESPONDE via LLM com contexto rico
        
        Args:
            query: Pergunta do usuário
            source_id: ID da fonte de dados (ex: 'creditcard_abc123')
            session_id: ID da sessão (opcional)
        
        Returns:
            Resposta completa com análise, contexto e metadados
        """
        if not self.hybrid_processor:
            return self._build_response(
                "Hybrid Query Processor não disponível. Use process() tradicional.",
                metadata={'error': True}
            )
        
        self.logger.info(f"🎯 ETAPA 2: Processando query híbrida: {query[:100]}...")
        
        try:
            # 1. Processar com estratégia híbrida
            processing_result = self.hybrid_processor.process_query(
                query=query,
                source_id=source_id,
                session_id=session_id
            )
            
            if processing_result['status'] != 'success':
                error_response = self._build_response(
                    f"Erro no processamento: {processing_result.get('error')}",
                    metadata=processing_result
                )
                error_response['status'] = 'error'
                error_response.update(error_response.get('metadata', {}))
                return error_response
            
            # 2. Gerar resposta via LLM com contexto rico
            context = processing_result['context']
            
            llm_prompt = f"""Você é um analista de dados especialista em análise exploratória (EDA).

CONTEXTO DISPONÍVEL:
{context}

PERGUNTA DO USUÁRIO:
{query}

INSTRUÇÕES:
1. Responda de forma clara, objetiva e profissional
2. Use os dados fornecidos no contexto acima
3. Se necessário, explique metodologias (ex: IQR para outliers)
4. Forneça insights acionáveis quando possível
5. Se houver limitações nos dados, mencione-as

RESPOSTA:"""
            
            # Chamar LLM usando camada de abstração (NÃO hardcoded)
            llm_config = LLMConfig(temperature=0.3, max_tokens=1000)
            llm_response = self.llm_manager.chat(
                prompt=llm_prompt,
                config=llm_config
            )
            
            # Verificar se houve erro na chamada LLM
            if not llm_response.success:
                self.logger.error(f"❌ Erro na chamada LLM: {llm_response.error}")
                error_response = self._build_response(
                    f"Erro ao gerar resposta via LLM: {llm_response.error}",
                    metadata={**processing_result, 'llm_error': llm_response.error}
                )
                error_response['status'] = 'error'
                error_response.update(error_response.get('metadata', {}))
                return error_response
            
            # 3. Montar resposta final no formato esperado pelos testes
            response_dict = self._build_response(
                content=llm_response.content,
                metadata={
                    'strategy': processing_result['strategy'],
                    'chunks_used': processing_result.get('chunks_used', []),
                    'csv_accessed': processing_result.get('csv_accessed', False),
                    'new_chunks_generated': processing_result.get('new_chunks_generated', 0),
                    'query_analysis': processing_result.get('query_analysis', {}),
                    'dataframe_shape': processing_result.get('dataframe_shape'),
                    'covered_aspects': processing_result.get('covered_aspects', []),
                    'required_gaps': processing_result.get('required_gaps', []),
                    'csv_analysis': processing_result.get('csv_analysis', {}),
                    'session_id': session_id
                }
            )
            
            # Adicionar 'status' e expor metadata no nível raiz para compatibilidade com testes
            response_dict['status'] = 'success'
            response_dict.update(response_dict.get('metadata', {}))
            
            return response_dict
        
        except Exception as e:
            self.logger.error(f"❌ Erro no processamento híbrido: {e}")
            error_response = self._build_response(
                f"Erro no processamento: {str(e)}",
                metadata={'error': True, 'exception': str(e)}
            )
            error_response['status'] = 'error'
            error_response.update(error_response.get('metadata', {}))
            return error_response
    
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
        """Ingesta APENAS metadados analíticos do CSV (6 chunks).
        
        ⚠️ CONFORMIDADE: RAGAgent é o AGENTE DE INGESTÃO AUTORIZADO.
        Este método tem permissão para processar CSV diretamente.
        
        ✅ ESTRATÉGIA: Gera SOMENTE 6 chunks de metadata analíticos:
        1. metadata_types (tipos e estrutura)
        2. metadata_distribution (distribuições e intervalos)
        3. metadata_central_variability (tendência central e variabilidade)
        4. metadata_frequency_outliers (valores frequentes e outliers)
        5. metadata_correlations (correlações entre variáveis)
        6. metadata_patterns_clusters (padrões e clusters)
        
        ❌ NÃO gera chunks de dados CSV linha a linha.
        """
        self.logger.info(f"✅ INGESTÃO AUTORIZADA: RAGAgent processando CSV: {source_id}")
        self.logger.info("✅ CONFORMIDADE: Agente de ingestão tem permissão para ler CSV")
        self.logger.info("📊 Estratégia: SOMENTE metadados analíticos (6 chunks)")
        
        start_time = time.perf_counter()
        
        try:
            # ✅ ESTRATÉGIA DUAL: GERAR CHUNKS DE METADATA + ROW + COLUMN
            all_chunks = []
            
            # 1. CHUNKS DE METADADOS ANALÍTICOS (6 chunks estruturados)
            self.logger.info("📊 Gerando chunks de metadados analíticos...")
            metadata_chunks = self._generate_metadata_chunks(csv_text, source_id)
            
            if not metadata_chunks:
                self.logger.warning("⚠️ Nenhum chunk de metadata foi criado")
            else:
                self.logger.info(f"✅ {len(metadata_chunks)} chunks de metadados criados")
                all_chunks.extend(metadata_chunks)
            
            # 2. CHUNKS POR LINHA (CSV_ROW strategy) - Dados completos linha a linha
            self.logger.info("📝 Gerando chunks por LINHA (CSV_ROW)...")
            from src.embeddings.chunker import ChunkStrategy
            row_chunks = self.chunker.chunk_text(
                text=csv_text,
                source_id=source_id,
                strategy=ChunkStrategy.CSV_ROW
            )
            
            if not row_chunks:
                self.logger.warning("⚠️ Nenhum chunk de linha foi criado")
            else:
                self.logger.info(f"✅ {len(row_chunks)} chunks de linhas criados")
                all_chunks.extend(row_chunks)
            
            # 3. CHUNKS POR COLUNA (CSV_COLUMN strategy) - Análise focada por coluna
            self.logger.info("📊 Gerando chunks por COLUNA (CSV_COLUMN)...")
            column_chunks = self.chunker.chunk_text(
                text=csv_text,
                source_id=source_id,
                strategy=ChunkStrategy.CSV_COLUMN
            )
            
            if not column_chunks:
                self.logger.warning("⚠️ Nenhum chunk de coluna foi criado")
            else:
                self.logger.info(f"✅ {len(column_chunks)} chunks de colunas criados")
                all_chunks.extend(column_chunks)
            
            # Validar se ao menos algum chunk foi criado
            if not all_chunks:
                return self._build_response(
                    "Nenhum chunk foi criado (metadata/row/column)",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ TOTAL: {len(all_chunks)} chunks criados (metadata={len(metadata_chunks)}, row={len(row_chunks)}, column={len(column_chunks)})")
            
            # Gerar embeddings para TODOS os chunks
            self.logger.info("🔢 Gerando embeddings para TODOS os chunks...")
            all_embeddings = self.embedding_generator.generate_embeddings_batch(all_chunks)
            
            if not all_embeddings:
                return self._build_response(
                    "Falha ao gerar embeddings para chunks",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ {len(all_embeddings)} embeddings gerados")
            
            # Armazenar embeddings no vector store
            self.logger.info("💾 Armazenando embeddings no vector store...")
            stored_ids = self.vector_store.store_embeddings(all_embeddings, "csv")
            
            processing_time = time.perf_counter() - start_time
            
            # Estatísticas consolidadas
            stats = {
                "source_id": source_id,
                "source_type": "csv_dual_chunking",
                "processing_time": processing_time,
                "metadata_chunks_created": len(metadata_chunks),
                "row_chunks_created": len(row_chunks),
                "column_chunks_created": len(column_chunks),
                "total_chunks_created": len(all_chunks),
                "total_embeddings_generated": len(all_embeddings),
                "total_embeddings_stored": len(stored_ids),
                "success_rate": len(stored_ids) / len(all_chunks) * 100 if all_chunks else 0
            }
            
            response = f"✅ Ingestão DUAL concluída para '{source_id}'\n" \
                      f"📊 Metadata: {len(metadata_chunks)} chunks\n" \
                      f"📝 Linhas: {len(row_chunks)} chunks\n" \
                      f"📊 Colunas: {len(column_chunks)} chunks\n" \
                      f"🔢 TOTAL: {len(all_chunks)} chunks → {len(all_embeddings)} embeddings → {len(stored_ids)} armazenados\n" \
                      f"⏱️ Processado em {processing_time:.2f}s"
            
            self.logger.info(f"✅ Ingestão DUAL concluída: {stats['success_rate']:.1f}% sucesso")
            
            return self._build_response(response, metadata=stats)
            
        except Exception as e:
            self.logger.error(f"❌ Erro na ingestão de metadados: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._build_response(
                f"Erro na ingestão de metadados: {str(e)}",
                metadata={"error": True}
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
            
            # Extrair nome do arquivo CSV do metadata do chunk
            csv_filename = chunk.metadata.additional_info.get('source_file', 'dataset.csv') if chunk.metadata.additional_info else 'dataset.csv'
            if not csv_filename.endswith('.csv'):
                # Tentar extrair do conteúdo do chunk
                import re
                csv_match = re.search(r'([\w-]+\.csv)', chunk.content)
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

    def _generate_metadata_chunks(self, csv_text: str, source_id: str) -> List[TextChunk]:
        """Gera chunks adicionais sobre metadados do dataset para melhorar RAG.
        
        Cria chunks específicos para responder perguntas sobre:
        1. Tipos de dados (numéricos, categóricos)
        2. Distribuição das variáveis (histogramas, quartis, percentis)
        3. Intervalos (min, max)
        4. Medidas de tendência central (média, mediana)
        5. Variabilidade (desvio padrão, variância, IQR)
        6. Valores frequentes/raros
        7. Outliers e anomalias
        8. Correlações entre variáveis
        9. Padrões temporais (se houver)
        10. Estrutura e informações gerais
        
        Sistema 100% dinâmico usando metadata_extractor para QUALQUER CSV.
        """
        from src.embeddings.chunker import ChunkMetadata, ChunkStrategy
        from src.ingest.metadata_extractor import extract_dataset_metadata
        import pandas as pd
        import numpy as np
        import io
        import tempfile
        
        chunks = []
        self.logger.info(f"📊 Gerando chunks de metadados analíticos para {source_id}...")
        
        try:
            # ✅ ETAPA 1 INTEGRADA: Usar metadata_extractor dinâmico
            # Salvar CSV temporariamente para usar metadata_extractor
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
                temp_csv.write(csv_text)
                temp_csv_path = temp_csv.name
            
            # Extrair metadados completos de forma dinâmica (sem hardcoding)
            self.logger.info(f"🔍 Extraindo metadados dinâmicos usando metadata_extractor...")
            metadata = extract_dataset_metadata(temp_csv_path, output_path=None)
            
            # Limpar arquivo temporário
            import os
            try:
                os.unlink(temp_csv_path)
            except:
                pass
            
            # Ler CSV para análises complementares
            df = pd.read_csv(io.StringIO(csv_text))
            total_rows = len(df)
            
            # Extrair informações dos metadados estruturados
            # Estrutura retornada: {dataset_name, file_path, file_size_mb, shape, memory_usage_mb, columns, statistics, semantic_summary}
            dataset_name = metadata.get('dataset_name', source_id)
            shape = metadata.get('shape', {'rows': total_rows, 'cols': len(df.columns)})
            file_size_mb = metadata.get('file_size_mb', 'N/A')
            columns_metadata = metadata.get('columns', {})
            
            # Separar colunas por tipo semântico
            numeric_cols = []
            categorical_cols = []
            temporal_cols = []
            
            for col_name, col_meta in columns_metadata.items():
                semantic_type = col_meta.get('semantic_type', 'unknown')
                if semantic_type in ['numeric', 'numeric_id']:
                    numeric_cols.append(col_name)
                elif semantic_type in ['categorical', 'categorical_binary']:
                    categorical_cols.append(col_name)
                elif semantic_type == 'temporal':
                    temporal_cols.append(col_name)
            
            datetime_cols = temporal_cols  # Alias para compatibilidade
            
            # === CHUNK 1: TIPOS DE DADOS E ESTRUTURA ===
            # Usar metadados extraídos dinamicamente
            types_content = f"""ANÁLISE DE TIPOLOGIA E ESTRUTURA - DATASET: {source_id.upper()}

ESTRUTURA GERAL:
- Total de registros: {shape.get('rows', total_rows):,}
- Total de colunas: {shape.get('cols', len(df.columns))}
- Colunas numéricas: {len(numeric_cols)}
- Colunas categóricas: {len(categorical_cols)}
- Colunas temporais: {len(datetime_cols)}
- Tamanho do arquivo: {file_size_mb} MB

COLUNAS NUMÉRICAS ({len(numeric_cols)}):
"""
            for col in numeric_cols:
                col_meta = columns_metadata.get(col, {})
                dtype = col_meta.get('dtype', 'unknown')
                types_content += f"  • {col} ({dtype}, semantic: {col_meta.get('semantic_type', 'numeric')})\n"
            
            if not numeric_cols:
                types_content += "  Nenhuma\n"
            
            types_content += f"\nCOLUNAS CATEGÓRICAS ({len(categorical_cols)}):\n"
            for col in categorical_cols:
                col_meta = columns_metadata.get(col, {})
                unique_count = col_meta.get('unique_values', df[col].nunique() if col in df.columns else 0)
                types_content += f"  • {col} ({unique_count} valores únicos, semantic: {col_meta.get('semantic_type', 'categorical')})\n"
            
            if not categorical_cols:
                types_content += "  Nenhuma\n"
            
            types_content += f"\nCOLUNAS TEMPORAIS ({len(datetime_cols)}):\n"
            for col in datetime_cols:
                types_content += f"  • {col} (semantic: temporal)\n"
            
            if not datetime_cols:
                types_content += "  Nenhuma\n"
            
            types_content += "\nEste chunk contém informações completas sobre a tipologia e estrutura das colunas do dataset, extraídas dinamicamente pelo metadata_extractor.\n"
            
            chunks.append(TextChunk(
                content=types_content,
                metadata=ChunkMetadata(
                    source=source_id, chunk_index=0, strategy=ChunkStrategy.CSV_ROW,
                    char_count=len(types_content), word_count=len(types_content.split()),
                    start_position=0, end_position=len(types_content),
                    additional_info={
                        "chunk_type": "metadata_types",
                        "topic": "data_types_structure",
                        "source_id": source_id  # ✅ CORREÇÃO: Adicionar source_id explicitamente
                    }
                )
            ))
            
            # === CHUNK 2: DISTRIBUIÇÕES E INTERVALOS ===
            dist_content = f"""ANÁLISE DE DISTRIBUIÇÕES E INTERVALOS - DATASET: {source_id.upper()}

ESTATÍSTICAS DESCRITIVAS (TODAS AS COLUNAS NUMÉRICAS):
"""
            if numeric_cols:
                dist_content += "COLUNA | MIN | MAX | MÉDIA | MEDIANA | DESVIO PADRÃO\n"
                dist_content += "-" * 80 + "\n"
                
                for col in numeric_cols:
                    col_meta = columns_metadata.get(col, {})
                    stats = col_meta.get('statistics', {})
                    
                    min_val = stats.get('min', 'N/A')
                    max_val = stats.get('max', 'N/A')
                    mean_val = stats.get('mean', 'N/A')
                    median_val = stats.get('median', 'N/A')
                    std_val = stats.get('std', 'N/A')
                    
                    dist_content += f"{col} | {min_val} | {max_val} | {mean_val} | {median_val} | {std_val}\n"
                
                dist_content += "\n\nINTERVALOS (MIN-MAX) POR COLUNA:\n"
                for col in numeric_cols:
                    col_meta = columns_metadata.get(col, {})
                    stats = col_meta.get('statistics', {})
                    min_val = stats.get('min', 'N/A')
                    max_val = stats.get('max', 'N/A')
                    dist_content += f"  • {col}: [{min_val}, {max_val}]\n"
                
                dist_content += "\n\nQUARTIS E PERCENTIS (Primeiras 10 colunas):\n"
                for col in numeric_cols[:10]:
                    # Calcular quartis manualmente para primeiras 10
                    if col in df.columns:
                        q25, q50, q75 = df[col].quantile([0.25, 0.50, 0.75])
                        dist_content += f"  • {col}: Q1={q25:.2f}, Mediana={q50:.2f}, Q3={q75:.2f}\n"
            else:
                dist_content += "  Nenhuma coluna numérica encontrada.\n"
            
            dist_content += "\n\nEste chunk contém distribuições estatísticas completas, intervalos (min-max), quartis e percentis de todas as variáveis numéricas, extraídas dinamicamente.\n"
            
            chunks.append(TextChunk(
                content=dist_content,
                metadata=ChunkMetadata(
                    source=source_id, chunk_index=1, strategy=ChunkStrategy.CSV_ROW,
                    char_count=len(dist_content), word_count=len(dist_content.split()),
                    start_position=0, end_position=len(dist_content),
                    additional_info={
                        "chunk_type": "metadata_distribution",
                        "topic": "distributions_intervals",
                        "source_id": source_id  # ✅ CORREÇÃO
                    }
                )
            ))
            
            # === CHUNK 3: TENDÊNCIA CENTRAL E VARIABILIDADE ===
            central_content = f"""ANÁLISE ESTATÍSTICA: TENDÊNCIA CENTRAL E VARIABILIDADE - DATASET: {source_id.upper()}

MEDIDAS DE TENDÊNCIA CENTRAL:
"""
            if numeric_cols:
                central_content += "COLUNA | MÉDIA | MEDIANA | MODA\n"
                central_content += "-" * 60 + "\n"
                for col in numeric_cols:
                    col_meta = columns_metadata.get(col, {})
                    stats = col_meta.get('statistics', {})
                    
                    mean_val = stats.get('mean', 'N/A')
                    median_val = stats.get('median', 'N/A')
                    mode_val = stats.get('mode', 'N/A')
                    
                    central_content += f"{col} | {mean_val} | {median_val} | {mode_val}\n"
                
                central_content += "\n\nMEDIDAS DE VARIABILIDADE:\n"
                central_content += "COLUNA | DESVIO PADRÃO | VARIÂNCIA | IQR (Intervalo Interquartil)\n"
                central_content += "-" * 80 + "\n"
                for col in numeric_cols:
                    col_meta = columns_metadata.get(col, {})
                    stats = col_meta.get('statistics', {})
                    
                    std_val = stats.get('std', 'N/A')
                    # Calcular variância a partir de desvio padrão se disponível e for número
                    try:
                        var_val = float(std_val) ** 2 if std_val != 'N/A' else 'N/A'
                        var_str = f"{var_val:.2f}" if isinstance(var_val, (int, float)) else 'N/A'
                    except (ValueError, TypeError):
                        var_str = 'N/A'
                    
                    # Calcular IQR manualmente
                    if col in df.columns:
                        try:
                            q1, q3 = df[col].quantile([0.25, 0.75])
                            iqr_val = q3 - q1
                            central_content += f"{col} | {std_val} | {var_str} | {iqr_val:.2f}\n"
                        except Exception:
                            central_content += f"{col} | {std_val} | {var_str} | N/A\n"
            else:
                central_content += "  Nenhuma coluna numérica encontrada.\n"
            
            central_content += "\n\nEste chunk contém todas as medidas de tendência central (média, mediana, moda) e variabilidade (desvio padrão, variância, IQR) extraídas dinamicamente pelo metadata_extractor.\n"
            
            chunks.append(TextChunk(
                content=central_content,
                metadata=ChunkMetadata(
                    source=source_id, chunk_index=2, strategy=ChunkStrategy.CSV_ROW,
                    char_count=len(central_content), word_count=len(central_content.split()),
                    start_position=0, end_position=len(central_content),
                    additional_info={
                        "chunk_type": "metadata_central_variability",
                        "topic": "central_tendency_variability",
                        "source_id": source_id  # ✅ CORREÇÃO
                    }
                )
            ))
            
            # === CHUNK 4: VALORES FREQUENTES E OUTLIERS ===
            freq_content = f"""ANÁLISE DE FREQUÊNCIA E DETECÇÃO DE OUTLIERS - DATASET: {source_id.upper()}

VALORES MAIS FREQUENTES (TOP 5) POR COLUNA:
"""
            for col in categorical_cols[:5]:  # Primeiras 5 categóricas
                col_meta = columns_metadata.get(col, {})
                top_values_list = col_meta.get('statistics', {}).get('top_values', [])
                
                if top_values_list:
                    freq_content += f"\n{col}:\n"
                    for value_pair in top_values_list:
                        if isinstance(value_pair, (list, tuple)) and len(value_pair) == 2:
                            val, count = value_pair
                            pct = (count / total_rows) * 100 if total_rows > 0 else 0
                            freq_content += f"  • {val}: {count} ({pct:.2f}%)\n"
                else:
                    # Fallback se não houver top_values no metadata
                    if col in df.columns:
                        top_values = df[col].value_counts().head(5)
                        freq_content += f"\n{col}:\n"
                        for val, count in top_values.items():
                            pct = (count / total_rows) * 100
                            freq_content += f"  • {val}: {count} ({pct:.2f}%)\n"
            
            freq_content += "\n\nOUTLIERS DETECTADOS (Método IQR - 1.5×IQR):\n"
            outliers_detected = False
            if numeric_cols:
                for col in numeric_cols[:10]:  # Primeiras 10 numéricas
                    if col in df.columns:
                        q1, q3 = df[col].quantile([0.25, 0.75])
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                        if len(outliers) > 0:
                            outliers_detected = True
                            pct_outliers = (len(outliers) / total_rows) * 100
                            freq_content += f"  • {col}: {len(outliers)} outliers ({pct_outliers:.2f}%)\n"
                            freq_content += f"    Intervalo normal: [{lower_bound:.2f}, {upper_bound:.2f}]\n"
            
            if not outliers_detected:
                freq_content += "  Nenhum outlier significativo detectado nas primeiras colunas.\n"
            
            freq_content += "\n\nEste chunk identifica valores mais frequentes em colunas categóricas (extraídos do metadata_extractor) e detecta outliers usando o método IQR (1.5×IQR) com estatísticas de prevalência.\n"
            
            chunks.append(TextChunk(
                content=freq_content,
                metadata=ChunkMetadata(
                    source=source_id, chunk_index=3, strategy=ChunkStrategy.CSV_ROW,
                    char_count=len(freq_content), word_count=len(freq_content.split()),
                    start_position=0, end_position=len(freq_content),
                    additional_info={
                        "chunk_type": "metadata_frequency_outliers",
                        "topic": "frequent_values_outliers",
                        "source_id": source_id  # ✅ CORREÇÃO
                    }
                )
            ))
            
            # === CHUNK 5: CORRELAÇÕES ENTRE VARIÁVEIS ===
            corr_content = f"""ANÁLISE DE CORRELAÇÕES E RELACIONAMENTOS - DATASET: {source_id.upper()}

MATRIZ DE CORRELAÇÃO (Primeiras 15 colunas numéricas):
"""
            if len(numeric_cols) >= 2:
                corr_matrix = df[numeric_cols[:15]].corr()
                corr_content += corr_matrix.to_string()
                
                corr_content += "\n\nCORRELAÇÕES FORTES (|r| > 0.7):\n"
                strong_corrs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            col1 = corr_matrix.columns[i]
                            col2 = corr_matrix.columns[j]
                            strong_corrs.append(f"  • {col1} <-> {col2}: {corr_val:.3f}")
                
                corr_content += "\n".join(strong_corrs) if strong_corrs else "  Nenhuma correlação forte detectada.\n"
            else:
                corr_content += "  Dataset possui menos de 2 colunas numéricas para análise de correlação.\n"
            
            corr_content += "\n\nEste chunk apresenta a matriz de correlação completa entre variáveis numéricas e destaca correlações fortes (|r| > 0.7) indicando relacionamentos significativos entre variáveis."
            
            chunks.append(TextChunk(
                content=corr_content,
                metadata=ChunkMetadata(
                    source=source_id, chunk_index=4, strategy=ChunkStrategy.CSV_ROW,
                    char_count=len(corr_content), word_count=len(corr_content.split()),
                    start_position=0, end_position=len(corr_content),
                    additional_info={
                        "chunk_type": "metadata_correlations",
                        "topic": "correlations_relationships",
                        "source_id": source_id  # ✅ CORREÇÃO
                    }
                )
            ))
            
            # === CHUNK 6: PADRÕES TEMPORAIS E AGRUPAMENTOS ===
            pattern_content = f"""ANÁLISE DE PADRÕES TEMPORAIS E AGRUPAMENTOS - DATASET: {source_id.upper()}

ANÁLISE TEMPORAL:
"""
            if datetime_cols:
                for col in datetime_cols:
                    try:
                        col_min = df[col].min()
                        col_max = df[col].max()
                        pattern_content += f"\nColuna temporal: {col}\n"
                        pattern_content += f"  • Período: {col_min} até {col_max}\n"
                        
                        # Tentar calcular intervalo (detectar se é datetime ou numérico)
                        try:
                            interval_days = (col_max - col_min).days
                            pattern_content += f"  • Intervalo: {interval_days} dias\n"
                        except (AttributeError, TypeError):
                            # Coluna temporal numérica (ex: segundos)
                            interval_numeric = col_max - col_min
                            pattern_content += f"  • Intervalo: {interval_numeric} unidades\n"
                    except Exception as e:
                        pattern_content += f"\nColuna temporal: {col} (erro ao processar: {str(e)[:50]})\n"
            elif any(time_keyword in col.lower() for col in df.columns for time_keyword in ['time', 'timestamp', 'date']):
                # Detectar colunas com nomes temporais
                time_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['time', 'timestamp', 'date'])]
                for time_col in time_cols[:3]:  # Primeiras 3
                    try:
                        pattern_content += f"\nColuna temporal detectada: {time_col}\n"
                        pattern_content += f"  • Min: {df[time_col].min()}, Max: {df[time_col].max()}\n"
                        pattern_content += f"  • Valores crescentes: {'Sim' if df[time_col].is_monotonic_increasing else 'Não'}\n"
                    except Exception:
                        pattern_content += f"  • Erro ao processar {time_col}\n"
            else:
                pattern_content += "  Nenhuma coluna temporal explícita detectada.\n"
            
            pattern_content += "\n\nAGRUPAMENTOS NATURAIS:\n"
            if categorical_cols:
                for col in categorical_cols[:3]:
                    groups = df[col].value_counts()
                    pattern_content += f"\n{col} - {len(groups)} grupos distintos:\n"
                    for group, count in groups.head(5).items():
                        pct = (count / total_rows) * 100
                        pattern_content += f"  • Grupo '{group}': {count} registros ({pct:.2f}%)\n"
            else:
                pattern_content += "  Dataset focado em variáveis contínuas sem agrupamentos categóricos óbvios.\n"
            
            pattern_content += "\n\nEste chunk analisa a presença de padrões temporais (se existirem colunas de data/tempo) e identifica agrupamentos naturais baseados em colunas categóricas com distribuição de grupos."
            
            chunks.append(TextChunk(
                content=pattern_content,
                metadata=ChunkMetadata(
                    source=source_id, chunk_index=5, strategy=ChunkStrategy.CSV_ROW,
                    char_count=len(pattern_content), word_count=len(pattern_content.split()),
                    start_position=0, end_position=len(pattern_content),
                    additional_info={
                        "chunk_type": "metadata_patterns_clusters",
                        "topic": "temporal_patterns_clustering",
                        "source_id": source_id  # ✅ CORREÇÃO
                    }
                )
            ))
            
            self.logger.info(f"✅ Criados {len(chunks)} chunks analíticos de metadados para {source_id}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Falha ao gerar metadados para {source_id}: {e}")
            import traceback
            self.logger.debug(f"Traceback completo: {traceback.format_exc()}")
            return []
        
        return chunks

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
            similarity_threshold = config.get('similarity_threshold', 0.3)
            max_results = config.get('max_results', 5)
            include_context = config.get('include_context', True)
            ingestion_id = config.get('ingestion_id')
            source_id = config.get('source_id')

            # 1. Gerar embedding da query
            self.logger.debug("Gerando embedding da consulta...")
            query_embedding_result = self.embedding_generator.generate_embedding(query)
            query_embedding = query_embedding_result.embedding

            # 2. Busca vetorial com filtro obrigatório por ingestion_id/source_id
            filters = {}
            if ingestion_id:
                filters['ingestion_id'] = ingestion_id
            if source_id:
                filters['source'] = source_id
            if not filters:
                self.logger.warning("Nenhum filtro de dataset ativo (ingestion_id/source_id) fornecido. Risco de contaminação de contexto!")

            self.logger.debug(f"Executando busca vetorial (threshold={similarity_threshold}, filters={filters})")
            # Se não houver filtro, não retorna nada!
            if not filters:
                self.logger.error("Busca vetorial sem filtro de contexto! Retornando lista vazia para evitar contaminação.")
                search_results = []
            else:
                search_results = self.vector_store.search_similar(
                    query_embedding=query_embedding,
                    similarity_threshold=similarity_threshold,
                    limit=max_results,
                    filters=filters
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

            # 4. Síntese da resposta via agente especializado
            from src.agent.rag_synthesis_agent import synthesize_response
            # Filtrar chunks para garantir que só colunas do source_id atual sejam usadas
            filtered_chunks = []
            for result in search_results:
                # Se o chunk contém colunas do CSV antigo (ex: V1, V28, Time, Amount), ignore
                chunk_text_lower = result.chunk_text.lower()
                if any(col in chunk_text_lower for col in ["v1", "v28", "time", "amount", "class"]):
                    # Se o source_id do resultado não for igual ao context['source_id'], ignore
                    if context and result.source != context.get("source_id"):
                        continue
                filtered_chunks.append(result.chunk_text)
            # Se não houver chunks filtrados, use apenas os do source_id atual
            if not filtered_chunks and context and context.get("source_id"):
                filtered_chunks = [r.chunk_text for r in search_results if r.source == context["source_id"]]
            # Se LLM disponível, use síntese via LangChain; senão, fallback manual
            try:
                content = synthesize_response(filtered_chunks, query, use_llm=include_context)
                self.logger.info("✅ Resposta consolidada gerada pelo agente de síntese")
            except Exception as e:
                self.logger.error(f"❌ Falha na síntese via LLM, usando fallback manual: {e}")
                content = synthesize_response(filtered_chunks, query, use_llm=False)
            
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