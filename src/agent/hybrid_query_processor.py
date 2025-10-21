"""
Hybrid Query Processor - Processador Inteligente de Queries com Fallback

Implementa estratégia híbrida:
1. PRIORIZA chunks analíticos existentes (6 metadata chunks)
2. FALLBACK automático para CSV completo quando necessário
3. GERA chunks adicionais sob demanda
4. ARMAZENA novos insights no Supabase
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path
import io

from src.agent.query_analyzer import QueryAnalyzer, QueryComplexity
from src.embeddings.vector_store import VectorStore
from src.embeddings.generator import EmbeddingGenerator
from src.embeddings.chunker import TextChunk, ChunkMetadata, ChunkStrategy
from src.utils.logging_config import get_logger


class HybridQueryProcessor:
    """
    Processador híbrido inteligente que:
    - Consulta chunks existentes primeiro
    - Fallback para CSV quando necessário
    - Gera e persiste novos chunks analíticos
    """
    
    def __init__(self, 
                 vector_store: VectorStore,
                 embedding_generator: EmbeddingGenerator,
                 csv_base_path: str = "data/processado"):
        """
        Args:
            vector_store: Vector store para busca e armazenamento
            embedding_generator: Gerador de embeddings
            csv_base_path: Caminho base para arquivos CSV
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.csv_base_path = Path(csv_base_path)
        self.query_analyzer = QueryAnalyzer()
        self.logger = get_logger(__name__)
        
        # Cache de DataFrames carregados
        self._dataframe_cache: Dict[str, pd.DataFrame] = {}
    
    def process_query(self, 
                     query: str, 
                     source_id: str,
                     session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa query com estratégia híbrida inteligente.
        
        Args:
            query: Pergunta do usuário
            source_id: ID da fonte de dados (ex: 'creditcard_abc123')
            session_id: ID da sessão (opcional)
        
        Returns:
            Dict com resposta, contexto, metadados e chunks usados
        """
        self.logger.info(f"🔍 Processando query: {query[:100]}...")
        
        # 1. ANÁLISE DA QUERY
        analysis = self._analyze_query(query, source_id)
        
        # 2. ESTRATÉGIA BASEADA EM COMPLEXIDADE
        if analysis['complexity'] == 'simple':
            result = self._process_simple_query(query, source_id, analysis)
        else:
            result = self._process_complex_query(query, source_id, analysis)
        
        # 3. ADICIONAR METADADOS
        result['query_analysis'] = analysis
        result['session_id'] = session_id
        result['timestamp'] = pd.Timestamp.now().isoformat()
        
        return result
    
    def _analyze_query(self, query: str, source_id: str) -> Dict:
        """
        Analisa query e determina estratégia.
        """
        # Buscar chunks disponíveis para este source_id
        available_chunks = self._get_available_chunk_types(source_id)
        
        # Analisar query
        analysis = self.query_analyzer.analyze(query, available_chunks)
        
        self.logger.info(f"📊 Análise: {analysis['complexity'].upper()} | "
                        f"Categoria: {analysis['category']} | "
                        f"Requer CSV: {analysis['requires_csv']}")
        
        return analysis
    
    def _process_simple_query(self, query: str, source_id: str, analysis: Dict) -> Dict:
        """
        Processa query SIMPLE usando apenas chunks existentes.
        """
        self.logger.info("✅ Estratégia SIMPLE: Usando chunks analíticos existentes")
        
        # 1. Gerar embedding da query
        embedding_result = self.embedding_generator.generate_embedding(query)
        query_embedding = embedding_result.embedding  # Extrair lista de floats
        
        # 2. Busca vetorial
        search_results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            similarity_threshold=0.7,
            limit=5
        )
        
        # 3. Filtrar por source_id
        relevant_results = [
            r for r in search_results
            if r.metadata.get('source_id') == source_id
        ]
        
        if not relevant_results:
            self.logger.warning("⚠️ Nenhum chunk encontrado, fallback para CSV")
            return self._process_complex_query(query, source_id, analysis)
        
        # 4. Montar contexto
        context = self._build_context_from_chunks(relevant_results)
        
        return {
            'status': 'success',
            'strategy': 'simple',
            'context': context,
            'chunks_used': [r.metadata.get('chunk_type') for r in relevant_results],
            'chunks_count': len(relevant_results),
            'similarity_scores': [r.similarity_score for r in relevant_results],  # Corrigido de .similarity para .similarity_score
            'requires_llm_response': True,
            'csv_accessed': False
        }
    
    def _process_complex_query(self, query: str, source_id: str, analysis: Dict) -> Dict:
        """
        Processa query COMPLEX com fallback GUIADO por chunks existentes.
        
        REFINAMENTO:
        - Usa chunks existentes como GUIA para evitar duplicação
        - Complementa apenas análises não cobertas
        - Logging detalhado de decisões
        """
        self.logger.info("🔄 Estratégia COMPLEX: Fallback guiado por chunks existentes")
        
        # 1. Gerar embedding da query
        embedding_result = self.embedding_generator.generate_embedding(query)
        query_embedding = embedding_result.embedding  # Extrair lista de floats
        
        # 2. Buscar chunks existentes PRIMEIRO (serão o guia)
        existing_chunks_raw = self.vector_store.search_similar(
            query_embedding=query_embedding,
            similarity_threshold=0.7,
            limit=6  # Buscar todos os 6 chunks analíticos
        )
        
        # 3. Filtrar por source_id
        existing_chunks = [
            r for r in existing_chunks_raw
            if r.metadata.get('source_id') == source_id
        ]
        
        self.logger.info(f"📦 Chunks existentes encontrados: {len(existing_chunks)}")
        
        # 2. Analisar quais aspectos JÁ ESTÃO COBERTOS pelos chunks
        covered_aspects = self._identify_covered_aspects(existing_chunks, query)
        self.logger.info(f"✅ Aspectos já cobertos: {covered_aspects}")
        
        # 3. Identificar gaps que REQUEREM CSV
        required_gaps = self._identify_required_gaps(query, analysis['category'], covered_aspects)
        self.logger.info(f"⚠️ Gaps que requerem CSV: {required_gaps}")
        
        # 4. DECISÃO: Carregar CSV SOMENTE se houver gaps críticos
        csv_analysis = None
        csv_accessed = False
        
        if required_gaps:
            self.logger.info(f"📂 Carregando CSV para preencher gaps: {required_gaps}")
            df = self._load_csv(source_id)
            
            if df is None:
                self.logger.warning("❌ CSV não disponível, usando apenas chunks existentes")
            else:
                csv_accessed = True
                # Análise FOCADA apenas nos gaps identificados
                csv_analysis = self._perform_focused_csv_analysis(
                    df, query, required_gaps, existing_chunks
                )
        else:
            self.logger.info("✅ Todos os aspectos cobertos por chunks existentes, CSV não necessário")
        
        # 5. Gerar chunks complementares (SOMENTE para gaps)
        new_chunks = []
        if csv_analysis and analysis['strategy'].get('generate_new_chunks') == 'complementary_only':
            new_chunks = self._generate_complementary_chunks(
                query=query,
                csv_analysis=csv_analysis,
                covered_aspects=covered_aspects,
                source_id=source_id
            )
            
            if new_chunks:
                self._store_new_chunks(new_chunks)
                self.logger.info(f"✅ {len(new_chunks)} chunks complementares armazenados")
        
        # 6. Montar contexto HÍBRIDO E OTIMIZADO
        context = self._build_optimized_hybrid_context(
            existing_chunks=existing_chunks,
            csv_analysis=csv_analysis,
            new_chunks=new_chunks,
            covered_aspects=covered_aspects
        )
        
        return {
            'status': 'success',
            'strategy': 'complex_guided',
            'context': context,
            'csv_analysis': csv_analysis,
            'chunks_used': [r.metadata.get('chunk_type') for r in existing_chunks],
            'new_chunks_generated': len(new_chunks),
            'requires_llm_response': True,
            'csv_accessed': csv_accessed,
            'covered_aspects': covered_aspects,
            'required_gaps': required_gaps,
            'dataframe_shape': df.shape if csv_accessed and df is not None else None
        }
    
    def _get_available_chunk_types(self, source_id: str) -> List[str]:
        """
        Busca quais chunk_types existem para este source_id.
        """
        try:
            # Gerar embedding dummy para busca ampla
            embedding_result = self.embedding_generator.generate_embedding("dataset metadata")
            dummy_embedding = embedding_result.embedding  # Extrair lista de floats
            
            # Buscar todos os chunks deste source_id
            all_chunks = self.vector_store.search_similar(
                query_embedding=dummy_embedding,
                similarity_threshold=0.0,  # Baixo threshold para pegar todos
                limit=100
            )
            
            # Filtrar por source_id e extrair chunk_types únicos
            chunk_types = set()
            for chunk in all_chunks:
                if chunk.metadata.get('source_id') == source_id:
                    chunk_type = chunk.metadata.get('chunk_type')
                    if chunk_type:
                        chunk_types.add(chunk_type)
            
            return list(chunk_types)
        
        except Exception as e:
            self.logger.warning(f"Erro ao buscar chunk_types: {e}")
            return []
    
    def _load_csv(self, source_id: str) -> Optional[pd.DataFrame]:
        """
        Carrega CSV do disco com cache.
        """
        # Verificar cache
        if source_id in self._dataframe_cache:
            self.logger.debug(f"📦 CSV carregado do cache: {source_id}")
            return self._dataframe_cache[source_id]
        
        # Buscar arquivo
        # source_id geralmente é 'filename_hash', extrair filename
        base_filename = source_id.split('_')[0]
        csv_path = self.csv_base_path / f"{base_filename}.csv"
        
        if not csv_path.exists():
            # Tentar outros padrões
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
            self.logger.info(f"✅ CSV carregado: {df.shape[0]} linhas, {df.shape[1]} colunas")
            return df
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar CSV: {e}")
            return None
    
    def _perform_csv_analysis(self, df: pd.DataFrame, query: str, category: str) -> Dict:
        """
        Executa análise específica no CSV baseada na categoria.
        """
        analysis = {
            'category': category,
            'dataframe_shape': df.shape,
            'columns': df.columns.tolist()
        }
        
        # Análises específicas por categoria
        if category == 'visualization':
            analysis['suggested_plots'] = self._suggest_visualizations(df, query)
        
        elif category == 'outliers':
            analysis['outliers_detailed'] = self._detect_outliers_detailed(df)
        
        elif category == 'correlation':
            analysis['correlation_matrix'] = df.select_dtypes(include='number').corr().to_dict()
        
        elif category == 'statistics':
            analysis['full_statistics'] = df.describe().to_dict()
        
        # Amostra de dados para contexto
        analysis['sample_data'] = df.head(5).to_dict(orient='records')
        
        return analysis
    
    def _suggest_visualizations(self, df: pd.DataFrame, query: str) -> List[Dict]:
        """
        Sugere visualizações baseadas no DataFrame e query.
        """
        suggestions = []
        
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include='object').columns.tolist()
        
        # Histogramas para numéricas
        for col in numeric_cols[:5]:
            suggestions.append({
                'type': 'histogram',
                'column': col,
                'description': f'Histograma da distribuição de {col}'
            })
        
        # Scatter plots para pares de numéricas
        if len(numeric_cols) >= 2:
            suggestions.append({
                'type': 'scatter',
                'columns': [numeric_cols[0], numeric_cols[1]],
                'description': f'Scatter plot: {numeric_cols[0]} vs {numeric_cols[1]}'
            })
        
        # Boxplots para outliers
        for col in numeric_cols[:3]:
            suggestions.append({
                'type': 'boxplot',
                'column': col,
                'description': f'Boxplot para detecção de outliers em {col}'
            })
        
        return suggestions
    
    def _detect_outliers_detailed(self, df: pd.DataFrame) -> Dict:
        """
        Detecção detalhada de outliers usando método IQR.
        """
        outliers_report = {}
        
        numeric_cols = df.select_dtypes(include='number').columns
        
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outliers_count = outliers_mask.sum()
            
            if outliers_count > 0:
                outliers_report[col] = {
                    'count': int(outliers_count),
                    'percentage': float(outliers_count / len(df) * 100),
                    'bounds': {'lower': float(lower_bound), 'upper': float(upper_bound)},
                    'outlier_values': df[outliers_mask][col].head(10).tolist()
                }
        
        return outliers_report
    
    def _generate_additional_chunks(self, df: pd.DataFrame, query: str, 
                                   analysis: Dict, source_id: str) -> List[TextChunk]:
        """
        Gera chunks analíticos adicionais baseados na análise do CSV.
        """
        chunks = []
        
        # Chunk específico para a análise realizada
        chunk_content = f"""ANÁLISE COMPLEMENTAR - {source_id.upper()}

Query original: {query}

Categoria de análise: {analysis.get('category', 'geral')}

RESULTADOS DA ANÁLISE:
"""
        
        # Adicionar resultados específicos
        if 'outliers_detailed' in analysis:
            chunk_content += "\n\nOUTLIERS DETALHADOS:\n"
            for col, outlier_data in analysis['outliers_detailed'].items():
                chunk_content += f"\n{col}:\n"
                chunk_content += f"  • Total: {outlier_data['count']} outliers ({outlier_data['percentage']:.2f}%)\n"
                chunk_content += f"  • Limites: [{outlier_data['bounds']['lower']:.2f}, {outlier_data['bounds']['upper']:.2f}]\n"
        
        if 'suggested_plots' in analysis:
            chunk_content += "\n\nVISUALIZAÇÕES SUGERIDAS:\n"
            for plot in analysis['suggested_plots']:
                chunk_content += f"  • {plot['type']}: {plot['description']}\n"
        
        # Adicionar amostra de dados
        chunk_content += f"\n\nAMOSTRA DE DADOS (primeiras 5 linhas):\n"
        chunk_content += pd.DataFrame(analysis.get('sample_data', [])).to_string()
        
        # Criar chunk
        chunk = TextChunk(
            content=chunk_content,
            metadata=ChunkMetadata(
                source=source_id,
                chunk_index=999,  # Índice especial para chunks dinâmicos
                strategy=ChunkStrategy.CSV_ROW,
                char_count=len(chunk_content),
                word_count=len(chunk_content.split()),
                start_position=0,
                end_position=len(chunk_content),
                additional_info={
                    'chunk_type': f'dynamic_analysis_{analysis.get("category", "custom")}',
                    'topic': f'complementary_analysis',
                    'query_driven': True,
                    'original_query': query
                }
            )
        )
        
        chunks.append(chunk)
        self.logger.info(f"✅ Gerado 1 chunk adicional para análise de {analysis.get('category')}")
        
        return chunks
    
    def _store_new_chunks(self, chunks: List[TextChunk]) -> None:
        """
        Armazena novos chunks no Supabase.
        """
        try:
            # Gerar embeddings
            embeddings = self.embedding_generator.generate_embeddings_batch(chunks)
            
            # Armazenar
            stored_ids = self.vector_store.store_embeddings(embeddings, source_type="csv")
            
            self.logger.info(f"✅ {len(stored_ids)} novos chunks armazenados no Supabase")
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao armazenar novos chunks: {e}")
    
    def _build_context_from_chunks(self, chunks: List) -> str:
        """
        Monta contexto a partir de chunks retornados pela busca vetorial.
        Suporta tanto List[Dict] quanto List[VectorSearchResult]
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Suportar tanto VectorSearchResult quanto Dict
            if hasattr(chunk, 'metadata'):
                # VectorSearchResult
                chunk_type = chunk.metadata.get('chunk_type', 'unknown')
                content = chunk.metadata.get('chunk_text', '') or chunk.metadata.get('content', '')
            else:
                # Dict
                chunk_type = chunk.get('metadata', {}).get('chunk_type', 'unknown')
                content = chunk.get('content', '') or chunk.get('chunk_text', '')
            
            context_parts.append(f"[CHUNK {i} - {chunk_type}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _build_hybrid_context(self, existing_chunks: List[Dict], 
                             csv_analysis: Dict, new_chunks: List[TextChunk]) -> str:
        """
        Monta contexto híbrido combinando chunks existentes + análise CSV + novos chunks.
        """
        context_parts = []
        
        # 1. Chunks existentes
        if existing_chunks:
            context_parts.append("=== CONTEXTO DOS CHUNKS ANALÍTICOS ===\n")
            context_parts.append(self._build_context_from_chunks(existing_chunks))
        
        # 2. Análise do CSV
        context_parts.append("\n=== ANÁLISE DO CSV COMPLETO ===\n")
        context_parts.append(f"Shape: {csv_analysis.get('dataframe_shape')}\n")
        context_parts.append(f"Colunas: {', '.join(csv_analysis.get('columns', []))}\n")
        
        if 'outliers_detailed' in csv_analysis:
            context_parts.append("\nOutliers detectados:\n")
            for col, data in csv_analysis['outliers_detailed'].items():
                context_parts.append(f"  • {col}: {data['count']} outliers ({data['percentage']:.2f}%)\n")
        
        # 3. Novos chunks gerados
        if new_chunks:
            context_parts.append("\n=== ANÁLISE COMPLEMENTAR GERADA ===\n")
            for chunk in new_chunks:
                context_parts.append(chunk.content + "\n")
        
        return "".join(context_parts)
    
    # ========================
    # NOVOS MÉTODOS - ETAPA 2 REFINADA
    # ========================
    
    def _identify_covered_aspects(self, existing_chunks: List, query: str) -> List[str]:
        """
        Identifica quais aspectos analíticos JÁ ESTÃO COBERTOS pelos chunks existentes.
        
        MAPEAMENTO:
        - metadata_types → structure
        - metadata_distribution → distribution, statistics
        - metadata_central_variability → statistics
        - metadata_frequency_outliers → outliers
        - metadata_correlations → correlation
        - metadata_patterns_clusters → patterns
        """
        covered = set()
        
        for chunk in existing_chunks:
            # Suportar VectorSearchResult e Dict
            if hasattr(chunk, 'metadata'):
                chunk_type = chunk.metadata.get('chunk_type', '')
            else:
                chunk_type = chunk.get('metadata', {}).get('chunk_type', '')
            
            # Mapear chunk_type → aspects cobertos
            if 'types' in chunk_type or 'structure' in chunk_type:
                covered.update(['structure', 'schema', 'data_types'])
            
            elif 'distribution' in chunk_type:
                covered.update(['distribution', 'value_distribution', 'statistics_basic'])
            
            elif 'central' in chunk_type or 'variability' in chunk_type:
                covered.update(['statistics', 'central_tendency', 'dispersion'])
            
            elif 'frequency' in chunk_type or 'outliers' in chunk_type:
                covered.update(['outliers', 'anomalies', 'frequency_analysis'])
            
            elif 'correlation' in chunk_type:
                covered.update(['correlation', 'relationships', 'associations'])
            
            elif 'patterns' in chunk_type or 'clusters' in chunk_type:
                covered.update(['patterns', 'trends', 'clusters', 'temporal'])
        
        return list(covered)
    
    def _identify_required_gaps(self, query: str, category: str, covered_aspects: List[str]) -> List[str]:
        """
        Identifica gaps que REQUEREM acesso ao CSV.
        
        LÓGICA:
        - Se a categoria da query está em covered_aspects → sem gaps
        - Se não está → gap crítico que requer CSV
        """
        gaps = []
        
        # Mapear categoria da query → aspectos necessários
        required_aspects = {
            'statistics': ['statistics', 'central_tendency', 'statistics_basic'],
            'distribution': ['distribution', 'value_distribution'],
            'correlation': ['correlation', 'relationships'],
            'outliers': ['outliers', 'anomalies'],
            'patterns': ['patterns', 'trends', 'temporal'],
            'structure': ['structure', 'schema', 'data_types']
        }
        
        # Verificar se algum aspecto necessário está coberto
        needed = required_aspects.get(category, [])
        
        if not any(aspect in covered_aspects for aspect in needed):
            gaps.append(category)
            self.logger.info(f"⚠️ Gap crítico identificado: {category} não está coberto pelos chunks")
        
        # Verificar se query menciona colunas específicas (requer CSV)
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ['coluna', 'column', 'variável', 'feature']):
            # Verificar se é uma análise específica de coluna
            if not any(kw in query_lower for kw in ['quais são', 'lista', 'nomes']):
                gaps.append('column_specific_analysis')
                self.logger.info("⚠️ Gap: Query requer análise específica de coluna")
        
        return gaps
    
    def _perform_focused_csv_analysis(
        self, df: pd.DataFrame, query: str, required_gaps: List[str], existing_chunks: List[Dict]
    ) -> Dict:
        """
        Executa análise CSV FOCADA apenas nos gaps identificados.
        
        NÃO refaz análises já cobertas pelos chunks.
        """
        self.logger.info(f"🎯 Análise focada nos gaps: {required_gaps}")
        
        analysis = {
            'focused_on': required_gaps,
            'shape': df.shape
        }
        
        for gap in required_gaps:
            if gap == 'statistics':
                analysis['statistics_detailed'] = df.describe().to_dict()
            
            elif gap == 'distribution':
                # Análise detalhada de distribuições
                analysis['distributions_detailed'] = {}
                for col in df.select_dtypes(include=['number']).columns[:10]:
                    analysis['distributions_detailed'][col] = {
                        'skewness': float(df[col].skew()),
                        'kurtosis': float(df[col].kurtosis()),
                        'quantiles': df[col].quantile([0.25, 0.5, 0.75]).to_dict()
                    }
            
            elif gap == 'correlation':
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                analysis['correlation_full'] = df[numeric_cols].corr().to_dict()
            
            elif gap == 'outliers':
                # Detecção avançada de outliers
                analysis['outliers_advanced'] = self._detect_outliers_advanced(df)
            
            elif gap == 'patterns':
                # Análise temporal avançada
                analysis['patterns_advanced'] = self._analyze_temporal_patterns(df)
            
            elif gap == 'column_specific_analysis':
                # Extrair nome da coluna da query
                analysis['column_analysis'] = self._analyze_specific_column(df, query)
        
        return analysis
    
    def _detect_outliers_advanced(self, df: pd.DataFrame) -> Dict:
        """Detecção avançada de outliers (IQR + Z-score)."""
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        outliers = {}
        
        for col in numeric_cols[:10]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            iqr_outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
            
            outliers[col] = {
                'iqr_method': {
                    'count': len(iqr_outliers),
                    'percentage': round(len(iqr_outliers) / len(df) * 100, 2)
                },
                'range': {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'lower_fence': float(Q1 - 1.5*IQR),
                    'upper_fence': float(Q3 + 1.5*IQR)
                }
            }
        
        return outliers
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Análise avançada de padrões temporais."""
        time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        
        if not time_cols:
            return {'message': 'Nenhuma coluna temporal encontrada'}
        
        time_col = time_cols[0]
        return {
            'time_column': time_col,
            'unique_periods': int(df[time_col].nunique()),
            'range': f"{df[time_col].min()} to {df[time_col].max()}",
            'distribution': df[time_col].value_counts().head(10).to_dict()
        }
    
    def _analyze_specific_column(self, df: pd.DataFrame, query: str) -> Dict:
        """Análise específica de coluna mencionada na query."""
        # Tentar extrair nome da coluna da query
        query_lower = query.lower()
        
        for col in df.columns:
            if col.lower() in query_lower:
                if df[col].dtype in ['int64', 'float64']:
                    return {
                        'column': col,
                        'type': 'numeric',
                        'statistics': {
                            'mean': float(df[col].mean()),
                            'median': float(df[col].median()),
                            'std': float(df[col].std()),
                            'min': float(df[col].min()),
                            'max': float(df[col].max())
                        }
                    }
                else:
                    return {
                        'column': col,
                        'type': 'categorical',
                        'unique_values': int(df[col].nunique()),
                        'value_counts': df[col].value_counts().head(10).to_dict()
                    }
        
        return {'message': 'Coluna não identificada na query'}
    
    def _generate_complementary_chunks(
        self, query: str, csv_analysis: Dict, covered_aspects: List[str], source_id: str
    ) -> List[TextChunk]:
        """
        Gera chunks COMPLEMENTARES (não duplicados) com base na análise focada.
        """
        self.logger.info(f"🆕 Gerando chunks complementares (evitando duplicação)")
        
        new_chunks = []
        
        for gap in csv_analysis.get('focused_on', []):
            # Verificar se já existe chunk para este gap
            if gap in covered_aspects:
                self.logger.info(f"⏭️ Pulando chunk para '{gap}' (já existe)")
                continue
            
            # Gerar chunk complementar
            chunk_text = f"Análise complementar: {gap}\n\n"
            
            if gap == 'statistics':
                chunk_text += f"Estatísticas detalhadas:\n{csv_analysis.get('statistics_detailed', {})}"
            
            elif gap == 'distribution':
                chunk_text += f"Distribuições detalhadas:\n{csv_analysis.get('distributions_detailed', {})}"
            
            elif gap == 'correlation':
                chunk_text += f"Matriz de correlação completa:\n{csv_analysis.get('correlation_full', {})}"
            
            elif gap == 'outliers':
                chunk_text += f"Outliers detectados (avançado):\n{csv_analysis.get('outliers_advanced', {})}"
            
            elif gap == 'patterns':
                chunk_text += f"Padrões temporais avançados:\n{csv_analysis.get('patterns_advanced', {})}"
            
            # Criar TextChunk com ChunkMetadata correto
            new_chunks.append(
                TextChunk(
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        source=source_id,
                        chunk_index=len(new_chunks),
                        strategy=ChunkStrategy.SEMANTIC,
                        char_count=len(chunk_text),
                        word_count=len(chunk_text.split()),
                        start_position=0,
                        end_position=len(chunk_text),
                        overlap_with_previous=0,
                        additional_info={
                            'chunk_type': f'complementary_{gap}',
                            'source_id': source_id,
                            'generated_for_query': query,
                            'complementary': True
                        }
                    )
                )
            )
        
        self.logger.info(f"✅ {len(new_chunks)} chunks complementares gerados")
        return new_chunks
    
    def _build_optimized_hybrid_context(
        self, existing_chunks: List, csv_analysis: Dict, 
        new_chunks: List[TextChunk], covered_aspects: List[str]
    ) -> str:
        """
        Monta contexto híbrido OTIMIZADO:
        - Prioriza chunks existentes
        - Adiciona análise CSV focada (se houver)
        - Inclui chunks complementares (se houver)
        """
        context_parts = []
        
        # 1. Chunks existentes (SEMPRE PRIMEIRO)
        context_parts.append("=== CONTEXTO DE CHUNKS EXISTENTES ===\n")
        for chunk in existing_chunks:
            # Suportar VectorSearchResult e Dict
            if hasattr(chunk, 'metadata'):
                chunk_type = chunk.metadata.get('chunk_type', 'unknown')
                chunk_text = chunk.metadata.get('chunk_text', '') or chunk.metadata.get('content', '')
            else:
                chunk_type = chunk.get('metadata', {}).get('chunk_type', 'unknown')
                chunk_text = chunk.get('chunk_text', '') or chunk.get('content', '')
            
            context_parts.append(f"[{chunk_type}]\n{chunk_text}\n\n")
        
        # 2. Análise CSV focada (SE HOUVER GAPS)
        if csv_analysis and csv_analysis.get('focused_on'):
            context_parts.append("\n=== ANÁLISE COMPLEMENTAR DO CSV ===\n")
            context_parts.append(f"Aspectos já cobertos: {covered_aspects}\n")
            context_parts.append(f"Gaps preenchidos: {csv_analysis.get('focused_on')}\n\n")
            context_parts.append(str(csv_analysis))
        
        # 3. Chunks complementares (SE GERADOS)
        if new_chunks:
            context_parts.append("\n=== CHUNKS COMPLEMENTARES GERADOS ===\n")
            for chunk in new_chunks:
                context_parts.append(f"{chunk.content}\n\n")
        
        return "\n".join(context_parts)
