"""Sistema de Prompts Dinâmicos e Adaptativos

Este módulo fornece geração dinâmica de prompts baseada em:
- Estrutura real do dataset (dtypes, shape, colunas)
- Contexto da pergunta do usuário
- Histórico conversacional
- Intenção detectada

ZERO hardcoding de estruturas específicas de dados.
Totalmente adaptável a qualquer dataset CSV genérico.

Autor: EDA AI Minds Team
Data: 2025-10-18
Versão: 4.0.0
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
from datetime import datetime


@dataclass
class DatasetContext:
    """Contexto completo do dataset atual."""
    file_path: str
    shape: tuple
    columns: List[str]
    dtypes: Dict[str, str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    temporal_columns: List[str]
    boolean_columns: List[str]
    missing_values: Dict[str, int]
    memory_usage_mb: float
    row_count: int
    column_count: int
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, file_path: str = "unknown") -> DatasetContext:
        """Cria contexto a partir de um DataFrame."""
        dtypes_dict = df.dtypes.astype(str).to_dict()
        
        # Classificação automática de tipos
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        temporal_cols = df.select_dtypes(include=['datetime', 'timedelta']).columns.tolist()
        boolean_cols = df.select_dtypes(include=['bool']).columns.tolist()
        
        missing = df.isnull().sum().to_dict()
        memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
        
        return cls(
            file_path=file_path,
            shape=df.shape,
            columns=df.columns.tolist(),
            dtypes=dtypes_dict,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            temporal_columns=temporal_cols,
            boolean_columns=boolean_cols,
            missing_values=missing,
            memory_usage_mb=memory_mb,
            row_count=len(df),
            column_count=len(df.columns)
        )


class DynamicPromptGenerator:
    """Gerador de prompts completamente dinâmico e adaptativo."""
    
    def __init__(self):
        """Inicializa o gerador."""
        self.last_context: Optional[DatasetContext] = None
    
    def generate_system_prompt(
        self,
        dataset_context: DatasetContext,
        analysis_intent: str = "general",
        additional_capabilities: List[str] = None
    ) -> str:
        """
        Gera prompt de sistema dinâmico baseado no dataset real.
        
        Args:
            dataset_context: Contexto completo do dataset
            analysis_intent: Intenção da análise (statistical, temporal, etc)
            additional_capabilities: Capacidades adicionais do agente
            
        Returns:
            Prompt de sistema personalizado
        """
        self.last_context = dataset_context
        
        # Construir descrição dinâmica do dataset
        dataset_description = self._build_dataset_description(dataset_context)
        
        # Construir capacidades analíticas baseadas no tipo de dados
        analytical_capabilities = self._build_analytical_capabilities(dataset_context)
        
        # Construir diretrizes específicas para o intent
        intent_guidelines = self._build_intent_guidelines(analysis_intent, dataset_context)
        
        # Montar prompt completo
        system_prompt = f"""🤖 **AGENTE EDA - Análise Exploratória de Dados**

📊 **DATASET ATUAL**
{dataset_description}

🧠 **CAPACIDADES ANALÍTICAS DISPONÍVEIS**
{analytical_capabilities}

🎯 **DIRETRIZES PARA ANÁLISE ATUAL**
{intent_guidelines}

⚡ **INSTRUÇÕES OPERACIONAIS**

1. **PRECISÃO ABSOLUTA**: 
   - Use APENAS os dados reais fornecidos
   - Cite números específicos, não aproximações
   - Quando incerto, declare explicitamente

2. **COBERTURA COMPLETA**:
   - Analise TODAS as colunas relevantes para a pergunta
   - Considere TODAS as linhas, exceto quando amostragem for solicitada
   - Identifique padrões globais E locais

3. **CLAREZA E DIDÁTICA**:
   - Explique conceitos técnicos quando necessário
   - Use tabelas Markdown para comparações
   - Destaque insights principais com **negrito**
   - Finalize sempre com "Se precisar de mais detalhes, é só perguntar!"

4. **CONTEXTUALIZAÇÃO**:
   - Sempre inicie com: "**Pergunta feita:** [pergunta]"
   - Referencie análises anteriores se houver histórico
   - Sugira análises complementares relevantes

5. **INTEGRIDADE DOS DADOS**:
   - Mencione valores ausentes se relevantes
   - Identifique limitações dos dados
   - Alerte sobre possíveis vieses

