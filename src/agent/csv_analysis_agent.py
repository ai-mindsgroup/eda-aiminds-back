"""
⚠️  ⚠️  ⚠️  DEPRECATION WARNING  ⚠️  ⚠️  ⚠️

ESTE ARQUIVO ESTÁ OBSOLETO E SERÁ REMOVIDO EM VERSÕES FUTURAS.

Use src/agent/rag_data_agent.py ao invés deste arquivo.

MOTIVO DA DEPRECAÇÃO:
- rag_data_agent.py implementa busca vetorial PURA sem keywords hardcoded
- csv_analysis_agent.py viola princípios RAG com detecção por palavras-chave
- Sistema deve ser 100% genérico e agnóstico ao dataset

IMPACTO:
- Este arquivo ainda funciona mas NÃO deve ser usado em novos desenvolvimentos
- Testes que usam EmbeddingsAnalysisAgent devem migrar para RAGDataAgent
- A remoção definitiva está planejada para próxima versão major

DATA DE DEPRECAÇÃO: 05/10/2025
⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️  ⚠️
"""
from __future__ import annotations

"""Agente especializado em análise de dados via tabela embeddings.

Este agente combina:
- Consulta exclusiva à tabela embeddings do Supabase
- Análise inteligente de dados estruturados armazenados como embeddings
- LLM para interpretação e insights baseados em embeddings
- Geração de análises sem acesso direto a arquivos CSV

NOTA CRÍTICA: Este agente NÃO acessa arquivos CSV diretamente.
Todos os dados vêm da tabela embeddings do Supabase.
"""
import json
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

try:
    from src.vectorstore.supabase_client import supabase
    SUPABASE_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    SUPABASE_AVAILABLE = False
    supabase = None
    print(f"⚠️ Supabase não disponível: {str(e)[:100]}...")

from src.agent.base_agent import BaseAgent, AgentError
# query_classifier removido - arquivo obsoleto deletado
# ⚠️ NOTA: Este arquivo está DEPRECATED e contém código quebrado (referências a QueryType)
# Mantido apenas para compatibilidade temporária. Use RAGDataAgent ao invés.


