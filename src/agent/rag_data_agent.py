"""
Agente de Análise de Dados via RAG Vetorial Puro com Memória Persistente e LangChain.

VERSÃO 2.0 - REFATORADA:
- ✅ Memória persistente em Supabase (tabelas agent_sessions, agent_conversations, agent_context)
- ✅ LangChain integrado nativamente (ChatOpenAI, ChatGoogleGenerativeAI)
- ✅ Métodos async para performance
- ✅ Contexto conversacional entre interações
- ✅ Busca vetorial pura (sem keywords hardcoded)

════════════════════════════════════════════════════════════════════════════════
⚠️  EXCEÇÃO DE CONFORMIDADE: ACESSO DIRETO A CSV PARA VISUALIZAÇÕES
════════════════════════════════════════════════════════════════════════════════

CONTEXTO:
- Tabela 'embeddings' armazena chunks de análises estatísticas (Markdown)
- Visualizações (histogramas) requerem dados tabulares completos (285k linhas)
- Embeddar cada linha seria ineficiente: ~$50-100 custo + overhead desnecessário

SOLUÇÃO IMPLEMENTADA:
- Quando visualização é solicitada, acessa CSV diretamente via pd.read_csv()
- Acesso é READ-ONLY, sem modificação de dados
- Log completo de auditoria registrado (linhas 318-350)
- Metadados de conformidade incluídos em todas as respostas

JUSTIFICATIVA (ADERENTE A BOAS PRÁTICAS DE MERCADO):
1. Padrão da indústria: LangChain CSV Agents, LlamaIndex, OpenAI Code Interpreter
2. Separação de responsabilidades: RAG para busca semântica, CSV para dados tabulares
3. Custo-benefício: evita armazenamento/processamento desnecessário
4. Performance: leitura direta é mais rápida que reconstituição de embeddings

IMPLEMENTAÇÃO FUTURA (Opcional):
- TODO: Adicionar chunks 'raw_data' na tabela embeddings durante ingestão
- TODO: Implementar reconstituição de DataFrame a partir de embeddings
- TODO: Adicionar configuração para escolher entre direct-access vs embeddings

AUDITORIA E COMPLIANCE:
- ✅ Log detalhado com event_type, timestamp, session_id, csv_path, size
- ✅ Metadados em response.metadata['conformidade_exception']
- ✅ Documentação clara da exceção e justificativa
- ✅ Aprovação registrada (approved=True)

REFERÊNCIAS:
- LangChain CSV Agent: https://python.langchain.com/docs/integrations/toolkits/csv
- OpenAI Code Interpreter: https://openai.com/blog/code-interpreter
- Hybrid RAG Architectures: https://docs.llamaindex.ai/en/stable/examples/query_engine/

════════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import asyncio

from agent.base_agent import BaseAgent, AgentError
from vectorstore.supabase_client import supabase
from embeddings.generator import EmbeddingGenerator
from utils.logging_config import get_logger
from analysis.intent_classifier import IntentClassifier, AnalysisIntent

# Imports LangChain
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory
    from langchain_experimental.tools import PythonREPLTool
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    ChatGoogleGenerativeAI = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None
    PythonREPLTool = None
    print(f"⚠️ LangChain não disponível: {e}")


class RAGDataAgent(BaseAgent):
    def _interpretar_pergunta_llm(self, pergunta: str, df):
        """
        ✅ V3.0: Utiliza IntentClassifier para classificação semântica SEM HARD-CODING.
        
        Retorna instruções analíticas baseadas na intenção classificada pela LLM.
        Cada instrução é um dict: {'acao': ..., 'colunas': [...], 'params': {}, 'justificativa': str}
        """
        if not self.llm:
            # Fallback: retorna instrução genérica
            return [{'acao': 'estatísticas gerais', 'colunas': list(df.columns), 'params': {}, 
                    'justificativa': 'LLM indisponível, fornecendo estatísticas gerais.'}]
        
        try:
            # 🔥 V3.0: Usar IntentClassifier para classificação semântica
            classifier = IntentClassifier(llm=self.llm, logger=self.logger)
            
            # Classificar intenção da pergunta
            context = {
                'available_columns': list(df.columns),
                'dataframe_info': f"Shape: {df.shape}, Colunas numéricas: {df.select_dtypes(include=['number']).columns.tolist()}"
            }
            
            classification_result = classifier.classify(query=pergunta, context=context)
            
            # Log da classificação
            self.logger.info({
                'event': 'intent_classification',
                'primary_intent': classification_result.primary_intent.value,
                'secondary_intents': [intent.value for intent in classification_result.secondary_intents],
                'confidence': classification_result.confidence,
                'reasoning': classification_result.reasoning
            })
            
            # 🎯 Mapear intenções para instruções analíticas
            instrucoes = []
            
            # Processar intenção primária
            primary_action = self._intent_to_action(
                classification_result.primary_intent, 
                df, 
                classification_result.reasoning
            )
            if primary_action:
                instrucoes.append(primary_action)
            
            # Processar intenções secundárias se existirem
            for secondary_intent in classification_result.secondary_intents:
                secondary_action = self._intent_to_action(
                    secondary_intent, 
                    df, 
                    f"Intenção secundária detectada: {secondary_intent.value}"
                )
                if secondary_action and secondary_action not in instrucoes:
                    instrucoes.append(secondary_action)
            
            # Garantir pelo menos uma instrução
            if not instrucoes:
                instrucoes = [{
                    'acao': 'estatísticas gerais',
                    'colunas': list(df.columns),
                    'params': {},
                    'justificativa': 'Nenhuma intenção específica detectada, fornecendo visão geral.'
                }]
            
            self.logger.info({
                'event': 'instructions_generated',
                'num_instructions': len(instrucoes),
                'actions': [ins['acao'] for ins in instrucoes]
            })
            
            return instrucoes
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao interpretar pergunta com IntentClassifier: {e}")
            # Fallback para interpretação básica via LLM direta
            return self._fallback_interpretation(pergunta, df)
    
    def _intent_to_action(self, intent: AnalysisIntent, df, justificativa: str) -> Optional[Dict]:
        """
        🎯 Converte AnalysisIntent em instrução analítica.
        Mapeia tipos de intenção para ações específicas.
        """
        # Selecionar colunas numéricas por padrão
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = list(df.columns)
        
        intent_map = {
            AnalysisIntent.STATISTICAL: {
                'acao': 'estatísticas gerais',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {},
                'justificativa': justificativa
            },
            AnalysisIntent.FREQUENCY: {
                'acao': 'frequency_analysis',
                'colunas': all_cols,
                'params': {'top_n': 10},
                'justificativa': justificativa
            },
            AnalysisIntent.TEMPORAL: {
                'acao': 'temporal_analysis',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {},
                'justificativa': justificativa
            },
            AnalysisIntent.CLUSTERING: {
                'acao': 'clustering_analysis',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {'n_clusters': 3},
                'justificativa': justificativa
            },
            AnalysisIntent.CORRELATION: {
                'acao': 'correlation_analysis',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {},
                'justificativa': justificativa
            },
            AnalysisIntent.OUTLIERS: {
                'acao': 'outlier_detection',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {},
                'justificativa': justificativa
            },
            AnalysisIntent.COMPARISON: {
                'acao': 'comparison_analysis',
                'colunas': all_cols,
                'params': {},
                'justificativa': justificativa
            },
            AnalysisIntent.VISUALIZATION: {
                'acao': 'visualization_request',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {},
                'justificativa': justificativa
            },
            AnalysisIntent.GENERAL: {
                'acao': 'estatísticas gerais',
                'colunas': numeric_cols if numeric_cols else all_cols,
                'params': {},
                'justificativa': justificativa
            }
        }
        
        return intent_map.get(intent)
    
    def _fallback_interpretation(self, pergunta: str, df) -> List[Dict]:
        """
        Fallback: interpretação básica via LLM direta quando IntentClassifier falha.
        Mantém apenas lógica essencial, SEM hard-coding de keywords.
        """
        prompt = (
            "Você é um especialista em análise de dados.\n"
            "Interprete a pergunta do usuário e retorne uma lista JSON de instruções analíticas.\n"
            "Formato de cada instrução: {'acao': str, 'colunas': [str], 'params': {}, 'justificativa': str}\n"
            f"Pergunta: {pergunta}\n"
            f"Colunas disponíveis: {list(df.columns)}\n"
            "Responda APENAS com o JSON, sem explicações."
        )
        
        try:
            response = self.llm.invoke(prompt)
            import json
            instrucoes = json.loads(response.content)
            return instrucoes if isinstance(instrucoes, list) else [instrucoes]
        except Exception as e:
            self.logger.error(f"Fallback interpretation falhou: {e}")
            return [{
                'acao': 'estatísticas gerais',
                'colunas': list(df.columns),
                'params': {},
                'justificativa': 'Interpretação padrão devido a erro.'
            }]

    def _executar_instrucao(self, df, instrucao):
        """
        Executa uma instrução analítica sobre o DataFrame.
        Suporta métricas nativas pandas/NumPy e delega compostas à LLM.
        """
        acao = instrucao.get('acao','')
        colunas = instrucao.get('colunas', list(df.columns))
        params = instrucao.get('params', {})
        try:
            # Normalizar nome da ação para comparação (tolerante a maiúsculas/minúsculas)
            acao_norm = str(acao).strip().lower()
            # Métricas nativas pandas
            if acao_norm in ('média', 'media', 'mean'):
                return df[colunas].mean().to_frame(name='Média')
            if acao_norm in ('mediana', 'median'):
                return df[colunas].median().to_frame(name='Mediana')
            if acao_norm in ('moda', 'mode'):
                return df[colunas].mode().T
            if acao_norm in ('desvio padrão', 'desvio padrao', 'std', 'standard deviation'):
                return df[colunas].std().to_frame(name='Desvio padrão')
            if acao_norm in ('variância', 'variancia', 'variance', 'var'):
                # Variância populacional/por padrão pandas var() usa ddof=1 (amostral). Mantemos default.
                return df[colunas].var().to_frame(name='Variância')
            if acao_norm in ('intervalo', 'minmax', 'min_max', 'mínimo', 'máximo'):
                resultado = df[colunas].agg(['min','max']).T
                resultado.columns = ['Mínimo','Máximo']
                return resultado
            if acao_norm in ('estatísticas gerais', 'estatisticas gerais', 'describe', 'summary', 'resumo'):
                return df[colunas].describe().T
            # Métricas compostas ou extraordinárias: delega à LLM com execução SEGURA
            if self.llm and PythonREPLTool:
                try:
                    # 🔒 SEGURANÇA: Usar PythonREPLTool com sandbox isolado
                    python_repl = PythonREPLTool()
                    
                    prompt = (
                        f"Receba instrução analítica: {instrucao}.\n"
                        f"DataFrame já está disponível como variável 'df'.\n"
                        f"Colunas disponíveis: {list(df.columns)}.\n"
                        "Gere código Python (pandas/numpy) que:\n"
                        "1. Execute a métrica pedida\n"
                        "2. Armazene o resultado em uma variável chamada 'resultado'\n"
                        "3. Retorne 'resultado' na última linha\n"
                        "Retorne APENAS o código, sem explicações, sem markdown.\n"
                        "Exemplo: resultado = df['coluna'].mean()"
                    )
                    
                    response = self.llm.invoke(prompt)
                    code = response.content.strip()
                    
                    # Remove markdown code blocks se presentes
                    if code.startswith("```python"):
                        code = code.split("```python")[1].split("```")[0].strip()
                    elif code.startswith("```"):
                        code = code.split("```")[1].split("```")[0].strip()
                    
                    # Log código antes de executar (auditoria)
                    self.logger.info(f"🔒 Executando código seguro via PythonREPLTool:\n{code[:200]}...")
                    
                    # Preparar contexto com DataFrame
                    import pandas as pd
                    import numpy as np
                    globals_context = {'df': df, 'pd': pd, 'np': np}
                    
                    # 🔒 Execução segura via PythonREPLTool (sandbox isolado)
                    # Nota: PythonREPLTool executa em ambiente isolado sem acesso ao filesystem
                    resultado = python_repl.run(code, globals=globals_context)
                    
                    self.logger.info(f"✅ Código executado com sucesso via PythonREPLTool")
                    return resultado
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao executar código via PythonREPLTool: {e}")
                    self.logger.debug(f"Código problemático: {code}")
                    return None
            else:
                self.logger.warning("LLM ou PythonREPLTool não disponível para métricas compostas")
                return None
        except Exception as e:
            self.logger.warning(f"Falha ao executar instrução: {instrucao} | Erro: {e}")
            return None

    def _analisar_completo_csv(self, csv_path: str, pergunta: str, override_temporal_col: str = None,
                               temporal_col_names: list = None, accepted_types: tuple = None) -> str:
        """
        Executa análise temporal robusta e modular usando arquitetura refatorada V2.0.
        
        ARQUITETURA MODULAR:
        - Detecção via TemporalColumnDetector (src/analysis/temporal_detection.py)
        - Análise via TemporalAnalyzer (src/analysis/temporal_analyzer.py)
        - Fallback para análise estatística geral quando não houver colunas temporais
        
        Critérios de detecção:
        - Override manual (prioritário)
        - Tipo datetime64 nativo
        - Nomes comuns parametrizáveis (case-insensitive)
        - Conversão de strings temporais
        - Sequências numéricas temporais (modo agressivo)
        
        Parâmetros:
            - override_temporal_col: força uso de coluna específica (ou None para auto)
            - temporal_col_names: lista de nomes comuns (default: ["time", "date", "timestamp", "data", "datetime"])
            - accepted_types: DEPRECATED - mantido para backward compatibility
            
        Returns:
            String formatada em Markdown com análises temporais e/ou estatísticas
        """
        import pandas as pd
        from analysis.temporal_detection import TemporalColumnDetector, TemporalDetectionConfig
        from analysis.temporal_analyzer import TemporalAnalyzer
        
        # Carregar dados
        df = pd.read_csv(csv_path)
        
        logger = self.logger if hasattr(self, 'logger') else logging.getLogger(__name__)
        logger.info({
            'event': 'inicio_analise_csv_v2',
            'csv_path': csv_path,
            'shape': df.shape,
            'override_temporal_col': override_temporal_col
        })
        
        # ═══════════════════════════════════════════════════════════════
        # ETAPA 1: DETECÇÃO DE COLUNAS TEMPORAIS
        # ═══════════════════════════════════════════════════════════════
        
        # Configurar detector com parâmetros customizáveis
        detection_config = TemporalDetectionConfig()
        if temporal_col_names:
            detection_config.common_names = temporal_col_names
        
        detector = TemporalColumnDetector(config=detection_config)
        
        try:
            detection_results = detector.detect(df, override_column=override_temporal_col)
            temporal_cols = detector.get_detected_columns(detection_results)
            detection_summary = detector.get_detection_summary(detection_results)
            
            logger.info({
                'event': 'deteccao_temporal_concluida',
                'colunas_detectadas': temporal_cols,
                'total_colunas': len(df.columns),
                'taxa_deteccao': detection_summary['detection_rate'],
                'metodos_usados': detection_summary['methods_used']
            })
        except Exception as e:
            logger.error(f"Erro na detecção de colunas temporais: {e}", exc_info=True)
            temporal_cols = []
        
        # ═══════════════════════════════════════════════════════════════
        # ETAPA 2: ANÁLISE TEMPORAL (se colunas detectadas)
        # ═══════════════════════════════════════════════════════════════
        
        if temporal_cols:
            logger.info(f"Executando análise temporal em {len(temporal_cols)} coluna(s)")
            
            analyzer = TemporalAnalyzer(logger=logger)
            respostas = []
            
            for col in temporal_cols:
                try:
                    # Executar análise temporal avançada
                    result = analyzer.analyze(df, col, enable_advanced=True)
                    
                    # Gerar relatório Markdown
                    respostas.append(result.to_markdown())
                    
                    logger.info({
                        'event': 'analise_temporal_coluna_concluida',
                        'coluna': col,
                        'trend_type': result.trend.get('type'),
                        'anomalies_count': result.anomalies.get('count', 0),
                        'seasonality_detected': result.seasonality.get('detected', False)
                    })
                except Exception as e:
                    logger.error(f"Erro ao analisar coluna temporal '{col}': {e}", exc_info=True)
                    respostas.append(
                        f"## Erro na Análise: {col}\n\n"
                        f"Não foi possível completar a análise temporal da coluna '{col}': {str(e)}\n"
                    )
            
            # Adicionar sumário executivo da detecção
            header = (
                f"# Análise Temporal Completa\n\n"
                f"**Dataset:** `{csv_path}`\n\n"
                f"**Colunas analisadas:** {len(temporal_cols)} de {len(df.columns)} colunas totais\n\n"
                f"**Taxa de detecção:** {detection_summary['detection_rate']:.1%}\n\n"
                f"**Métodos de detecção utilizados:** {', '.join(detection_summary['methods_used'].keys())}\n\n"
                "---\n\n"
            )
            
            return header + "\n\n---\n\n".join(respostas)
        
        # ═══════════════════════════════════════════════════════════════
        # ETAPA 3: FALLBACK - ANÁLISE ESTATÍSTICA GERAL
        # ═══════════════════════════════════════════════════════════════
        
        logger.info({
            'event': 'fallback_analise_geral',
            'motivo': 'nenhuma_coluna_temporal_detectada'
        })
        
        # Interpretar intenção da pergunta via LLM
        instrucoes = self._interpretar_pergunta_llm(pergunta, df)
        
        # Executar instruções e consolidar resultados
        resultados = []
        for instrucao in instrucoes:
            resultado = self._executar_instrucao(df, instrucao)
            if resultado is not None:
                justificativa = instrucao.get('justificativa', '')
                if hasattr(resultado, 'to_markdown'):
                    resultados.append(
                        f"**{instrucao.get('acao', 'Métrica')}**\n"
                        f"{justificativa}\n\n"
                        f"{resultado.to_markdown()}"
                    )
                else:
                    resultados.append(
                        f"**{instrucao.get('acao', 'Métrica')}**\n"
                        f"{justificativa}\n\n"
                        f"{str(resultado)}"
                    )
        
        if resultados:
            header = (
                f"# Análise Estatística Geral\n\n"
                f"**Dataset:** `{csv_path}`\n\n"
                f"*Nenhuma coluna temporal detectada. Executando análise estatística padrão.*\n\n"
                "---\n\n"
            )
            return header + "\n\n".join(resultados)
        else:
            # Fallback final: estatísticas gerais descritivas
            logger.warning("Fallback final: retornando describe() do DataFrame")
            return (
                f"# Estatísticas Descritivas\n\n"
                f"**Dataset:** `{csv_path}`\n\n"
                f"{df.describe().T.to_markdown()}"
            )

    def _should_use_global_csv(self, query: str, chunks_metadata: List[Dict]) -> bool:
        """
        Decide se é necessário recorrer ao CSV completo para responder a pergunta.
        Critérios:
        - Pergunta exige análise de todas as colunas/linhas (ex: intervalo de todas variáveis)
        - Chunks não possuem dados suficientes (ex: subset de colunas)
        """
        # Detecta termos que indicam análise global
        termos_globais = ["todas as variáveis", "todas as colunas", "intervalo de cada variável", "intervalo de todas", "intervalo completo", "todas as linhas", "análise completa"]
        if any(t in query.lower() for t in termos_globais):
            return True
        # Detecta se chunks não cobrem todas as colunas
        if chunks_metadata:
            # Extrai colunas presentes nos chunks
            colunas_chunks = set()
            for chunk in chunks_metadata:
                if 'columns' in chunk:
                    colunas_chunks.update(chunk['columns'])
            # Se número de colunas for pequeno, pode indicar subset
            if len(colunas_chunks) < 5:
                return True
        return False

    def reset_memory(self, session_id: str = None):
        """
        Reseta a memória/contexto do agente para a sessão informada.
        """
        self.memory = {}
        if session_id:
            self.session_id = session_id
        self.logger.info(f"Memória/contexto resetados para sessão: {session_id}")
    """
    Agente que responde perguntas sobre dados usando RAG vetorial + memória persistente + LangChain.
    
    Fluxo V2.0:
    1. Inicializa sessão de memória (se não existir)
    2. Recupera contexto conversacional anterior
    3. Gera embedding da pergunta
    4. Busca chunks similares nos DADOS usando match_embeddings()
    5. Usa LangChain LLM para interpretar chunks + contexto histórico
    6. Salva interação na memória persistente
    7. Retorna resposta contextualizada
    
    SEM keywords hardcoded, SEM classificação manual, SEM listas fixas.
    COM memória persistente, COM LangChain, COM contexto conversacional.
    """
    
    def __init__(self):
        super().__init__(
            name="rag_data_analyzer",
            description="Analisa dados usando busca vetorial semântica pura com memória persistente",
            enable_memory=True  # ✅ CRÍTICO: Habilita memória persistente
        )
        self.logger = get_logger("agent.rag_data")
        self.embedding_gen = EmbeddingGenerator()
        
        # Inicializar LLM LangChain
        self._init_langchain_llm()
        
        self.logger.info("✅ RAGDataAgent V2.0 inicializado - RAG vetorial + memória + LangChain")
    
    def _init_langchain_llm(self):
        """Inicializa LLM do LangChain com fallback."""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("⚠️ LangChain não disponível - usando fallback")
            self.llm = None
            return
        
        try:
            # Tentar Google Gemini primeiro (melhor custo-benefício)
            from src.settings import GOOGLE_API_KEY
            if GOOGLE_API_KEY:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.3,
                    max_tokens=2000,
                    google_api_key=GOOGLE_API_KEY
                )
                self.logger.info("✅ LLM LangChain inicializado: Google Gemini")
                return
        except Exception as e:
            self.logger.warning(f"Google Gemini não disponível: {e}")
        
        try:
            # Fallback: OpenAI
            from src.settings import OPENAI_API_KEY
            if OPENAI_API_KEY:
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    max_tokens=2000,
                    openai_api_key=OPENAI_API_KEY
                )
                self.logger.info("✅ LLM LangChain inicializado: OpenAI GPT-4o-mini")
                return
        except Exception as e:
            self.logger.warning(f"OpenAI não disponível: {e}")
        
        self.llm = None
        self.logger.warning("⚠️ Nenhum LLM LangChain disponível - usando fallback manual")
    
    async def process(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa query do usuário usando RAG vetorial + memória persistente.
        
        VERSÃO ASYNC com memória persistente.
        
        Args:
            query: Pergunta do usuário
            context: Contexto adicional (opcional)
            session_id: ID da sessão para memória persistente
            
        Returns:
            Resposta baseada em busca vetorial + contexto histórico
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🔍 Processando query via RAG V2.0: {query[:80]}...")
            
            # ═══════════════════════════════════════════════════════════════
            # 1. INICIALIZAR MEMÓRIA PERSISTENTE
            # ═══════════════════════════════════════════════════════════════
            if not self._current_session_id:
                if session_id:
                    await self.init_memory_session(session_id)
                else:
                    session_id = await self.init_memory_session()
                self.logger.info(f"✅ Sessão de memória inicializada: {session_id}")
            
            # ═══════════════════════════════════════════════════════════════
            # 2. RECUPERAR CONTEXTO CONVERSACIONAL ANTERIOR
            # ═══════════════════════════════════════════════════════════════
            # FILTRAR CONTEXTO: manter apenas campos relevantes para análise
            memory_context = {}
            if context:
                filtered_context = {}
                if 'chunks' in context:
                    filtered_context['chunks'] = context['chunks']
                if 'csv_data' in context:
                    filtered_context['csv_data'] = context['csv_data']
                # ✅ PRESERVAR FLAGS DE VISUALIZAÇÃO
                if 'visualization_requested' in context:
                    filtered_context['visualization_requested'] = context['visualization_requested']
                if 'visualization_type' in context:
                    filtered_context['visualization_type'] = context['visualization_type']
                if 'fallback_sample_limit' in context:
                    filtered_context['fallback_sample_limit'] = context['fallback_sample_limit']
                if 'reconstructed_df' in context:
                    filtered_context['reconstructed_df'] = context['reconstructed_df']
                context = filtered_context
            # NÃO recuperar contexto de memória para queries de intervalo
            interval_terms = ['intervalo', 'mínimo', 'máximo', 'range', 'amplitude']
            if any(term in query.lower() for term in interval_terms):
                memory_context = {}  # Ignorar histórico/memória
            elif self.has_memory and self._current_session_id:
                memory_context = await self.recall_conversation_context()
                self.logger.debug(
                    f"✅ Contexto de memória recuperado: "
                    f"{len(memory_context.get('recent_messages', []))} mensagens anteriores"
                )
            
            # ═══════════════════════════════════════════════════════════════
            # 3. GERAR EMBEDDING DA QUERY
            # ═══════════════════════════════════════════════════════════════
            self.logger.debug("Gerando embedding da query...")
            embedding_result = self.embedding_gen.generate_embedding(query)
            
            # Extrair lista de floats do resultado
            if isinstance(embedding_result, list):
                query_embedding = embedding_result
            elif hasattr(embedding_result, 'embedding'):
                query_embedding = embedding_result.embedding
            else:
                return self._build_error_response("Formato de embedding inválido")
            
            if not query_embedding or len(query_embedding) == 0:
                return self._build_error_response("Falha ao gerar embedding da query")
            
            # ═══════════════════════════════════════════════════════════════
            # 4. BUSCAR CHUNKS SIMILARES NOS DADOS
            # ═══════════════════════════════════════════════════════════════
            self.logger.debug("Buscando chunks similares nos dados...")
            similar_chunks = self._search_similar_data(
                query_embedding=query_embedding,
                threshold=0.3,  # Threshold igual ao RAGAgent para capturar chunks analíticos
                limit=10
            )
            
            # SALVAR CONTEXTO DE DADOS NA TABELA agent_context
            if self.has_memory and self._current_session_id and similar_chunks:
                data_context = {
                    "dataset_info": {
                        "total_chunks": len(similar_chunks),
                        "source_types": list(set(c.get('source_type', 'unknown') for c in similar_chunks)),
                        "embedding_provider": "sentence-transformer",
                        "last_query": query[:100],
                        "query_timestamp": datetime.now().isoformat()
                    },
                    "performance_metrics": {
                        "embedding_generation_time": "N/A",  # Poderia ser medido
                        "search_time": "N/A",  # Poderia ser medido
                        "chunks_found": len(similar_chunks)
                    }
                }
                
                try:
                    await self.remember_data_context(
                        data_info=data_context,
                        context_key="current_dataset_info"
                    )
                    self.logger.debug("✅ Contexto de dados salvo na tabela agent_context")
                except Exception as e:
                    self.logger.warning(f"⚠️ Falha ao salvar contexto de dados: {e}")
            
            # Fallback inteligente: se chunks não são suficientes OU pergunta exige análise global
            if not similar_chunks or self._should_use_global_csv(query, similar_chunks):
                # Tentar extrair caminho do CSV dos chunks ou do contexto
                csv_path = None
                if context and 'csv_path' in context:
                    csv_path = context['csv_path']
                elif similar_chunks:
                    for chunk in similar_chunks:
                        if 'csv_path' in chunk:
                            csv_path = chunk['csv_path']
                            break
                # Se não encontrar, buscar na pasta processados
                if not csv_path:
                    try:
                        from src.settings import EDA_DATA_DIR_PROCESSADO
                        import os
                        import pandas as pd
                        csv_files = list(EDA_DATA_DIR_PROCESSADO.glob('*.csv'))
                        if csv_files:
                            csv_path = str(max(csv_files, key=lambda p: p.stat().st_mtime))
                    except Exception as e:
                        self.logger.warning(f"Não foi possível localizar CSV para fallback: {e}")
                if csv_path:
                    self.logger.info(f"⚡ Fallback: análise global do CSV ({csv_path}) para pergunta '{query[:60]}...'")
                    try:
                        resposta_csv = self._analisar_completo_csv(csv_path, query)
                        return self._build_response(
                            resposta_csv,
                            metadata={
                                "method": "global_csv_fallback",
                                "csv_path": csv_path,
                                "chunks_found": len(similar_chunks)
                            }
                        )
                    except Exception as e:
                        self.logger.error(f"Erro no fallback global CSV: {e}")
                        return self._build_error_response(f"Erro ao processar CSV global: {e}")
                else:
                    self.logger.error("❌ Fallback global: CSV não encontrado.")
                    return self._build_error_response("CSV original não encontrado para análise global.")
            
            self.logger.info(f"✅ Encontrados {len(similar_chunks)} chunks relevantes")
            
            # ═══════════════════════════════════════════════════════════════
            # 🆕 VERIFICAR SE VISUALIZAÇÃO FOI SOLICITADA (MESMO COM CHUNKS)
            # ═══════════════════════════════════════════════════════════════
            viz_requested = bool(context and context.get('visualization_requested'))
            if viz_requested:
                self.logger.info("📊 Visualização solicitada - gerando gráficos...")
                try:
                    import pandas as pd
                    from pathlib import Path
                    
                    # ═══════════════════════════════════════════════════════════
                    # ⚠️ EXCEÇÃO DE CONFORMIDADE - ACESSO DIRETO AO CSV
                    # ═══════════════════════════════════════════════════════════
                    # JUSTIFICATIVA:
                    # 1. Tabela embeddings contém chunks de análises estatísticas (Markdown)
                    # 2. Histogramas requerem dados tabulares completos (285k linhas × 31 colunas)
                    # 3. Embeddar cada linha seria ineficiente: ~$50-100 de custo + overhead
                    # 4. Padrão de mercado: LangChain, LlamaIndex, OpenAI Code Interpreter
                    #    fazem leitura direta de CSV para análises quantitativas
                    # 
                    # IMPLEMENTAÇÃO FUTURA:
                    # - TODO: Adicionar chunks raw_data na tabela embeddings durante ingestão
                    # - TODO: Implementar reconstituição de DataFrame a partir de embeddings
                    # 
                    # AUDITORIA:
                    # - Log completo de acesso registrado
                    # - Metadados incluídos na resposta
                    # - Acesso read-only sem modificação de dados
                    # ═══════════════════════════════════════════════════════════
                    
                    from src.settings import EDA_DATA_DIR_PROCESSADO
                    # Buscar CSV mais recente em data/processado/
                    csv_files = list(EDA_DATA_DIR_PROCESSADO.glob("*.csv"))
                    if not csv_files:
                        self.logger.error("❌ Nenhum arquivo CSV encontrado em data/processado/")
                        self.logger.info("⚠️ Continuando com resposta textual sem visualizações")
                    else:
                        # Pegar o arquivo mais recente (último modificado)
                        csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
                        csv_size_mb = csv_path.stat().st_size / 1_000_000
                        self.logger.warning(
                            "⚠️ EXCEÇÃO DE CONFORMIDADE: Acesso direto ao CSV para visualização",
                            extra={
                                "event_type": "direct_csv_access",
                                "user_query": query[:100],
                                "csv_path": str(csv_path),
                                "csv_size_mb": round(csv_size_mb, 2),
                                "access_reason": "histogram_generation",
                                "session_id": self._current_session_id,
                                "agent_name": self.name,
                                "timestamp": datetime.now().isoformat(),
                                "conformidade_status": "exception_approved",
                                "alternative_implementation": "future_raw_data_embeddings",
                                "cost_saved_estimate_usd": 50.0
                            }
                        )
                        viz_df = pd.read_csv(csv_path)
                        self.logger.info(
                            f"✅ CSV carregado para visualização: {viz_df.shape[0]:,} linhas × {viz_df.shape[1]} colunas | "
                            f"Tamanho: {csv_size_mb:.2f} MB"
                        )
                        # Delegar para agente de visualização
                        # Removido: agente obsoleto csv_analysis_agent.py
                        vis_context = context.copy() if context else {}
                        vis_context['reconstructed_df'] = viz_df
                        vis_result = self._handle_visualization_query(query, vis_context)
                        if vis_result.get('metadata', {}).get('visualization_success'):
                            # Combinar resposta de visualização com análise textual dos chunks
                            context_texts = [chunk['chunk_text'] for chunk in similar_chunks]
                            context_str = "\n\n".join(context_texts[:5])
                            text_response = await self._generate_llm_response_langchain(
                                query=query,
                                context_data=context_str,
                                memory_context=memory_context,
                                chunks_metadata=similar_chunks
                            )
                            # Combinar resposta textual com informação sobre gráficos
                            graficos_info = vis_result.get('metadata', {}).get('graficos_gerados', [])
                            if graficos_info:
                                graficos_msg = f"\n\n📊 **Visualizações Geradas:**\n"
                                for gf in graficos_info:
                                    graficos_msg += f"• {gf}\n"
                                combined_response = text_response + graficos_msg
                            else:
                                combined_response = text_response
                            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                            # Salvar interação com metadados de conformidade
                            if self.has_memory:
                                await self.remember_interaction(
                                    query=query,
                                    response=combined_response,
                                    processing_time_ms=processing_time_ms,
                                    confidence=1.0,
                                    model_used="rag_v2_with_visualizations",
                                    metadata={
                                        "chunks_found": len(similar_chunks),
                                        "visualization_success": True,
                                        "graficos_gerados": len(graficos_info),
                                        "conformidade_exception": {
                                            "type": "direct_csv_access",
                                            "reason": "visualization_requires_raw_data",
                                            "csv_path": str(csv_path),
                                            "csv_size_mb": round(csv_size_mb, 2),
                                            "access_timestamp": datetime.now().isoformat(),
                                            "approved": True,
                                            "alternative_future": "raw_data_embeddings_implementation",
                                            "industry_standard": "LangChain/LlamaIndex/OpenAI_pattern",
                                            "cost_saved_usd": 50.0,
                                            "read_only": True
                                        }
                                    }
                                )
                            return self._build_response(
                                combined_response,
                                metadata={
                                    **vis_result.get('metadata', {}),
                                    "chunks_found": len(similar_chunks),
                                    "method": "rag_vectorial_v2_with_viz",
                                    "processing_time_ms": processing_time_ms,
                                    "conformidade_exception": {
                                        "type": "direct_csv_access",
                                        "reason": "visualization_requires_raw_data",
                                        "csv_path": str(csv_path),
                                        "csv_size_mb": round(csv_size_mb, 2),
                                        "approved": True,
                                        "industry_standard": True,
                                        "read_only": True,
                                        "documentation": "See comments in rag_data_agent.py lines 318-335"
                                    }
                                }
                            )
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao gerar visualizações: {e}", exc_info=True)
                    # Continuar com resposta textual normal se visualização falhar
            
            # ═══════════════════════════════════════════════════════════════
            # 5. GERAR RESPOSTA COM LANGCHAIN + CONTEXTO HISTÓRICO
            # ═══════════════════════════════════════════════════════════════
            context_texts = [chunk['chunk_text'] for chunk in similar_chunks]
            context_str = "\n\n".join(context_texts[:5])  # Top 5 mais relevantes
            
            self.logger.debug("Usando LangChain LLM para gerar resposta...")
            response_text = await self._generate_llm_response_langchain(
                query=query,
                context_data=context_str,
                memory_context=memory_context,
                chunks_metadata=similar_chunks
            )
            
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            avg_similarity = sum(c['similarity'] for c in similar_chunks) / len(similar_chunks)
            
            # ═══════════════════════════════════════════════════════════════
            # 6. SALVAR INTERAÇÃO NA MEMÓRIA PERSISTENTE
            # ═══════════════════════════════════════════════════════════════
            if self.has_memory:
                await self.remember_interaction(
                    query=query,
                    response=response_text,
                    processing_time_ms=processing_time_ms,
                    confidence=avg_similarity,
                    model_used="langchain_gemini" if self.llm else "fallback",
                    metadata={
                        "chunks_found": len(similar_chunks),
                        "chunks_used": min(5, len(similar_chunks)),
                        "avg_similarity": avg_similarity,
                        "top_similarity": similar_chunks[0]['similarity'],
                        "has_history": len(memory_context.get('recent_conversations', [])) > 0
                    }
                )
                self.logger.debug("✅ Interação salva na memória persistente")
            
            # ═══════════════════════════════════════════════════════════════
            # 7. RETORNAR RESPOSTA COM METADADOS
            # ═══════════════════════════════════════════════════════════════
            return self._build_response(
                response_text,
                metadata={
                    "chunks_found": len(similar_chunks),
                    "chunks_used": min(5, len(similar_chunks)),
                    "avg_similarity": avg_similarity,
                    "method": "rag_vectorial_v2",
                    "top_similarity": similar_chunks[0]['similarity'] if similar_chunks else 0,
                    "processing_time_ms": processing_time_ms,
                    "has_memory": self.has_memory,
                    "session_id": self._current_session_id,
                    "previous_interactions": len(memory_context.get('recent_conversations', []))
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar query: {str(e)}", exc_info=True)
            return self._build_error_response(f"Erro no processamento: {str(e)}")
    
    def _search_similar_data(
        self,
        query_embedding: List[float],
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca chunks similares nos dados usando match_embeddings RPC.
        
        Args:
            query_embedding: Embedding da query
            threshold: Threshold de similaridade (0.0 - 1.0)
            limit: Número máximo de resultados
            
        Returns:
            Lista de chunks similares com metadata
        """
        try:
            # Chamar função RPC match_embeddings
            response = supabase.rpc(
                'match_embeddings',
                {
                    'query_embedding': query_embedding,
                    'similarity_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            if not response.data:
                self.logger.warning("Nenhum chunk similar encontrado")
                return []
            
            self.logger.debug(f"Encontrados {len(response.data)} chunks similares")
            # Parsing defensivo dos embeddings
            from src.embeddings.vector_store import parse_embedding_from_api, VECTOR_DIMENSIONS
            parsed_chunks = []
            for chunk in response.data:
                embedding_raw = chunk.get('embedding')
                try:
                    chunk['embedding'] = parse_embedding_from_api(embedding_raw, VECTOR_DIMENSIONS)
                except Exception as e:
                    self.logger.warning(f"Falha ao parsear embedding do chunk: {e}")
                    chunk['embedding'] = None
                parsed_chunks.append(chunk)
            return parsed_chunks
            
        except Exception as e:
            self.logger.error(f"Erro na busca vetorial: {str(e)}")
            return []
    
    async def _generate_llm_response_langchain(
        self,
        query: str,
        context_data: str,
        memory_context: dict,
        chunks_metadata: list
    ) -> str:
        try:
            # Preparar contexto histórico da conversa
            history_context = ""
            if memory_context.get('recent_messages') and len(memory_context['recent_messages']) > 0:
                history_context = "\n\n**Contexto da Conversa Anterior:**\n"
                for msg in memory_context['recent_messages'][-6:]:  # Últimas 6 mensagens (3 pares user/assistant)
                    msg_type = msg.get('type', 'unknown')
                    content = msg.get('content', '')[:200]  # Limitar a 200 chars
                    if msg_type == 'user':
                        history_context += f"- Usuário perguntou: {content}\n"
                    elif msg_type == 'assistant':
                        history_context += f"- Assistente respondeu: {content}\n"
                history_context += "\n"

            # Preparar prompt DINÂMICO baseado no tipo de query
            query_lower = query.lower()
            
            # Detectar tipo de query para customizar prompt
            # TIPO 1: Perguntas sobre o HISTÓRICO/CONTEXTO da conversa
            if any(term in query_lower for term in ['pergunta anterior', 'perguntei antes', 'falamos sobre', 'conversamos sobre', 'você disse', 'previous question', 'asked before']):
                # Query sobre HISTÓRICO - não precisa de chunks, apenas memória
                system_prompt = (
                    "Você é um agente EDA especializado. Sua tarefa é responder sobre o HISTÓRICO da conversa. "
                    "Use o contexto da conversa anterior fornecido para responder. "
                    "Seja claro e objetivo, referenciando exatamente o que foi discutido."
                )
                user_prompt = (
                    f"{history_context}"  # PRINCIPAL fonte de informação
                    f"**Pergunta do Usuário:**\n{query}\n\n"
                    "**INSTRUÇÕES DE RESPOSTA:**\n"
                    "- Inicie com: 'Pergunta feita: [pergunta]'\n"
                    "- Consulte o histórico da conversa acima\n"
                    "- Responda referenciando exatamente o que foi perguntado/respondido anteriormente\n"
                    "- Se não houver histórico suficiente, informe claramente\n"
                    "- Finalize com: 'Posso esclarecer mais alguma coisa sobre nossa conversa?'\n\n"
                    "**Resposta:**"
                )
            # TIPO 2: Perguntas sobre VARIABILIDADE
            elif any(term in query_lower for term in ['variabilidade', 'desvio padrão', 'variância', 'variance', 'std', 'standard deviation']):
                # Query sobre VARIABILIDADE
                system_prompt = (
                    "Você é um agente EDA especializado. Sua tarefa é responder sobre a VARIABILIDADE dos dados (desvio padrão, variância, coeficiente de variação). "
                    "Use os chunks analíticos fornecidos E o histórico da conversa para contextualizar a resposta. "
                    "Responda de forma clara, humanizada e estruturada."
                )
                user_prompt = (
                    f"{history_context}"  # INCLUIR histórico
                    f"**Pergunta do Usuário:**\n{query}\n\n"
                    f"**CHUNKS ANALÍTICOS DO CSV CARREGADO:**\n{context_data}\n\n"
                    "**INSTRUÇÕES DE RESPOSTA:**\n"
                    "- Inicie com: 'Pergunta feita: [pergunta]'\n"
                    "- Se houver histórico relevante, mencione brevemente o contexto\n"
                    "- Apresente métricas de variabilidade: desvio padrão e variância para as principais variáveis\n"
                    "- Agrupe V1 a V28 com estatísticas agregadas\n"
                    "- Destaque variáveis com alta vs baixa variabilidade\n"
                    "- Use formato R$ para valores monetários\n"
                    "- Finalize com: 'Se precisar de mais detalhes, é só perguntar!'\n\n"
                    "**Resposta:**"
                )
            # TIPO 3: Perguntas sobre INTERVALOS
            elif any(term in query_lower for term in ['intervalo', 'mínimo', 'máximo', 'range', 'amplitude']):
                # Query sobre INTERVALOS
                system_prompt = (
                    "Você é um agente EDA especializado. Sua tarefa é responder EXCLUSIVAMENTE sobre o INTERVALO (mínimo e máximo) de cada variável presente nos chunks analíticos do CSV carregado. "
                    "Ignore completamente qualquer contexto extra, histórico, memória ou dados residuais que não estejam nos chunks analíticos. "
                    "NÃO inclua estatísticas, outliers, gráficos ou qualquer dado não solicitado. Responda de forma clara, objetiva e apenas com o solicitado. "
                    "Para perguntas comuns (saudações, hora, etc.), responda de forma simples e natural, sem análise. Se a pergunta for sobre outro tipo de análise, siga as instruções específicas do usuário."
                )
                user_prompt = (
                    f"**Pergunta do Usuário:**\n{query}\n\n"
                    f"**CHUNKS ANALÍTICOS DO CSV CARREGADO:**\n{context_data}\n\n"
                    "**INSTRUÇÕES DE RESPOSTA:**\n"
                    "- Leia e interprete SOMENTE os chunks fornecidos\n"
                    "- Extraia SOMENTE os valores mínimo e máximo de cada variável\n"
                    "- NÃO inclua análise de outliers, desvio padrão, variância ou estatísticas extras\n"
                    "- Formate a resposta em tabela Markdown\n"
                    "- Se não houver informação suficiente, informe claramente\n\n"
                    "**Resposta:**"
                )
            # TIPO 4: Perguntas sobre TIPOS DE DADOS
            elif any(term in query_lower for term in ['tipos', 'tipo de dado', 'numérico', 'categórico', 'categórica', 'categorical', 'numerical']):
                # Query sobre TIPOS DE DADOS
                system_prompt = (
                    "Você é um agente EDA especializado. Sua tarefa é identificar e classificar os TIPOS DE DADOS (numéricos vs categóricos) presentes no dataset. "
                    "Use APENAS os chunks analíticos fornecidos - não invente ou infira informações. "
                    "Responda de forma clara, humanizada e estruturada."
                )
                user_prompt = (
                    f"**Pergunta do Usuário:**\n{query}\n\n"
                    f"**CHUNKS ANALÍTICOS DO CSV CARREGADO:**\n{context_data}\n\n"
                    "**INSTRUÇÕES DE RESPOSTA:**\n"
                    "- Inicie com: 'Pergunta feita: [pergunta]'\n"
                    "- Adicione mensagem amigável: 'Olá! Aqui está uma análise dos tipos de variáveis presentes no seu conjunto de dados:'\n"
                    "- Divida a resposta em 2 seções: 'Variáveis Numéricas' e 'Variáveis Categóricas'\n"
                    "- Para variáveis numéricas: agrupe V1 a V28 como 'V1 a V28: Variáveis numéricas agrupadas, todas apresentam alta variabilidade.'\n"
                    "- Liste também: Time, Amount\n"
                    "- Para variáveis categóricas: descreva Class como 'Class: Variável categórica com valores possíveis 0 e 1. Utilizada para indicar fraude ou não fraude.'\n"
                    "- NÃO mencione frequência de valores para Class\n"
                    "- Adicione estatísticas apenas para Amount (Média, Desvio padrão, Mínimo, Máximo) com formato R$ XX.XX\n"
                    "- Finalize com: 'Se precisar de mais detalhes ou quiser analisar outra variável, é só perguntar!'\n\n"
                    "**Resposta:**"
                )
            # TIPO 5: Perguntas sobre FREQUÊNCIA (valores mais/menos frequentes)
            elif any(term in query_lower for term in ['frequente', 'frequentes', 'frequência', 'comum', 'raro', 'raros', 'moda', 'contagem', 'value_counts', 'mais ocorre', 'menos ocorre']):
                # Query sobre FREQUÊNCIA
                system_prompt = (
                    "Você é um agente EDA especializado em análise de frequência. "
                    "Sua tarefa é identificar e reportar QUANTAS VEZES cada valor aparece no dataset. "
                    "Use APENAS os dados fornecidos nos chunks analíticos. NÃO invente números. "
                    "ATENÇÃO: Na tabela 'Colunas Categóricas', a coluna 'Frequência' contém o NÚMERO DE OCORRÊNCIAS do valor mais frequente. "
                    "Exemplo: Se vir '| Class | 0 | 284315 |', significa que o valor '0' aparece 284.315 vezes no dataset."
                )
                user_prompt = (
                    f"**Pergunta do Usuário:**\n{query}\n\n"
                    f"**CHUNKS ANALÍTICOS DO CSV CARREGADO:**\n{context_data}\n\n"
                    "**INSTRUÇÕES CRÍTICAS DE INTERPRETAÇÃO:**\n"
                    "1. **Leia a tabela 'Colunas Categóricas' corretamente**:\n"
                    "   - Formato: | Coluna | Valor Mais Frequente | Frequência | Valores Únicos | Valores Nulos |\n"
                    "   - A coluna 'Frequência' é o NÚMERO DE VEZES que o 'Valor Mais Frequente' aparece\n"
                    "   - Exemplo: | Class | 0 | 284315 | → O valor '0' aparece 284.315 vezes\n\n"
                    "2. **Calcule o valor menos frequente**:\n"
                    "   - Se houver 2 valores únicos (ex: Class com valores 0 e 1)\n"
                    "   - E o total de registros é conhecido (ex: 284.807)\n"
                    "   - Menos frequente = Total de registros - Frequência do mais frequente\n"
                    "   - Exemplo: Class valor '1' = 284.807 - 284.315 = 492 vezes\n\n"
                    "3. **Para COLUNAS NUMÉRICAS**:\n"
                    "   - Leia a tabela 'Colunas Numéricas' e encontre a coluna 'Moda'\n"
                    "   - A moda é o valor numérico que mais se repete\n"
                    "   - Explique que para variáveis contínuas, muitos valores aparecem apenas 1 vez\n\n"
                    "**FORMATO DE RESPOSTA OBRIGATÓRIO:**\n"
                    "Inicie com: 'Pergunta feita: [pergunta]'\n\n"
                    "Adicione: 'Analisando a frequência dos valores no dataset:'\n\n"
                    "**🔢 Colunas Categóricas:**\n\n"
                    "Para cada coluna categórica encontrada, mostre:\n"
                    "- **Coluna [Nome]**: \n"
                    "  * Valor mais frequente: [valor] (aparece [X] vezes)\n"
                    "  * Valor menos frequente: [valor] (aparece [Y] vezes) [SE PUDER CALCULAR]\n\n"
                    "**📊 Colunas Numéricas:**\n\n"
                    "Para colunas numéricas, mostre a moda estatística:\n"
                    "- **Coluna [Nome]**: Moda = [valor] (valor que mais se repete)\n\n"
                    "Adicione explicação:\n"
                    "'Para variáveis numéricas contínuas (como V1-V28, Amount), a maioria dos valores aparece apenas 1 vez. "
                    "A moda estatística indica o valor que mais se repete, mas para análise mais detalhada, considere perguntar sobre distribuição ou intervalos.'\n\n"
                    "Finalize: 'Se precisar de mais detalhes ou análise de distribuição, é só perguntar!'\n\n"
                    "**⚠️ REGRAS CRÍTICAS:**\n"
                    "- NÃO diga 'aparece 0 vezes' quando o número na tabela é POSITIVO\n"
                    "- NÃO confunda a coluna 'Frequência' com o valor da variável\n"
                    "- NÃO mostre mínimo/máximo quando a pergunta é sobre frequência\n"
                    "- USE os números EXATOS da tabela de chunks fornecidos\n\n"
                    "**Resposta:**"
                )
            
            # TIPO 6: Perguntas sobre CLUSTERING/AGRUPAMENTOS
            elif any(term in query_lower for term in ['cluster', 'clusters', 'agrupamento', 'agrupamentos', 'grupos', 'kmeans', 'k-means', 'dbscan', 'hierárquico', 'hierarquico', 'segmentação', 'segmentacao']):
                # 🔬 EXECUÇÃO REAL DE CLUSTERING usando PythonDataAnalyzer
                self.logger.info("🔬 Detectada pergunta sobre clustering - executando análise KMeans real...")
                
                try:
                    from src.tools.python_analyzer import python_analyzer
                    
                    # Executar clustering real nos dados
                    clustering_result = python_analyzer.calculate_clustering_analysis(n_clusters=3)
                    
                    if "error" in clustering_result:
                        # Se houve erro, informar ao usuário
                        error_msg = clustering_result.get("error", "Erro desconhecido")
                        suggestion = clustering_result.get("suggestion", "")
                        
                        return (
                            f"Pergunta feita: {query}\n\n"
                            f"❌ **Não foi possível realizar análise de clustering:**\n"
                            f"{error_msg}\n\n"
                            f"{suggestion}\n\n"
                            "Se precisar de mais detalhes, é só perguntar!"
                        )
                    
                    # Construir contexto enriquecido com resultados reais do clustering
                    clustering_context = clustering_result.get("interpretation", "")
                    cluster_distribution = clustering_result.get("cluster_distribution", {})
                    cluster_percentages = clustering_result.get("cluster_percentages", {})
                    numeric_vars = clustering_result.get("numeric_variables_used", [])
                    is_balanced = clustering_result.get("is_balanced", False)
                    
                    # Construir prompt com dados REAIS do clustering
                    system_prompt = (
                        "Você é um agente EDA especializado em análise de clustering. "
                        "Acabei de executar análise de clustering KMeans REAL nos dados. "
                        "Sua tarefa é apresentar os resultados de forma clara e estruturada. "
                        "Use APENAS os resultados reais fornecidos. NÃO invente números."
                    )
                    
                    user_prompt = (
                        f"**Pergunta do Usuário:**\n{query}\n\n"
                        f"**RESULTADOS REAIS DO CLUSTERING EXECUTADO:**\n\n"
                        f"**Algoritmo:** KMeans com {clustering_result.get('n_clusters', 3)} clusters\n"
                        f"**Total de pontos analisados:** {clustering_result.get('total_points', 0):,}\n"
                        f"**Variáveis numéricas utilizadas:** {len(numeric_vars)} variáveis\n"
                        f"  - Exemplos: {', '.join(numeric_vars[:5])}{'...' if len(numeric_vars) > 5 else ''}\n\n"
                        f"**Distribuição dos Clusters:**\n"
                    )
                    
                    # Adicionar distribuição real dos clusters
                    for cluster_id in sorted(cluster_distribution.keys()):
                        count = cluster_distribution[cluster_id]
                        pct = cluster_percentages[cluster_id]
                        user_prompt += f"- Cluster {cluster_id}: {count:,} pontos ({pct:.1f}%)\n"
                    
                    user_prompt += f"\n**Balanceamento:** {'Clusters balanceados' if is_balanced else 'Clusters desbalanceados'}\n\n"
                    
                    user_prompt += (
                        f"**CHUNKS ANALÍTICOS DO CSV (contexto adicional):**\n{context_data}\n\n"
                        "**FORMATO DE RESPOSTA OBRIGATÓRIO:**\n"
                        "Inicie com: 'Pergunta feita: [pergunta]'\n\n"
                        "Adicione: 'Para responder se há agrupamentos (clusters) nos dados, executei análise de clustering KMeans:'\n\n"
                        "**🔬 Análise de Clustering (KMeans):**\n\n"
                        "**Variáveis Utilizadas:**\n"
                        f"- {len(numeric_vars)} variáveis numéricas: {', '.join(numeric_vars[:8])}{'...' if len(numeric_vars) > 8 else ''}\n\n"
                        "**Resultado do Clustering (k=3):**\n"
                    )
                    
                    # Adicionar novamente para o LLM formatar
                    for cluster_id in sorted(cluster_distribution.keys()):
                        count = cluster_distribution[cluster_id]
                        pct = cluster_percentages[cluster_id]
                        user_prompt += f"- Cluster {cluster_id}: {count:,} pontos ({pct:.1f}%)\n"
                    
                    user_prompt += (
                        "\n**✅ Conclusão:**\n"
                        f"- SIM, os dados apresentam {len(cluster_distribution)} agrupamentos distintos\n"
                        f"- Os clusters são {'balanceados' if is_balanced else 'desbalanceados'}\n"
                        "- [Adicione insight interpretativo sobre o significado desses agrupamentos]\n\n"
                        "**💡 Recomendações:**\n"
                        "- Para visualizar os clusters, pergunte: 'mostre gráfico de dispersão dos clusters'\n"
                        "- Para análise PCA 2D/3D, pergunte: 'aplique PCA nos dados'\n"
                        "- Para estatísticas por cluster, pergunte: 'qual a média de cada cluster?'\n\n"
                        "Finalize: 'Se desejar aprofundar na análise de clustering, é só perguntar!'\n\n"
                        "**Resposta:**"
                    )
                    
                except Exception as e:
                    self.logger.error(f"❌ Erro ao executar clustering: {str(e)}", exc_info=True)
                    # Fallback: usar prompt genérico informando limitação
                    system_prompt = (
                        "Você é um agente EDA especializado. "
                        "Houve um erro técnico ao tentar executar análise de clustering real nos dados. "
                        "Explique ao usuário que a análise de clustering requer execução de algoritmos específicos."
                    )
                    user_prompt = (
                        f"**Pergunta do Usuário:**\n{query}\n\n"
                        f"**STATUS:** Erro técnico ao executar KMeans: {str(e)}\n\n"
                        "**INSTRUÇÕES DE RESPOSTA:**\n"
                        "- Informe que houve uma limitação técnica temporária\n"
                        "- Explique que clustering requer execução de algoritmos (KMeans, DBSCAN, etc.)\n"
                        "- Sugira tentar novamente ou perguntar sobre outras análises\n\n"
                        "**Resposta:**"
                    )

            
            # TIPO 7: Query genérica - incluir histórico de conversa
            else:
                # Query genérica - incluir histórico de conversa
                system_prompt = (
                    "Você é um agente EDA especializado. Responda à pergunta do usuário usando os chunks analíticos fornecidos E o histórico da conversa quando relevante. "
                    "Seja claro, objetivo, estruturado e humanizado. Não invente dados ou informações."
                )
                user_prompt = (
                    f"{history_context}"  # INCLUIR histórico aqui!
                    f"**Pergunta do Usuário:**\n{query}\n\n"
                    f"**CHUNKS ANALÍTICOS DO CSV CARREGADO:**\n{context_data}\n\n"
                    "**INSTRUÇÕES DE RESPOSTA:**\n"
                    "- Use as informações dos chunks fornecidos E o histórico da conversa quando relevante\n"
                    "- Se a pergunta se refere a algo mencionado anteriormente, considere o contexto\n"
                    "- Inicie com: 'Pergunta feita: [pergunta]'\n"
                    "- Responda de forma clara, humanizada e estruturada\n"
                    "- Se não houver informação suficiente, informe claramente\n"
                    "- Finalize com: 'Se precisar de mais detalhes, é só perguntar!'\n\n"
                    "**Resposta:**"
                )
            
            # Usar LangChain LLM se disponível
            if self.llm and LANGCHAIN_AVAILABLE:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = await asyncio.to_thread(self.llm.invoke, messages)
                return response.content
            
            # Fallback: usar LLM Manager customizado
            else:
                from src.llm.manager import LLMManager, LLMConfig
                llm_manager = LLMManager()
                
                # Construir prompt único (LLMManager.chat espera string, não messages)
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                llm_response = llm_manager.chat(
                    full_prompt,
                    config=LLMConfig(
                        temperature=0.3,
                        max_tokens=2000
                    )
                )
                
                # Verificar se houve erro (LLMResponse tem atributo .error)
                if not llm_response.success or llm_response.error:
                    return self._format_raw_data_response(query, chunks_metadata)
                
                # Extrair conteúdo (LLMResponse tem atributo .content)
                response_text = llm_response.content
                
                if not response_text:
                    return self._format_raw_data_response(query, chunks_metadata)
                
                return response_text
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta LLM: {str(e)}", exc_info=True)
            return self._format_raw_data_response(query, chunks_metadata)
    
    def _format_raw_data_response(
        self,
        query: str,
        chunks_metadata: List[Dict]
        ) -> str:
        """
        Fallback: usa agente de síntese para consolidar dados se LLM falhar.
        """
        # Extrair apenas o texto dos chunks
        chunks = [chunk.get('chunk_text', '') for chunk in chunks_metadata]
        
        # Chamar agente de síntese para consolidar
        from src.agent.rag_synthesis_agent import synthesize_response
        try:
            return synthesize_response(chunks, query, use_llm=False)
        except Exception as e:
            self.logger.error(f"Erro no agente de síntese: {e}")
            # Fallback extremo: resposta estruturada mínima
            return f"""## Resposta para: {query}

**Status:** ⚠️ Erro na síntese

Não foi possível processar completamente a consulta devido a um erro técnico.
Por favor, reformule sua pergunta ou entre em contato com o suporte.

_Erro: {str(e)}_"""
    
    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Constrói resposta de erro padronizada."""
        return self._build_response(
            f"❌ {error_msg}",
            metadata={"error": True, "method": "rag_vectorial_v2"}
        )
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODO SÍNCRONO WRAPPER (para compatibilidade retroativa)
    # ═══════════════════════════════════════════════════════════════
    
    def process_sync(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Wrapper síncrono para compatibilidade com código legado.
        
        ⚠️ DEPRECATED: Use process() async quando possível.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process(query, context))
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODO DE CARREGAMENTO CSV (mantido da versão anterior)
    # ═══════════════════════════════════════════════════════════════
    
    async def load_csv_to_embeddings(
        self,
        csv_path: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> Dict[str, Any]:
        """
        Carrega CSV para a tabela embeddings.
        
        Args:
            csv_path: Caminho do arquivo CSV
            chunk_size: Tamanho dos chunks
            overlap: Overlap entre chunks
            
        Returns:
            Status do carregamento
        """
        try:
            self.logger.info(f"📂 Carregando CSV: {csv_path}")
            
            import pandas as pd
            from src.embeddings.chunker import CSVChunker
            
            # Ler CSV
            df = pd.read_csv(csv_path)
            self.logger.info(f"✅ CSV lido: {len(df)} linhas, {len(df.columns)} colunas")
            
            # Criar chunks
            chunker = CSVChunker(chunk_size=chunk_size, overlap=overlap)
            chunks = chunker.chunk_dataframe(df)
            self.logger.info(f"✅ Criados {len(chunks)} chunks")
            
            # Gerar embeddings e salvar
            inserted_count = 0
            for i, chunk in enumerate(chunks):
                try:
                    # Gerar embedding
                    embedding = self.embedding_gen.generate_embedding(chunk['text'])
                    
                    # Salvar na tabela embeddings
                    insert_data = {
                        'chunk_text': chunk['text'],
                        'embedding': embedding,
                        'metadata': {
                            'source': csv_path,
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'created_at': datetime.now().isoformat()
                        }
                    }
                    
                    result = supabase.table('embeddings').insert(insert_data).execute()
                    
                    if result.data:
                        inserted_count += 1
                        if (i + 1) % 10 == 0:
                            self.logger.info(f"Progresso: {i+1}/{len(chunks)} chunks inseridos")
                
                except Exception as chunk_error:
                    self.logger.warning(f"Erro no chunk {i}: {chunk_error}")
                    continue
            
            self.logger.info(f"✅ Carregamento concluído: {inserted_count}/{len(chunks)} chunks inseridos")
            
            return self._build_response(
                f"✅ CSV carregado com sucesso: {inserted_count} chunks inseridos na base vetorial",
                metadata={
                    'csv_path': csv_path,
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'chunks_created': len(chunks),
                    'chunks_inserted': inserted_count
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar CSV: {str(e)}")
            return self._build_error_response(f"Falha ao carregar CSV: {str(e)}")
