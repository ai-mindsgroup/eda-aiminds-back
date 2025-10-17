"""
Orquestrador de Análises - Coordenação Modular e Inteligente

Este módulo coordena a execução de múltiplos analisadores especializados
de forma inteligente, baseando-se na classificação de intenção via LLM.

Autor: EDA AI Minds Team
Data: 2025-10-16
Versão: 3.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import pandas as pd
import logging
from datetime import datetime

from analysis.intent_classifier import IntentClassifier, AnalysisIntent, IntentClassificationResult
from analysis.statistical_analyzer import StatisticalAnalyzer, StatisticalAnalysisResult
from analysis.frequency_analyzer import FrequencyAnalyzer, FrequencyAnalysisResult
from analysis.temporal_analyzer import TemporalAnalyzer, TemporalAnalysisResult
from analysis.clustering_analyzer import ClusteringAnalyzer, ClusteringAnalysisResult


@dataclass
class OrchestrationResult:
    """
    Resultado da orquestração de análises.
    
    Attributes:
        intent_classification: Classificação de intenção original
        analysis_results: Resultados de cada análise executada
        combined_interpretation: Interpretação combinada
        execution_order: Ordem de execução dos módulos
        metadata: Metadados de orquestração
    """
    intent_classification: IntentClassificationResult
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    combined_interpretation: str = ""
    execution_order: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Gera relatório consolidado em Markdown."""
        md = "# Relatório de Análise Integrada\n\n"
        
        # Intenção detectada
        md += "## Intenção Detectada\n\n"
        md += f"**Análise principal:** {self.intent_classification.primary_intent.value}\n"
        if self.intent_classification.secondary_intents:
            intents = ", ".join([i.value for i in self.intent_classification.secondary_intents])
            md += f"**Análises complementares:** {intents}\n"
        md += f"**Confiança:** {self.intent_classification.confidence:.1%}\n\n"
        md += f"*{self.intent_classification.reasoning}*\n\n"
        
        md += "---\n\n"
        
        # Resultados de cada análise
        for analyzer_name, result in self.analysis_results.items():
            if hasattr(result, 'to_markdown'):
                md += result.to_markdown() + "\n\n---\n\n"
        
        # Interpretação combinada
        if self.combined_interpretation:
            md += "## Síntese e Conclusões\n\n"
            md += self.combined_interpretation + "\n\n"
        
        # Metadados
        md += "## Metadados de Execução\n\n"
        md += f"- **Módulos executados:** {', '.join(self.execution_order)}\n"
        md += f"- **Tempo total:** {self.metadata.get('total_time_ms', 0):.0f}ms\n"
        md += f"- **Timestamp:** {self.metadata.get('timestamp', 'N/A')}\n"
        
        return md


