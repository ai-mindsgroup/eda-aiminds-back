"""Agente Orquestrador Central para coordenar sistema multiagente.

Este agente é responsável por:
- Receber consultas dos usuários
- Determinar qual(is) agente(s) especializado(s) utilizar
- Coordenar múltiplos agentes quando necessário
- Combinar respostas de diferentes agentes
- Manter contexto da conversação
- Fornecer interface única para o sistema completo
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from src.agent.base_agent import BaseAgent, AgentError
from src.agent.csv_analysis_agent import EmbeddingsAnalysisAgent
from src.data.data_processor import DataProcessor

# Lazy loading para RAGAgent - será importado apenas quando necessário
RAG_AGENT_AVAILABLE = None  # None = não verificado ainda
_rag_agent_module = None

def _get_rag_agent():
    """Importa RAGAgent lazily."""
    global RAG_AGENT_AVAILABLE, _rag_agent_module
    
    if RAG_AGENT_AVAILABLE is None:
        try:
            from src.agent.rag_agent import RAGAgent
            _rag_agent_module = RAGAgent
            RAG_AGENT_AVAILABLE = True
        except (ImportError, RuntimeError) as e:
            RAG_AGENT_AVAILABLE = False
            _rag_agent_module = None
            print(f"⚠️ RAGAgent não disponível: {str(e)[:100]}...")
    
    return _rag_agent_module

# Import do cliente Supabase para verificação de dados
try:
    from src.vectorstore.supabase_client import supabase
    SUPABASE_CLIENT_AVAILABLE = True
except ImportError as e:
    SUPABASE_CLIENT_AVAILABLE = False
    supabase = None
    print(f"⚠️ Cliente Supabase não disponível: {str(e)[:100]}...")
except RuntimeError as e:
    SUPABASE_CLIENT_AVAILABLE = False  
    supabase = None
    print(f"⚠️ Cliente Supabase não disponível: {str(e)[:100]}...")

# Import da ferramenta de análise Python
try:
    from src.tools.python_analyzer import python_analyzer
    PYTHON_ANALYZER_AVAILABLE = True
except ImportError as e:
    PYTHON_ANALYZER_AVAILABLE = False
    python_analyzer = None
    print(f"⚠️ Python Analyzer não disponível: {str(e)[:100]}...")

# Import dos guardrails de validação
try:
    from src.tools.guardrails import statistics_guardrails
    GUARDRAILS_AVAILABLE = True
except ImportError as e:
    GUARDRAILS_AVAILABLE = False
    statistics_guardrails = None
    print(f"⚠️ Guardrails não disponível: {str(e)[:100]}...")# Import do LLM Manager (camada de abstração para múltiplos provedores)
try:
    from src.llm.manager import get_llm_manager, LLMManager, LLMConfig
    LLM_MANAGER_AVAILABLE = True
except ImportError as e:
    LLM_MANAGER_AVAILABLE = False
    print(f"⚠️ LLM Manager não disponível: {str(e)[:100]}...")
except RuntimeError as e:
    LLM_MANAGER_AVAILABLE = False
    print(f"⚠️ LLM Manager não disponível: {str(e)[:100]}...")

# Import do sistema de prompts
try:
    from src.prompts.manager import get_prompt_manager, AgentRole
    PROMPT_MANAGER_AVAILABLE = True
except ImportError as e:
    PROMPT_MANAGER_AVAILABLE = False
    print(f"⚠️ Prompt Manager não disponível: {str(e)[:100]}...")
except RuntimeError as e:
    PROMPT_MANAGER_AVAILABLE = False
    print(f"⚠️ Prompt Manager não disponível: {str(e)[:100]}...")


class QueryType(Enum):
    """Tipos de consultas que o orquestrador pode processar."""
    CSV_ANALYSIS = "csv_analysis"      # Análise de dados CSV
    RAG_SEARCH = "rag_search"          # Busca semântica/contextual
    DATA_LOADING = "data_loading"      # Carregamento de dados
    LLM_ANALYSIS = "llm_analysis"      # Análise via LLM (Google Gemini)
    HYBRID = "hybrid"                  # Múltiplos agentes necessários
    GENERAL = "general"                # Consulta geral/conversacional
    UNKNOWN = "unknown"                # Tipo não identificado


@dataclass
class AgentTask:
    """Representa uma tarefa para um agente específico."""
    agent_name: str
    query: str
    context: Optional[Dict[str, Any]] = None
    priority: int = 1  # 1=alta, 2=média, 3=baixa


@dataclass
class OrchestratorResponse:
    """Resposta consolidada do orquestrador."""
    content: str
    query_type: QueryType
    agents_used: List[str]
    metadata: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


class OrchestratorAgent(BaseAgent):
    """Agente central que coordena todos os agentes especializados."""
    
    def __init__(self, 
                 enable_csv_agent: bool = True,
                 enable_rag_agent: bool = True,
                 enable_llm_manager: bool = True,
                 enable_data_processor: bool = True):
        """Inicializa o orquestrador com agentes especializados.
        
        Args:
            enable_csv_agent: Habilitar agente de análise CSV
            enable_rag_agent: Habilitar agente RAG
            enable_llm_manager: Habilitar LLM Manager (camada de abstração para múltiplos LLMs)
            enable_data_processor: Habilitar processador de dados
        """
        super().__init__(
            name="orchestrator",
            description="Coordenador central do sistema multiagente de IA para análise de dados",
            enable_memory=True  # Habilita sistema de memória
        )
        
        # Inicializar agentes especializados
        self.agents = {}
        
        # MIGRAÇÃO: conversation_history e current_data_context agora são persistentes
        # Mantém compatibilidade temporária para transição gradual
        self.conversation_history = []  # DEPRECIADO - usar memória Supabase
        self.current_data_context = {}  # DEPRECIADO - usar memória Supabase
        
        # Inicializar LLM Manager (camada de abstração)
        self.llm_manager = None
        
        # Inicializar Prompt Manager
        self.prompt_manager = None
        if PROMPT_MANAGER_AVAILABLE:
            try:
                self.prompt_manager = get_prompt_manager()
                self.logger.info("✅ Prompt Manager inicializado")
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao inicializar Prompt Manager: {str(e)}")
        
        # Inicializar agentes com tratamento de erro gracioso
        initialization_errors = []
        
        # CSV Agent (sempre disponível - sem dependências externas)
        if enable_csv_agent:
            try:
                self.agents["csv"] = EmbeddingsAnalysisAgent()
                self.logger.info("✅ Agente CSV inicializado")
            except Exception as e:
                error_msg = f"CSV Agent: {str(e)}"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")
        
        # RAG Agent (requer Supabase configurado)
        if enable_rag_agent:
            RAGAgentClass = _get_rag_agent()
            if RAGAgentClass:
                try:
                    self.agents["rag"] = RAGAgentClass()
                    self.logger.info("✅ Agente RAG inicializado")
                except Exception as e:
                    error_msg = f"RAG Agent: {str(e)}"
                    initialization_errors.append(error_msg)
                    self.logger.warning(f"⚠️ {error_msg}")
            else:
                error_msg = "RAG Agent: Dependências não disponíveis (Supabase não configurado)"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")

        # LLM Manager (camada de abstração para múltiplos provedores)
        if enable_llm_manager and LLM_MANAGER_AVAILABLE:
            try:
                self.llm_manager = get_llm_manager()
                self.logger.info("✅ LLM Manager inicializado")
                
                # Adicionar informações do provedor ativo
                status = self.llm_manager.get_status()
                active_provider = status.get("active_provider", "unknown")
                self.logger.info(f"🤖 Provedor LLM ativo: {active_provider}")
                
            except Exception as e:
                error_msg = f"LLM Manager: {str(e)}"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")
        elif enable_llm_manager and not LLM_MANAGER_AVAILABLE:
            error_msg = "LLM Manager: Dependências não disponíveis"
            initialization_errors.append(error_msg)
            self.logger.warning(f"⚠️ {error_msg}")
        
        # Data Processor (sempre disponível - sem dependências externas)  
        if enable_data_processor:
            try:
                self.data_processor = DataProcessor(caller_agent='orchestrator_agent')
                self.logger.info("✅ Data Processor inicializado")
            except Exception as e:
                error_msg = f"Data Processor: {str(e)}"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")
                self.data_processor = None
        else:
            self.data_processor = None
        
        # Log do resultado da inicialização
        if self.agents or self.data_processor:
            self.logger.info(f"🚀 Orquestrador inicializado com {len(self.agents)} agentes")
            if initialization_errors:
                self.logger.warning(f"⚠️ {len(initialization_errors)} componentes falharam na inicialização")
        else:
            self.logger.error("❌ Nenhum agente foi inicializado com sucesso")
            if initialization_errors:
                raise AgentError(
                    self.name, 
                    f"Falha na inicialização de todos os componentes: {'; '.join(initialization_errors)}"
                )
    
    def _check_embeddings_data_availability(self) -> bool:
        """Verifica se existem dados na tabela embeddings (CONFORMIDADE)."""
        if not SUPABASE_CLIENT_AVAILABLE or not supabase:
            return False
        
        try:
            result = supabase.table('embeddings').select('id').limit(1).execute()
            has_data = bool(result.data)
            
            if has_data:
                self.logger.info("✅ Dados encontrados na tabela embeddings")
            else:
                self.logger.warning("⚠️ Nenhum dado encontrado na tabela embeddings")
            
            return has_data
        except Exception as e:
            self.logger.error(f"Erro ao verificar dados embeddings: {str(e)}")
            return False
    
    def _ensure_embeddings_compliance(self) -> bool:
        """Garante conformidade com regra embeddings-only.
        
        Returns:
            True se dados estão disponíveis via embeddings
        """
        if self._check_embeddings_data_availability():
            return True
        
        self.logger.error("⚠️ VIOLAÇÃO DE CONFORMIDADE: Dados não disponíveis via embeddings!")
        self.logger.error("⚠️ Sistema deve funcionar APENAS com dados da tabela embeddings!")
        return False
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta determinando agente(s) apropriado(s).
        
        ⚠️ CONFORMIDADE: Prioriza dados da tabela embeddings.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional (file_path, dados, configurações)
        
        Returns:
            Resposta consolidada do sistema
        """
        self.logger.info(f"🎯 Processando consulta: '{query[:50]}...'")
        
        # Verificar conformidade com embeddings-only
        if not self._ensure_embeddings_compliance():
            return {
                'success': False,
                'error': 'Dados não disponíveis via embeddings. Sistema em conformidade apenas com dados indexados.',
                'message': 'Por favor, certifique-se de que os dados foram adequadamente indexados na tabela embeddings.',
                'suggestion': 'Execute o processo de ingestão para indexar os dados primeiro.'
            }
        
        try:
            # 1. Adicionar à história da conversa (compatibilidade)
            self.conversation_history.append({
                "type": "user_query",
                "query": query,
                "timestamp": self._get_timestamp(),
                "context": context
            })
            
            # 2. Analisar tipo da consulta
            query_type = self._classify_query(query, context)
            self.logger.info(f"📝 Tipo de consulta identificado: {query_type.value}")
            
            # 3. Processar baseado no tipo
            if query_type == QueryType.CSV_ANALYSIS:
                result = self._handle_csv_analysis(query, context)
            elif query_type == QueryType.RAG_SEARCH:
                result = self._handle_rag_search(query, context)
            elif query_type == QueryType.DATA_LOADING:
                result = self._handle_data_loading(query, context)
            elif query_type == QueryType.LLM_ANALYSIS:
                result = self._handle_llm_analysis(query, context)
            elif query_type == QueryType.HYBRID:
                result = self._handle_hybrid_query(query, context)
            elif query_type == QueryType.GENERAL:
                result = self._handle_general_query(query, context)
            else:
                result = self._handle_unknown_query(query, context)
            
            # 4. Adicionar à história
            self.conversation_history.append({
                "type": "system_response",
                "response": result,
                "timestamp": self._get_timestamp()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento: {str(e)}")
            return self._build_response(
                f"❌ Erro no processamento da consulta: {str(e)}",
                metadata={
                    "error": True,
                    "query_type": "error",
                    "agents_used": []
                }
            )
    
    def _check_data_availability(self) -> bool:
        """Verifica se há dados disponíveis na base de dados.
        
        Returns:
            True se há dados carregados, False caso contrário
        """
        # 1. Verificar contexto em memória primeiro (mais rápido)
        if self.current_data_context.get("csv_loaded", False):
            self.logger.debug("✅ Dados encontrados no contexto em memória")
            return True
        
        # 2. Verificar dados na base de dados Supabase
        if SUPABASE_CLIENT_AVAILABLE and supabase:
            try:
                # Verificar se há dados na tabela embeddings
                result = supabase.table('embeddings').select('id').limit(1).execute()
                if result.data and len(result.data) > 0:
                    self.logger.debug("✅ Dados encontrados na tabela embeddings")
                    # Atualizar contexto em memória para próximas consultas
                    self.current_data_context["csv_loaded"] = True
                    self.current_data_context["data_source"] = "database_embeddings"
                    return True
                
                # Verificar se há dados na tabela chunks
                result = supabase.table('chunks').select('id').limit(1).execute()
                if result.data and len(result.data) > 0:
                    self.logger.debug("✅ Dados encontrados na tabela chunks")
                    # Atualizar contexto em memória para próximas consultas
                    self.current_data_context["csv_loaded"] = True
                    self.current_data_context["data_source"] = "database_chunks"
                    return True
                
                self.logger.debug("❌ Nenhum dado encontrado nas tabelas da base de dados")
                return False
                
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao verificar dados na base: {str(e)}")
                return False
        else:
            self.logger.debug("⚠️ Cliente Supabase não disponível")
            return False
    
    def _detect_visualization_need(self, query: str) -> Optional[str]:
        """
        Detecta se a query do usuário requer visualização gráfica.
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            Tipo de gráfico necessário ou None
        """
        try:
            from src.tools.graph_generator import detect_visualization_need
            viz_type = detect_visualization_need(query)
            if viz_type:
                self.logger.info(f"🎨 Visualização detectada: {viz_type}")
            return viz_type
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao detectar visualização: {e}")
            return None
    
    def _retrieve_data_context_from_supabase(self) -> Optional[Dict[str, Any]]:
        """Recupera contexto de dados armazenados no Supabase.
        
        Returns:
            Dicionário com informações sobre os dados ou None se não conseguir recuperar
        """
        if not SUPABASE_CLIENT_AVAILABLE or not supabase:
            return None
            
        try:
            # CORREÇÃO: Recuperar dados da tabela embeddings (não chunks)
            embeddings_result = supabase.table('embeddings').select('chunk_text, metadata').limit(10).execute()
            
            if not embeddings_result.data:
                self.logger.debug("❌ Nenhum embedding encontrado para análise")
                return None
            
            # Analisar chunk_text para extrair informações sobre a estrutura dos dados
            total_embeddings = len(embeddings_result.data)
            sample_chunks = []
            columns_found = set()
            dataset_info = {}
            
            for embedding in embeddings_result.data:
                chunk_text = embedding.get('chunk_text', '')
                metadata = embedding.get('metadata', {})
                
                # Coletar amostra dos chunks para análise
                if chunk_text:
                    sample_chunks.append(chunk_text[:200])  # Primeiros 200 caracteres
                
                # Extrair informações específicas dos chunks sobre dataset
                if 'creditcard.csv' in chunk_text.lower():
                    dataset_info['dataset_name'] = 'creditcard.csv'
                    dataset_info['type'] = 'fraud_detection'
                
                # Tentar extrair informações de colunas dos chunks
                if 'colunas:' in chunk_text.lower() or 'columns:' in chunk_text.lower():
                    # Procurar por padrões de colunas no texto
                    import re
                    col_patterns = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', chunk_text)
                    for pattern in col_patterns:
                        if len(pattern) > 2 and not pattern.lower() in ['dataset', 'chunk', 'transacoes', 'linhas']:
                            columns_found.add(pattern)
            
            # Construir contexto baseado nos dados encontrados
            context = {
                'csv_loaded': True,
                'data_source': 'database_embeddings',
                'csv_analysis': f"Dados encontrados na base vetorial: {total_embeddings} embeddings disponíveis."
            }
            
            if dataset_info.get('dataset_name'):
                context['file_path'] = dataset_info['dataset_name']
                context['csv_analysis'] += f" Dataset: {dataset_info['dataset_name']}"
                
                if dataset_info.get('type') == 'fraud_detection':
                    context['csv_analysis'] += " (detecção de fraude em cartão de crédito)"
                    
                    # NOVA FUNCIONALIDADE: Calcular estatísticas reais usando Python Analyzer
                    if PYTHON_ANALYZER_AVAILABLE and python_analyzer:
                        try:
                            self.logger.info("🔢 Calculando estatísticas reais com Python Analyzer...")
                            real_stats = python_analyzer.calculate_real_statistics("all")
                            
                            if "error" not in real_stats:
                                # Usar estatísticas reais ao invés de estimativas
                                context['csv_analysis'] += f"\n\n📊 ESTATÍSTICAS REAIS:"
                                context['csv_analysis'] += f"\n- Total de registros: {real_stats['total_records']:,}"
                                context['csv_analysis'] += f"\n- Total de colunas: {real_stats['total_columns']}"
                                
                                if 'tipos_dados' in real_stats:
                                    tipos = real_stats['tipos_dados']
                                    context['columns_summary'] = f"Numéricos: {', '.join(tipos['numericos'][:5])}... ({tipos['total_numericos']} colunas), Categóricos: {', '.join(tipos['categoricos'])}"
                                
                                if 'estatisticas' in real_stats:
                                    stats = real_stats['estatisticas']
                                    if 'Amount' in stats:
                                        amt = stats['Amount']
                                        context['csv_analysis'] += f"\n- Amount: média=R$ {amt['mean']:.2f}, desvio=R$ {amt['std']:.2f}, min=R$ {amt['min']:.2f}, max=R$ {amt['max']:.2f}"
                                    
                                    if 'Class' in stats:
                                        cls = stats['Class']
                                        context['csv_analysis'] += f"\n- Class: {cls['value_counts']}"
                                        for val, pct in cls['percentages'].items():
                                            label = "Normal" if val == 0 else "Fraude"
                                            context['csv_analysis'] += f"\n  • {label} (Class {val}): {pct:.2f}%"
                                
                                self.logger.info("✅ Estatísticas reais calculadas com sucesso")
                            else:
                                self.logger.warning(f"⚠️ Erro no Python Analyzer: {real_stats.get('error')}")
                                # Fallback para informações genéricas
                                context['columns_summary'] = "Time, V1-V28 (features anônimas), Amount, Class"
                                context['shape'] = "284.807 transações, 31 colunas"
                                context['csv_analysis'] += "\n\nEstrutura genérica do dataset de fraudes (estatísticas aproximadas)"
                        
                        except Exception as e:
                            self.logger.error(f"❌ Erro ao calcular estatísticas reais: {str(e)}")
                            # Fallback para informações genéricas
                            context['columns_summary'] = "Time, V1-V28 (features anônimas), Amount, Class"
                            context['shape'] = "284.807 transações, 31 colunas"
                            context['csv_analysis'] += "\n\nEstrutura genérica do dataset de fraudes"
                    else:
                        # Informações genéricas quando Python Analyzer não disponível
                        context['columns_summary'] = "Time, V1-V28 (features anônimas), Amount, Class"
                        context['shape'] = "284.807 transações, 31 colunas"
                        context['csv_analysis'] += "\n\nEstrutura do dataset de fraudes:\n"
                        context['csv_analysis'] += "- Time: timestamp da transação\n"
                        context['csv_analysis'] += "- V1 a V28: features numéricas anônimas (PCA)\n"
                        context['csv_analysis'] += "- Amount: valor da transação (numérico)\n"
                        context['csv_analysis'] += "- Class: 0=normal, 1=fraude (categórico binário)"
            
            if columns_found:
                context['csv_analysis'] += f" Colunas identificadas: {', '.join(list(columns_found)[:10])}"
            
            # Tentar recuperar uma amostra dos dados reais usando RAG
            if "rag" in self.agents:
                try:
                    sample_query = "tipos dados colunas numéricos categóricos"  # Query mais específica e curta
                    rag_result = self.agents["rag"].process(sample_query, {})
                    if rag_result and not rag_result.get("metadata", {}).get("error", False):
                        # Adicionar informações do RAG ao contexto (LIMITADO)
                        rag_content = rag_result.get("content", "")
                        if rag_content and len(rag_content) > 50:  # Se temos conteúdo significativo
                            # LIMITAÇÃO: Usar apenas os primeiros 300 caracteres para evitar token overflow
                            context['csv_analysis'] += f"\n\nInformações dos dados:\n{rag_content[:300]}..."
                            self.logger.info("✅ Contexto enriquecido com dados do RAG (resumido)")
                except Exception as e:
                    self.logger.debug(f"⚠️ Erro ao recuperar amostra via RAG: {str(e)}")
                    # Se RAG falha, fornecer informação básica sobre o dataset de fraude
                    context['csv_analysis'] += "\n\nInformações básicas: Dataset contém transações de cartão de crédito com detecção de fraude."
            
            return context
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao recuperar contexto do Supabase: {str(e)}")
            return None
    
    def _classify_query(self, query: str, context: Optional[Dict[str, Any]]) -> QueryType:
        """Classifica o tipo de consulta para roteamento adequado.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
        
        Returns:
            Tipo da consulta identificado
        """
        query_lower = query.lower()
        
        # Verificar se é solicitação de visualização
        viz_type = self._detect_visualization_need(query)
        if viz_type:
            self.logger.info(f"📊 Visualização detectada: {viz_type}")
            # Adicionar flag ao contexto para processamento posterior
            if context is None:
                context = {}
            context['visualization_requested'] = viz_type
        
        # Palavras-chave para cada tipo de consulta
        csv_keywords = [
            'csv', 'tabela', 'dados', 'análise', 'estatística', 'correlação',
            'gráfico', 'plot', 'visualização', 'resumo', 'describe', 'dataset',
            'colunas', 'linhas', 'média', 'mediana', 'fraude', 'outlier',
            'tipos de dados', 'numéricos', 'categóricos', 'distribuição'
        ]
        
        rag_keywords = [
            'buscar', 'procurar', 'encontrar', 'pesquisar', 'consultar',
            'conhecimento', 'base', 'documento', 'texto', 'similar',
            'contexto', 'embedding', 'semântica', 'retrieval'
        ]
        
        data_keywords = [
            'carregar', 'upload', 'importar', 'abrir', 'arquivo',
            'dados sintéticos', 'gerar dados', 'criar dados', 'load'
        ]
        
        llm_keywords = [
            'explicar', 'explique', 'interpretar', 'interprete', 'insight', 'insights', 
            'conclusão', 'conclusões', 'recomendação', 'recomendações', 'recomende',
            'sugestão', 'sugestões', 'sugira', 'opinião', 'análise detalhada', 
            'relatório', 'sumário', 'resume', 'resumo detalhado', 'padrão', 'padrões', 
            'tendência', 'tendências', 'previsão', 'hipótese', 'teoria', 'tire', 'conclua',
            'analise', 'avalie', 'considere', 'entenda', 'compreenda', 'descoberta',
            'descobrimentos', 'comportamento', 'anomalia', 'anômalo', 'suspeito',
            'detalhado', 'profundo', 'aprofunde', 'discuta', 'comente', 'o que',
            'quais', 'como', 'por que', 'porque'
        ]
        
        general_keywords = [
            'olá', 'oi', 'ajuda', 'como', 'o que', 'qual', 'quando',
            'onde', 'por que', 'definir', 'status', 'sistema'
        ]
        
        # Verificar contexto de arquivo
        has_file_context = context and 'file_path' in context
        
        # CORREÇÃO: Verificar se há dados carregados no Supabase
        has_supabase_data = self._check_data_availability()
        
        # Classificar baseado em palavras-chave e contexto
        csv_score = sum(1 for kw in csv_keywords if kw in query_lower)
        rag_score = sum(1 for kw in rag_keywords if kw in query_lower)
        data_score = sum(1 for kw in data_keywords if kw in query_lower)
        llm_score = sum(3 for kw in llm_keywords if kw in query_lower)  # Peso triplicado para LLM
        general_score = sum(1 for kw in general_keywords if kw in query_lower)
        
        # NOVA LÓGICA: Se há dados no Supabase, priorizar LLM analysis
        if has_supabase_data and (csv_score > 0 or data_score > 0):
            self.logger.info("🔄 Redirecionando para LLM analysis (dados no Supabase detectados)")
            return QueryType.LLM_ANALYSIS
        
        # Adicionar peso do contexto
        if has_file_context:
            if any(ext in str(context.get('file_path', '')).lower() for ext in ['.csv', '.xlsx', '.json']):
                csv_score += 1  # Reduzido para não sobrepor LLM
        
        # Verificar se precisa de múltiplos agentes
        scores = [csv_score, rag_score, data_score, llm_score]
        high_scores = [s for s in scores if s >= 2]
        
        # Se LLM tem score alto, priorizar sobre hybrid
        if llm_score >= 3:
            return QueryType.LLM_ANALYSIS
        
        if len(high_scores) >= 2:
            return QueryType.HYBRID
        
        # Determinar tipo baseado na maior pontuação
        max_score = max(csv_score, rag_score, data_score, llm_score, general_score)
        
        if max_score == 0:
            return QueryType.UNKNOWN
        elif max_score == csv_score:
            return QueryType.CSV_ANALYSIS
        elif max_score == rag_score:
            return QueryType.RAG_SEARCH
        elif max_score == data_score:
            return QueryType.DATA_LOADING
        elif max_score == llm_score:
            return QueryType.LLM_ANALYSIS
        else:
            return QueryType.GENERAL
    
    def _handle_csv_analysis(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Delega análise CSV para o agente especializado."""
        if "csv" not in self.agents:
            return self._build_response(
                "❌ Agente de análise CSV não está disponível",
                metadata={"error": True, "agents_used": []}
            )
        
        self.logger.info("📊 Delegando para agente CSV")
        
        # Preparar contexto para o agente CSV
        csv_context = context or {}
        
        # Se há dados carregados no orquestrador, passar para o agente
        if self.current_data_context:
            csv_context.update(self.current_data_context)
        
        result = self.agents["csv"].process(query, csv_context)
        
        # Atualizar contexto se dados foram carregados
        if result.get("metadata") and not result["metadata"].get("error"):
            self.current_data_context.update(result["metadata"])
        
        return self._enhance_response(result, ["csv"])
    
    def _handle_rag_search(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Delega busca semântica para o agente RAG."""
        if "rag" not in self.agents:
            return self._build_response(
                "❌ Agente RAG não está disponível",
                metadata={"error": True, "agents_used": []}
            )
        
        self.logger.info("🔍 Delegando para agente RAG")
        
        result = self.agents["rag"].process(query, context)
        return self._enhance_response(result, ["rag"])
    
    def _handle_data_loading(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa carregamento de dados."""
        if not self.data_processor:
            return self._build_response(
                "❌ Sistema de carregamento de dados não está disponível",
                metadata={"error": True, "agents_used": []}
            )
        
        self.logger.info("📁 Processando carregamento de dados")
        
        try:
            # ⚠️ CONFORMIDADE: OrchestratorAgent NÃO deve carregar CSV para consultas
            # Este método deve ser usado apenas para ingestão inicial
            self.logger.warning("🚨 ATENÇÃO: OrchestratorAgent realizando carregamento de dados!")
            self.logger.warning("🚨 Consultas devem usar APENAS a tabela embeddings!")
            
            # Verificar se foi fornecido um arquivo
            if context and 'file_path' in context:
                file_path = context['file_path']
                
                # Carregar dados usando DataProcessor (que deve validar autorização)
                result = self.data_processor.load_from_file(file_path)
                
                if not result.get('error'):
                    # Armazenar contexto dos dados carregados
                    self.current_data_context = {
                        'file_path': file_path,
                        'data_info': result.get('data_info', {}),
                        'quality_report': result.get('quality_report', {})
                    }
                    
                    # Criar resposta informativa
                    data_info = result.get('data_info', {})
                    quality_report = result.get('quality_report', {})
                    
                    response = f"""✅ **Dados Carregados com Sucesso**

📄 **Arquivo:** {file_path}
📊 **Dimensões:** {data_info.get('rows', 0):,} linhas × {data_info.get('columns', 0)} colunas
⭐ **Qualidade:** {quality_report.get('overall_score', 0):.1f}/100

**Próximos passos disponíveis:**
• Análise exploratória: "faça um resumo dos dados"
• Correlações: "mostre as correlações"  
• Visualizações: "crie gráficos dos dados"
• Busca semântica: "busque informações sobre fraude"
"""
                    
                    return self._build_response(
                        response,
                        metadata={
                            "agents_used": ["data_processor"],
                            "data_loaded": True,
                            "file_path": file_path,
                            "data_info": data_info,
                            "quality_report": quality_report
                        }
                    )
                else:
                    return self._build_response(
                        f"❌ Erro ao carregar dados: {result.get('error', 'Erro desconhecido')}",
                        metadata={"error": True, "agents_used": ["data_processor"]}
                    )
            
            else:
                # Instruções de como carregar dados
                response = """📁 **Como Carregar Dados**

Para carregar dados, use:
```
context = {"file_path": "caminho/para/seu/arquivo.csv"}
```

**Formatos suportados:**
• CSV (.csv)
• Excel (.xlsx) - *em desenvolvimento*
• JSON (.json) - *em desenvolvimento*

**Dados sintéticos disponíveis:**
• Detecção de fraude
• Dados de vendas  
• Dados de clientes
• Dados genéricos
"""
                
                return self._build_response(
                    response,
                    metadata={"agents_used": [], "instructions": True}
                )
        
        except Exception as e:
            self.logger.error(f"Erro no carregamento: {str(e)}")
            return self._build_response(
                f"❌ Erro no carregamento de dados: {str(e)}",
                metadata={"error": True, "agents_used": ["data_processor"]}
            )

    def _handle_llm_analysis(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas através do LLM Manager com verificação de base de dados."""
        if not self.llm_manager:
            return self._build_response(
                "❌ LLM Manager não está disponível",
                metadata={"error": True, "agents_used": []}
            )
        
        self.logger.info("🤖 Delegando para LLM Manager")
        
        # 1. VERIFICAÇÃO OBRIGATÓRIA: Identificar se consulta requer dados específicos
        data_specific_keywords = [
            'tipos de dados', 'colunas', 'variáveis', 'estatísticas', 'resumo',
            'distribuição', 'correlação', 'missing', 'nulos', 'formato',
            'csv', 'arquivo', 'dataset', 'base de dados', 'planilha'
        ]
        
        needs_data_analysis = any(keyword in query.lower() for keyword in data_specific_keywords)
        
        # 2. VERIFICAR ESTADO DOS DADOS
        has_loaded_data = self._check_data_availability()
        has_file_context = bool(context and context.get("file_path"))
        
        self.logger.info(f"📊 Análise necessária: {needs_data_analysis}, Dados carregados: {has_loaded_data}, Arquivo no contexto: {has_file_context}")
        
        # 3. LÓGICA DE DECISÃO BASEADA NO ESTADO
        if needs_data_analysis and not has_loaded_data and not has_file_context:
            # Caso 1: Precisa de dados específicos mas não há nada carregado
            return self._build_response(
                """❓ **Base de Dados Necessária**
                
Sua pergunta requer análise de dados específicos, mas não há nenhuma base de dados carregada no momento.

**Opções disponíveis:**

🔸 **Análise específica**: Carregue um arquivo CSV primeiro:
   • "carregar arquivo dados.csv"
   • "analisar arquivo /caminho/para/arquivo.csv"

🔸 **Resposta genérica**: Se deseja uma explicação geral sobre o conceito, reformule sua pergunta:
   • "o que são tipos de dados em geral?"
   • "explique conceitos básicos de análise de dados"

**Como posso te ajudar?**""",
                metadata={
                    "error": False, 
                    "agents_used": ["llm_manager"],
                    "requires_data": True,
                    "data_available": False
                }
            )
        
        elif needs_data_analysis and not has_loaded_data and has_file_context:
            # Caso 2: Precisa de dados, tem arquivo no contexto, mas não carregou ainda
            self.logger.info("🔄 Carregando dados automaticamente para análise específica...")
            
            # Tentar carregar dados usando agente CSV
            if "csv" in self.agents:
                try:
                    load_query = f"carregar e analisar estrutura básica"
                    csv_result = self.agents["csv"].process(load_query, context)
                    
                    if csv_result and not csv_result.get("metadata", {}).get("error", False):
                        # Extrair informações do CSV e atualizar contexto
                        self._update_data_context_from_csv_result(csv_result, context)
                        self.logger.info("✅ Dados carregados automaticamente")
                    else:
                        return self._build_response(
                            f"❌ Não foi possível carregar o arquivo: {csv_result.get('content', 'Erro desconhecido')}",
                            metadata={"error": True, "agents_used": ["csv"]}
                        )
                except Exception as e:
                    return self._build_response(
                        f"❌ Erro ao carregar arquivo: {str(e)}",
                        metadata={"error": True, "agents_used": ["csv"]}
                    )
            else:
                return self._build_response(
                    "❌ Agente CSV não disponível para carregar dados",
                    metadata={"error": True, "agents_used": []}
                )
        
        # 4. PREPARAR CONTEXTO PARA LLM
        llm_context = context.copy() if context else {}
        
        # Adicionar dados carregados se disponíveis
        if self.current_data_context:
            llm_context.update(self.current_data_context)
        
        # NOVA FUNCIONALIDADE: Recuperar dados do Supabase quando necessário
        if needs_data_analysis and has_loaded_data and not llm_context.get("csv_analysis"):
            self.logger.info("🔍 Recuperando dados da base Supabase para análise...")
            try:
                # Recuperar informações sobre os dados armazenados
                supabase_data_context = self._retrieve_data_context_from_supabase()
                if supabase_data_context:
                    llm_context.update(supabase_data_context)
                    self.logger.info("✅ Contexto de dados recuperado do Supabase")
                else:
                    self.logger.warning("⚠️ Não foi possível recuperar contexto de dados do Supabase")
            except Exception as e:
                self.logger.error(f"❌ Erro ao recuperar dados do Supabase: {str(e)}")
        
        # 5. CONSTRUIR PROMPT CONTEXTUALIZADO
        prompt = self._build_llm_prompt(query, llm_context, needs_data_analysis)
        
        try:
            # 6. CHAMAR LLM MANAGER com configuração otimizada
            config = LLMConfig(temperature=0.2, max_tokens=512)  # Reduzir tokens de resposta
            response = self.llm_manager.chat(prompt, config)
            
            if not response.success:
                raise RuntimeError(response.error)
            
            # 7. APLICAR GUARDRAILS DE VALIDAÇÃO
            if GUARDRAILS_AVAILABLE and statistics_guardrails and needs_data_analysis:
                validation_result = statistics_guardrails.validate_response(response.content, llm_context)
                
                if not validation_result.is_valid and validation_result.confidence_score < 0.7:
                    self.logger.warning(f"⚠️ Resposta falhol na validação (score: {validation_result.confidence_score:.2f})")
                    self.logger.warning(f"Issues detectados: {', '.join(validation_result.issues[:3])}")
                    
                    # Se há valores corrigidos, tentar nova consulta com correções
                    if validation_result.corrected_values and len(validation_result.issues) <= 3:
                        correction_prompt = statistics_guardrails.generate_correction_prompt(validation_result)
                        
                        # Adicionar correções ao contexto
                        corrected_context = llm_context.copy()
                        corrected_context['correction_prompt'] = correction_prompt
                        
                        # Tentar novamente com correções
                        self.logger.info("🔄 Tentando nova consulta com correções...")
                        corrected_prompt = self._build_llm_prompt(query, corrected_context, needs_data_analysis)
                        
                        try:
                            config = LLMConfig(temperature=0.1, max_tokens=512)  # Temperatura mais baixa para precisão
                            corrected_response = self.llm_manager.chat(corrected_prompt, config)
                            
                            if corrected_response.success:
                                response = corrected_response
                                self.logger.info("✅ Resposta corrigida gerada com sucesso")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Falha na correção automática: {str(e)}")
                
                elif validation_result.confidence_score >= 0.7:
                    self.logger.info(f"✅ Resposta aprovada pelos guardrails (score: {validation_result.confidence_score:.2f})")
            
            # 8. CONSTRUIR RESPOSTA COM METADADOS CORRETOS
            result = {
                "content": response.content,
                "metadata": {
                    "provider": response.provider.value,
                    "model": response.model,
                    "processing_time": response.processing_time,
                    "tokens_used": response.tokens_used,
                    "data_analysis": needs_data_analysis,
                    "data_loaded": bool(self.current_data_context.get("csv_loaded", False))
                }
            }
            
            # 8. REGISTRAR AGENTES USADOS CORRETAMENTE
            agents_used = ["llm_manager"]
            if needs_data_analysis and self.current_data_context.get("csv_loaded"):
                agents_used.append("csv")  # CSV foi usado para carregar dados
            
            return self._enhance_response(result, agents_used)
            
        except Exception as e:
            self.logger.error(f"Erro no LLM Manager: {str(e)}")
            return self._build_response(
                f"❌ Erro na análise LLM: {str(e)}",
                metadata={"error": True, "agents_used": ["llm_manager"]}
            )
    
    def _handle_hybrid_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas que requerem múltiplos agentes."""
        self.logger.info("🔄 Processando consulta híbrida (múltiplos agentes)")
        
        results = []
        agents_used = []
        
        # Determinar quais agentes são necessários
        query_lower = query.lower()
        
        # CSV + RAG (ex: "analise os dados e busque informações similares")
        if any(kw in query_lower for kw in ['dados', 'csv', 'análise']) and \
           any(kw in query_lower for kw in ['buscar', 'similar', 'contexto']):
            
            # Primeiro: análise CSV se há dados
            if "csv" in self.agents and self.current_data_context:
                csv_result = self.agents["csv"].process(query, context)
                results.append(("csv", csv_result))
                agents_used.append("csv")
            
            # Segundo: busca RAG
            if "rag" in self.agents:
                rag_result = self.agents["rag"].process(query, context)
                results.append(("rag", rag_result))
                agents_used.append("rag")
        
        # Se nenhum resultado, usar abordagem padrão
        if not results:
            return self._handle_csv_analysis(query, context)
        
        # Combinar resultados
        combined_response = self._combine_agent_responses(results)
        
        return self._build_response(
            combined_response,
            metadata={"agents_used": agents_used, "hybrid_query": True}
        )
    
    def _handle_general_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas gerais/conversacionais."""
        self.logger.info("💬 Processando consulta geral")
        
        query_lower = query.lower()
        
        # Saudações
        if any(greeting in query_lower for greeting in ['olá', 'oi', 'ola']):
            response = """👋 **Olá! Sou o Orquestrador do Sistema EDA AI Minds**

Sou o coordenador central que pode te ajudar com:

🔍 **Análise de Dados CSV**
• Carregamento e validação de arquivos
• Estatísticas e correlações  
• Visualizações e insights

🧠 **Busca Semântica (RAG)**
• Consultas contextualizadas
• Base de conhecimento vetorial
• Respostas inteligentes

**Como posso te ajudar hoje?**
"""
            return self._build_response(response, metadata={"agents_used": [], "greeting": True})
        
        # Status do sistema
        elif any(status in query_lower for status in ['status', 'sistema', 'agentes']):
            return self._get_system_status()
        
        # Ajuda
        elif 'ajuda' in query_lower or 'help' in query_lower:
            return self._get_help_response()
        
        # Usar LLM Manager para resposta geral se disponível
        elif self.llm_manager:
            try:
                prompt = self._build_llm_prompt(query, context)
                config = LLMConfig(temperature=0.3, max_tokens=512)  # Mais criativo para consultas gerais
                response = self.llm_manager.chat(prompt, config)
                
                if response.success:
                    result = {"content": response.content}
                    return self._enhance_response(result, ["llm_manager"])
                else:
                    raise RuntimeError(response.error)
                    
            except Exception as e:
                self.logger.warning(f"Erro ao usar LLM Manager para consulta geral: {str(e)}")
                # Fallback para resposta padrão
                response = "Desculpe, não consegui processar sua consulta com o LLM. Tente ser mais específico ou pergunte sobre análise de dados CSV."
                return self._build_response(response, metadata={"agents_used": [], "fallback": True})
        
        # Resposta padrão quando LLM não está disponível
        else:
            response = """💭 **Consulta Geral Recebida**

Como não tenho acesso ao LLM no momento, posso te ajudar especificamente com:

📊 **Análise de Dados CSV:**
• "analise o arquivo dados.csv"
• "mostre correlações"
• "detecte fraudes"

🔍 **Carregamento de Dados:**  
• "carregue o arquivo X"
• "valide os dados"

**Tente ser mais específico sobre dados ou análises!**
"""
            return self._build_response(response, metadata={"agents_used": [], "general_query": True})
    
    def _handle_unknown_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa consultas de tipo desconhecido."""
        self.logger.warning(f"🤔 Consulta de tipo desconhecido: {query[:50]}...")
        
        response = f"""🤔 **Não consegui identificar o tipo da sua consulta**

**Sua consulta:** "{query}"

**Posso te ajudar com:**
• 📊 **Análise de dados:** "analise o arquivo dados.csv"
• 🔍 **Busca semântica:** "busque informações sobre fraude"
• 📁 **Carregar dados:** use context={{"file_path": "arquivo.csv"}}

**Reformule sua pergunta ou seja mais específico sobre o que precisa.**
"""
        
        return self._build_response(response, metadata={"agents_used": [], "unknown_query": True})
    
    def _combine_agent_responses(self, results: List[Tuple[str, Dict[str, Any]]]) -> str:
        """Combina respostas de múltiplos agentes em uma resposta coesa."""
        if not results:
            return "Nenhum resultado disponível."
        
        combined = "🔄 **Resposta Consolidada de Múltiplos Agentes**\n\n"
        
        for agent_name, result in results:
            agent_display = {
                "csv": "📊 **Análise CSV**",
                "rag": "🔍 **Busca Semântica**"
            }.get(agent_name, f"🤖 **{agent_name.upper()}**")
            
            combined += f"{agent_display}\n"
            combined += f"{result.get('content', 'Sem conteúdo')}\n\n"
            combined += "─" * 50 + "\n\n"
        
        return combined.rstrip("─\n ")
    
    def _enhance_response(self, agent_result: Dict[str, Any], agents_used: List[str]) -> Dict[str, Any]:
        """Melhora resposta do agente com informações do orquestrador."""
        if not agent_result:
            return self._build_response("Erro: resposta vazia do agente", metadata={"error": True})
        
        # Preservar conteúdo original
        enhanced = agent_result.copy()
        
        # Adicionar informações do orquestrador
        if "metadata" not in enhanced:
            enhanced["metadata"] = {}
        
        # CORREÇÃO: Registrar agentes usados no nível principal da metadata
        enhanced["metadata"]["agents_used"] = agents_used
        enhanced["metadata"]["orchestrator"] = {
            "conversation_length": len(self.conversation_history),
            "has_data_context": bool(self.current_data_context)
        }
        
        return enhanced
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema."""
        status_info = {
            "agents": {},
            "data_context": bool(self.current_data_context),
            "conversation_history": len(self.conversation_history)
        }
        
        # Status dos agentes
        for name, agent in self.agents.items():
            status_info["agents"][name] = {
                "available": True,
                "name": agent.name,
                "description": agent.description
            }
        
        # Status do data processor
        if self.data_processor:
            status_info["data_processor"] = {"available": True}
        
        # Informações sobre dados carregados
        data_info = ""
        if self.current_data_context:
            file_path = self.current_data_context.get('file_path', 'N/A')
            data_info = f"\n📁 **Dados Carregados:** {file_path}"
        
        response = f"""⚡ **Status do Sistema EDA AI Minds**

🤖 **Agentes Disponíveis:** {len(self.agents)}
{chr(10).join(f'• {name.upper()}: {agent.description}' for name, agent in self.agents.items())}

💾 **Data Processor:** {'✅ Ativo' if self.data_processor else '❌ Inativo'}
💬 **Histórico:** {len(self.conversation_history)} interações{data_info}

🚀 **Sistema Operacional e Pronto!**
"""
        
        return self._build_response(response, metadata=status_info)
    
    def _get_help_response(self) -> Dict[str, Any]:
        """Retorna informações de ajuda completas."""
        help_text = """📚 **Guia de Uso do Sistema EDA AI Minds**

## 🔍 **Tipos de Consulta**

### 📊 **Análise de Dados CSV**
```python
# Carregar arquivo
context = {"file_path": "dados.csv"}
query = "carregue os dados"

# Análises
"faça um resumo dos dados"
"mostre as correlações"
"analise fraudes"
"crie visualizações"
```

### 🧠 **Busca Semântica (RAG)**
```python
"busque informações sobre detecção de fraude"
"encontre dados similares a transações suspeitas"
"qual o contexto sobre análise de risco?"
```

### 📁 **Carregamento de Dados**
```python
"carregar arquivo CSV"
"importar dados"
"gerar dados sintéticos"
```

## 💡 **Dicas**
• Seja específico nas consultas
• Use contexto para fornecer arquivos
• Combine diferentes tipos de análise
• Pergunte sobre status do sistema

**Exemplo Completo:**
```python
# 1. Carregar dados
context = {"file_path": "fraude.csv"}
"carregue e analise os dados"

# 2. Análise específica  
"mostre correlações entre valor e fraude"

# 3. Busca contextual
"busque padrões similares na base de conhecimento"
```
"""
        
        return self._build_response(help_text, metadata={"help": True, "agents_used": []})
    
    # ========================================================================
    # MÉTODOS DE PROCESSAMENTO COM MEMÓRIA
    # ========================================================================
    
    async def process_with_persistent_memory(self, query: str, context: Optional[Dict[str, Any]] = None,
                                           session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa consulta utilizando sistema de memória persistente Supabase.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
            session_id: ID da sessão (inicializa se None)
            
        Returns:
            Resposta processada com persistência de memória
        """
        self.logger.info(f"🧠 Processando com memória persistente: '{query[:50]}...'")
        
        try:
            # 1. Inicializar sessão de memória se necessário
            if session_id and self.has_memory:
                if not self._current_session_id or self._current_session_id != session_id:
                    await self.init_memory_session(session_id)
            elif not self._current_session_id and self.has_memory:
                session_id = await self.init_memory_session()
            
            # 2. Recuperar contexto de memória
            memory_context = {}
            if self.has_memory and self._current_session_id:
                memory_context = await self.recall_conversation_context()
                self.logger.debug(f"Contexto de memória recuperado: {len(memory_context.get('recent_conversations', []))} interações")
                
                # Mescla contexto de memória com contexto atual
                if context:
                    context.update({"memory_context": memory_context})
                else:
                    context = {"memory_context": memory_context}
            
            # 3. Verificar cache de análises
            analysis_cache_key = None
            if context and context.get('file_path'):
                analysis_cache_key = f"analysis_{hash(query + str(context.get('file_path')))}"
                cached_result = await self.recall_cached_analysis(analysis_cache_key)
                if cached_result:
                    self.logger.info("📦 Resultado recuperado do cache de análises")
                    cached_result['metadata']['from_cache'] = True
                    return cached_result
            
            # 4. Processar consulta normalmente
            result = self.process(query, context)
            
            # 5. Salvar interação na memória persistente
            if self.has_memory and self._current_session_id:
                await self.remember_interaction(
                    query=query,
                    response=result.get('content', str(result)),
                    metadata=result.get('metadata', {})
                )
                
                # 6. Cachear resultado de análise se aplicável
                if analysis_cache_key and result.get('metadata', {}).get('query_type') in ['csv_analysis', 'llm_analysis']:
                    await self.remember_analysis_result(analysis_cache_key, result, expiry_hours=24)
                
                # 7. Salvar contexto de dados se carregado
                if context and context.get('file_path'):
                    data_context = {
                        'file_path': context['file_path'],
                        'last_query': query,
                        'timestamp': self._get_timestamp()
                    }
                    await self.remember_data_context(data_context, "current_data")
            
            # 8. Adicionar informações de memória à resposta
            if self.has_memory:
                result.setdefault('metadata', {})['session_id'] = self._current_session_id
                result.setdefault('metadata', {})['memory_enabled'] = True
                
                # Estatísticas de memória
                memory_stats = await self.get_memory_stats()
                result.setdefault('metadata', {})['memory_stats'] = memory_stats
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro no processamento com memória: {e}")
            # Fallback para processamento sem memória
            return self.process(query, context)
    
    # ========================================================================
    # MÉTODOS DE GESTÃO DE MEMÓRIA PARA COMPATIBILIDADE
    # ========================================================================
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retorna histórico completo da conversa (compatibilidade).
        
        DEPRECIADO: Use get_persistent_conversation_history() para memória Supabase.
        """
        return self.conversation_history.copy()
    
    async def get_persistent_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna histórico de conversação da memória persistente."""
        if not self.has_memory or not self._current_session_id:
            return self.get_conversation_history()  # Fallback
        
        try:
            conversations = await self.recall_conversation()
            return conversations[:limit]
        except Exception as e:
            self.logger.error(f"Erro ao recuperar histórico persistente: {e}")
            return self.get_conversation_history()  # Fallback
    
    def clear_conversation_history(self) -> Dict[str, Any]:
        """Limpa histórico da conversa (compatibilidade).
        
        DEPRECIADO: Use clear_persistent_memory() para memória Supabase.
        """
        count = len(self.conversation_history)
        self.conversation_history.clear()
        self.logger.info(f"Histórico limpo: {count} interações removidas")
        
        return self._build_response(
            f"✅ Histórico limpo: {count} interações removidas",
            metadata={"cleared_count": count}
        )
    
    async def clear_persistent_memory(self) -> Dict[str, Any]:
        """Limpa memória persistente da sessão atual."""
        if not self.has_memory or not self._current_session_id:
            return self.clear_conversation_history()  # Fallback
        
        try:
            # Implementar limpeza via memory manager se necessário
            # Por enquanto, inicia nova sessão
            old_session = self._current_session_id
            await self.init_memory_session()
            
            return self._build_response(
                f"✅ Memória persistente limpa. Nova sessão: {self._current_session_id}",
                metadata={"old_session": old_session, "new_session": self._current_session_id}
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar memória persistente: {e}")
            return self.clear_conversation_history()  # Fallback
    
    def clear_data_context(self) -> Dict[str, Any]:
        """Limpa contexto de dados carregados (compatibilidade).
        
        DEPRECIADO: Use clear_persistent_data_context() para memória Supabase.
        """
        if self.current_data_context:
            file_path = self.current_data_context.get('file_path', 'N/A')
            self.current_data_context.clear()
            self.logger.info(f"Contexto de dados limpo: {file_path}")
            
            return self._build_response(
                f"✅ Contexto de dados limpo: {file_path}",
                metadata={"cleared_data": file_path}
            )
        else:
            return self._build_response(
                "ℹ️ Nenhum contexto de dados para limpar",
                metadata={"no_data_context": True}
            )
    
    async def clear_persistent_data_context(self) -> Dict[str, Any]:
        """Limpa contexto de dados da memória persistente."""
        if not self.has_memory or not self._current_session_id:
            return self.clear_data_context()  # Fallback
        
        try:
            # Aqui implementaríamos limpeza específica do contexto de dados
            # Por simplicidade, vamos usar o método de compatibilidade
            result = self.clear_data_context()
            
            # Também limpar do sistema de memória se houver implementação específica
            self.logger.info("Contexto de dados persistente limpo")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar contexto de dados persistente: {e}")
            return self.clear_data_context()  # Fallback
    
    def _update_data_context_from_csv_result(self, csv_result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Atualiza contexto de dados com resultado da análise CSV."""
        try:
            csv_content = csv_result.get("content", "")
            
            # Extrair informações básicas do resultado CSV
            data_info = {
                "file_path": context.get("file_path", ""),
                "csv_loaded": True,
                "structure_analyzed": True,
                "csv_analysis": csv_content
            }
            
            # Tentar extrair informações específicas do conteúdo
            if "Colunas:" in csv_content:
                # Extrair lista de colunas se disponível
                lines = csv_content.split('\n')
                for i, line in enumerate(lines):
                    if "Colunas:" in line and i + 1 < len(lines):
                        columns_info = lines[i + 1].strip()
                        data_info["columns_summary"] = columns_info
                        break
            
            if "Shape:" in csv_content:
                # Extrair informações de shape
                lines = csv_content.split('\n')
                for line in lines:
                    if "Shape:" in line:
                        shape_info = line.replace("Shape:", "").strip()
                        data_info["shape"] = shape_info
                        break
            
            # Atualizar contexto global
            self.current_data_context.update(data_info)
            self.logger.info(f"✅ Contexto de dados atualizado: {data_info['file_path']}")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar contexto de dados: {e}")

    def get_available_agents(self) -> Dict[str, Any]:
        """Retorna informações sobre agentes disponíveis."""
        agents_info = {}
        
        for name, agent in self.agents.items():
            agents_info[name] = {
                "name": agent.name,
                "description": agent.description,
                "class": agent.__class__.__name__
            }
        
        response = "🤖 **Agentes Disponíveis**\n\n"
        for name, info in agents_info.items():
            response += f"• **{name.upper()}**: {info['description']}\n"
        
        return self._build_response(response, metadata={"agents": agents_info})

    def _build_llm_prompt(self, query: str, context: Optional[Dict[str, Any]] = None, needs_data_analysis: bool = False) -> Tuple[str, Optional[str]]:
        """Constrói prompt contextualizado para o LLM Manager.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional (dados, histórico, etc.)
            needs_data_analysis: Se a consulta requer análise de dados específicos
            
        Returns:
            Tuple[str, Optional[str]]: (user_prompt, system_prompt)
        """
        prompt_parts = []
        
        # Instrução base diferenciada
        if needs_data_analysis and context and context.get("csv_loaded"):
            prompt_parts.append("""Você é um assistente especializado em análise de dados CSV.
Responda com base ESPECIFICAMENTE nos dados carregados fornecidos no contexto.
Use português brasileiro e seja preciso e detalhado sobre os dados reais.""")
        else:
            prompt_parts.append("""Você é um assistente de análise de dados especializado em CSV e análise estatística.
Responda de forma clara, precisa e útil. Use português brasileiro.""")
        
        # Adicionar contexto de dados se disponível
        if context:
            if 'file_path' in context:
                prompt_parts.append(f"\n📊 ARQUIVO CARREGADO: {context['file_path']}")
            
            if 'csv_analysis' in context:
                prompt_parts.append(f"\n📈 ANÁLISE DOS DADOS:\n{context['csv_analysis']}")
                
            if 'columns_summary' in context:
                prompt_parts.append(f"\n📋 COLUNAS: {context['columns_summary']}")
                
            if 'shape' in context:
                prompt_parts.append(f"\n� DIMENSÕES: {context['shape']}")
        
        # Adicionar a consulta do usuário
        prompt_parts.append(f"\n❓ CONSULTA DO USUÁRIO: {query}")
        
        # Instrução final diferenciada
        if needs_data_analysis and context and context.get("csv_loaded"):
            prompt_parts.append("""\n🎯 INSTRUÇÕES CRÍTICAS PARA ANÁLISE DE DADOS:
- Use EXCLUSIVAMENTE os dados reais fornecidos no contexto
- Para tipos de dados: Base-se apenas nos dtypes técnicos (int64=numérico, object=categórico)
- Para estatísticas: Use apenas os valores calculados fornecidos
- Para distribuições: Use apenas as contagens reais fornecidas
- NÃO interprete semanticamente nomes de colunas
- NÃO faça suposições além dos dados fornecidos
- Seja preciso sobre números e estatísticas REAIS
- Se a informação não está no contexto, diga que não tem acesso a ela""")
        else:
            prompt_parts.append("\n🎯 Forneça uma resposta útil e estruturada:")
        
        # Adicionar correções se disponíveis
        if context and 'correction_prompt' in context:
            prompt_parts.append(f"\n{context['correction_prompt']}")
            prompt_parts.append("\nRefaça sua resposta com os valores corretos fornecidos acima.")
        
        return "\n".join(prompt_parts)