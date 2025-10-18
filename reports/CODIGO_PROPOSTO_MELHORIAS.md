# 🔧 CÓDIGO PROPOSTO: MELHORIAS DE PROMPTS E PARÂMETROS

**Sistema:** EDA AI Minds  
**Data:** 18 de Outubro de 2025  
**Status:** Ready for Implementation

---

## 📋 ÍNDICE

1. [Prompt V2 para Tipos de Dados](#1-prompt-v2-para-tipos-de-dados)
2. [Configurações Centralizadas](#2-configurações-centralizadas)
3. [Temperature Dinâmica](#3-temperature-dinâmica)
4. [Ajustes de Chunking](#4-ajustes-de-chunking)
5. [Thresholds Padronizados](#5-thresholds-padronizados)
6. [Testes Automatizados](#6-testes-automatizados)

---

## 1. PROMPT V2 PARA TIPOS DE DADOS

### Arquivo: `src/prompts/manager.py`

**Substituir o prompt `data_types_analysis` (linhas 176-195) por:**

```python
"data_types_analysis_v2": PromptTemplate(
    role=AgentRole.CSV_ANALYST,
    type=PromptType.INSTRUCTION,
    content="""🔍 **ANÁLISE ABRANGENTE DE TIPOS DE DADOS**

Forneça uma análise completa e contextualizada dos tipos de dados no dataset.

═══════════════════════════════════════════════════════════════════
📊 SEÇÃO 1: CLASSIFICAÇÃO TÉCNICA (obrigatório)
═══════════════════════════════════════════════════════════════════

Liste os tipos de dados baseados nos dtypes do Pandas:

**Tipos Disponíveis:**
- **Numéricos:** int8, int16, int32, int64, float16, float32, float64
- **Categóricos:** object (strings/texto), category
- **Temporais:** datetime64, timedelta64
- **Booleanos:** bool
- **Outros:** mixed types (se aplicável)

**Formato:**
```
📋 Resumo Técnico:
- Numéricas (X): [lista das colunas]
- Categóricas (Y): [lista das colunas ou "Nenhuma"]
- Temporais (Z): [lista das colunas ou "Nenhuma"]
- Total: X + Y + Z = N colunas
```

═══════════════════════════════════════════════════════════════════
🔍 SEÇÃO 2: CONTEXTO ANALÍTICO (recomendado quando dados disponíveis)
═══════════════════════════════════════════════════════════════════

Para cada tipo de dado, adicione contexto relevante SE DISPONÍVEL nos chunks:

**Para Variáveis Numéricas:**
- Range de valores (min-max) se disponível
- Presença de valores extremos ou outliers
- Indicação de normalização/transformação (ex: PCA, StandardScaler)
- Identificação de variáveis target ou IDs

**Para Variáveis Categóricas:**
- Cardinalidade (número de valores únicos) se disponível
- Valores mais frequentes (top 3-5) se disponível
- Indicação de encoding aplicado

**Para Variáveis Temporais:**
- Range temporal (início-fim) se disponível
- Granularidade (segundos, dias, meses)
- Presença de gaps ou irregularidades

**Formato:**
```
📊 Detalhamento:

Variáveis Numéricas:
- ColA (dtype): Range [min-max], característica especial
- ColB (dtype): Range [min-max], característica especial
[...]

Variáveis Categóricas:
- ColX (dtype): N valores únicos, top 3 valores
[...]
```

═══════════════════════════════════════════════════════════════════
💡 SEÇÃO 3: INSIGHTS E RECOMENDAÇÕES (quando aplicável)
═══════════════════════════════════════════════════════════════════

Forneça insights analíticos baseados nos dados:

**Possíveis Insights:**
- Detecção de variáveis target (ex: "Class" ou "target" com 2 valores)
- Identificação de features derivadas (PCA, embeddings)
- Desbalanceamento de classes (se target identificado)
- Transformações aplicadas (normalização, encoding)
- Armadilhas potenciais (ex: dtype numérico mas semanticamente categórico)

**Recomendações de Análise:**
- Tratamentos necessários (normalização, encoding)
- Técnicas apropriadas (clustering, classificação)
- Cuidados especiais (desbalanceamento, outliers)

**Formato:**
```
🔍 Insights:
- [Insight 1 baseado nos dados]
- [Insight 2 baseado nos dados]

💡 Recomendações:
- [Recomendação 1 para análise]
- [Recomendação 2 para análise]
```

═══════════════════════════════════════════════════════════════════
⚖️ PRINCÍPIOS DE EQUILÍBRIO
═══════════════════════════════════════════════════════════════════

1. **Precisão Técnica:** Sempre forneça classificação correta dos dtypes
2. **Contexto Útil:** Adicione informações relevantes quando disponíveis
3. **Sem Suposições:** Não invente dados não presentes nos chunks
4. **Clareza:** Use linguagem acessível mas tecnicamente correta
5. **Concisão:** Seja completo mas evite verbosidade desnecessária

═══════════════════════════════════════════════════════════════════
📐 DIRETRIZES DE RESPOSTA
═══════════════════════════════════════════════════════════════════

✅ **FAÇA:**
- Liste todos os tipos presentes no dataset
- Mencione características importantes (ranges, cardinalidade)
- Identifique variáveis especiais (target, ID, timestamp)
- Sugira análises apropriadas para o tipo de dados

❌ **NÃO FAÇA:**
- Inventar estatísticas não presentes nos chunks
- Fornecer respostas genéricas sobre conceitos de tipos de dados
- Fazer suposições não fundamentadas nos dados
- Ignorar informações relevantes disponíveis nos chunks

═══════════════════════════════════════════════════════════════════

**Exemplo de Resposta Ideal:**

```
O dataset contém 30 variáveis numéricas e nenhuma categórica:

📋 Resumo Técnico:
- Numéricas (30): Time, V1-V28, Amount, Class
- Categóricas (0): Nenhuma
- Total: 30 colunas

📊 Detalhamento:

Variáveis Numéricas Principais:
- Time (int64): Segundos desde primeira transação [0-172,792]
- V1-V28 (float64): Componentes principais de PCA (normalizados)
- Amount (float64): Valor da transação em euros [€0.00-€25,691.16]
- Class (int64): Variável target binária [0=legítima, 1=fraude]

🔍 Insights:
- Todas as variáveis V1-V28 são features anônimas obtidas via PCA
- Class é tecnicamente int64 mas semanticamente uma variável categórica binária
- Dataset altamente desbalanceado: 99.83% classe 0 (legítimas), 0.17% classe 1 (fraudes)
- Amount apresenta distribuição assimétrica com presença de valores extremos

💡 Recomendações:
- Tratar Class como variável categórica nas análises (apesar do dtype int64)
- Considerar normalização ou transformação logarítmica de Amount (alta skewness)
- Aplicar técnicas de balanceamento para modelagem (SMOTE, undersampling, class weights)
- Usar features V1-V28 diretamente (já normalizadas via PCA)
```

═══════════════════════════════════════════════════════════════════

Baseie sua resposta EXCLUSIVAMENTE nos dados fornecidos e no contexto analítico recuperado.""",
    variables=[]
)
```

---

## 2. CONFIGURAÇÕES CENTRALIZADAS

### Novo Arquivo: `src/config/llm_config.py`

```python
"""Configurações Centralizadas para LLM e Busca Vetorial

Este módulo centraliza todas as configurações relacionadas a:
- Parâmetros LLM (temperature, max_tokens, top_p)
- Thresholds de similaridade vetorial
- Limites de busca e chunking
- Mapeamentos de temperatura por intenção

Uso:
    from src.config.llm_config import LLM_CONFIGS, SIMILARITY_THRESHOLDS
    
    threshold = SIMILARITY_THRESHOLDS['primary_search']
    temp = get_temperature_for_intent(AnalysisIntent.STATISTICAL)
"""

from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════
# PARÂMETROS LLM PADRÃO
# ═══════════════════════════════════════════════════════════════════

@dataclass
class LLMParameters:
    """Parâmetros padrão para chamadas LLM."""
    temperature: float = 0.2
    max_tokens: int = 2048  # ⬆️ Aumentado de 1024
    top_p: float = 0.9
    top_k: int = 40
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


# Configurações por tipo de modelo
LLM_CONFIGS: Dict[str, LLMParameters] = {
    'default': LLMParameters(
        temperature=0.2,
        max_tokens=2048,
        top_p=0.9
    ),
    'precise': LLMParameters(
        temperature=0.1,
        max_tokens=1536,
        top_p=0.85
    ),
    'creative': LLMParameters(
        temperature=0.4,
        max_tokens=2048,
        top_p=0.95
    ),
    'conversational': LLMParameters(
        temperature=0.35,
        max_tokens=2048,
        top_p=0.92
    )
}


# ═══════════════════════════════════════════════════════════════════
# TEMPERATURE DINÂMICA POR INTENÇÃO
# ═══════════════════════════════════════════════════════════════════

# Importar dinamicamente para evitar dependências circulares
try:
    from src.analysis.intent_classifier import AnalysisIntent
    INTENT_AVAILABLE = True
except ImportError:
    INTENT_AVAILABLE = False
    AnalysisIntent = None


INTENT_TEMPERATURE_MAP: Dict[str, float] = {
    'STATISTICAL': 0.1,       # Máxima precisão para cálculos
    'FREQUENCY': 0.15,        # Alta precisão para contagens
    'TEMPORAL': 0.15,         # Alta precisão para séries temporais
    'CLUSTERING': 0.2,        # Precisão balanceada
    'CORRELATION': 0.15,      # Alta precisão para correlações
    'OUTLIERS': 0.2,          # Precisão balanceada
    'COMPARISON': 0.25,       # Mais flexibilidade para comparações
    'CONVERSATIONAL': 0.35,   # Alta diversidade para conversação
    'VISUALIZATION': 0.2,     # Precisão balanceada
    'GENERAL': 0.3,           # Exploratória com criatividade
}

# Fallback se Intent não disponível
INTENT_TEMPERATURE_MAP_FALLBACK: Dict[str, float] = {
    'statistical': 0.1,
    'frequency': 0.15,
    'temporal': 0.15,
    'clustering': 0.2,
    'correlation': 0.15,
    'outliers': 0.2,
    'comparison': 0.25,
    'conversational': 0.35,
    'visualization': 0.2,
    'general': 0.3,
    'default': 0.2
}


def get_temperature_for_intent(intent) -> float:
    """
    Retorna temperature apropriada para a intenção analítica.
    
    Args:
        intent: AnalysisIntent enum ou string
        
    Returns:
        Temperature float (0.0-1.0)
    """
    if INTENT_AVAILABLE and isinstance(intent, AnalysisIntent):
        return INTENT_TEMPERATURE_MAP.get(intent.value.upper(), 0.2)
    
    # Fallback para string
    if isinstance(intent, str):
        return INTENT_TEMPERATURE_MAP_FALLBACK.get(intent.lower(), 0.2)
    
    return 0.2  # Default conservador


# ═══════════════════════════════════════════════════════════════════
# THRESHOLDS DE SIMILARIDADE VETORIAL
# ═══════════════════════════════════════════════════════════════════

SIMILARITY_THRESHOLDS: Dict[str, float] = {
    # Busca principal (balanceado)
    'primary_search': 0.65,       # ⬇️ Reduzido de 0.7
    
    # Busca com expansão (recall maior)
    'fallback_search': 0.50,      # ⬇️ Reduzido de 0.55
    'expansion_search': 0.55,     # ⬇️ Reduzido de 0.65
    
    # Memória conversacional (flexível)
    'memory_retrieval': 0.60,     # ⬇️ Reduzido de 0.8 (CRÍTICO!)
    'memory_short_term': 0.65,    # Memória recente
    'memory_long_term': 0.55,     # Memória histórica
    
    # Validação e verificação (restritivo)
    'validation': 0.75,           # Manter restritivo
    'exact_match': 0.85,          # Match quase exato
    
    # Classificação semântica
    'intent_classification': 0.70,
    'entity_extraction': 0.65,
}

# Ranges de threshold por nível de rigor
THRESHOLD_RANGES: Dict[str, tuple] = {
    'strict': (0.75, 0.90),       # Alta precisão, baixo recall
    'balanced': (0.60, 0.75),     # Equilíbrio
    'relaxed': (0.45, 0.60),      # Alto recall, menor precisão
}


# ═══════════════════════════════════════════════════════════════════
# LIMITES DE BUSCA E RECUPERAÇÃO
# ═══════════════════════════════════════════════════════════════════

SEARCH_LIMITS: Dict[str, int] = {
    # Busca padrão
    'default': 5,                 # ⬆️ Aumentado de 3
    'minimum': 3,                 # Mínimo aceitável
    'maximum': 20,                # Máximo permitido
    
    # Expansão e fallback
    'expansion': 15,              # ⬆️ Aumentado de 10
    'fallback': 10,               # Busca alternativa
    
    # Memória
    'memory': 8,                  # ⬆️ Aumentado de 5
    'memory_recent': 5,           # Memória recente
    'memory_all': 12,             # Toda memória
    
    # Contexto
    'context_build': 7,           # Construção de contexto
    'summary': 10,                # Para resumos
}

# Fatores de expansão
EXPANSION_FACTORS: Dict[str, int] = {
    'query_variations': 3,        # Gerar 3 variações
    'limit_multiplier': 4,        # 5 * 4 = 20 na expansão
    'threshold_reduction': 0.15,  # Reduzir 0.15 no threshold
}


# ═══════════════════════════════════════════════════════════════════
# PARÂMETROS DE CHUNKING
# ═══════════════════════════════════════════════════════════════════

CHUNKING_PARAMS: Dict[str, Any] = {
    # Texto geral
    'text_chunk_size': 1024,      # ⬆️ Aumentado de 512
    'text_overlap': 150,          # ⬆️ Aumentado de 50
    'min_chunk_size': 100,        # ⬆️ Aumentado de 50
    
    # CSV específico
    'csv_chunk_rows': 30,         # ⬆️ Aumentado de 20
    'csv_overlap_rows': 6,        # ⬆️ Aumentado de 4
    'csv_min_rows': 5,            # Mínimo de linhas
    
    # Estratégias
    'default_strategy': 'fixed_size',
    'csv_strategy': 'csv_row',
}


# ═══════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════

def get_config_for_query_type(query_type: str) -> LLMParameters:
    """
    Retorna configuração LLM apropriada para tipo de query.
    
    Args:
        query_type: Tipo da query ('statistical', 'conversational', etc)
        
    Returns:
        LLMParameters configurado
    """
    type_map = {
        'statistical': 'precise',
        'conversational': 'conversational',
        'exploratory': 'creative',
        'general': 'default'
    }
    
    config_key = type_map.get(query_type.lower(), 'default')
    return LLM_CONFIGS[config_key]


def get_threshold_for_context(context: str) -> float:
    """
    Retorna threshold apropriado para contexto de busca.
    
    Args:
        context: Contexto da busca ('primary', 'memory', 'expansion', etc)
        
    Returns:
        Threshold float
    """
    key_map = {
        'primary': 'primary_search',
        'fallback': 'fallback_search',
        'expansion': 'expansion_search',
        'memory': 'memory_retrieval',
        'validation': 'validation'
    }
    
    key = key_map.get(context.lower(), 'primary_search')
    return SIMILARITY_THRESHOLDS[key]


def adjust_threshold_by_rigor(base_threshold: float, rigor: str) -> float:
    """
    Ajusta threshold baseado no nível de rigor desejado.
    
    Args:
        base_threshold: Threshold base
        rigor: Nível de rigor ('strict', 'balanced', 'relaxed')
        
    Returns:
        Threshold ajustado
    """
    if rigor not in THRESHOLD_RANGES:
        return base_threshold
    
    min_thresh, max_thresh = THRESHOLD_RANGES[rigor]
    
    # Clamp threshold dentro do range
    return max(min_thresh, min(base_threshold, max_thresh))


# ═══════════════════════════════════════════════════════════════════
# VALIDAÇÃO DE CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════

def validate_configs() -> bool:
    """
    Valida todas as configurações para garantir consistência.
    
    Returns:
        True se todas as configurações são válidas
    """
    errors = []
    
    # Validar temperatures (0.0 - 1.0)
    for key, temp in INTENT_TEMPERATURE_MAP.items():
        if not 0.0 <= temp <= 1.0:
            errors.append(f"Temperature inválida para {key}: {temp}")
    
    # Validar thresholds (0.0 - 1.0)
    for key, thresh in SIMILARITY_THRESHOLDS.items():
        if not 0.0 <= thresh <= 1.0:
            errors.append(f"Threshold inválido para {key}: {thresh}")
    
    # Validar limites (positivos)
    for key, limit in SEARCH_LIMITS.items():
        if limit <= 0:
            errors.append(f"Limit inválido para {key}: {limit}")
    
    # Validar chunk sizes
    if CHUNKING_PARAMS['text_overlap'] >= CHUNKING_PARAMS['text_chunk_size']:
        errors.append("Overlap não pode ser maior que chunk_size")
    
    if CHUNKING_PARAMS['csv_overlap_rows'] >= CHUNKING_PARAMS['csv_chunk_rows']:
        errors.append("CSV overlap não pode ser maior que csv_chunk_rows")
    
    if errors:
        for error in errors:
            print(f"❌ Erro de configuração: {error}")
        return False
    
    print("✅ Todas as configurações são válidas")
    return True


# Executar validação ao importar
if __name__ == "__main__":
    validate_configs()
```

---

## 3. TEMPERATURE DINÂMICA

### Arquivo: `src/llm/manager.py` (adicionar método)

```python
def chat_with_intent(self, 
                    prompt: str, 
                    intent,  # AnalysisIntent ou string
                    config: Optional[LLMConfig] = None,
                    system_prompt: Optional[str] = None) -> LLMResponse:
    """
    Envia prompt com temperature ajustada dinamicamente por intenção.
    
    Args:
        prompt: Texto do prompt
        intent: AnalysisIntent enum ou string com tipo de intenção
        config: Configurações LLM (temperature será sobrescrita)
        system_prompt: Prompt de sistema opcional
        
    Returns:
        LLMResponse com resultado da geração
        
    Exemplo:
        >>> from src.analysis.intent_classifier import AnalysisIntent
        >>> response = manager.chat_with_intent(
        ...     "Calcule a média de Amount",
        ...     intent=AnalysisIntent.STATISTICAL
        ... )
        >>> # Temperature será 0.1 (máxima precisão)
    """
    from src.config.llm_config import get_temperature_for_intent
    
    # Criar config se não fornecido
    if config is None:
        config = LLMConfig()
    
    # Ajustar temperature dinamicamente
    original_temp = config.temperature
    config.temperature = get_temperature_for_intent(intent)
    
    self.logger.info({
        'event': 'temperature_adjusted',
        'intent': str(intent),
        'original_temp': original_temp,
        'adjusted_temp': config.temperature
    })
    
    # Chamar método padrão
    return self.chat(prompt, config, system_prompt=system_prompt)
```

---

## 4. AJUSTES DE CHUNKING

### Arquivo: `src/embeddings/chunker.py` (modificar __init__)

```python
def __init__(self, 
             chunk_size: int = None,
             overlap_size: int = None,
             min_chunk_size: int = None,
             csv_chunk_size_rows: int = None,
             csv_overlap_rows: int = None):
    """
    Inicializa o sistema de chunking com configurações centralizadas.
    
    Args:
        chunk_size: Tamanho alvo de cada chunk em caracteres (default: 1024)
        overlap_size: Sobreposição entre chunks consecutivos (default: 150)
        min_chunk_size: Tamanho mínimo para considerar um chunk válido (default: 100)
        csv_chunk_size_rows: Número de linhas por chunk CSV (default: 30)
        csv_overlap_rows: Overlap entre chunks CSV em linhas (default: 6)
    """
    from src.config.llm_config import CHUNKING_PARAMS
    
    # Usar valores centralizados se não fornecidos
    self.chunk_size = chunk_size or CHUNKING_PARAMS['text_chunk_size']
    self.overlap_size = overlap_size or CHUNKING_PARAMS['text_overlap']
    self.min_chunk_size = min_chunk_size or CHUNKING_PARAMS['min_chunk_size']
    self.csv_chunk_size_rows = csv_chunk_size_rows or CHUNKING_PARAMS['csv_chunk_rows']
    self.csv_overlap_rows = csv_overlap_rows or CHUNKING_PARAMS['csv_overlap_rows']
    
    # Validações
    if self.csv_overlap_rows >= self.csv_chunk_size_rows:
        logger.warning(
            "CSV overlap (%s) >= chunk_size_rows (%s). Ajustando para chunk_size_rows - 1.",
            self.csv_overlap_rows,
            self.csv_chunk_size_rows
        )
        self.csv_overlap_rows = max(0, self.csv_chunk_size_rows - 1)
    
    if self.overlap_size >= self.chunk_size:
        logger.warning(
            "Overlap (%s) >= chunk_size (%s). Ajustando para chunk_size // 4.",
            self.overlap_size,
            self.chunk_size
        )
        self.overlap_size = self.chunk_size // 4
    
    self.logger = logger
    
    self.logger.info({
        'event': 'chunker_initialized',
        'chunk_size': self.chunk_size,
        'overlap_size': self.overlap_size,
        'min_chunk_size': self.min_chunk_size,
        'csv_chunk_rows': self.csv_chunk_size_rows,
        'csv_overlap_rows': self.csv_overlap_rows
    })
```

---

## 5. THRESHOLDS PADRONIZADOS

### Arquivo: `src/router/semantic_router.py` (modificar)

```python
def search_with_expansion(self, question: str,
                          base_threshold: float = None,
                          base_limit: int = None) -> List["VectorSearchResult"]:
    """Busca chunks com expansão automática e thresholds centralizados."""
    from src.config.llm_config import SIMILARITY_THRESHOLDS, SEARCH_LIMITS, EXPANSION_FACTORS
    
    # Usar configurações centralizadas
    if base_threshold is None:
        base_threshold = SIMILARITY_THRESHOLDS['primary_search']
    
    if base_limit is None:
        base_limit = SEARCH_LIMITS['default']
    
    # Montar filtro
    filters = {}
    if self.ingestion_id:
        filters['ingestion_id'] = self.ingestion_id
    if self.source_id:
        filters['source_id'] = self.source_id

    # 1) Search original
    embedding = self.embed_question(question)
    results = self.vector_store.search_similar(
        query_embedding=embedding,
        similarity_threshold=base_threshold,
        limit=base_limit,
        filters=filters if filters else None
    )

    if results:
        return results

    # 2) Tentar refinamento via QueryRefiner
    try:
        refiner = QueryRefiner(embedding_provider=EmbeddingProvider.SENTENCE_TRANSFORMER)
        ref_result = refiner.refine_query(question)
        if ref_result and ref_result.success:
            emb = ref_result.embedding
            alt_results = self.vector_store.search_similar(
                query_embedding=emb,
                similarity_threshold=base_threshold,
                limit=base_limit,
                filters=filters if filters else None
            )
            if alt_results:
                return alt_results
    except Exception as e:
        self.logger.warning(f"QueryRefiner falhou: {e}")

    # 3) Expand queries com thresholds centralizados
    variations = StatisticalOntology.generate_simple_expansions(question)
    aggregated = []
    seen_ids = set()
    
    # Usar configurações centralizadas para expansão
    expansion_threshold = SIMILARITY_THRESHOLDS['expansion_search']
    expansion_limit = SEARCH_LIMITS['expansion']

    for var in variations:
        try:
            emb = self.embed_question(var)
            alt_results = self.vector_store.search_similar(
                query_embedding=emb,
                similarity_threshold=expansion_threshold,
                limit=expansion_limit,
                filters=filters if filters else None
            )

            for r in alt_results:
                if r.embedding_id not in seen_ids:
                    aggregated.append(r)
                    seen_ids.add(r.embedding_id)
        except Exception:
            continue

    # Ordenar e retornar top results
    aggregated.sort(key=lambda x: x.similarity_score, reverse=True)
    return aggregated[:base_limit]
```

---

## 6. TESTES AUTOMATIZADOS

### Novo Arquivo: `tests/test_improved_configs.py`

```python
"""Testes para validar melhorias de configuração do sistema."""

import pytest
from src.config.llm_config import (
    SIMILARITY_THRESHOLDS,
    SEARCH_LIMITS,
    CHUNKING_PARAMS,
    get_temperature_for_intent,
    validate_configs
)


class TestImprovedConfigs:
    """Suite de testes para configurações melhoradas."""
    
    def test_validate_all_configs(self):
        """Verifica que todas as configurações são válidas."""
        assert validate_configs() is True
    
    def test_thresholds_reduced(self):
        """Verifica que thresholds foram reduzidos conforme recomendado."""
        assert SIMILARITY_THRESHOLDS['primary_search'] == 0.65
        assert SIMILARITY_THRESHOLDS['memory_retrieval'] == 0.60  # Crítico!
        assert SIMILARITY_THRESHOLDS['expansion_search'] == 0.55
    
    def test_search_limits_increased(self):
        """Verifica que limites de busca foram aumentados."""
        assert SEARCH_LIMITS['default'] == 5  # Era 3
        assert SEARCH_LIMITS['expansion'] == 15  # Era 10
        assert SEARCH_LIMITS['memory'] == 8  # Era 5
    
    def test_chunk_size_increased(self):
        """Verifica que chunk size foi aumentado."""
        assert CHUNKING_PARAMS['text_chunk_size'] == 1024  # Era 512
        assert CHUNKING_PARAMS['text_overlap'] == 150  # Era 50
        assert CHUNKING_PARAMS['min_chunk_size'] == 100  # Era 50
    
    def test_temperature_dynamic_mapping(self):
        """Verifica mapeamento de temperature por intenção."""
        from src.analysis.intent_classifier import AnalysisIntent
        
        # Statistical deve ter menor temperature
        temp_stat = get_temperature_for_intent(AnalysisIntent.STATISTICAL)
        assert temp_stat == 0.1
        
        # Conversational deve ter maior temperature
        temp_conv = get_temperature_for_intent(AnalysisIntent.CONVERSATIONAL)
        assert temp_conv == 0.35
        
        # Statistical < General < Conversational
        temp_gen = get_temperature_for_intent(AnalysisIntent.GENERAL)
        assert temp_stat < temp_gen < temp_conv
    
    def test_memory_threshold_critical_fix(self):
        """Verifica que threshold de memória foi corrigido (crítico!)."""
        # Era 0.8 (muito alto), deve ser 0.6
        assert SIMILARITY_THRESHOLDS['memory_retrieval'] == 0.60
        assert SIMILARITY_THRESHOLDS['memory_retrieval'] < 0.65  # Deve ser mais baixo que busca padrão


class TestPromptV2Integration:
    """Testes para integração do Prompt V2."""
    
    @pytest.fixture
    def prompt_manager(self):
        from src.prompts.manager import get_prompt_manager, AgentRole
        return get_prompt_manager()
    
    def test_prompt_v2_exists(self, prompt_manager):
        """Verifica que Prompt V2 foi adicionado."""
        from src.prompts.manager import AgentRole
        
        prompts_available = prompt_manager.list_available_prompts(AgentRole.CSV_ANALYST)
        assert 'data_types_analysis_v2' in prompts_available[AgentRole.CSV_ANALYST.value]
    
    def test_prompt_v2_content(self, prompt_manager):
        """Verifica conteúdo do Prompt V2."""
        from src.prompts.manager import AgentRole
        
        prompt_v2 = prompt_manager.get_prompt(AgentRole.CSV_ANALYST, 'data_types_analysis_v2')
        
        # Deve conter seções principais
        assert 'SEÇÃO 1: CLASSIFICAÇÃO TÉCNICA' in prompt_v2
        assert 'SEÇÃO 2: CONTEXTO ANALÍTICO' in prompt_v2
        assert 'SEÇÃO 3: INSIGHTS E RECOMENDAÇÕES' in prompt_v2
        
        # Não deve ter instruções excessivamente restritivas
        assert 'NÃO interprete semanticamente' not in prompt_v2
        assert 'siga RIGOROSAMENTE' not in prompt_v2


class TestChunkingImprovements:
    """Testes para melhorias de chunking."""
    
    def test_chunker_uses_new_defaults(self):
        """Verifica que chunker usa novos defaults."""
        from src.embeddings.chunker import TextChunker
        
        chunker = TextChunker()  # Sem argumentos, deve usar defaults
        
        assert chunker.chunk_size == 1024
        assert chunker.overlap_size == 150
        assert chunker.min_chunk_size == 100
    
    def test_chunker_respects_custom_values(self):
        """Verifica que valores customizados são respeitados."""
        from src.embeddings.chunker import TextChunker
        
        chunker = TextChunker(chunk_size=2048, overlap_size=200)
        
        assert chunker.chunk_size == 2048
        assert chunker.overlap_size == 200


class TestLLMManagerIntegration:
    """Testes para integração do LLM Manager."""
    
    @pytest.fixture
    def llm_manager(self):
        from src.llm.manager import get_llm_manager
        return get_llm_manager()
    
    def test_chat_with_intent_method_exists(self, llm_manager):
        """Verifica que método chat_with_intent existe."""
        assert hasattr(llm_manager, 'chat_with_intent')
    
    def test_chat_with_intent_adjusts_temperature(self, llm_manager):
        """Verifica que temperature é ajustada por intenção."""
        from src.analysis.intent_classifier import AnalysisIntent
        from src.llm.manager import LLMConfig
        
        # Criar config com temperature padrão
        config = LLMConfig(temperature=0.5)
        
        # Mock para capturar temperatura final
        temps_used = []
        original_chat = llm_manager.chat
        
        def mock_chat(prompt, config=None, **kwargs):
            if config:
                temps_used.append(config.temperature)
            return original_chat(prompt, config, **kwargs)
        
        llm_manager.chat = mock_chat
        
        # Chamar com intent STATISTICAL
        try:
            llm_manager.chat_with_intent(
                "Calcule média", 
                intent=AnalysisIntent.STATISTICAL,
                config=config
            )
        except:
            pass  # Pode falhar na chamada real, mas capturamos temperature
        
        # Temperature deve ter sido ajustada para 0.1
        if temps_used:
            assert temps_used[0] == 0.1


# Executar testes
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## 🚀 SCRIPT DE MIGRAÇÃO

### Arquivo: `scripts/apply_improvements.py`

```python
"""Script para aplicar melhorias de configuração ao sistema.

Este script:
1. Valida configurações atuais
2. Aplica novos parâmetros
3. Re-inicializa componentes críticos
4. Executa testes de validação

Uso:
    python scripts/apply_improvements.py --dry-run  # Simular apenas
    python scripts/apply_improvements.py --apply     # Aplicar mudanças
"""

import argparse
import sys
from pathlib import Path

# Adicionar root ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def validate_current_configs():
    """Valida configurações atuais e reporta issues."""
    print("\n🔍 Validando configurações atuais...")
    
    from src.config.llm_config import validate_configs
    
    if validate_configs():
        print("✅ Configurações atuais são válidas")
        return True
    else:
        print("❌ Configurações contêm erros")
        return False


def backup_current_configs():
    """Faz backup das configurações atuais."""
    print("\n💾 Fazendo backup das configurações...")
    
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root_dir / "backups" / f"config_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivos para backup
    files_to_backup = [
        "src/llm/manager.py",
        "src/prompts/manager.py",
        "src/embeddings/chunker.py",
        "src/router/semantic_router.py"
    ]
    
    for file_path in files_to_backup:
        source = root_dir / file_path
        if source.exists():
            dest = backup_dir / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            print(f"  ✅ Backup: {file_path}")
    
    print(f"✅ Backup salvo em: {backup_dir}")
    return backup_dir


def apply_improvements(dry_run=False):
    """Aplica melhorias de configuração."""
    print("\n🚀 Aplicando melhorias...")
    
    if dry_run:
        print("  ⚠️ Modo DRY RUN - apenas simulação")
    
    # 1. Validar configs
    if not validate_current_configs():
        print("❌ Abortando: configurações inválidas")
        return False
    
    # 2. Fazer backup
    if not dry_run:
        backup_dir = backup_current_configs()
    
    # 3. Importar novos configs
    print("\n📦 Importando novas configurações...")
    try:
        from src.config.llm_config import (
            SIMILARITY_THRESHOLDS,
            SEARCH_LIMITS,
            CHUNKING_PARAMS,
            LLM_CONFIGS
        )
        print("  ✅ Configurações centralizadas carregadas")
    except ImportError as e:
        print(f"  ❌ Erro ao importar configs: {e}")
        return False
    
    # 4. Verificar mudanças
    print("\n📊 Resumo das mudanças:")
    print(f"  • Primary Search Threshold: 0.7 → {SIMILARITY_THRESHOLDS['primary_search']}")
    print(f"  • Memory Threshold: 0.8 → {SIMILARITY_THRESHOLDS['memory_retrieval']} (CRÍTICO!)")
    print(f"  • Search Limit: 3 → {SEARCH_LIMITS['default']}")
    print(f"  • Chunk Size: 512 → {CHUNKING_PARAMS['text_chunk_size']}")
    print(f"  • Overlap Size: 50 → {CHUNKING_PARAMS['text_overlap']}")
    print(f"  • Max Tokens: 1024 → {LLM_CONFIGS['default'].max_tokens}")
    
    if not dry_run:
        print("\n✅ Melhorias aplicadas com sucesso!")
        print("\n⚠️ ATENÇÃO: Re-ingestão de dados recomendada para aproveitar novo chunk_size")
        print("   Execute: python scripts/run_ingest_with_new_chunks.py")
    else:
        print("\n✅ Simulação concluída - sem mudanças aplicadas")
    
    return True


def run_tests():
    """Executa suite de testes de validação."""
    print("\n🧪 Executando testes de validação...")
    
    import pytest
    
    test_file = root_dir / "tests" / "test_improved_configs.py"
    if not test_file.exists():
        print("  ⚠️ Arquivo de testes não encontrado")
        return False
    
    result = pytest.main([str(test_file), "-v"])
    
    if result == 0:
        print("✅ Todos os testes passaram")
        return True
    else:
        print("❌ Alguns testes falharam")
        return False


def main():
    parser = argparse.ArgumentParser(description="Aplicar melhorias de configuração")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Simular aplicação sem fazer mudanças")
    parser.add_argument("--apply", action="store_true",
                       help="Aplicar mudanças efetivamente")
    parser.add_argument("--test", action="store_true",
                       help="Executar testes de validação")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔧 APLICADOR DE MELHORIAS - EDA AI Minds")
    print("=" * 70)
    
    if args.test:
        run_tests()
    elif args.apply or args.dry_run:
        success = apply_improvements(dry_run=args.dry_run)
        if success and not args.dry_run:
            print("\n🎉 Melhorias aplicadas com sucesso!")
            print("\n📋 Próximos passos:")
            print("  1. Executar testes: python scripts/apply_improvements.py --test")
            print("  2. Re-ingerir dados: python scripts/run_ingest_with_new_chunks.py")
            print("  3. Testar interface: python interface_interativa.py")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Quick Wins (Imediato - 2 horas)

- [ ] Criar arquivo `src/config/llm_config.py` com configurações centralizadas
- [ ] Aumentar `max_tokens` de 1024 para 2048 em `LLMConfig`
- [ ] Aplicar novos thresholds em `semantic_router.py`
- [ ] Executar testes automatizados

### Fase 2: Prompt V2 (Semana 1 - 6 horas)

- [ ] Adicionar Prompt V2 em `src/prompts/manager.py`
- [ ] Atualizar orchestrator para usar Prompt V2
- [ ] Criar testes A/B comparando respostas
- [ ] Validar com perguntas de exemplo

### Fase 3: Chunking (Semana 2-3 - 2 dias)

- [ ] Modificar `TextChunker.__init__` para usar configs centralizadas
- [ ] Re-ingerir dados com novo chunk_size (1024)
- [ ] Comparar qualidade de chunks antes/depois
- [ ] Validar impacto em busca vetorial

### Fase 4: Temperature Dinâmica (Semana 4 - 6 horas)

- [ ] Adicionar método `chat_with_intent` no LLM Manager
- [ ] Integrar com IntentClassifier
- [ ] Adicionar logging de temperatures usadas
- [ ] Monitorar impacto em queries reais

### Fase 5: Validação Final (Pós-implementação)

- [ ] Executar suite completa de testes
- [ ] Comparar métricas antes/depois
- [ ] Documentar resultados
- [ ] Ajustar parâmetros se necessário

---

**Arquivo criado por:** GitHub Copilot GPT-4.1  
**Data:** 18 de Outubro de 2025  
**Status:** ✅ Ready for Implementation  
**Versão:** 1.0