class AnalysisOrchestrator:
    """
    Orquestrador inteligente de análises modulares.
    
    PRINCÍPIOS:
    1. Classificação de intenção via LLM (zero hard-coding)
    2. Execução condicional de módulos especializados
    3. Combinação inteligente de resultados
    4. Extensível para novos tipos de análise
    
    Exemplo:
        >>> orchestrator = AnalysisOrchestrator(llm)
        >>> result = orchestrator.orchestrate("Qual a dispersão dos dados?", df)
        >>> print(result.to_markdown())
    """
    
    def __init__(self, llm, logger: Optional[logging.Logger] = None):
        """
        Inicializa orquestrador.
        
        Args:
            llm: Instância de LLM para classificação de intenção
            logger: Logger opcional
        """
        self.llm = llm
        self.logger = logger or logging.getLogger(__name__)
        
        # Inicializar classificador e analisadores
        self.intent_classifier = IntentClassifier(llm, logger)
        self.statistical_analyzer = StatisticalAnalyzer(logger)
        self.frequency_analyzer = FrequencyAnalyzer(logger)
        self.temporal_analyzer = TemporalAnalyzer(logger)
        self.clustering_analyzer = ClusteringAnalyzer(logger)
        
        # Mapeamento de intenções para analisadores
        self._intent_to_analyzer = {
            AnalysisIntent.STATISTICAL: self._run_statistical_analysis,
            AnalysisIntent.FREQUENCY: self._run_frequency_analysis,
            AnalysisIntent.TEMPORAL: self._run_temporal_analysis,
            AnalysisIntent.CLUSTERING: self._run_clustering_analysis,
            AnalysisIntent.GENERAL: self._run_general_analysis
        }
        
        self.logger.info("✅ AnalysisOrchestrator inicializado")
    
    def orchestrate(
        self,
        query: str,
        df: pd.DataFrame,
        context: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """
        Orquestra execução de análises baseada na query do usuário.
        
        FLUXO:
        1. Classifica intenção via LLM
        2. Identifica módulos necessários
        3. Executa análises em ordem apropriada
        4. Combina resultados
        5. Gera interpretação integrada
        
        Args:
            query: Query do usuário
            df: DataFrame a analisar
            context: Contexto adicional
            
        Returns:
            Resultado consolidado de todas análises
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🎯 Orquestrando análise para query: {query[:80]}...")
            
            # ═══════════════════════════════════════════════════════════
            # 1. CLASSIFICAR INTENÇÃO (LLM decide tudo)
            # ═══════════════════════════════════════════════════════════
            intent_result = self.intent_classifier.classify(query, context)
            
            self.logger.info(
                f"Intenção classificada: {intent_result.primary_intent.value} "
                f"(confiança: {intent_result.confidence:.2f})"
            )
            
            # ═══════════════════════════════════════════════════════════
            # 2. IDENTIFICAR MÓDULOS NECESSÁRIOS
            # ═══════════════════════════════════════════════════════════
            intents_to_execute = [intent_result.primary_intent]
            intents_to_execute.extend(intent_result.secondary_intents)
            
            # ═══════════════════════════════════════════════════════════
            # 3. EXECUTAR ANÁLISES
            # ═══════════════════════════════════════════════════════════
            result = OrchestrationResult(intent_classification=intent_result)
            
            for intent in intents_to_execute:
                analyzer_func = self._intent_to_analyzer.get(intent)
                
                if analyzer_func:
                    try:
                        self.logger.info(f"Executando análise: {intent.value}")
                        
                        analysis_result = analyzer_func(df, query, context)
                        
                        if analysis_result:
                            analyzer_name = intent.value
                            result.analysis_results[analyzer_name] = analysis_result
                            result.execution_order.append(analyzer_name)
                            
                            self.logger.info(f"✅ Análise {intent.value} concluída")
                    
                    except Exception as e:
                        self.logger.error(f"Erro na análise {intent.value}: {e}", exc_info=True)
                        # Continua para próximas análises
            
            # ═══════════════════════════════════════════════════════════
            # 4. COMBINAR RESULTADOS E GERAR INTERPRETAÇÃO INTEGRADA
            # ═══════════════════════════════════════════════════════════
            result.combined_interpretation = self._generate_combined_interpretation(
                query, result
            )
            
            # ═══════════════════════════════════════════════════════════
            # 5. METADADOS
            # ═══════════════════════════════════════════════════════════
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result.metadata = {
                "total_time_ms": total_time,
                "modules_executed": len(result.execution_order),
                "timestamp": datetime.now().isoformat(),
                "dataframe_shape": df.shape
            }
            
            self.logger.info(
                f"🎯 Orquestração concluída: {len(result.execution_order)} módulos "
                f"executados em {total_time:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na orquestração: {e}", exc_info=True)
            raise
    
    def _run_statistical_analysis(
        self,
        df: pd.DataFrame,
        query: str,
        context: Optional[Dict] = None
    ) -> StatisticalAnalysisResult:
        """Executa análise estatística."""
        return self.statistical_analyzer.analyze(df)
    
    def _run_frequency_analysis(
        self,
        df: pd.DataFrame,
        query: str,
        context: Optional[Dict] = None
    ) -> FrequencyAnalysisResult:
        """Executa análise de frequência."""
        return self.frequency_analyzer.analyze(df)
    
    def _run_temporal_analysis(
        self,
        df: pd.DataFrame,
        query: str,
        context: Optional[Dict] = None
    ) -> Optional[TemporalAnalysisResult]:
        """Executa análise temporal."""
        # Detectar colunas temporais
        from analysis.temporal_detection import TemporalColumnDetector
        
        detector = TemporalColumnDetector()
        detection_results = detector.detect(df)
        temporal_cols = detector.get_detected_columns(detection_results)
        
        if not temporal_cols:
            self.logger.warning("Nenhuma coluna temporal detectada")
            return None
        
        # Analisar primeira coluna temporal encontrada
        return self.temporal_analyzer.analyze(df, temporal_cols[0])
    
    def _run_clustering_analysis(
        self,
        df: pd.DataFrame,
        query: str,
        context: Optional[Dict] = None
    ) -> ClusteringAnalysisResult:
        """Executa análise de clustering."""
        # Usar KMeans com 3 clusters como padrão
        # TODO: Usar LLM para extrair parâmetros da query
        return self.clustering_analyzer.analyze(df, n_clusters=3)
    
    def _run_general_analysis(
        self,
        df: pd.DataFrame,
        query: str,
        context: Optional[Dict] = None
    ) -> StatisticalAnalysisResult:
        """Executa análise geral (fallback)."""
        return self.statistical_analyzer.analyze(df)
    
    def _generate_combined_interpretation(
        self,
        query: str,
        result: OrchestrationResult
    ) -> str:
        """
        Gera interpretação combinada de múltiplas análises via LLM.
        
        Args:
            query: Query original do usuário
            result: Resultado da orquestração
            
        Returns:
            Interpretação integrada
        """
        try:
            # Extrair interpretações individuais
            interpretations = []
            for analyzer_name, analysis_result in result.analysis_results.items():
                if hasattr(analysis_result, 'interpretation'):
                    interp = analysis_result.interpretation
                    if interp:
                        interpretations.append(f"**{analyzer_name}**: {interp}")
            
            if not interpretations:
                return "Análise concluída. Consulte seções acima para detalhes."
            
            # Usar LLM para sintetizar
            from langchain.schema import HumanMessage, SystemMessage
            
            system_prompt = """
Você é um agente EDA expert em síntese de análises.
Sua tarefa é combinar múltiplas interpretações analíticas em uma síntese coerente e contextual.

Regras:
1. Mantenha foco na pergunta do usuário
2. Destaque insights mais relevantes
3. Identifique padrões cruzados entre análises
4. Seja conciso (máximo 3 parágrafos)
5. Sugira próximos passos integrados
"""
            
            user_prompt = f"""
Pergunta do usuário: {query}

Interpretações analíticas:
{chr(10).join(interpretations)}

Sintetize essas interpretações de forma coerente e contextual.
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar interpretação combinada: {e}")
            return "Análise concluída. Consulte seções acima para detalhes."
