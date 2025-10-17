"""
Classificador Inteligente de Intenção - Zero Hard-coding

Este módulo usa LLMs para classificar a intenção analítica do usuário
SEM keywords hardcoded, listas fixas ou lógica condicional.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 3.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import logging
from datetime import datetime


class AnalysisIntent(Enum):
    """
    Tipos de intenção analítica identificados semanticamente.
    
    IMPORTANTE: Esta enumeração é apenas para organização interna.
    A detecção é feita via LLM, NÃO por keywords.
    """
    STATISTICAL = "statistical"  # Estatísticas descritivas gerais
    FREQUENCY = "frequency"  # Análise de frequência/distribuição
    TEMPORAL = "temporal"  # Análise de séries temporais
    CLUSTERING = "clustering"  # Análise de agrupamentos
    CORRELATION = "correlation"  # Análise de correlação
    OUTLIERS = "outliers"  # Detecção de outliers/anomalias
    COMPARISON = "comparison"  # Comparação entre grupos/períodos
    CONVERSATIONAL = "conversational"  # Query sobre histórico/contexto
    VISUALIZATION = "visualization"  # Solicitação de gráficos
    GENERAL = "general"  # Query genérica/exploratória
    

@dataclass
class IntentClassificationResult:
    """
    Resultado da classificação de intenção.
    
    Attributes:
        primary_intent: Intenção principal detectada
        secondary_intents: Intenções secundárias (queries mistas)
        confidence: Confiança da classificação (0.0-1.0)
        requires_code_execution: Se requer execução de código Python
        requires_historical_context: Se requer consulta ao histórico
        suggested_modules: Módulos analíticos sugeridos
        reasoning: Explicação do raciocínio da LLM
        metadata: Metadados adicionais
    """
    primary_intent: AnalysisIntent
    secondary_intents: List[AnalysisIntent] = field(default_factory=list)
    confidence: float = 0.0
    requires_code_execution: bool = False
    requires_historical_context: bool = False
    suggested_modules: List[str] = field(default_factory=list)
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentClassifier:
    """
    Classificador inteligente de intenção usando LLM.
    
    PRINCÍPIOS:
    1. Zero keywords hardcoded
    2. Classificação puramente semântica via LLM
    3. Suporte a múltiplas intenções simultâneas
    4. Raciocínio explicável
    5. Flexível para novos tipos de análise
    
    Exemplo:
        >>> classifier = IntentClassifier(llm)
        >>> result = classifier.classify("Qual a dispersão dos dados?")
        >>> print(result.primary_intent)  # AnalysisIntent.STATISTICAL
        >>> print(result.reasoning)  # "Dispersão indica análise de variabilidade..."
    """
    
    def __init__(self, llm, logger: Optional[logging.Logger] = None):
        """
        Inicializa classificador com LLM.
        
        Args:
            llm: Instância de LLM (LangChain ChatOpenAI, ChatGoogleGenerativeAI, etc)
            logger: Logger opcional
        """
        self.llm = llm
        self.logger = logger or logging.getLogger(__name__)
        
        # System prompt para classificação inteligente
        self._system_prompt = self._build_classification_prompt()
    
    def _build_classification_prompt(self) -> str:
        """
        Constrói prompt para classificação semântica de intenção.
        
        Este prompt capacita a LLM a reconhecer QUALQUER tipo de análise
        sem depender de keywords fixas.
        """
        return """
Você é um classificador expert de intenções analíticas em EDA (Exploratory Data Analysis).

═══════════════════════════════════════════════════════════════════
CAPACIDADES COGNITIVAS
═══════════════════════════════════════════════════════════════════

Classifique perguntas do usuário nas seguintes categorias de análise:

1. **STATISTICAL** - Estatísticas descritivas gerais
   - Exemplos: média, mediana, moda, desvio padrão, variância, quartis
   - Sinônimos: tendência central, dispersão, espalhamento, variabilidade
   - Inclui: intervalo, amplitude, range, min/max, IQR
   
2. **FREQUENCY** - Análise de frequência e distribuição
   - Exemplos: valores mais/menos frequentes, contagens, proporções
   - Sinônimos: comum, raro, moda, distribuição, ocorrências
   - Inclui: histogramas de frequência, tabelas de contagem

3. **TEMPORAL** - Análise de séries temporais
   - Exemplos: tendências, sazonalidade, autocorrelação, anomalias temporais
   - Sinônimos: evolução, progressão, mudanças ao longo do tempo
   - Inclui: decomposição temporal, previsão, detecção de mudanças

4. **CLUSTERING** - Análise de agrupamentos
   - Exemplos: clusters, grupos, segmentos, padrões de agrupamento
   - Sinônimos: agrupamentos, segmentação, particionamento
   - Inclui: KMeans, DBSCAN, hierárquico, silhouette score