class EmbeddingsAnalysisAgent(BaseAgent):
    """Agente para análise inteligente de dados via embeddings.
    
    CONFORMIDADE: Este agente acessa APENAS a tabela embeddings do Supabase.
    Jamais lê arquivos CSV diretamente para responder consultas.
    """
    
    def __init__(self):
        super().__init__(
            name="embeddings_analyzer",
            description="Especialista em análise de dados via tabela embeddings do Supabase",
            enable_memory=True  # Habilita sistema de memória
        )
        self.current_embeddings: List[Dict[str, Any]] = []
        self.dataset_metadata: Dict[str, Any] = {}
        
        # Cache de análises em memória local (otimização)
        self._analysis_cache: Dict[str, Any] = {}
        self._patterns_cache: Dict[str, Any] = {}
        
        # REMOVED: RAGQueryClassifier não existe no codebase (corrigido em 2025-01-06)
        # self.query_classifier = RAGQueryClassifier()
        self.query_classifier = None  # Fallback seguro para permitir inicialização
        
        if not SUPABASE_AVAILABLE:
            raise AgentError(self.name, "Supabase não disponível - necessário para acesso a embeddings")
        
        self.logger.info("Agente de análise via embeddings inicializado com sistema de memória")
    
    def _validate_embeddings_access_only(self) -> None:
        """Valida que o agente só acessa embeddings, nunca CSV diretamente."""
        if hasattr(self, 'current_df') or hasattr(self, 'current_file_path'):
            raise AgentError(
                self.name, 
                "VIOLAÇÃO CRÍTICA: Tentativa de acesso direto a CSV detectada"
            )
    
    def _classify_query_by_keywords(self, query: str):
        """Classificação básica via keywords (fallback quando RAGQueryClassifier indisponível).
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            QueryType correspondente
        """
        from src.agent.orchestrator_agent import QueryType
        
        query_lower = query.lower()
        
        # Mapeamento de keywords para tipos
        keywords_map = {
            QueryType.VISUALIZATION: ['gráfico', 'grafico', 'histograma', 'distribuição', 'plot', 'visualizar', 'mostrar'],
            QueryType.CORRELATION: ['correlação', 'correlacao', 'relação', 'relacao', 'associação', 'associacao'],
            QueryType.VARIABILITY: ['variabilidade', 'variação', 'variacao', 'desvio', 'dispersão', 'dispersao'],
            QueryType.CENTRAL_TENDENCY: ['média', 'media', 'mediana', 'moda', 'central'],
            QueryType.DISTRIBUTION: ['distribuição', 'distribuicao', 'frequência', 'frequencia'],
            QueryType.OUTLIERS: ['outlier', 'discrepante', 'anômalo', 'anomalo', 'fora da curva'],
            QueryType.INTERVAL: ['intervalo', 'faixa', 'range', 'mínimo', 'minimo', 'máximo', 'maximo'],
            QueryType.COUNT: ['quantos', 'quantas', 'quantidade', 'contar', 'número', 'numero'],
            QueryType.SUMMARY: ['resumo', 'visão geral', 'visao geral', 'overview', 'sumário', 'sumario'],
        }
        
        # Procurar palavras-chave
        for qtype, keywords in keywords_map.items():
            if any(kw in query_lower for kw in keywords):
                return qtype
        
        # Fallback para ANALYSIS se não encontrar match específico
        return QueryType.ANALYSIS
    
    def load_from_embeddings(self, 
                           dataset_filter: Optional[str] = None,
                           limit: int = 1000) -> Dict[str, Any]:
        """Carrega dados da tabela embeddings do Supabase para análise.
        
        Args:
            dataset_filter: Filtro opcional por dataset específico
            limit: Limite de embeddings para carregar
        
        Returns:
            Informações sobre os dados carregados dos embeddings
        """
        self._validate_embeddings_access_only()
        
        try:
            self.logger.info(f"Carregando dados da tabela embeddings (limite: {limit})")
            
            # Consultar tabela embeddings
            query = supabase.table('embeddings').select('chunk_text, metadata, created_at')
            
            if dataset_filter:
                query = query.eq('metadata->>source', dataset_filter)
            
            response = query.limit(limit).execute()
            
            if not response.data:
                return self._build_response(
                    "❌ Nenhum embedding encontrado na base de dados",
                    metadata={'embeddings_count': 0}
                )
            
            self.current_embeddings = response.data
            
            # Extrair metadados do dataset
            self.dataset_metadata = self._extract_dataset_metadata()
            
            # Análise inicial dos embeddings
            analysis = self._analyze_embeddings_data()
            
            return self._build_response(
                f"✅ Dados carregados: {len(self.current_embeddings)} embeddings encontrados",
                metadata=analysis
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar embeddings: {str(e)}")
            raise AgentError(self.name, f"Falha ao carregar dados dos embeddings: {str(e)}")
    
    def _extract_dataset_metadata(self) -> Dict[str, Any]:
        """Extrai metadados dos embeddings carregados."""
        if not self.current_embeddings:
            return {}
        
        sources = set()
        providers = set()
        chunk_types = set()
        dates = []
        
        for embedding in self.current_embeddings:
            metadata = embedding.get('metadata', {})
            sources.add(metadata.get('source', 'unknown'))
            providers.add(metadata.get('provider', 'unknown'))
            chunk_types.add(metadata.get('chunk_type', 'unknown'))
            
            if embedding.get('created_at'):
                dates.append(embedding['created_at'])
        
        return {
            'sources': list(sources),
            'providers': list(providers), 
            'chunk_types': list(chunk_types),
            'date_range': {
                'earliest': min(dates) if dates else None,
                'latest': max(dates) if dates else None
            },
            'total_embeddings': len(self.current_embeddings)
        }
    
    def _analyze_embeddings_data(self) -> Dict[str, Any]:
        """Análise dos dados dos embeddings carregados."""
        if not self.current_embeddings:
            return {}
        
        # Analisar conteúdo dos chunks
        chunk_texts = [emb['chunk_text'] for emb in self.current_embeddings]
        
        # Tentar detectar estrutura de dados CSV nos chunks
        detected_columns = set()
        numeric_patterns = []
        
        for chunk_text in chunk_texts[:50]:  # Analisar amostra
            # Buscar padrões de colunas/campos
            if ',' in chunk_text or '|' in chunk_text or '\t' in chunk_text:
                # Possível dados tabulares
                lines = chunk_text.split('\n')
                for line in lines[:3]:  # Primeiras linhas
                    if ',' in line:
                        parts = line.split(',')
                        for part in parts:
                            part = part.strip()
                            if part and len(part) < 50:  # Possível nome de coluna
                                detected_columns.add(part)
        
        return {
            'embeddings_count': len(self.current_embeddings),
            'dataset_metadata': self.dataset_metadata,
            'detected_columns': list(detected_columns)[:20],  # Limite
            'content_analysis': {
                'avg_chunk_length': np.mean([len(text) for text in chunk_texts]),
                'total_content_length': sum(len(text) for text in chunk_texts)
            }
        }
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta sobre dados via embeddings.
        
        Args:
            query: Pergunta ou comando sobre os dados
            context: Contexto adicional (pode incluir dataset_filter)
        
        Returns:
            Resposta com análise baseada em embeddings
        """
        self._validate_embeddings_access_only()
        
        try:
            # Verificar se precisa carregar embeddings
            if not self.current_embeddings:
                dataset_filter = context.get('dataset_filter') if context else None
                load_result = self.load_from_embeddings(dataset_filter=dataset_filter)
                if 'error' in load_result.get('metadata', {}):
                    return load_result
            
            if not self.current_embeddings:
                return self._build_response(
                    "❌ Nenhum embedding carregado. Verifique se há dados na tabela embeddings.",
                    metadata={"error": True, "conformidade": "embeddings_only"}
                )
            
            # ===================================================================
            # CLASSIFICAÇÃO INTELIGENTE VIA RAG (substituiu keywords hardcoded)
            # ===================================================================
            self.logger.info(f"🔍 Classificando query via RAG: {query[:60]}...")
            
            # Guard: query_classifier pode não existir (bug RAGQueryClassifier corrigido em 2025-01-06)
            if self.query_classifier is None:
                # Fallback: classificação básica via keywords
                from src.agent.orchestrator_agent import QueryType
                classification_type = self._classify_query_by_keywords(query)
                class FallbackClassification:
                    def __init__(self, qtype):
                        self.query_type = qtype
                        self.confidence = 0.7
                        self.metadata = {'method': 'keyword_fallback'}
                classification = FallbackClassification(classification_type)
                self.logger.warning("⚠️  query_classifier indisponível, usando fallback por keywords")
            else:
                classification = self.query_classifier.classify_query(query)
            
            self.logger.info(
                f"📊 Query classificada como: {classification.query_type.value} "
                f"(confiança: {classification.confidence:.2f})"
            )
            
            # Adicionar metadados de classificação ao contexto
            if context is None:
                context = {}
            context['classification'] = {
                'type': classification.query_type.value,
                'confidence': classification.confidence,
                'method': classification.metadata.get('method', 'unknown')
            }
            
            # Rotear para o handler apropriado baseado na classificação RAG
            handler_map = {
                QueryType.VARIABILITY: self._handle_variability_query_from_embeddings,
                QueryType.INTERVAL: self._handle_statistics_query_from_embeddings,
                QueryType.CENTRAL_TENDENCY: self._handle_central_tendency_query_from_embeddings,
                QueryType.CORRELATION: self._handle_correlation_query_from_embeddings,
                QueryType.DISTRIBUTION: self._handle_distribution_query_from_embeddings,
                QueryType.OUTLIERS: self._handle_outliers_query_from_embeddings,
                QueryType.VISUALIZATION: self._handle_visualization_query,
                QueryType.SUMMARY: self._handle_summary_query_from_embeddings,
                QueryType.ANALYSIS: self._handle_analysis_query_from_embeddings,
                QueryType.SEARCH: self._handle_search_query_from_embeddings,
                QueryType.COUNT: self._handle_count_query_from_embeddings,
                QueryType.GENERAL: self._handle_general_query_from_embeddings,
            }
            
            handler = handler_map.get(classification.query_type)
            
            if handler is None:
                self.logger.warning(f"Handler não encontrado para tipo: {classification.query_type}")
                handler = self._handle_general_query_from_embeddings
            
            # Executar handler
            response = handler(query, context)
            
            # Aprender com a query processada (melhoria contínua)
            try:
                # Guard: query_classifier pode não existir
                if self.query_classifier is not None:
                    self.query_classifier.learn_from_query(
                        query=query,
                        correct_type=classification.query_type,
                        response=response.get('response', ''),
                        metadata={'confidence': classification.confidence}
                    )
                else:
                    self.logger.debug("query_classifier indisponível, pulando learn_from_query")
            except Exception as learn_error:
                self.logger.warning(f"Falha ao registrar aprendizado: {learn_error}")
            
            return response
                
        except Exception as e:
            self.logger.error(f"Erro ao processar consulta via embeddings: {str(e)}")
            return self._build_response(
                f"Erro ao processar consulta: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )
    
    # ========================================================================
    # MÉTODOS DE PROCESSAMENTO COM MEMÓRIA
    # ========================================================================
    
    async def process_with_memory(self, query: str, context: Optional[Dict[str, Any]] = None,
                                session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa consulta utilizando sistema de memória para cache de análises.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
            session_id: ID da sessão
            
        Returns:
            Resposta processada com cache otimizado
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
            
            # 2. Verificar cache de análises específicas
            analysis_key = self._generate_analysis_cache_key(query, context)
            cached_result = await self.recall_cached_analysis(analysis_key)
            
            if cached_result:
                self.logger.info(f"📦 Análise recuperada do cache: {analysis_key}")
                cached_result['metadata']['from_cache'] = True
                cached_result['metadata']['cache_key'] = analysis_key
                return cached_result
            
            # 3. Recuperar padrões de consulta aprendidos
            learned_patterns = await self.recall_learned_patterns()
            if learned_patterns:
                self.logger.debug(f"🧠 Aplicando {len(learned_patterns)} padrões aprendidos")
                context = context or {}
                context['learned_patterns'] = learned_patterns
            
            # 4. Processar consulta normalmente
            result = self.process(query, context)
            
            # 5. Calcular tempo de processamento
            processing_time_ms = int((time.time() - start_time) * 1000)
            result.setdefault('metadata', {})['processing_time_ms'] = processing_time_ms
            
            # 6. Salvar resultado no cache se significativo
            if self._should_cache_analysis(result, processing_time_ms):
                await self.remember_analysis_result(analysis_key, result, expiry_hours=12)
                self.logger.debug(f"💾 Análise salva no cache: {analysis_key}")
            
            # 7. Aprender padrões da consulta
            await self.learn_query_pattern(query, result)
            
            # 8. Salvar interação na memória
            if self.has_memory and self._current_session_id:
                await self.remember_interaction(
                    query=query,
                    response=result.get('content', str(result)),
                    processing_time_ms=processing_time_ms,
                    metadata=result.get('metadata', {})
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento com memória: {e}")
            # Fallback para processamento sem memória
            return self.process(query, context)
    
    # ========================================================================
    # MÉTODOS DE MEMÓRIA ESPECÍFICOS
    # ========================================================================
    
    def _generate_analysis_cache_key(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Gera chave única para cache de análise."""
        import hashlib
        
        # Normaliza query para cache
        normalized_query = query.lower().strip()
        
        # Adiciona contexto relevante
        context_str = ""
        if context:
            relevant_context = {
                'dataset_filter': context.get('dataset_filter'),
                'limit': context.get('limit'),
                'embeddings_count': len(self.current_embeddings)
            }
            context_str = str(sorted(relevant_context.items()))
        
        # Gera hash
        cache_input = f"{normalized_query}_{context_str}"
        return f"analysis_{hashlib.md5(cache_input.encode()).hexdigest()[:12]}"
    
    def _should_cache_analysis(self, result: Dict[str, Any], processing_time_ms: int) -> bool:
        """Determina se uma análise deve ser cacheada."""
        # Cachear se:
        # 1. Processamento demorado (> 500ms)
        # 2. Resultado significativo (tem metadados de análise)
        # 3. Não é erro
        
        if result.get('metadata', {}).get('error', False):
            return False
        
        if processing_time_ms > 500:
            return True
        
        metadata = result.get('metadata', {})
        has_analysis = any(key in metadata for key in [
            'embeddings_count', 'detected_columns', 'content_analysis'
        ])
        
        return has_analysis
    
    async def learn_query_pattern(self, query: str, result: Dict[str, Any]) -> None:
        """Aprende padrões de consulta para otimização futura."""
        if not self.has_memory or not self._current_session_id:
            return
        
        try:
            # Extrai características da consulta
            query_features = {
                'length': len(query),
                'words': len(query.split()),
                'type': self._classify_query_type(query),
                'embeddings_used': len(self.current_embeddings),
                'success': not result.get('metadata', {}).get('error', False)
            }
            
            # Salva padrão de aprendizado
            pattern_data = {
                'query_sample': query[:100],  # Trunca para privacidade
                'features': query_features,
                'result_type': result.get('metadata', {}).get('query_type', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            pattern_key = f"pattern_{self._classify_query_type(query)}"
            context_key = f"learning_patterns_{pattern_key}"
            
            # Salva na memória de contexto
            await self.remember_data_context(pattern_data, context_key)
            
            self.logger.debug(f"Padrão de consulta aprendido: {pattern_key}")
            
        except Exception as e:
            self.logger.debug(f"Erro ao aprender padrão: {e}")
    
    async def recall_learned_patterns(self) -> List[Dict[str, Any]]:
        """Recupera padrões de consulta aprendidos."""
        if not self.has_memory or not self._current_session_id:
            return []
        
        try:
            # Recupera contexto de aprendizado
            context = await self.recall_conversation_context(hours=168)  # 1 semana
            
            patterns = []
            for key, data in context.get('data_context', {}).items():
                if key.startswith('learning_patterns_'):
                    patterns.append(data)
            
            return patterns
            
        except Exception as e:
            self.logger.debug(f"Erro ao recuperar padrões: {e}")
            return []
    
    def _classify_query_type(self, query: str) -> str:
        """Classifica tipo de consulta para aprendizado."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['resumo', 'describe', 'info']):
            return 'summary'
        elif any(word in query_lower for word in ['análise', 'analyze', 'estatística']):
            return 'analysis'
        elif any(word in query_lower for word in ['busca', 'search', 'procura']):
            return 'search'
        elif any(word in query_lower for word in ['contagem', 'count', 'quantos']):
            return 'count'
        else:
            return 'general'
    
    def _handle_summary_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de resumo usando dados dos embeddings."""
        analysis = self._analyze_embeddings_data()
        
        summary = f"""📊 **Resumo dos Dados (via Embeddings)**
        
**Fonte:** Tabela embeddings do Supabase
**Total de Embeddings:** {analysis['embeddings_count']:,}
**Datasets Identificados:** {', '.join(self.dataset_metadata.get('sources', ['N/A']))}
**Tipos de Chunk:** {', '.join(self.dataset_metadata.get('chunk_types', ['N/A']))}

**Colunas Detectadas nos Dados:**
{', '.join(analysis.get('detected_columns', ['Nenhuma detectada']))}

**Análise de Conteúdo:**
• Tamanho médio dos chunks: {analysis['content_analysis']['avg_chunk_length']:.1f} caracteres
• Conteúdo total analisado: {analysis['content_analysis']['total_content_length']:,} caracteres

⚠️ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings
        """
        
        return self._build_response(summary, metadata={
            **analysis,
            'conformidade': 'embeddings_only',
            'query_type': 'summary'
        })
    
    def _handle_analysis_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de análise usando embeddings.
        
        ⚠️ DEPRECATION: Este método está obsoleto. Use RAGDataAgent ao invés.
        """
        if not self.current_embeddings:
            return self._build_response("❌ Nenhum embedding disponível para análise")
        
        # Análise genérica baseada no conteúdo dos chunks (SEM detecção de fraude)
        chunk_texts = [emb['chunk_text'] for emb in self.current_embeddings]
        
        # Estatísticas genéricas sobre chunks
        total_chunks = len(chunk_texts)
        avg_length = sum(len(text) for text in chunk_texts) / total_chunks if total_chunks > 0 else 0
        
        response = f"""🔍 **Análise de Dados (via Embeddings)**
        
**Estatísticas Gerais:**
• Total de chunks analisados: {total_chunks}
• Tamanho médio dos chunks: {avg_length:.0f} caracteres

⚠️ **AVISO:** Para análises detalhadas, use RAGDataAgent com busca vetorial.
        """
        
        return self._build_response(response, metadata={
            'total_chunks': total_chunks,
            'avg_chunk_length': avg_length,
            'conformidade': 'embeddings_only',
            'deprecation_warning': 'Use RAGDataAgent instead'
        })
    
    def _handle_search_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de busca nos embeddings."""
        search_term = query.lower()
        
        # Buscar termo nos chunks
        matches = []
        for i, embedding in enumerate(self.current_embeddings):
            chunk_text = embedding['chunk_text'].lower()
            if any(term in chunk_text for term in search_term.split()):
                matches.append({
                    'index': i,
                    'chunk_preview': embedding['chunk_text'][:200] + '...',
                    'metadata': embedding.get('metadata', {})
                })
        
        if matches:
            response = f"🔍 **Resultados da Busca (via Embeddings)**\n\n"
            response += f"Encontrados {len(matches)} chunks relevantes:\n\n"
            
            for i, match in enumerate(matches[:5]):  # Limite de 5 resultados
                response += f"**Resultado {i+1}:**\n{match['chunk_preview']}\n\n"
        else:
            response = f"❌ Nenhum resultado encontrado para: '{query}'"
        
        return self._build_response(response, metadata={
            'matches_count': len(matches),
            'query': query,
            'conformidade': 'embeddings_only'
        })
    
    def _handle_count_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de contagem usando embeddings."""
        analysis = self._analyze_embeddings_data()
        
        response = f"""📊 **Contagens dos Dados (via Embeddings)**
        
• Total de embeddings: {analysis['embeddings_count']:,}
• Datasets identificados: {len(self.dataset_metadata.get('sources', []))}
• Tipos de chunk: {len(self.dataset_metadata.get('chunk_types', []))}
• Colunas detectadas: {len(analysis.get('detected_columns', []))}
        """
        
        return self._build_response(response, metadata={
            **analysis,
            'conformidade': 'embeddings_only'
        })
    
    def _handle_statistics_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas sobre estatísticas (min, max, intervalos) usando dados reais dos embeddings.
        
        Args:
            query: Pergunta do usuário sobre estatísticas
            context: Contexto adicional
            
        Returns:
            Resposta com estatísticas calculadas a partir dos dados reais
        """
        try:
            self.logger.info("📊 Calculando estatísticas reais dos dados via embeddings...")
            
            # Importar Python Analyzer para processar chunk_text
            try:
                from src.tools.python_analyzer import PythonDataAnalyzer
                analyzer = PythonDataAnalyzer()
            except ImportError as e:
                self.logger.error(f"Erro ao importar PythonDataAnalyzer: {e}")
                return self._build_response(
                    "❌ Erro: PythonDataAnalyzer não disponível para calcular estatísticas",
                    metadata={"error": True}
                )
            
            # Obter DataFrame real dos chunks
            df = analyzer.get_data_from_embeddings(limit=None, parse_chunk_text=True)
            
            if df is None or df.empty:
                return self._build_response(
                    "❌ Não foi possível obter dados dos embeddings para calcular estatísticas",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ DataFrame carregado: {len(df)} registros, {len(df.columns)} colunas")
            
            # Calcular intervalos (min/max) para TODAS as colunas numéricas
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                return self._build_response(
                    "❌ Nenhuma coluna numérica encontrada nos dados",
                    metadata={"error": True}
                )
            
            # Calcular estatísticas de intervalo
            stats_data = []
            for col in numeric_cols:
                col_min = df[col].min()
                col_max = df[col].max()
                col_range = col_max - col_min
                stats_data.append({
                    'variavel': col,
                    'minimo': col_min,
                    'maximo': col_max,
                    'amplitude': col_range
                })
            
            # Formatar resposta
            response = f"""📊 **Intervalo de Cada Variável (Mínimo e Máximo)**

**Fonte:** Dados reais extraídos da tabela embeddings (coluna chunk_text parseada)
**Total de registros analisados:** {len(df):,}
**Total de variáveis numéricas:** {len(numeric_cols)}

"""
            
            # Adicionar tabela formatada
            response += "| Variável | Mínimo | Máximo | Amplitude |\n"
            response += "|----------|--------|--------|----------|\n"
            
            # Mostrar TODAS as variáveis (removida limitação de 15)
            for stat in stats_data:
                var_name = stat['variavel']
                var_min = stat['minimo']
                var_max = stat['maximo']
                var_range = stat['amplitude']
                
                # Formatar valores com precisão adequada
                if abs(var_min) < 1000 and abs(var_max) < 1000:
                    response += f"| {var_name} | {var_min:.6f} | {var_max:.6f} | {var_range:.6f} |\n"
                else:
                    response += f"| {var_name} | {var_min:.2f} | {var_max:.2f} | {var_range:.2f} |\n"
            
            response += f"\n✅ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings\n"
            response += f"✅ **Método:** Parsing de chunk_text + análise com pandas\n"
            
            return self._build_response(response, metadata={
                'total_records': len(df),
                'total_numeric_columns': len(numeric_cols),
                'statistics': stats_data,
                'conformidade': 'embeddings_only',
                'query_type': 'statistics'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular estatísticas: {str(e)}")
            return self._build_response(
                f"❌ Erro ao calcular estatísticas dos dados: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )
    
    def _handle_variability_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas sobre VARIABILIDADE/DISPERSÃO (desvio padrão, variância) usando dados REAIS dos embeddings.
        
        Este método é GENÉRICO e funciona com qualquer CSV carregado nos embeddings.
        
        Args:
            query: Pergunta do usuário sobre variabilidade (ex: "Qual a variabilidade dos dados?")
            context: Contexto adicional
            
        Returns:
            Resposta com desvio padrão, variância e coeficiente de variação calculados
        """
        try:
            self.logger.info("📊 Calculando VARIABILIDADE (desvio padrão, variância) dos dados via embeddings...")
            
            # Importar Python Analyzer para processar chunk_text
            try:
                from src.tools.python_analyzer import PythonDataAnalyzer
                analyzer = PythonDataAnalyzer()
            except ImportError as e:
                self.logger.error(f"Erro ao importar PythonDataAnalyzer: {e}")
                return self._build_response(
                    "❌ Erro: PythonDataAnalyzer não disponível para calcular variabilidade",
                    metadata={"error": True}
                )
            
            # Obter DataFrame real dos chunks (GENÉRICO - qualquer CSV)
            df = analyzer.get_data_from_embeddings(limit=None, parse_chunk_text=True)
            
            if df is None or df.empty:
                return self._build_response(
                    "❌ Não foi possível obter dados dos embeddings para calcular variabilidade",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ DataFrame carregado: {len(df)} registros, {len(df.columns)} colunas")
            
            # Calcular VARIABILIDADE para TODAS as colunas numéricas (GENÉRICO)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                return self._build_response(
                    "❌ Nenhuma coluna numérica encontrada nos dados",
                    metadata={"error": True}
                )
            
            # Calcular medidas de DISPERSÃO
            variability_data = []
            for col in numeric_cols:
                col_std = df[col].std()  # Desvio padrão
                col_var = df[col].var()  # Variância
                col_mean = df[col].mean()
                col_cv = (col_std / col_mean) * 100 if col_mean != 0 else 0  # Coeficiente de Variação
                
                variability_data.append({
                    'variavel': col,
                    'desvio_padrao': col_std,
                    'variancia': col_var,
                    'coeficiente_variacao': col_cv
                })
            
            # Formatar resposta
            response = f"""📊 **Variabilidade dos Dados (Desvio Padrão e Variância)**

**Fonte:** Dados reais extraídos da tabela embeddings (coluna chunk_text parseada)
**Total de registros analisados:** {len(df):,}
**Total de variáveis numéricas:** {len(numeric_cols)}

"""
            
            # Adicionar tabela formatada
            response += "| Variável | Desvio Padrão | Variância | Coef. Variação (%) |\n"
            response += "|----------|---------------|-----------|--------------------| \n"
            
            # Mostrar TODAS as variáveis
            for stat in variability_data:
                var_name = stat['variavel']
                var_std = stat['desvio_padrao']
                var_var = stat['variancia']
                var_cv = stat['coeficiente_variacao']
                
                # Formatar valores com precisão adequada
                response += f"| {var_name} | {var_std:.6f} | {var_var:.6f} | {var_cv:.2f} |\n"
            
            response += f"\n✅ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings\n"
            response += f"✅ **Método:** Parsing de chunk_text + cálculo std() e var() com pandas\n"
            response += f"\n**Interpretação:**\n"
            response += f"- **Desvio Padrão:** Mede a dispersão dos dados em relação à média\n"
            response += f"- **Variância:** Quadrado do desvio padrão (mesma medida, escala diferente)\n"
            response += f"- **Coef. Variação:** Percentual de dispersão relativa (útil para comparar variáveis)\n"
            
            return self._build_response(response, metadata={
                'total_records': len(df),
                'total_numeric_columns': len(numeric_cols),
                'variability_data': variability_data,
                'conformidade': 'embeddings_only',
                'query_type': 'variability'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular variabilidade: {str(e)}")
            return self._build_response(
                f"❌ Erro ao calcular variabilidade dos dados: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )
    
    def _handle_central_tendency_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas sobre medidas de tendência central (média, mediana, moda) usando dados REAIS dos embeddings.
        
        Args:
            query: Pergunta do usuário sobre medidas de tendência central
            context: Contexto adicional
            
        Returns:
            Resposta com medidas de tendência central calculadas a partir dos dados reais
        """
        try:
            self.logger.info("📊 Calculando medidas de tendência central dos dados via embeddings...")
            
            # Importar Python Analyzer para processar chunk_text
            try:
                from src.tools.python_analyzer import PythonDataAnalyzer
                analyzer = PythonDataAnalyzer(caller_agent=self.name)
            except ImportError as e:
                self.logger.error(f"Erro ao importar PythonDataAnalyzer: {e}")
                return self._build_response(
                    "❌ Erro: PythonDataAnalyzer não disponível para calcular medidas de tendência central",
                    metadata={"error": True}
                )
            
            # Obter DataFrame real dos chunks (APENAS EMBEDDINGS - NUNCA CSV)
            df = analyzer.get_data_from_embeddings(limit=None, parse_chunk_text=True)
            
            if df is None or df.empty:
                return self._build_response(
                    "❌ Não foi possível obter dados dos embeddings para calcular medidas de tendência central",
                    metadata={"error": True}
                )
            
            self.logger.info(f"✅ DataFrame carregado: {len(df)} registros, {len(df.columns)} colunas")
            
            # Calcular medidas de tendência central para TODAS as colunas numéricas
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                return self._build_response(
                    "❌ Nenhuma coluna numérica encontrada nos dados",
                    metadata={"error": True}
                )
            
            # Calcular média, mediana e moda
            stats_data = []
            for col in numeric_cols:
                col_mean = df[col].mean()
                col_median = df[col].median()
                
                # Moda (pode ter múltiplas modas)
                mode_values = df[col].mode()
                col_mode = mode_values.iloc[0] if len(mode_values) > 0 else None
                
                stats_data.append({
                    'variavel': col,
                    'media': col_mean,
                    'mediana': col_median,
                    'moda': col_mode
                })
            
            # Formatar resposta
            response = f"""📊 **Medidas de Tendência Central**

**Fonte:** Dados reais extraídos da tabela embeddings (coluna chunk_text parseada)
**Total de registros analisados:** {len(df):,}
**Total de variáveis numéricas:** {len(numeric_cols)}

**O que são Medidas de Tendência Central?**

As medidas de tendência central são estatísticas que descrevem o valor central de uma distribuição de dados:

• **Média**: Soma de todos os valores dividida pelo número de valores. Sensível a outliers.
• **Mediana**: Valor do meio quando os dados estão ordenados. Mais robusta a outliers.
• **Moda**: Valor que aparece com maior frequência nos dados.

"""
            
            # Adicionar tabela formatada
            response += "| Variável | Média | Mediana | Moda |\n"
            response += "|----------|-------|---------|------|\n"
            
            # Mostrar TODAS as variáveis (removida limitação de 15)
            for stat in stats_data:
                var_name = stat['variavel']
                var_mean = stat['media']
                var_median = stat['mediana']
                var_mode = stat['moda']
                
                # Formatar valores com precisão adequada
                if abs(var_mean) < 1000 and abs(var_median) < 1000:
                    mode_str = f"{var_mode:.6f}" if var_mode is not None else "N/A"
                    response += f"| {var_name} | {var_mean:.6f} | {var_median:.6f} | {mode_str} |\n"
                else:
                    mode_str = f"{var_mode:.2f}" if var_mode is not None else "N/A"
                    response += f"| {var_name} | {var_mean:.2f} | {var_median:.2f} | {mode_str} |\n"
            
            response += f"\n**Diferença entre Média e Mediana:**\n"
            response += f"• A média é sensível a valores extremos (outliers), enquanto a mediana não.\n"
            response += f"• Se houver outliers nos dados, a mediana é uma medida mais representativa do centro.\n"
            response += f"• Para distribuições simétricas, média e mediana têm valores próximos.\n"
            
            response += f"\n✅ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings\n"
            response += f"✅ **Método:** Parsing de chunk_text + análise com pandas\n"
            
            return self._build_response(response, metadata={
                'total_records': len(df),
                'total_numeric_columns': len(numeric_cols),
                'central_tendency': stats_data,
                'conformidade': 'embeddings_only',
                'query_type': 'central_tendency'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular medidas de tendência central: {str(e)}")
            return self._build_response(
                f"❌ Erro ao calcular medidas de tendência central dos dados: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )
    
    def _handle_correlation_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas sobre correlação entre variáveis usando dados dos embeddings.
        
        Args:
            query: Pergunta sobre correlação
            context: Contexto adicional
            
        Returns:
            Resposta com matriz de correlação
        """
        try:
            self.logger.info("📊 Calculando correlações entre variáveis...")
            
            from src.tools.python_analyzer import PythonDataAnalyzer
            analyzer = PythonDataAnalyzer()
            
            # Parsing dos chunks para DataFrame
            # Primeiro, tentar reconstruir dados via Supabase embeddings (método público recomendado)
            df = analyzer.reconstruct_original_data()

            # Se não conseguiu (ex: ambiente de testes sem Supabase), tentar parsear current_embeddings diretamente
            if df is None:
                full_text = "\n".join([emb.get('chunk_text', '') for emb in self.current_embeddings])
                import pandas as pd
                embeddings_df = pd.DataFrame([{'chunk_text': full_text}])
                df = analyzer._parse_chunk_text_to_dataframe(embeddings_df=embeddings_df)

            if df is None or df.empty:
                return self._build_response(
                    "❌ Não foi possível extrair dados dos embeddings",
                    metadata={"error": True}
                )
            
            # Selecionar apenas colunas numéricas
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) < 2:
                return self._build_response(
                    "❌ É necessário pelo menos 2 variáveis numéricas para calcular correlação",
                    metadata={"error": True}
                )
            
            # Calcular matriz de correlação
            corr_matrix = df[numeric_cols].corr()
            
            response = f"## 🔗 Matriz de Correlação\n\n"
            response += f"**Total de variáveis analisadas:** {len(numeric_cols)}\n\n"
            
            # Formatar matriz
            response += "| Variáveis |"
            for col in numeric_cols[:10]:  # Limitar para não ficar muito grande
                response += f" {col} |"
            response += "\n|"
            response += "---|" * (len(numeric_cols[:10]) + 1)
            response += "\n"
            
            for idx in numeric_cols[:10]:
                response += f"| {idx} |"
                for col in numeric_cols[:10]:
                    corr_val = corr_matrix.loc[idx, col]
                    response += f" {corr_val:.3f} |"
                response += "\n"
            
            response += f"\n✅ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings\n"
            
            return self._build_response(response, metadata={
                'total_variables': len(numeric_cols),
                'correlation_matrix': corr_matrix.to_dict(),
                'conformidade': 'embeddings_only',
                'query_type': 'correlation'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular correlação: {str(e)}")
            return self._build_response(
                f"❌ Erro ao calcular correlação: {str(e)}",
                metadata={"error": True}
            )
    
    def _handle_distribution_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas sobre distribuição de dados usando embeddings.
        
        Args:
            query: Pergunta sobre distribuição
            context: Contexto adicional
            
        Returns:
            Resposta com análise de distribuição
        """
        try:
            self.logger.info("📊 Analisando distribuição dos dados...")
            
            from src.tools.python_analyzer import PythonDataAnalyzer
            from scipy import stats
            analyzer = PythonDataAnalyzer()
            
            # Tentar reconstruir via método público
            df = analyzer.reconstruct_original_data()

            # Se não conseguiu (ambiente de testes), tentar parsear current_embeddings diretamente
            if df is None:
                full_text = "\n".join([emb.get('chunk_text', '') for emb in self.current_embeddings])
                import pandas as pd
                embeddings_df = pd.DataFrame([{'chunk_text': full_text}])
                df = analyzer._parse_chunk_text_to_dataframe(embeddings_df=embeddings_df)

            if df is None or df.empty:
                return self._build_response(
                    "❌ Não foi possível extrair dados dos embeddings",
                    metadata={"error": True}
                )
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            # Construir sumário estatístico (texto)
            response = f"## 📊 Análise de Distribuição\n\n"
            response += f"**Total de variáveis numéricas:** {len(numeric_cols)}\n\n"

            stats_summary = {}
            for col in numeric_cols[:10]:  # Limitar
                try:
                    if len(df[col].dropna()) > 3:
                        stat, pvalue = stats.shapiro(df[col].dropna()[:5000])  # Max 5000 amostras
                        is_normal = "Sim" if pvalue > 0.05 else "Não"
                        skewness = df[col].skew()
                        kurtosis_val = df[col].kurtosis()

                        response += f"### {col}\n"
                        response += f"- **Normal?** {is_normal} (p-value: {pvalue:.4f})\n"
                        response += f"- **Assimetria (skewness):** {skewness:.3f}\n"
                        response += f"- **Curtose (kurtosis):** {kurtosis_val:.3f}\n\n"

                        stats_summary[col] = {
                            'normal': is_normal,
                            'pvalue': float(pvalue),
                            'skewness': float(skewness),
                            'kurtosis': float(kurtosis_val)
                        }
                except Exception as e:
                    self.logger.warning(f"Falha ao calcular estatísticas para {col}: {e}")

            response += f"\n✅ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings\n"

            # Delegar geração de gráficos para o handler de visualização para garantir que os PNGs sejam criados
            try:
                vis_result = self._handle_visualization_query(query, context)
                # Mesclar metadados e resposta textual
                metadata = vis_result.get('metadata', {}) if isinstance(vis_result, dict) else {}
                # Garantir campos estatísticos incluso
                metadata.setdefault('distribution_stats', stats_summary)

                # Se a visualização gerou gráficos, anexar ao texto
                if metadata.get('visualization_success'):
                    response += f"\n📈 Gráficos gerados: {len(metadata.get('graficos_gerados', []))}\n"

                return self._build_response(response, metadata={
                    'total_variables': len(numeric_cols),
                    'conformidade': 'embeddings_only',
                    'query_type': 'distribution',
                    **metadata
                })
            except Exception as e:
                self.logger.warning(f"Falha ao gerar visualizações a partir de distribuição: {e}")
                return self._build_response(response, metadata={
                    'total_variables': len(numeric_cols),
                    'conformidade': 'embeddings_only',
                    'query_type': 'distribution',
                    'visualization_error': str(e)
                })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao analisar distribuição: {str(e)}")
            return self._build_response(
                f"❌ Erro ao analisar distribuição: {str(e)}",
                metadata={"error": True}
            )
    
    def _handle_outliers_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas sobre outliers usando dados dos embeddings.
        
        Args:
            query: Pergunta sobre outliers
            context: Contexto adicional
            
        Returns:
            Resposta com detecção de outliers
        """
        try:
            self.logger.info("📊 Detectando outliers nos dados...")
            
            from src.tools.python_analyzer import PythonDataAnalyzer
            analyzer = PythonDataAnalyzer()
            
            full_text = "\n".join([emb.get('chunk_text', '') for emb in self.current_embeddings])
            df = analyzer.parse_chunk_text(full_text)
            
            if df.empty:
                return self._build_response(
                    "❌ Não foi possível extrair dados dos embeddings",
                    metadata={"error": True}
                )
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            response = f"## 🔍 Detecção de Outliers (Método IQR)\n\n"
            response += f"**Método:** Interquartile Range (IQR)\n"
            response += f"**Critério:** Valores abaixo de Q1 - 1.5*IQR ou acima de Q3 + 1.5*IQR\n\n"
            
            response += "| Variável | Outliers Inferiores | Outliers Superiores | Total Outliers | % do Total |\n"
            response += "|----------|---------------------|---------------------|----------------|------------|\n"
            
            total_records = len(df)
            
            for col in numeric_cols[:15]:  # Limitar
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                lower_outliers = (df[col] < lower_bound).sum()
                upper_outliers = (df[col] > upper_bound).sum()
                total_outliers = lower_outliers + upper_outliers
                pct_outliers = (total_outliers / total_records) * 100
                
                response += f"| {col} | {lower_outliers} | {upper_outliers} | {total_outliers} | {pct_outliers:.2f}% |\n"
            
            response += f"\n✅ **Conformidade:** Dados obtidos exclusivamente da tabela embeddings\n"
            
            return self._build_response(response, metadata={
                'total_variables': len(numeric_cols),
                'total_records': total_records,
                'conformidade': 'embeddings_only',
                'query_type': 'outliers'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao detectar outliers: {str(e)}")
            return self._build_response(
                f"❌ Erro ao detectar outliers: {str(e)}",
                metadata={"error": True}
            )
    
    def _handle_visualization_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas que solicitam visualizações (histogramas, gráficos, distribuição).
        
        Args:
            query: Pergunta do usuário solicitando visualização
            context: Contexto adicional
            
        Returns:
            Resposta com histogramas gerados e salvos em arquivos
        """
        try:
            self.logger.info("📊 Processando solicitação de visualização...")
            
            # Importar módulos necessários
            from src.tools.python_analyzer import PythonDataAnalyzer
            import matplotlib.pyplot as plt
            import seaborn as sns
            import os
            from pathlib import Path
            
            # Configurar estilo dos gráficos
            sns.set_style("whitegrid")
            
            # Inicializar analyzer
            analyzer = PythonDataAnalyzer(caller_agent=self.name)
            
            # Reconstruir DataFrame a partir dos embeddings
            self.logger.info("🔄 Reconstruindo DataFrame a partir dos embeddings...")
            df = analyzer.reconstruct_original_data()
            
            if df is None or df.empty:
                return self._build_response(
                    "❌ Não foi possível reconstruir os dados para gerar visualizações. Verifique se há dados na tabela embeddings.",
                    metadata={"error": True, "conformidade": "embeddings_only"}
                )
            
            self.logger.info(f"✅ DataFrame reconstruído: {df.shape[0]} linhas, {df.shape[1]} colunas")
            
            # Criar diretório de saída
            output_dir = Path('outputs/histogramas')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Separar variáveis numéricas e categóricas
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            self.logger.info(f"📊 Gerando histogramas para {len(numeric_cols)} variáveis numéricas...")
            self.logger.info(f"📊 Gerando gráficos de barras para {len(categorical_cols)} variáveis categóricas...")
            
            graficos_gerados = []
            estatisticas_geradas = {}
            
            # Gerar histogramas para variáveis numéricas
            for col in numeric_cols:
                try:
                    self.logger.info(f"  Gerando histograma para: {col}")
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Histograma
                    ax.hist(df[col].dropna(), bins=50, alpha=0.7, color='steelblue', edgecolor='black')
                    
                    # Estatísticas
                    mean_val = df[col].mean()
                    median_val = df[col].median()
                    std_val = df[col].std()
                    
                    # Linhas de referência
                    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Média: {mean_val:.2f}')
                    ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Mediana: {median_val:.2f}')
                    
                    ax.set_xlabel(col, fontsize=12)
                    ax.set_ylabel('Frequência', fontsize=12)
                    ax.set_title(f'Distribuição de {col}', fontsize=14, fontweight='bold')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    # Salvar
                    filename = output_dir / f'hist_{col}.png'
                    plt.tight_layout()
                    plt.savefig(filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    
                    graficos_gerados.append(str(filename))
                    estatisticas_geradas[col] = {
                        'mean': float(mean_val),
                        'median': float(median_val),
                        'std': float(std_val),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'count': int(df[col].count()),
                        'missing': int(df[col].isna().sum())
                    }
                    
                    self.logger.info(f"  ✅ Histograma salvo: {filename}")
                    
                except Exception as e:
                    self.logger.error(f"  ❌ Erro ao gerar histograma para {col}: {e}")
            
            # Gerar gráficos de barras para variáveis categóricas (limitado a variáveis com poucos valores únicos)
            for col in categorical_cols:
                try:
                    unique_count = df[col].nunique()
                    if unique_count > 20:  # Limitar a variáveis com até 20 valores únicos
                        self.logger.info(f"  Pulando {col} (muitos valores únicos: {unique_count})")
                        continue
                    
                    self.logger.info(f"  Gerando gráfico de barras para: {col}")
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Contagem de valores
                    value_counts = df[col].value_counts()
                    
                    # Gráfico de barras
                    value_counts.plot(kind='bar', ax=ax, color='coral', edgecolor='black', alpha=0.7)
                    
                    ax.set_xlabel(col, fontsize=12)
                    ax.set_ylabel('Frequência', fontsize=12)
                    ax.set_title(f'Distribuição de {col}', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3, axis='y')
                    
                    # Rotacionar labels se necessário
                    plt.xticks(rotation=45, ha='right')
                    
                    # Salvar
                    filename = output_dir / f'bar_{col}.png'
                    plt.tight_layout()
                    plt.savefig(filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    
                    graficos_gerados.append(str(filename))
                    estatisticas_geradas[col] = {
                        'unique_values': unique_count,
                        'most_common': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                        'most_common_count': int(value_counts.values[0]) if len(value_counts) > 0 else 0,
                        'count': int(df[col].count()),
                        'missing': int(df[col].isna().sum())
                    }
                    
                    self.logger.info(f"  ✅ Gráfico de barras salvo: {filename}")
                    
                except Exception as e:
                    self.logger.error(f"  ❌ Erro ao gerar gráfico para {col}: {e}")
            
            # Construir resposta
            if graficos_gerados:
                response = f"""📊 **Visualizações Geradas com Sucesso!**

✅ Total de gráficos gerados: {len(graficos_gerados)}
   • Histogramas (variáveis numéricas): {len([g for g in graficos_gerados if 'hist_' in g])}
   • Gráficos de barras (variáveis categóricas): {len([g for g in graficos_gerados if 'bar_' in g])}

📁 **Local dos arquivos:**
   {output_dir.absolute()}

📈 **Gráficos salvos:**
"""
                for i, grafico in enumerate(graficos_gerados, 1):
                    response += f"   {i}. {Path(grafico).name}\n"
                
                response += f"\n💡 **Dica:** Você pode visualizar os gráficos abrindo os arquivos PNG no diretório indicado."
                
                return self._build_response(response, metadata={
                    'graficos_gerados': graficos_gerados,
                    'estatisticas': estatisticas_geradas,
                    'output_dir': str(output_dir.absolute()),
                    'numeric_cols': numeric_cols,
                    'categorical_cols': categorical_cols,
                    'conformidade': 'embeddings_only',
                    'visualization_success': True
                })
            else:
                return self._build_response(
                    "❌ Não foi possível gerar visualizações. Verifique os logs para mais detalhes.",
                    metadata={'error': True, 'conformidade': 'embeddings_only'}
                )
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar visualização: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._build_response(
                f"❌ Erro ao gerar visualizações: {str(e)}",
                metadata={'error': True, 'conformidade': 'embeddings_only', 'exception': str(e)}
            )
    
    def _handle_general_query_from_embeddings(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas gerais usando embeddings."""
        if not self.current_embeddings:
            return self._build_response("❌ Nenhum embedding disponível")
        
        analysis = self._analyze_embeddings_data()
        
        response = f"""💡 **Informações Disponíveis (via Embeddings)**
        
Dados carregados: {analysis['embeddings_count']} embeddings
Datasets: {', '.join(self.dataset_metadata.get('sources', ['N/A']))}

**Para análises específicas, tente:**
• "resumo" - visão geral dos dados
• "análise" - análise de padrões
• "busca [termo]" - buscar conteúdo específico
• "contagem" - estatísticas básicas
        """
        
        return self._build_response(response, metadata={
            **analysis,
            'conformidade': 'embeddings_only',
            'suggestions': ['resumo', 'análise', 'busca', 'contagem']
        })
    
    def get_embeddings_info(self) -> Dict[str, Any]:
        """Retorna informações dos embeddings carregados.
        
        CONFORMIDADE: Apenas dados da tabela embeddings.
        """
        self._validate_embeddings_access_only()
        
        if not self.current_embeddings:
            return {"error": "Nenhum embedding carregado", "conformidade": "embeddings_only"}
        
        return {
            **self._analyze_embeddings_data(),
            'conformidade': 'embeddings_only',
            'agente': self.name
        }
    
    def validate_architecture_compliance(self) -> Dict[str, Any]:
        """Valida conformidade com arquitetura de embeddings-only.
        
        Returns:
            Relatório de conformidade
        """
        compliance_report = {
            'compliant': True,
            'violations': [],
            'data_source': 'embeddings_table_only',
            'csv_access': False,
            'agent_name': self.name,
            'compliance_score': 1.0  # Score inicial perfeito
        }
        
        # Verificar se há vestígios de acesso a CSV
        forbidden_attributes = ['current_df', 'current_file_path', 'pandas_agent']
        for attr in forbidden_attributes:
            if hasattr(self, attr):
                compliance_report['compliant'] = False
                compliance_report['violations'].append(f"Atributo proibido encontrado: {attr}")
                compliance_report['compliance_score'] -= 0.3  # Penalizar por violação
        
        # Verificar se usa apenas Supabase
        if not SUPABASE_AVAILABLE:
            compliance_report['compliant'] = False
            compliance_report['violations'].append("Supabase não disponível")
            compliance_report['compliance_score'] -= 0.5
        
        # Garantir score mínimo 0
        compliance_report['compliance_score'] = max(0.0, compliance_report['compliance_score'])
        
        return compliance_report
    
    def export_embeddings_analysis(self, output_path: str) -> Dict[str, Any]:
        """Exporta análise dos embeddings para arquivo.
        
        CONFORMIDADE: Exporta apenas dados derivados da tabela embeddings.
        """
        self._validate_embeddings_access_only()
        
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'agent': self.name,
                'conformidade': 'embeddings_only',
                'embeddings_analysis': self._analyze_embeddings_data(),
                'dataset_metadata': self.dataset_metadata,
                'compliance_report': self.validate_architecture_compliance()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            return self._build_response(
                f"✅ Análise de embeddings exportada para: {output_path}",
                metadata={
                    "export_path": output_path,
                    "conformidade": "embeddings_only"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar análise de embeddings: {str(e)}")
            return self._build_response(
                f"Erro na exportação: {str(e)}",
                metadata={"error": True, "conformidade": "embeddings_only"}
            )


# Alias para compatibilidade com código existente
# DEPRECATED: Use EmbeddingsAnalysisAgent diretamente
CSVAnalysisAgent = EmbeddingsAnalysisAgent