🚫 **PROIBIÇÕES**:
- NÃO invente dados que não existem
- NÃO assuma características não verificadas
- NÃO use respostas genéricas de conceitos
- NÃO ignore colunas disponíveis sem justificativa

📝 **FORMATO DE RESPOSTA**:
- Estruture em seções claras com títulos
- Use listas para itens múltiplos
- Inclua tabelas quando comparar valores
- Destaque números e métricas chave
"""
        
        return system_prompt
    
    def _build_dataset_description(self, ctx: DatasetContext) -> str:
        """Constrói descrição dinâmica do dataset."""
        desc = f"""
- **Arquivo**: `{ctx.file_path}`
- **Dimensões**: {ctx.row_count:,} linhas × {ctx.column_count} colunas
- **Memória**: {ctx.memory_usage_mb:.2f} MB

**Estrutura de Colunas:**
"""
        
        if ctx.numeric_columns:
            desc += f"\n- **Numéricas ({len(ctx.numeric_columns)})**: {', '.join(f'`{col}`' for col in ctx.numeric_columns[:10])}"
            if len(ctx.numeric_columns) > 10:
                desc += f" ... e mais {len(ctx.numeric_columns) - 10}"
        
        if ctx.categorical_columns:
            desc += f"\n- **Categóricas ({len(ctx.categorical_columns)})**: {', '.join(f'`{col}`' for col in ctx.categorical_columns[:5])}"
            if len(ctx.categorical_columns) > 5:
                desc += f" ... e mais {len(ctx.categorical_columns) - 5}"
        
        if ctx.temporal_columns:
            desc += f"\n- **Temporais ({len(ctx.temporal_columns)})**: {', '.join(f'`{col}`' for col in ctx.temporal_columns)}"
        
        if ctx.boolean_columns:
            desc += f"\n- **Booleanas ({len(ctx.boolean_columns)})**: {', '.join(f'`{col}`' for col in ctx.boolean_columns)}"
        
        # Valores ausentes
        missing_cols = {col: count for col, count in ctx.missing_values.items() if count > 0}
        if missing_cols:
            desc += f"\n\n**Valores Ausentes:**"
            for col, count in list(missing_cols.items())[:5]:
                pct = (count / ctx.row_count) * 100
                desc += f"\n- `{col}`: {count:,} ({pct:.2f}%)"
            if len(missing_cols) > 5:
                desc += f"\n- ... e mais {len(missing_cols) - 5} colunas com dados ausentes"
        
        return desc
    
    def _build_analytical_capabilities(self, ctx: DatasetContext) -> str:
        """Constrói lista de capacidades baseada no tipo de dados disponível."""
        capabilities = []
        
        if ctx.numeric_columns:
            capabilities.append("""
**Análise Estatística Descritiva**:
- Medidas de tendência central (média, mediana, moda)
- Medidas de dispersão (desvio padrão, variância, IQR)
- Intervalos (mínimo, máximo, range)
- Percentis e quartis
- Assimetria e curtose""")
        
        if len(ctx.numeric_columns) >= 2:
            capabilities.append("""
**Análise de Correlação**:
- Matriz de correlação entre variáveis numéricas
- Identificação de relações lineares
- Detecção de multicolinearidade""")
        
        if ctx.categorical_columns:
            capabilities.append("""
**Análise de Frequência**:
- Valores mais/menos frequentes
- Distribuições categóricas
- Tabelas de contingência
- Análise de proporções""")
        
        if ctx.temporal_columns:
            capabilities.append("""
**Análise Temporal**:
- Identificação de tendências
- Detecção de sazonalidade
- Análise de padrões temporais
- Evolução de métricas ao longo do tempo""")
        
        capabilities.append("""
**Detecção de Anomalias**:
- Identificação de outliers (Z-score, IQR)
- Análise de valores atípicos
- Impacto de outliers nas estatísticas""")
        
        if ctx.row_count > 100:
            capabilities.append("""
**Análise de Agrupamentos**:
- Identificação de clusters naturais
- Segmentação de dados
- Análise de padrões de similaridade""")
        
        capabilities.append("""