5. **CORRELATION** - Análise de correlação/associação
   - Exemplos: correlação, covariância, associação entre variáveis
   - Sinônimos: relação, dependência, vínculo entre variáveis
   - Inclui: matriz de correlação, correlação de Pearson/Spearman

6. **OUTLIERS** - Detecção de outliers e anomalias
   - Exemplos: valores atípicos, discrepantes, anormais
   - Sinônimos: outliers, extremos, anomalias, discrepantes
   - Inclui: Z-score, IQR method, Isolation Forest

7. **COMPARISON** - Comparação entre grupos/períodos
   - Exemplos: comparar grupos, antes vs depois, A vs B
   - Sinônimos: diferenças, mudanças, variações entre grupos
   - Inclui: testes estatísticos, comparações pareadas

8. **CONVERSATIONAL** - Query sobre histórico/contexto
   - Exemplos: "pergunta anterior", "o que falamos", "você disse"
   - Sinônimos: conversa prévia, histórico, mencionado antes
   - Inclui: referências a interações anteriores

9. **VISUALIZATION** - Solicitação de gráficos/visualizações
   - Exemplos: "mostre gráfico", "plote", "visualize"
   - Sinônimos: desenhe, exiba graficamente, crie visualização
   - Inclui: histogramas, scatter plots, boxplots, heatmaps

10. **GENERAL** - Query exploratória genérica
    - Exemplos: "explore os dados", "o que tem nos dados", "resumo geral"
    - Sinônimos: visão geral, overview, panorama dos dados
    - Inclui: perguntas abertas sem foco específico

═══════════════════════════════════════════════════════════════════
REGRAS DE CLASSIFICAÇÃO
═══════════════════════════════════════════════════════════════════

1. **Reconheça sinônimos automaticamente:**
   - "dispersão", "espalhamento", "variabilidade" → STATISTICAL
   - "amplitude", "range", "extensão" → STATISTICAL (intervalo)
   - "grupos", "segmentos", "partições" → CLUSTERING
   - "mais comum", "mais frequente", "que mais aparece" → FREQUENCY

2. **Detecte múltiplas intenções em queries mistas:**
   - "Mostre intervalo E variabilidade" → primary: STATISTICAL, secondary: []
   - "Compare clusters ao longo do tempo" → primary: COMPARISON, secondary: [CLUSTERING, TEMPORAL]
   - "Plote histograma de frequências" → primary: VISUALIZATION, secondary: [FREQUENCY]

3. **Identifique necessidade de execução de código:**
   - Queries que requerem cálculos não-triviais
   - Análises que não estão pré-computadas nos chunks
   - Exemplos: clustering, PCA, testes estatísticos

4. **Identifique necessidade de contexto histórico:**
   - Queries com "anterior", "antes", "você disse", "falamos"
   - Referências a interações prévias

═══════════════════════════════════════════════════════════════════
FORMATO DE RESPOSTA (JSON)
═══════════════════════════════════════════════════════════════════

Retorne SEMPRE um JSON válido com esta estrutura exata:

```json
{
    "primary_intent": "STATISTICAL|FREQUENCY|TEMPORAL|CLUSTERING|CORRELATION|OUTLIERS|COMPARISON|CONVERSATIONAL|VISUALIZATION|GENERAL",
    "secondary_intents": ["INTENT1", "INTENT2"],
    "confidence": 0.85,
    "requires_code_execution": true,
    "requires_historical_context": false,
    "suggested_modules": ["StatisticalAnalyzer", "FrequencyAnalyzer"],
    "reasoning": "A pergunta solicita análise de dispersão (sinônimo de variabilidade), que é uma estatística descritiva. Como 'dispersão' não está pré-computada, requer execução de código para calcular desvio padrão."
}
```

═══════════════════════════════════════════════════════════════════
EXEMPLOS DE CLASSIFICAÇÃO
═══════════════════════════════════════════════════════════════════

Pergunta: "Qual a dispersão dos dados?"
Resposta:
```json
{
    "primary_intent": "STATISTICAL",
    "secondary_intents": [],
    "confidence": 0.90,
    "requires_code_execution": true,
    "requires_historical_context": false,
    "suggested_modules": ["StatisticalAnalyzer"],
    "reasoning": "Dispersão é sinônimo de variabilidade, que engloba desvio padrão e variância. Como é uma estatística descritiva, classifica-se como STATISTICAL."
}
```

Pergunta: "Há grupos nos dados?"
Resposta:
```json
{
    "primary_intent": "CLUSTERING",
    "secondary_intents": [],
    "confidence": 0.95,
    "requires_code_execution": true,
    "requires_historical_context": false,
    "suggested_modules": ["ClusteringAnalyzer"],
    "reasoning": "A pergunta questiona a existência de agrupamentos (clusters) nos dados, o que requer execução de algoritmo de clustering (ex: KMeans)."
}
```

