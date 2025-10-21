"""
Query Analyzer - Classificador Inteligente de Complexidade de Perguntas via LLM

Analisa perguntas do usuário usando LLMs para determinar a estratégia de resposta:
- SIMPLE: Usa apenas chunks analíticos existentes (6 chunks de metadata)
- COMPLEX: Requer acesso ao CSV completo + geração de chunks adicionais

✨ REFATORADO: Usa análise semântica via LLM ao invés de listas estáticas de keywords
✅ FIXED: Retorna objetos QueryAnalysis em vez de dict para evitar AttributeError
"""

from typing import Dict, Literal, Optional, List
from enum import Enum
from dataclasses import dataclass, field, asdict
import json
from src.utils.logging_config import get_logger
from src.llm.manager import get_llm_manager, LLMConfig

logger = get_logger(__name__)


@dataclass
class QueryStrategy:
    """
    Estratégia de execução para uma query.
    
    ✅ COMPATIBILIDADE: Suporta acesso tanto por atributo quanto por dict.
    """
    action: str
    chunks_to_query: List[str] = field(default_factory=list)
    fallback_to_csv: bool = False
    generate_new_chunks: bool = False
    use_chunks_as_guide: bool = False
    csv_operations: List[str] = field(default_factory=list)
    avoid_duplicate_analysis: bool = False
    requires_row_level_data: bool = False
    
    def __getitem__(self, key: str):
        """Permite acesso estilo dict: strategy['action']"""
        return getattr(self, key)
    
    def __setitem__(self, key: str, value):
        """Permite atribuição estilo dict: strategy['action'] = 'rag'"""
        setattr(self, key, value)
    
    def get(self, key: str, default=None):
        """Emula dict.get(): strategy.get('action', 'default')"""
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict:
        """Converte para dict para compatibilidade legada"""
        return asdict(self)


@dataclass
class QueryAnalysis:
    """
    Resultado da análise de uma query.
    
    ✅ TIPADO: Objeto estruturado em vez de dict solto.
    Evita erros como: 'dict' object has no attribute 'category'
    
    ✅ COMPATIBILIDADE: Suporta acesso tanto por atributo quanto por dict:
       - analysis.category  ← Novo (recomendado)
       - analysis['category']  ← Legado (mantém compatibilidade)
    """
    query: str
    complexity: str  # 'simple' ou 'complex'
    category: str    # 'statistics', 'correlation', etc
    strategy: QueryStrategy
    justification: str
    requires_csv: bool
    llm_confidence: float = 0.8
    fallback_used: bool = False
    
    def __getitem__(self, key: str):
        """Permite acesso estilo dict para compatibilidade: analysis['category']"""
        return getattr(self, key)
    
    def __setitem__(self, key: str, value):
        """Permite atribuição estilo dict para compatibilidade: analysis['category'] = 'stats'"""
        setattr(self, key, value)
    
    def get(self, key: str, default=None):
        """Emula dict.get() para compatibilidade: analysis.get('category', 'unknown')"""
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict:
        """Converte para dict para compatibilidade com código legado"""
        result = asdict(self)
        # Converter estratégia aninhada
        if isinstance(result['strategy'], QueryStrategy):
            result['strategy'] = result['strategy'].to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QueryAnalysis':
        """Cria QueryAnalysis a partir de dict"""
        # Converter estratégia se for dict
        if 'strategy' in data and isinstance(data['strategy'], dict):
            data['strategy'] = QueryStrategy(**data['strategy'])
        return cls(**data)


class QueryComplexity(str, Enum):
    """Níveis de complexidade de consulta"""
    SIMPLE = "simple"      # Responde com chunks existentes
    COMPLEX = "complex"    # Requer CSV completo + análise profunda


class QueryCategory(str, Enum):
    """Categorias de perguntas analíticas"""
    STRUCTURE = "structure"                    # Estrutura, tipos, dimensões
    STATISTICS = "statistics"                  # Estatísticas descritivas
    DISTRIBUTION = "distribution"              # Distribuições, histogramas
    CORRELATION = "correlation"                # Correlações entre variáveis
    OUTLIERS = "outliers"                      # Detecção de outliers
    PATTERNS = "patterns"                      # Padrões temporais/clusters
    VISUALIZATION = "visualization"            # Geração de gráficos
    CUSTOM_ANALYSIS = "custom_analysis"        # Análises customizadas