**Visualizações Dinâmicas**:
- Histogramas para distribuições
- Gráficos de dispersão para relações
- Boxplots para comparações
- Heatmaps para correlações""")
        
        return "\n".join(capabilities)
    
    def _build_intent_guidelines(self, intent: str, ctx: DatasetContext) -> str:
        """Constrói diretrizes específicas baseadas na intenção detectada."""
        intent_map = {
            "statistical": self._guidelines_statistical(ctx),
            "frequency": self._guidelines_frequency(ctx),
            "temporal": self._guidelines_temporal(ctx),
            "correlation": self._guidelines_correlation(ctx),
            "outliers": self._guidelines_outliers(ctx),
            "clustering": self._guidelines_clustering(ctx),
            "comparison": self._guidelines_comparison(ctx),
            "visualization": self._guidelines_visualization(ctx),
            "general": self._guidelines_general(ctx)
        }
        
        return intent_map.get(intent.lower(), intent_map["general"])
    
    def _guidelines_statistical(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise estatística descritiva."""
        cols = ', '.join(f'`{c}`' for c in ctx.numeric_columns[:5])
        if len(ctx.numeric_columns) > 5:
            cols += f" ... ({len(ctx.numeric_columns)} no total)"
        
        return f"""
**Análise Estatística Descritiva Solicitada**

Para as colunas numéricas disponíveis ({cols}):

1. **Calcule e reporte**:
   - Média, mediana e moda
   - Desvio padrão e variância
   - Valores mínimo e máximo
   - Quartis (Q1, Q2, Q3) e IQR
   
2. **Interprete os resultados**:
   - Compare média vs mediana (indica assimetria?)
   - Desvio padrão alto/baixo (o que significa?)
   - Range dos dados (escala de variação)
   
3. **Identifique características**:
   - Distribuições simétricas vs assimétricas
   - Presença de valores extremos
   - Variabilidade relativa entre colunas"""
    
    def _guidelines_frequency(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise de frequência."""
        return f"""
**Análise de Frequência e Distribuição Solicitada**

Dataset possui {ctx.column_count} colunas para análise.

1. **Para colunas categóricas**:
   - Liste valores únicos e suas contagens
   - Identifique os TOP 10 valores mais frequentes
   - Identifique valores raros (frequência < 1%)
   - Calcule proporções relativas

2. **Para colunas numéricas**:
   - Agrupe em bins/intervalos apropriados
   - Gere distribuição de frequências
   - Identifique modas (picos de frequência)
   - Sugira visualização (histograma)

3. **Insights esperados**:
   - Distribuição balanceada ou desbalanceada?
   - Valores dominantes?
   - Presença de valores únicos/raros significativos?"""
    
    def _guidelines_temporal(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise temporal."""
        if ctx.temporal_columns:
            temp_cols = ', '.join(f'`{c}`' for c in ctx.temporal_columns)
            return f"""
**Análise Temporal Solicitada**

Colunas temporais disponíveis: {temp_cols}

1. **Identifique padrões**:
   - Tendências (crescimento, declínio, estabilidade)
   - Sazonalidade (padrões recorrentes)
   - Ciclos e periodicidade
   
2. **Análise de séries**:
   - Evolução de métricas ao longo do tempo
   - Mudanças abruptas (changepoints)
   - Autocorrelação
   
3. **Agregações temporais**:
   - Por dia, semana, mês conforme granularidade
   - Médias móveis
   - Taxas de crescimento"""
        else:
            return f"""
**Análise Temporal Solicitada (SEM COLUNAS TEMPORAIS EXPLÍCITAS)**

⚠️ **IMPORTANTE**: Dataset NÃO possui colunas de datetime explícitas.

Alternativas de análise:
1. Verificar se existe coluna numérica representando tempo/sequência
2. Analisar a ordem dos dados (se houver significância temporal implícita)
3. Sugerir que o usuário especifique qual coluna representa tempo
4. Indicar impossibilidade de análise temporal clássica sem coluna apropriada"""
    
    def _guidelines_correlation(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise de correlação."""
        n_numeric = len(ctx.numeric_columns)
        return f"""
**Análise de Correlação Solicitada**

{n_numeric} colunas numéricas disponíveis para análise de correlação.

1. **Calcule correlações**:
   - Matriz de correlação completa (Pearson)
   - Identifique correlações fortes (|r| > 0.7)
   - Identifique correlações moderadas (0.4 < |r| < 0.7)
   - Identifique correlações fracas (|r| < 0.4)

2. **Interprete relações**:
   - Correlações positivas (crescem juntas)
   - Correlações negativas (inversamente proporcionais)
   - Ausência de correlação linear (r ≈ 0)

3. **Insights práticos**:
   - Quais variáveis estão mais relacionadas?
   - Possíveis relações causa-efeito (cuidado com causalidade!)
   - Redundância entre variáveis (multicolinearidade)

4. **Visualização sugerida**:
   - Heatmap de correlação
   - Scatter plots para pares de maior correlação"""
    
    def _guidelines_outliers(self, ctx: DatasetContext) -> str:
        """Diretrizes para detecção de outliers."""
        return f"""
**Detecção de Anomalias e Outliers Solicitada**

Análise para {len(ctx.numeric_columns)} colunas numéricas.

1. **Métodos de detecção**:
   - IQR Method: valores fora de [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
   - Z-Score: valores com |z| > 3
   - Percentis: valores nos extremos (<1% ou >99%)

2. **Caracterização de outliers**:
   - Quantos outliers identificados por coluna?
   - Porcentagem do dataset
   - Valores específicos detectados
   - São outliers legítimos ou erros?

3. **Impacto nos dados**:
   - Como outliers afetam média e desvio padrão?
   - Mediana é mais robusta a outliers
   - Considerar remoção, transformação ou investigação?

4. **Recomendações**:
   - Investigar causa dos outliers
   - Validar se são erros de medição
   - Decidir tratamento apropriado"""
    
    def _guidelines_clustering(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise de agrupamentos."""
        return f"""
**Análise de Agrupamentos (Clustering) Solicitada**

Dataset com {ctx.row_count:,} linhas e {len(ctx.numeric_columns)} features numéricas.

1. **Preparação**:
   - Normalização/padronização de features
   - Seleção de features relevantes
   - Tratamento de valores ausentes

2. **Identificação de clusters**:
   - Quantos grupos naturais existem?
   - Características distintivas de cada cluster
   - Tamanho e proporção dos clusters

3. **Interpretação**:
   - O que diferencia os clusters?
   - Perfis típicos de cada grupo
   - Aplicabilidade prática da segmentação

4. **Métricas de qualidade**:
   - Coesão intra-cluster (quão similares dentro do grupo)
   - Separação inter-cluster (quão diferentes entre grupos)
   - Silhouette score se disponível"""
    
    def _guidelines_comparison(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise comparativa."""
        return f"""
**Análise Comparativa Solicitada**

1. **Identifique grupos a comparar**:
   - Baseado em colunas categóricas ou booleanas
   - Ou segmentos temporais
   - Ou clusters/agrupamentos

2. **Compare estatísticas**:
   - Médias, medianas por grupo
   - Desvios padrão por grupo
   - Distribuições (histogramas lado a lado)

3. **Teste diferenças**:
   - Diferenças absolutas e relativas
   - Significância estatística (se aplicável)
   - Magnitude do efeito

4. **Visualizações sugeridas**:
   - Boxplots comparativos
   - Barras agrupadas
   - Tabelas de resumo"""
    
    def _guidelines_visualization(self, ctx: DatasetContext) -> str:
        """Diretrizes para solicitações de visualização."""
        return f"""
**Visualização de Dados Solicitada**

Gráficos disponíveis baseados no dataset:

1. **Para distribuições**:
   - Histogramas (variáveis numéricas)
   - Densidade KDE
   - Boxplots (identificar outliers)

2. **Para relações**:
   - Scatter plots (correlação entre 2 variáveis)
   - Pairplots (múltiplas variáveis)
   - Heatmap de correlação

3. **Para frequências**:
   - Gráficos de barras (categorias)
   - Pizza charts (proporções)

4. **Para séries temporais**:
   - Line plots (evolução)
   - Área plots (tendências)

**IMPORTANTE**: Descreva o gráfico em texto E gere o arquivo de imagem."""
    
    def _guidelines_general(self, ctx: DatasetContext) -> str:
        """Diretrizes para análise geral/exploratória."""
        return f"""
**Análise Exploratória Geral**

Forneça uma visão completa do dataset:

1. **Overview estrutural**:
   - Quantidade de dados ({ctx.row_count:,} linhas)
   - Tipos de variáveis disponíveis
   - Qualidade dos dados (missing values)

2. **Estatísticas resumidas**:
   - Para TODAS as colunas numéricas
   - Frequências para colunas categóricas principais

3. **Identificação de padrões**:
   - Distribuições (simétricas, assimétricas, bimodais)
   - Correlações aparentes
   - Outliers significativos

4. **Sugestões de análise**:
   - Próximos passos recomendados
   - Análises mais profundas possíveis
   - Potenciais insights a explorar"""
    
    def generate_user_prompt_enhancement(
        self,
        original_query: str,
        dataset_context: DatasetContext,
        historical_context: str = "",
        retrieved_chunks: str = ""
    ) -> str:
        """
        Enriquece o prompt do usuário com contexto relevante.
        
        Args:
            original_query: Pergunta original do usuário
            dataset_context: Contexto do dataset
            historical_context: Histórico conversacional
            retrieved_chunks: Chunks recuperados via RAG
            
        Returns:
            Prompt enriquecido para a LLM
        """
        prompt = f"**Pergunta do Usuário:** {original_query}\n\n"
        
        if historical_context:
            prompt += f"**Contexto Conversacional:**\n{historical_context}\n\n"
        
        if retrieved_chunks:
            prompt += f"**Informações Analíticas Disponíveis (RAG):**\n{retrieved_chunks}\n\n"
        
        prompt += f"""**Instruções de Resposta:**
- Responda de forma completa e humanizada
- Base sua resposta nos dados reais do dataset
- Cite números específicos e métricas exatas
- Estruture a resposta de forma clara e organizada
- Finalize com "Se precisar de mais detalhes, é só perguntar!\""""
        
        return prompt
    
    def generate_data_types_prompt(self, dataset_context: DatasetContext) -> str:
        """
        Gera prompt especializado para responder sobre tipos de dados.
        Elimina interpretação semântica, foca apenas em dtypes técnicos.
        """
        return f"""**ANÁLISE PRECISA DE TIPOS DE DADOS**

Dataset: `{dataset_context.file_path}`
Total de colunas: {dataset_context.column_count}

**CLASSIFICAÇÃO BASEADA EXCLUSIVAMENTE EM DTYPES:**

**Colunas Numéricas ({len(dataset_context.numeric_columns)})**:
{chr(10).join(f'- `{col}` (dtype: {dataset_context.dtypes[col]})' for col in dataset_context.numeric_columns)}

**Colunas Categóricas ({len(dataset_context.categorical_columns)})**:
{chr(10).join(f'- `{col}` (dtype: {dataset_context.dtypes[col]})' for col in dataset_context.categorical_columns) if dataset_context.categorical_columns else '- Nenhuma coluna categórica identificada'}

**Colunas Temporais ({len(dataset_context.temporal_columns)})**:
{chr(10).join(f'- `{col}` (dtype: {dataset_context.dtypes[col]})' for col in dataset_context.temporal_columns) if dataset_context.temporal_columns else '- Nenhuma coluna temporal identificada'}

**Colunas Booleanas ({len(dataset_context.boolean_columns)})**:
{chr(10).join(f'- `{col}` (dtype: {dataset_context.dtypes[col]})' for col in dataset_context.boolean_columns) if dataset_context.boolean_columns else '- Nenhuma coluna booleana identificada'}

⚠️ **REGRA CRÍTICA**: 
- NÃO interprete semanticamente os nomes das colunas
- Uma coluna "Class" com dtype int64 é NUMÉRICA, não categórica
- Use APENAS a informação técnica dos dtypes pandas
- Se todos os dtypes são numéricos (int/float), diga que NÃO há categóricas

📋 **FORMATO DE RESPOSTA OBRIGATÓRIO**:

**Tipos de Dados do Dataset:**

- **Numéricas ({len(dataset_context.numeric_columns)})**: [lista todas as colunas]
- **Categóricas ({len(dataset_context.categorical_columns)})**: [lista todas ou "Nenhuma"]
- **Temporais ({len(dataset_context.temporal_columns)})**: [lista todas ou "Nenhuma"]
- **Booleanas ({len(dataset_context.boolean_columns)})**: [lista todas ou "Nenhuma"]

**Total**: {dataset_context.column_count} colunas no dataset."""


# Instância global para uso facilitado
_dynamic_prompt_generator = DynamicPromptGenerator()


def get_dynamic_prompt_generator() -> DynamicPromptGenerator:
    """Retorna instância global do gerador de prompts dinâmicos."""
    return _dynamic_prompt_generator
