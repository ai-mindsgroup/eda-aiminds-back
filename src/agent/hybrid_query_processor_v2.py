"""
Hybrid Query Processor V2 - Refatoração Completa com Fragmentação e Memória

PRINCIPAIS MELHORIAS:
1. ✅ Integração com sistema de fragmentação de queries (FastQueryFragmenter)
2. ✅ Busca de resultados parciais/históricos no Supabase antes de processar
3. ✅ Fallback guiado pelos 6 chunks originais (evita redundância)
4. ✅ Controle dinâmico: embeddings vs CSV com fragmentação
5. ✅ Logging detalhado para auditoria completa
6. ✅ Uso consistente da camada de abstração LLM
"""

from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import asyncio

from src.agent.query_analyzer import QueryAnalyzer, QueryComplexity
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.chunker import TextChunk, ChunkMetadata, ChunkStrategy
from src.memory.supabase_memory import SupabaseMemoryManager
from src.memory.base_memory import ContextType
from src.llm.fast_fragmenter import FastQueryFragmenter, fragment_query_fast
from src.llm.simple_aggregator import execute_and_aggregate
from src.llm.query_fragmentation import TokenBudget
from src.llm.manager import get_llm_manager
from src.utils.logging_config import get_logger


class HybridQueryProcessorV2:
    """
    Processador híbrido inteligente V2 com:
    - Fragmentação automática de queries grandes (GROQ 6000 TPM)
    - Busca de histórico/cache antes de processar
    - Fallback guiado por chunks existentes (evita duplicação)
    - Controle dinâmico embeddings/CSV
    - Logging detalhado para auditoria
    """
    
    def __init__(self, 
                 vector_store: VectorStore,
                 embedding_generator: EmbeddingGenerator,
                 csv_base_path: str = "data/processado",
                 agent_name: str = "hybrid_processor"):
        """
        Args:
            vector_store: Vector store para busca e armazenamento
            embedding_generator: Gerador de embeddings
            csv_base_path: Caminho base para arquivos CSV
            agent_name: Nome do agente para memória
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.csv_base_path = Path(csv_base_path)
        self.agent_name = agent_name
        
        # Componentes integrados
        self.query_analyzer = QueryAnalyzer()
        self.fragmenter = FastQueryFragmenter()
        self.llm_manager = get_llm_manager()
        self.memory_manager = SupabaseMemoryManager(agent_name=agent_name)
        
        # Cache e configuração
        self._dataframe_cache: Dict[str, pd.DataFrame] = {}
        self.token_budget = TokenBudget(max_tokens_per_request=6000)  # GROQ limit
        
        self.logger = get_logger(f"agent.{agent_name}")
        self.logger.info(f"🚀 HybridQueryProcessorV2 inicializado")
    
    # ========================================================================
    # MÉTODO PRINCIPAL DE PROCESSAMENTO
    # ========================================================================
    
    async def process_query(self, 
                           query: str, 
                           source_id: str,
                           session_id: Optional[str] = None,
                           force_csv: bool = False) -> Dict[str, Any]:
        """
        Processa query com estratégia híbrida OTIMIZADA.
        
        FLUXO:
        1. Buscar histórico/cache no Supabase
        2. Analisar query e determinar estratégia
        3. Buscar chunks existentes (RAG)
        4. Decidir: RAG suficiente OU fallback CSV
        5. Fragmentar query se necessário (GROQ 6000 TPM)
        6. Processar com LLM (camada de abstração)
        7. Armazenar resultado em cache
        
        Args:
            query: Pergunta do usuário
            source_id: ID da fonte de dados (ex: 'creditcard_abc123')
            session_id: ID da sessão (opcional)
            force_csv: Forçar uso do CSV (debug/teste)
        
        Returns:
            Dict com resposta, contexto, metadados e chunks usados
        """
        start_time = datetime.now()
        self.logger.info(f"📥 INÍCIO - Query: {query[:100]}...")
        self.logger.info(f"   Source: {source_id} | Session: {session_id} | Force CSV: {force_csv}")
        
        # Criar sessão se não existir
        if not session_id:
            session_info = await self.memory_manager.create_session(
                metadata={'source_id': source_id, 'query': query}
            )
            session_id = session_info.session_id
            self.logger.info(f"✅ Sessão criada: {session_id}")
        
        try:
            # ETAPA 1: Buscar histórico/cache
            cached_result = await self._search_cached_result(query, source_id, session_id)
            if cached_result:
                self.logger.info("✅ CACHE HIT - Retornando resultado armazenado")
                cached_result['from_cache'] = True
                cached_result['cache_timestamp'] = cached_result.get('timestamp')
                return cached_result
            
            # ETAPA 2: Analisar query
            analysis = await self._analyze_query_with_llm(query, source_id)
            self.logger.info(f"📊 Análise: {analysis['complexity'].upper()} | "
                           f"Categoria: {analysis['category']} | "
                           f"Requer CSV: {analysis.get('requires_csv', False)}")
            
            # ETAPA 3: Buscar chunks existentes (RAG)
            existing_chunks = await self._search_existing_chunks(query, source_id)
            self.logger.info(f"📦 Chunks encontrados: {len(existing_chunks)}")
            
            # ETAPA 4: Decidir estratégia (RAG vs CSV)
            strategy_decision = await self._decide_strategy(
                query=query,
                analysis=analysis,
                existing_chunks=existing_chunks,
                force_csv=force_csv
            )
            
            self.logger.info(f"🎯 Estratégia: {strategy_decision['strategy']} | "
                           f"Razão: {strategy_decision['reason']}")
            
            # ETAPA 5: Processar baseado na estratégia
            if strategy_decision['strategy'] == 'rag_only':
                result = await self._process_with_rag_only(
                    query, source_id, existing_chunks, analysis
                )
            
            elif strategy_decision['strategy'] == 'csv_fallback':
                result = await self._process_with_csv_fallback(
                    query, source_id, existing_chunks, analysis, session_id
                )
            
            elif strategy_decision['strategy'] == 'csv_fragmented':
                result = await self._process_with_csv_fragmented(
                    query, source_id, existing_chunks, analysis, session_id
                )
            
            else:
                raise ValueError(f"Estratégia desconhecida: {strategy_decision['strategy']}")
            
            # ETAPA 6: Adicionar metadados e timing
            elapsed = (datetime.now() - start_time).total_seconds()
            result.update({
                'query': query,
                'source_id': source_id,
                'session_id': session_id,
                'query_analysis': analysis,
                'strategy_decision': strategy_decision,
                'processing_time_seconds': elapsed,
                'timestamp': datetime.now().isoformat(),
                'from_cache': False
            })
            
            # ETAPA 7: Armazenar em cache
            await self._cache_result(query, source_id, session_id, result)
            
            self.logger.info(f"✅ SUCESSO - Tempo: {elapsed:.2f}s | "
                           f"Estratégia: {result.get('strategy', 'unknown')}")
            
            return result
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ ERRO após {elapsed:.2f}s: {str(e)}", exc_info=True)
            
            return {
                'status': 'error',
                'error': str(e),
                'query': query,
                'source_id': source_id,
                'session_id': session_id,
                'processing_time_seconds': elapsed,
                'timestamp': datetime.now().isoformat()
            }
    
    # ========================================================================
    # BUSCA DE HISTÓRICO E CACHE
    # ========================================================================
    
    async def _search_cached_result(self, query: str, source_id: str, 
                                    session_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca resultados parciais/históricos no Supabase.
        
        ESTRATÉGIA:
        1. Gerar cache_key da query (hash)
        2. Buscar em agent_context com ContextType.CACHE
        3. Validar TTL (24h padrão)
        4. Retornar se válido
        """
        cache_key = self._generate_cache_key(query, source_id)
        
        try:
            self.logger.debug(f"🔍 Buscando cache: {cache_key}")
            
            cached_context = await self.memory_manager.get_context(
                session_id=session_id,
                context_type=ContextType.CACHE,
                context_key=cache_key
            )
            
            if cached_context and cached_context.context_data:
                # Verificar TTL (timezone-aware)
                now = datetime.now()
                expires_at = cached_context.expires_at
                
                # Garantir que ambos sejam timezone-aware ou timezone-naive
                if expires_at and expires_at.tzinfo:
                    now = now.replace(tzinfo=expires_at.tzinfo)
                    
                if expires_at and expires_at > now:
                    self.logger.info("✅ Cache válido encontrado")
                    return cached_context.context_data.get('result')
                else:
                    self.logger.debug("⏰ Cache expirado, ignorando")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao buscar cache: {e}")
        
        return None
    
    async def _cache_result(self, query: str, source_id: str, 
                           session_id: str, result: Dict[str, Any]) -> None:
        """
        Armazena resultado em cache no Supabase.
        
        TTL: 24 horas (configurável)
        """
        cache_key = self._generate_cache_key(query, source_id)
        
        try:
            expires_at = datetime.now() + timedelta(hours=24)
            
            await self.memory_manager.save_context(
                session_id=session_id,
                context_type=ContextType.CACHE,
                context_key=cache_key,
                context_data={'result': result, 'query': query, 'source_id': source_id},
                expires_at=expires_at,
                metadata={'cache_created_at': datetime.now().isoformat()}
            )
            
            self.logger.info(f"💾 Resultado armazenado em cache (TTL: 24h)")
        
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao armazenar cache: {e}")
    
    def _generate_cache_key(self, query: str, source_id: str) -> str:
        """Gera chave de cache baseada em query + source_id."""
        combined = f"{query.lower().strip()}|{source_id}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    # ========================================================================
    # ANÁLISE DE QUERY COM LLM
    # ========================================================================
    
    async def _analyze_query_with_llm(self, query: str, source_id: str) -> Dict[str, Any]:
        """
        Analisa query usando camada de abstração LLM.
        
        USA: QueryAnalyzer + LLMManager para decisões inteligentes
        """
        # Buscar chunks disponíveis
        available_chunks = await self._get_available_chunk_types(source_id)
        
        # Análise estruturada
        analysis = self.query_analyzer.analyze(query, available_chunks)
        
        # Enriquecer com decisão do LLM se necessário
        if analysis['complexity'] == QueryComplexity.COMPLEX.value:
            prompt = f"""Analise esta query sobre dataset {source_id}:

Query: {query}

Chunks disponíveis: {', '.join(available_chunks)}

Responda em JSON:
{{
    "requires_full_csv": true/false,
    "estimated_complexity": "low/medium/high",
    "recommended_strategy": "rag_only/csv_fallback/csv_fragmented",
    "reasoning": "explicação"
}}"""
            
            try:
                from src.llm.manager import LLMConfig
                config = LLMConfig(temperature=0.2)
                llm_response = self.llm_manager.chat(prompt, config=config)
                llm_decision = self._parse_llm_json_response(llm_response.content)
                
                analysis['llm_recommendation'] = llm_decision
                self.logger.info(f"🤖 LLM recomenda: {llm_decision.get('recommended_strategy')}")
            
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao consultar LLM: {e}")
        
        return analysis
    
    def _parse_llm_json_response(self, response: str) -> Dict[str, Any]:
        """Parse resposta JSON do LLM."""
        import json
        import re
        
        # Extrair JSON da resposta (pode ter markdown)
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return {}
    
    # ========================================================================
    # BUSCA DE CHUNKS EXISTENTES (RAG)
    # ========================================================================
    
    async def _search_existing_chunks(self, query: str, source_id: str) -> List[Dict]:
        """
        Busca chunks existentes com busca vetorial.
        
        RETORNA: Os 6 chunks analíticos originais (se existirem)
        """
        # Gerar embedding da query
        embedding_result = self.embedding_generator.generate_embedding(query)
        query_embedding = embedding_result.embedding
        
        # Busca vetorial
        search_results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            similarity_threshold=0.7,
            limit=6  # Buscar até 6 chunks analíticos
        )
        
        # Filtrar por source_id
        relevant_chunks = [
            r for r in search_results
            if r.metadata.get('source_id') == source_id
        ]
        
        self.logger.info(f"📦 Busca RAG: {len(relevant_chunks)}/{len(search_results)} relevantes")
        
        return relevant_chunks
    
    async def _get_available_chunk_types(self, source_id: str) -> List[str]:
        """
        Busca quais chunk_types existem para este source_id.
        """
        try:
            # Gerar embedding dummy para busca ampla
            embedding_result = self.embedding_generator.generate_embedding("dataset metadata")
            dummy_embedding = embedding_result.embedding
            
            # Buscar todos os chunks deste source_id
            all_chunks = self.vector_store.search_similar(
                query_embedding=dummy_embedding,
                similarity_threshold=0.0,  # Baixo threshold
                limit=100
            )
            
            # Extrair chunk_types únicos
            chunk_types = set()
            for chunk in all_chunks:
                if chunk.metadata.get('source_id') == source_id:
                    chunk_type = chunk.metadata.get('chunk_type')
                    if chunk_type:
                        chunk_types.add(chunk_type)
            
            return list(chunk_types)
        
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao buscar chunk_types: {e}")
            return []
    
    # ========================================================================
    # DECISÃO DE ESTRATÉGIA
    # ========================================================================
    
    async def _decide_strategy(self, query: str, analysis: Dict, 
                               existing_chunks: List, force_csv: bool) -> Dict[str, str]:
        """
        Decide estratégia baseada em chunks existentes e análise.
        
        ESTRATÉGIAS:
        - rag_only: Chunks suficientes para responder
        - csv_fallback: Precisa CSV, mas cabe em memória (sem fragmentar)
        - csv_fragmented: Dataset grande, requer fragmentação (GROQ 6000 TPM)
        """
        if force_csv:
            return {
                'strategy': 'csv_fragmented',
                'reason': 'Forçado por parâmetro force_csv=True'
            }
        
        # Verificar se chunks cobrem a query
        covered_aspects = self._identify_covered_aspects(existing_chunks, query)
        required_aspects = self._get_required_aspects(analysis['category'])
        
        coverage = len(covered_aspects.intersection(required_aspects)) / len(required_aspects) if required_aspects else 1.0
        
        self.logger.info(f"📊 Cobertura: {coverage*100:.1f}% ({len(covered_aspects)}/{len(required_aspects)} aspectos)")
        
        # Decisão baseada em cobertura
        if coverage >= 0.8 and len(existing_chunks) >= 3:
            return {
                'strategy': 'rag_only',
                'reason': f'Chunks cobrem {coverage*100:.0f}% dos aspectos necessários'
            }
        
        # Verificar se query é pequena (não precisa fragmentar)
        if len(query.split()) < 50:
            return {
                'strategy': 'csv_fallback',
                'reason': 'Query simples, CSV sem fragmentação'
            }
        
        # Query grande, requer fragmentação
        return {
            'strategy': 'csv_fragmented',
            'reason': f'Query complexa ({len(query.split())} palavras), fragmentação necessária'
        }
    
    def _identify_covered_aspects(self, chunks: List, query: str) -> set:
        """Identifica aspectos cobertos pelos chunks existentes."""
        covered = set()
        
        for chunk in chunks:
            chunk_type = chunk.metadata.get('chunk_type', '') if hasattr(chunk, 'metadata') else ''
            
            if 'types' in chunk_type or 'structure' in chunk_type:
                covered.update(['structure', 'schema'])
            elif 'distribution' in chunk_type:
                covered.update(['distribution', 'statistics'])
            elif 'correlation' in chunk_type:
                covered.add('correlation')
            elif 'outliers' in chunk_type or 'frequency' in chunk_type:
                covered.update(['outliers', 'anomalies'])
            elif 'patterns' in chunk_type:
                covered.add('patterns')
        
        return covered
    
    def _get_required_aspects(self, category: str) -> set:
        """Mapeia categoria da query para aspectos necessários."""
        mapping = {
            'statistics': {'statistics', 'distribution'},
            'correlation': {'correlation'},
            'outliers': {'outliers', 'anomalies'},
            'patterns': {'patterns'},
            'structure': {'structure', 'schema'},
            'visualization': {'distribution', 'statistics'}
        }
        return mapping.get(category, {'statistics'})
    
    # ========================================================================
    # PROCESSAMENTO: RAG ONLY
    # ========================================================================
    
    async def _process_with_rag_only(self, query: str, source_id: str,
                                     chunks: List, analysis: Dict) -> Dict[str, Any]:
        """
        Processa usando APENAS chunks existentes (sem CSV).
        
        VANTAGEM: Rápido, sem acesso a disco, usa embeddings otimizados
        """
        self.logger.info("✅ ESTRATÉGIA: RAG ONLY")
        
        # Montar contexto dos chunks
        context = self._build_context_from_chunks(chunks)
        
        # Gerar resposta com LLM
        prompt = f"""Baseado nos chunks analíticos abaixo, responda à query do usuário.

CHUNKS:
{context}

QUERY: {query}

Responda de forma clara e objetiva, citando os chunks quando relevante."""
        
        try:
            from src.llm.manager import LLMConfig
            config = LLMConfig(temperature=0.3, max_tokens=2048)
            llm_response = self.llm_manager.chat(prompt, config=config)
            answer = llm_response.content
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar resposta LLM: {e}")
            answer = f"Erro ao processar: {str(e)}"
        
        return {
            'status': 'success',
            'strategy': 'rag_only',
            'answer': answer,
            'context': context,
            'chunks_used': [c.metadata.get('chunk_type', 'unknown') for c in chunks],
            'chunks_count': len(chunks),
            'csv_accessed': False
        }
    
    # ========================================================================
    # PROCESSAMENTO: CSV FALLBACK (SEM FRAGMENTAÇÃO)
    # ========================================================================
    
    async def _process_with_csv_fallback(self, query: str, source_id: str,
                                         existing_chunks: List, analysis: Dict,
                                         session_id: str) -> Dict[str, Any]:
        """
        Processa com fallback CSV GUIADO pelos chunks existentes.
        
        OTIMIZAÇÃO:
        - Usa os 6 chunks como GUIA para evitar duplicação
        - Gera apenas análises complementares
        - Armazena novos chunks no Supabase
        """
        self.logger.info("🔄 ESTRATÉGIA: CSV FALLBACK GUIADO")
        
        # Identificar o que já está coberto
        covered_aspects = self._identify_covered_aspects(existing_chunks, query)
        required_aspects = self._get_required_aspects(analysis['category'])
        
        gaps = required_aspects - covered_aspects
        
        self.logger.info(f"📊 Aspectos cobertos: {covered_aspects}")
        self.logger.info(f"⚠️ Gaps identificados: {gaps}")
        
        # Carregar CSV apenas se houver gaps
        csv_analysis = None
        new_chunks = []
        
        if gaps:
            self.logger.info("📂 Carregando CSV para preencher gaps...")
            df = await self._load_csv_async(source_id)
            
            if df is not None:
                # Análise FOCADA nos gaps
                csv_analysis = await self._perform_focused_analysis(df, query, gaps)
                
                # Gerar chunks COMPLEMENTARES (não duplicados)
                new_chunks = await self._generate_complementary_chunks(
                    query, csv_analysis, covered_aspects, source_id
                )
                
                if new_chunks:
                    await self._store_chunks_async(new_chunks)
                    self.logger.info(f"✅ {len(new_chunks)} chunks complementares armazenados")
        
        # Montar contexto híbrido
        context = self._build_optimized_context(existing_chunks, csv_analysis, new_chunks)
        
        # Gerar resposta com LLM
        prompt = f"""Baseado no contexto híbrido abaixo, responda à query.

CONTEXTO:
{context}

QUERY: {query}

Responda de forma clara, integrando informações dos chunks e análise CSV."""
        
        try:
            from src.llm.manager import LLMConfig
            config = LLMConfig(temperature=0.3, max_tokens=2048)
            llm_response = self.llm_manager.chat(prompt, config=config)
            answer = llm_response.content
        except Exception as e:
            self.logger.error(f"❌ Erro LLM: {e}")
            answer = f"Erro: {str(e)}"
        
        return {
            'status': 'success',
            'strategy': 'csv_fallback',
            'answer': answer,
            'context': context,
            'chunks_used': [c.metadata.get('chunk_type', 'unknown') for c in existing_chunks],
            'new_chunks_generated': len(new_chunks),
            'covered_aspects': list(covered_aspects),
            'gaps_filled': list(gaps),
            'csv_accessed': True,
            'csv_analysis': csv_analysis
        }
    
    # ========================================================================
    # PROCESSAMENTO: CSV COM FRAGMENTAÇÃO (GROQ 6000 TPM)
    # ========================================================================
    
    async def _process_with_csv_fragmented(self, query: str, source_id: str,
                                           existing_chunks: List, analysis: Dict,
                                           session_id: str) -> Dict[str, Any]:
        """
        Processa com CSV usando FRAGMENTAÇÃO para respeitar limite GROQ.
        
        INTEGRAÇÃO:
        - Usa FastQueryFragmenter para dividir em queries menores
        - Cada fragmento <= 6000 tokens
        - Processa sequencialmente e agrega resultados
        - Usa chunks existentes como guia para evitar redundância
        """
        self.logger.info("🚀 ESTRATÉGIA: CSV COM FRAGMENTAÇÃO (GROQ 6000 TPM)")
        
        # Carregar CSV
        df = await self._load_csv_async(source_id)
        if df is None:
            self.logger.error("❌ CSV não disponível, fallback para RAG")
            return await self._process_with_rag_only(query, source_id, existing_chunks, analysis)
        
        self.logger.info(f"📊 CSV carregado: {df.shape[0]} linhas x {df.shape[1]} colunas")
        
        # FRAGMENTAÇÃO DA QUERY
        self.logger.info("🔪 Fragmentando query...")
        needs_frag, fragments, reason = fragment_query_fast(
            query=query,
            df=df,
            token_budget=self.token_budget
        )
        
        self.logger.info(f"📦 Fragmentação: {len(fragments) if fragments else 0} fragmentos | Razão: {reason}")
        
        # Processar fragmentos
        if fragments:
            fragment_results = await self._execute_fragments(df, fragments, query)
            
            # Agregar resultados
            aggregated = execute_and_aggregate(df, fragments, operation='select')
            
            self.logger.info(f"✅ {aggregated.get('fragments_success', 0)}/{aggregated.get('fragments_total', 0)} fragmentos processados")
        else:
            # Query não precisa fragmentar
            fragment_results = {'message': 'Query não requer fragmentação'}
            aggregated = {'success': True, 'result': df.head(100).to_dict()}
        
        # Identificar gaps cobertos
        covered_aspects = self._identify_covered_aspects(existing_chunks, query)
        
        # Gerar chunks complementares
        new_chunks = await self._generate_fragments_as_chunks(
            fragments, fragment_results, covered_aspects, source_id
        )
        
        if new_chunks:
            await self._store_chunks_async(new_chunks)
            self.logger.info(f"✅ {len(new_chunks)} chunks fragmentados armazenados")
        
        # Montar contexto final
        context = self._build_fragmented_context(
            existing_chunks, fragment_results, aggregated, covered_aspects
        )
        
        # Gerar resposta final com LLM
        prompt = f"""Baseado nos fragmentos processados e chunks existentes, responda:

CONTEXTO:
{context}

QUERY ORIGINAL: {query}

Responda integrando todas as informações de forma coerente."""
        
        try:
            from src.llm.manager import LLMConfig
            config = LLMConfig(temperature=0.3, max_tokens=2048)
            llm_response = self.llm_manager.chat(prompt, config=config)
            answer = llm_response.content
        except Exception as e:
            self.logger.error(f"❌ Erro LLM: {e}")
            answer = f"Erro: {str(e)}"
        
        return {
            'status': 'success',
            'strategy': 'csv_fragmented',
            'answer': answer,
            'context': context,
            'chunks_used': [c.metadata.get('chunk_type', 'unknown') for c in existing_chunks],
            'fragments_count': len(fragments) if fragments else 0,
            'fragments_success': aggregated.get('fragments_success', 0),
            'new_chunks_generated': len(new_chunks),
            'covered_aspects': list(covered_aspects),
            'csv_accessed': True,
            'fragmentation_reason': reason,
            'aggregated_result': aggregated.get('result')
        }
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    async def _load_csv_async(self, source_id: str) -> Optional[pd.DataFrame]:
        """Carrega CSV com cache (versão async)."""
        return await asyncio.to_thread(self._load_csv_sync, source_id)
    
    def _load_csv_sync(self, source_id: str) -> Optional[pd.DataFrame]:
        """Carrega CSV do disco com cache."""
        if source_id in self._dataframe_cache:
            self.logger.debug(f"📦 CSV do cache: {source_id}")
            return self._dataframe_cache[source_id]
        
        # Buscar arquivo
        base_filename = source_id.split('_')[0]
        csv_path = self.csv_base_path / f"{base_filename}.csv"
        
        if not csv_path.exists():
            possible_paths = list(self.csv_base_path.glob(f"{base_filename}*.csv"))
            if possible_paths:
                csv_path = possible_paths[0]
            else:
                self.logger.error(f"❌ CSV não encontrado: {csv_path}")
                return None
        
        try:
            self.logger.info(f"📂 Carregando CSV: {csv_path}")
            df = pd.read_csv(csv_path)
            self._dataframe_cache[source_id] = df
            self.logger.info(f"✅ CSV carregado: {df.shape}")
            return df
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar CSV: {e}")
            return None
    
    async def _perform_focused_analysis(self, df: pd.DataFrame, query: str, 
                                       gaps: set) -> Dict[str, Any]:
        """Executa análise CSV FOCADA apenas nos gaps."""
        analysis = {'focused_on': list(gaps), 'shape': df.shape}
        
        for gap in gaps:
            if gap == 'statistics':
                analysis['statistics'] = df.describe().to_dict()
            elif gap == 'correlation':
                numeric = df.select_dtypes(include='number')
                analysis['correlation'] = numeric.corr().to_dict()
            elif gap == 'outliers':
                analysis['outliers'] = self._detect_outliers(df)
            elif gap == 'distribution':
                analysis['distribution'] = {
                    col: df[col].value_counts().head(10).to_dict()
                    for col in df.select_dtypes(include='number').columns[:5]
                }
        
        return analysis
    
    def _detect_outliers(self, df: pd.DataFrame) -> Dict:
        """Detecção rápida de outliers (IQR)."""
        outliers = {}
        for col in df.select_dtypes(include='number').columns[:10]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            mask = (df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)
            outliers[col] = {'count': int(mask.sum()), 'percentage': float(mask.sum()/len(df)*100)}
        return outliers
    
    async def _generate_complementary_chunks(self, query: str, csv_analysis: Dict,
                                            covered: set, source_id: str) -> List[TextChunk]:
        """Gera chunks COMPLEMENTARES (não duplicados)."""
        new_chunks = []
        
        for gap in csv_analysis.get('focused_on', []):
            if gap in covered:
                continue  # Pular se já coberto
            
            content = f"Análise complementar: {gap}\n\n{csv_analysis.get(gap, {})}"
            
            new_chunks.append(TextChunk(
                content=content,
                metadata=ChunkMetadata(
                    source=source_id,
                    chunk_index=len(new_chunks),
                    strategy=ChunkStrategy.SEMANTIC,
                    char_count=len(content),
                    word_count=len(content.split()),
                    start_position=0,
                    end_position=len(content),
                    additional_info={
                        'chunk_type': f'complementary_{gap}',
                        'source_id': source_id,
                        'generated_for_query': query
                    }
                )
            ))
        
        return new_chunks
    
    async def _execute_fragments(self, df: pd.DataFrame, fragments: List, 
                                query: str) -> Dict[str, Any]:
        """Executa fragmentos sequencialmente."""
        results = []
        
        for frag in fragments:
            try:
                # Slice DataFrame
                if frag.row_range:
                    start, end = frag.row_range
                    df_slice = df.iloc[start:end]
                else:
                    df_slice = df
                
                if frag.columns:
                    df_slice = df_slice[frag.columns]
                
                # Executar análise básica
                result = {
                    'fragment_id': frag.fragment_id,
                    'shape': df_slice.shape,
                    'statistics': df_slice.describe().to_dict()
                }
                results.append(result)
            
            except Exception as e:
                self.logger.error(f"❌ Erro ao processar fragmento {frag.fragment_id}: {e}")
        
        return {'fragments': results, 'total': len(results)}
    
    async def _generate_fragments_as_chunks(self, fragments: List, results: Dict,
                                           covered: set, source_id: str) -> List[TextChunk]:
        """Converte resultados de fragmentos em chunks para armazenamento."""
        chunks = []
        
        for i, frag_result in enumerate(results.get('fragments', [])):
            content = f"Fragmento {i}: {frag_result}"
            
            chunks.append(TextChunk(
                content=content,
                metadata=ChunkMetadata(
                    source=source_id,
                    chunk_index=i,
                    strategy=ChunkStrategy.SEMANTIC,
                    char_count=len(content),
                    word_count=len(content.split()),
                    start_position=0,
                    end_position=len(content),
                    additional_info={
                        'chunk_type': 'fragment_result',
                        'source_id': source_id,
                        'fragment_index': i
                    }
                )
            ))
        
        return chunks
    
    async def _store_chunks_async(self, chunks: List[TextChunk]) -> None:
        """Armazena chunks no Supabase (async)."""
        try:
            embeddings = self.embedding_generator.generate_embeddings_batch(chunks)
            stored_ids = self.vector_store.store_embeddings(embeddings, source_type="csv")
            self.logger.info(f"✅ {len(stored_ids)} chunks armazenados")
        except Exception as e:
            self.logger.error(f"❌ Erro ao armazenar chunks: {e}")
    
    def _build_context_from_chunks(self, chunks: List) -> str:
        """Monta contexto a partir de chunks."""
        parts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_type = chunk.metadata.get('chunk_type', 'unknown') if hasattr(chunk, 'metadata') else 'unknown'
            content = chunk.metadata.get('chunk_text', '') if hasattr(chunk, 'metadata') else str(chunk)
            parts.append(f"[CHUNK {i} - {chunk_type}]\n{content}\n")
        return "\n".join(parts)
    
    def _build_optimized_context(self, chunks: List, csv_analysis: Optional[Dict],
                                 new_chunks: List[TextChunk]) -> str:
        """Monta contexto híbrido otimizado."""
        parts = ["=== CHUNKS EXISTENTES ===\n"]
        parts.append(self._build_context_from_chunks(chunks))
        
        if csv_analysis:
            parts.append("\n=== ANÁLISE CSV FOCADA ===\n")
            parts.append(str(csv_analysis))
        
        if new_chunks:
            parts.append("\n=== CHUNKS COMPLEMENTARES ===\n")
            for chunk in new_chunks:
                parts.append(f"{chunk.content}\n")
        
        return "\n".join(parts)
    
    def _build_fragmented_context(self, chunks: List, fragment_results: Dict,
                                  aggregated: Dict, covered: set) -> str:
        """Monta contexto com resultados fragmentados."""
        parts = ["=== CHUNKS EXISTENTES ===\n"]
        parts.append(self._build_context_from_chunks(chunks))
        
        parts.append("\n=== RESULTADOS DOS FRAGMENTOS ===\n")
        parts.append(f"Total fragmentos: {fragment_results.get('total', 0)}\n")
        parts.append(str(fragment_results))
        
        parts.append("\n=== RESULTADO AGREGADO ===\n")
        parts.append(str(aggregated.get('result', {})))
        
        return "\n".join(parts)