class QueryAnalyzer:
    """
    Analisador inteligente de queries usando LLMs para classificação semântica.
    
    ✨ REFATORADO:
    - Usa LLMs para detectar complexidade dinamicamente
    - Elimina dependência de listas fixas de palavras-chave
    - Adapta-se a variações linguísticas automaticamente
    - Prioriza uso dos 6 chunks analíticos antes de fallback
    
    100% dinâmico - sem hardcoding de datasets ou keywords.
    """
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.QueryAnalyzer")
        self.llm_manager = get_llm_manager()
        
        # Mapeamento de categorias para chunks disponíveis (metadados)
        self.category_to_chunks = {
            'structure': ['metadata_types'],
            'statistics': ['metadata_distribution', 'metadata_central_variability'],
            'distribution': ['metadata_distribution'],
            'correlation': ['metadata_correlations'],
            'outliers': ['metadata_frequency_outliers'],
            'patterns': ['metadata_patterns_clusters']
        }
        
    def analyze(self, query: str, available_chunks: List[str] = None) -> QueryAnalysis:
        """
        Analisa uma query usando LLM para classificação semântica inteligente.
        
        Args:
            query: Pergunta do usuário
            available_chunks: Lista de chunk_types disponíveis (ex: ['metadata_types', 'metadata_distribution'])
        
        Returns:
            QueryAnalysis: Objeto tipado com análise completa
        """
        
        # 1. Análise semântica via LLM
        llm_analysis = self._analyze_with_llm(query, available_chunks)
        
        # 2. Extrair complexidade e categoria
        complexity = QueryComplexity(llm_analysis.get('complexity', 'simple'))
        category = llm_analysis.get('category', 'unknown')
        
        # 3. Determinar estratégia (retorna QueryStrategy)
        strategy = self._determine_strategy(complexity, category, available_chunks, llm_analysis)
        
        # 4. Gerar justificativa
        justification = llm_analysis.get('reasoning', 'Análise automática via LLM')
        
        # ✅ RETORNAR OBJETO, NÃO DICT
        result = QueryAnalysis(
            query=query,
            complexity=complexity.value,
            category=category,
            strategy=strategy,
            justification=justification,
            requires_csv=(complexity == QueryComplexity.COMPLEX),
            llm_confidence=llm_analysis.get('confidence', 0.8),
            fallback_used=llm_analysis.get('fallback_used', False)
        )
        
        self.logger.info(f"📊 Query analisada: {result.complexity.upper()} | Categoria: {result.category}")
        self.logger.debug(f"Estratégia: {result.strategy.action} | Confiança: {result.llm_confidence:.2f}")
        
        return result
    
    def _analyze_with_llm(self, query: str, available_chunks: List[str] = None) -> Dict:
        """
        Usa LLM para análise semântica da query.
        
        Retorna classificação inteligente de complexidade e categoria.
        """
        
        chunks_description = self._describe_available_chunks(available_chunks)
        
        prompt = f"""Você é um especialista em análise de dados.

Analise a pergunta do usuário e classifique com base NO TIPO DE RESPOSTA ESPERADA.

PERGUNTA: "{query}"

CHUNKS DISPONÍVEIS: {chunks_description}

REGRAS:

🔹 SIMPLE = Resposta é UM VALOR/CONCEITO/ESTATÍSTICA AGREGADA
Exemplos:
- "Qual a média de X?" → Resposta: "88.35"
- "Quantas colunas?" → Resposta: "31 colunas"
- "Há correlação?" → Resposta: "Sim, 0.45"
- "Distribuição de X" → Resposta: "Mín:0, Max:100, Média:50, Q1:25, Q3:75"
- "Histograma de X" → Resposta: Descrição estatística da distribuição
- "Mostre distribuição estatística" → Resposta: Estatísticas agregadas (não linhas individuais)

🔹 COMPLEX = Resposta é LISTAGEM DE REGISTROS INDIVIDUAIS
Exemplos:
- "Quais transações com X>Y?" → Resposta: TABELA com linhas específicas
- "Mostre top 10 valores" → Resposta: LISTA de 10 registros individuais
- "Liste todas as fraudes" → Resposta: Linhas específicas do dataset

⚠️ ATENÇÃO: Foque no OUTPUT esperado, NÃO no cálculo
- "Quais linhas com Amount>1000?" → COMPLEX (output = lista de linhas)
- "Qual % de linhas com Amount>1000?" → SIMPLE (output = número estatístico)

CATEGORIAS:
structure, statistics, distribution, correlation, outliers, patterns, visualization, custom_analysis, unknown

JSON (sem markdown):
{{
    "complexity": "simple" ou "complex",
    "category": "categoria",
    "reasoning": "1 frase focada NO TIPO DE OUTPUT",
    "confidence": 0.0-1.0,
    "requires_row_level_data": booleano
}}

JSON:"""

        try:
            config = LLMConfig(temperature=0.1, max_tokens=300)  # Baixa temperatura para classificação
            response = self.llm_manager.chat(prompt=prompt, config=config)
            
            if not response.success:
                self.logger.warning(f"LLM falhou, usando fallback heurístico: {response.error}")
                return self._fallback_heuristic_analysis(query, available_chunks)
            
            # Parse JSON da resposta
            content = response.content.strip()
            
            # Remover possíveis markers de código
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            analysis = json.loads(content)
            
            # Validar campos obrigatórios
            if 'complexity' not in analysis or 'category' not in analysis:
                raise ValueError("Campos obrigatórios ausentes na resposta LLM")
            
            self.logger.debug(f"✅ Análise LLM: {analysis['complexity']} | {analysis['category']}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise LLM: {e}")
            return self._fallback_heuristic_analysis(query, available_chunks)
    
    
    def _describe_available_chunks(self, available_chunks: List[str] = None) -> str:
        """
        Gera descrição legível dos chunks disponíveis para o LLM.
        """
        
        chunk_descriptions = {
            'metadata_types': 'Tipos de dados das colunas (numérico, categórico, temporal)',
            'metadata_distribution': 'Distribuições estatísticas (min, max, média, mediana, quartis)',
            'metadata_central_variability': 'Medidas de tendência central e variabilidade (média, desvio padrão, variância)',
            'metadata_frequency_outliers': 'Detecção de outliers e valores atípicos',
            'metadata_correlations': 'Correlações entre variáveis numéricas',
            'metadata_patterns_clusters': 'Padrões temporais e agrupamentos naturais'
        }
        
        if not available_chunks:
            return "Nenhum chunk disponível ainda."
        
        descriptions = []
        for chunk in available_chunks:
            desc = chunk_descriptions.get(chunk, chunk)
            descriptions.append(f"- {chunk}: {desc}")
        
        return "\n".join(descriptions)
    
    def _fallback_heuristic_analysis(self, query: str, available_chunks: List[str] = None) -> Dict:
        """
        Fallback heurístico caso LLM falhe.
        
        Usa regras básicas para classificação quando LLM não está disponível.
        """
        
        query_lower = query.lower()
        
        # Whitelist de termos estatísticos simples (prioridade máxima)
        simple_stats = ['média', 'mediana', 'correlação', 'desvio', 'variância', 'quartis', 'mínimo', 'máximo', 'distribuição', 'histograma']
        has_simple_stat = any(stat in query_lower for stat in simple_stats)
        
        # Heurística: palavras que REALMENTE indicam necessidade de dados linha a linha
        # Removido 'mostre' porque aparece em queries simples como "mostre a distribuição"
        complex_indicators = [
            'quais', 'liste', 'filtr', 'específic', 'exat', 'precis',
            'detalh', 'linha', 'registro', 'transaç', 'acima de', 'abaixo de', 'maior que', 'menor que',
            'todos os', 'todas as'
        ]
        
        # Critério primário: se tem termo estatístico simples em query curta/média, é SIMPLE
        if has_simple_stat and len(query_lower.split()) <= 15:
            is_complex = False
        else:
            # Verificar indicadores complexos apenas se não for query estatística simples
            is_complex = any(indicator in query_lower for indicator in complex_indicators)
        
        # Tentar inferir categoria por palavras-chave básicas
        category = 'unknown'
        if any(word in query_lower for word in ['tipo', 'coluna', 'estrutura', 'dimensão']):
            category = 'structure'
        elif any(word in query_lower for word in ['média', 'mediana', 'estatística', 'mínimo', 'máximo']):
            category = 'statistics'
        elif any(word in query_lower for word in ['distribuição', 'intervalo']):
            category = 'distribution'
        elif any(word in query_lower for word in ['correlação', 'relacionamento']):
            category = 'correlation'
        elif any(word in query_lower for word in ['outlier', 'anomalia', 'atípico']):
            category = 'outliers'
        elif any(word in query_lower for word in ['padrão', 'tendência', 'cluster']):
            category = 'patterns'
        elif any(word in query_lower for word in ['gráfico', 'plot', 'visualização']):
            category = 'visualization'
        
        complexity_value = 'complex' if is_complex else 'simple'
        
        return {
            'complexity': complexity_value,
            'category': category,
            'reasoning': 'Classificação heurística (LLM indisponível)',
            'confidence': 0.6,
            'requires_row_level_data': is_complex,
            'fallback_used': True
        }
    
    def _determine_strategy(self, complexity: QueryComplexity, 
                           category: str,
                           available_chunks: List[str] = None,
                           llm_analysis: Dict = None) -> QueryStrategy:
        """
        Determina estratégia de resposta baseada em complexidade e chunks disponíveis.
        
        REFINAMENTO: Fallback usa chunks existentes como GUIA, não duplica análises.
        
        Returns:
            QueryStrategy: Objeto tipado com estratégia de execução
        """
        
        if complexity == QueryComplexity.SIMPLE:
            # Verificar se temos chunks relevantes
            relevant_chunks = self._get_relevant_chunks(category, available_chunks)
            
            return QueryStrategy(
                action='use_existing_chunks',
                chunks_to_query=relevant_chunks,
                fallback_to_csv=False,
                generate_new_chunks=False,
                use_chunks_as_guide=False  # Não precisa, já responde direto
            )
        
        else:  # COMPLEX
            # Chunks existentes servem como GUIA para fallback
            requires_row_data = llm_analysis.get('requires_row_level_data', True) if llm_analysis else True
            
            return QueryStrategy(
                action='guided_csv_analysis',  # Fallback guiado
                chunks_to_query=available_chunks or [],  # Chunks como referência
                fallback_to_csv=True,
                generate_new_chunks='complementary_only',  # Apenas complementos
                use_chunks_as_guide=True,  # Usa chunks como guia
                csv_operations=self._suggest_csv_operations(category),
                avoid_duplicate_analysis=True,  # Não duplica análises existentes
                requires_row_level_data=requires_row_data
            )
    
    def _get_relevant_chunks(self, category: str, 
                            available_chunks: List[str] = None) -> List[str]:
        """
        Mapeia categoria para chunk_types relevantes.
        """
        
        if not category or not available_chunks:
            return available_chunks or []
        
        # Buscar chunks relevantes para a categoria
        relevant = self.category_to_chunks.get(category, [])
        
        # Filtrar apenas chunks que realmente existem
        return [chunk for chunk in relevant if chunk in available_chunks]
    
    def _suggest_csv_operations(self, category: str) -> List[str]:
        """
        Sugere operações necessárias no CSV completo baseado na categoria.
        """
        
        operations_map = {
            'visualization': ['load_full_dataframe', 'generate_plot', 'save_visualization'],
            'custom_analysis': ['load_full_dataframe', 'apply_custom_logic', 'generate_insights'],
            'outliers': ['load_full_dataframe', 'detect_outliers_detailed', 'generate_outlier_report'],
            'correlation': ['load_full_dataframe', 'compute_correlations', 'generate_heatmap'],
            'patterns': ['load_full_dataframe', 'analyze_temporal_patterns', 'detect_clusters']
        }
        
        return operations_map.get(category, ['load_full_dataframe', 'perform_analysis'])


def analyze_query(query: str, available_chunks: List[str] = None) -> QueryAnalysis:
    """
    Função helper para análise rápida de query.
    
    Args:
        query: Pergunta do usuário
        available_chunks: Lista de chunk_types disponíveis
    
    Returns:
        QueryAnalysis: Objeto tipado com análise completa
    """
    analyzer = QueryAnalyzer()
    return analyzer.analyze(query, available_chunks)