Pergunta: "E a variância?"
Resposta:
```json
{
    "primary_intent": "CONVERSATIONAL",
    "secondary_intents": ["STATISTICAL"],
    "confidence": 0.80,
    "requires_code_execution": false,
    "requires_historical_context": true,
    "suggested_modules": ["StatisticalAnalyzer"],
    "reasoning": "A pergunta usa 'E a', indicando continuação de conversa prévia. Requer consultar histórico para saber de qual variável. Secundariamente, é uma estatística descritiva."
}
```

Pergunta: "Plote histograma das variáveis numéricas"
Resposta:
```json
{
    "primary_intent": "VISUALIZATION",
    "secondary_intents": ["FREQUENCY"],
    "confidence": 0.95,
    "requires_code_execution": true,
    "requires_historical_context": false,
    "suggested_modules": ["VisualizationAnalyzer", "FrequencyAnalyzer"],
    "reasoning": "A pergunta solicita explicitamente visualização (histograma). Histogramas mostram distribuição de frequências, então FREQUENCY é intenção secundária."
}
```

Pergunta: "Compare a variabilidade entre clusters"
Resposta:
```json
{
    "primary_intent": "COMPARISON",
    "secondary_intents": ["CLUSTERING", "STATISTICAL"],
    "confidence": 0.85,
    "requires_code_execution": true,
    "requires_historical_context": false,
    "suggested_modules": ["ClusteringAnalyzer", "StatisticalAnalyzer"],
    "reasoning": "A pergunta pede comparação (COMPARISON) de variabilidade (STATISTICAL) entre clusters (CLUSTERING). Query mista que requer múltiplos módulos."
}
```

═══════════════════════════════════════════════════════════════════

Agora classifique a pergunta do usuário de forma inteligente e semântica.
"""
    
    def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> IntentClassificationResult:
        """
        Classifica intenção da query usando LLM.
        
        Args:
            query: Pergunta do usuário
            context: Contexto adicional (opcional)
            
        Returns:
            Resultado da classificação com intenção, confiança e raciocínio
        """
        try:
            # Preparar prompt
            from langchain.schema import HumanMessage, SystemMessage
            
            user_prompt = f"Pergunta do usuário: {query}"
            
            if context:
                user_prompt += f"\n\nContexto adicional: {json.dumps(context, ensure_ascii=False)}"
            
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Invocar LLM
            self.logger.info(f"Classificando intenção da query: {query[:80]}...")
            response = self.llm.invoke(messages)
            
            # Parse JSON
            response_text = response.content.strip()
            
            # Remover markdown code blocks se presentes
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            classification = json.loads(response_text)
            
            # Construir resultado
            result = IntentClassificationResult(
                primary_intent=AnalysisIntent[classification["primary_intent"]],
                secondary_intents=[
                    AnalysisIntent[intent] for intent in classification.get("secondary_intents", [])
                ],
                confidence=classification.get("confidence", 0.0),
                requires_code_execution=classification.get("requires_code_execution", False),
                requires_historical_context=classification.get("requires_historical_context", False),
                suggested_modules=classification.get("suggested_modules", []),
                reasoning=classification.get("reasoning", ""),
                metadata={
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "llm_response": response_text
                }
            )
            
            self.logger.info(
                f"✅ Intenção classificada: {result.primary_intent.value} "
                f"(confiança: {result.confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao classificar intenção: {e}", exc_info=True)
            
            # Fallback: classificação genérica
            return IntentClassificationResult(
                primary_intent=AnalysisIntent.GENERAL,
                confidence=0.0,
                reasoning=f"Erro na classificação: {str(e)}. Usando fallback genérico.",
                metadata={"error": str(e)}
            )
    
    def explain_classification(self, result: IntentClassificationResult) -> str:
        """
        Gera explicação humanizada da classificação.
        
        Args:
            result: Resultado da classificação
            
        Returns:
            Explicação formatada em texto
        """
        explanation = f"## Classificação de Intenção\n\n"
        explanation += f"**Intenção Principal:** {result.primary_intent.value}\n"
        explanation += f"**Confiança:** {result.confidence:.1%}\n\n"
        
        if result.secondary_intents:
            intents_str = ", ".join([i.value for i in result.secondary_intents])
            explanation += f"**Intenções Secundárias:** {intents_str}\n\n"
        
        explanation += f"**Raciocínio:** {result.reasoning}\n\n"
        
        if result.requires_code_execution:
            explanation += "⚠️ Esta análise requer execução de código Python.\n"
        
        if result.requires_historical_context:
            explanation += "📜 Esta análise requer consulta ao histórico de conversa.\n"
        
        if result.suggested_modules:
            modules_str = ", ".join(result.suggested_modules)
            explanation += f"\n**Módulos Sugeridos:** {modules_str}\n"
        
        return explanation
