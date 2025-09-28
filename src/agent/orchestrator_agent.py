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
from src.agent.csv_analysis_agent import CSVAnalysisAgent
from src.data.data_processor import DataProcessor

# Import condicional do RAGAgent (pode falhar se Supabase não configurado)
try:
    from src.agent.rag_agent import RAGAgent
    RAG_AGENT_AVAILABLE = True
except ImportError as e:
    RAG_AGENT_AVAILABLE = False
    RAGAgent = None
    print(f"⚠️ RAGAgent não disponível: {str(e)[:100]}...")
except RuntimeError as e:
    RAG_AGENT_AVAILABLE = False  
    RAGAgent = None
    print(f"⚠️ RAGAgent não disponível: {str(e)[:100]}...")

# Import condicional do GoogleLLMAgent
try:
    from src.agent.google_llm_agent import GoogleLLMAgent
    GOOGLE_LLM_AGENT_AVAILABLE = True
except ImportError as e:
    GOOGLE_LLM_AGENT_AVAILABLE = False
    GoogleLLMAgent = None
    print(f"⚠️ GoogleLLMAgent não disponível: {str(e)[:100]}...")
except RuntimeError as e:
    GOOGLE_LLM_AGENT_AVAILABLE = False
    GoogleLLMAgent = None
    print(f"⚠️ GoogleLLMAgent não disponível: {str(e)[:100]}...")


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
                 enable_google_llm_agent: bool = True,
                 enable_data_processor: bool = True):
        """Inicializa o orquestrador com agentes especializados.
        
        Args:
            enable_csv_agent: Habilitar agente de análise CSV
            enable_rag_agent: Habilitar agente RAG
            enable_google_llm_agent: Habilitar agente Google LLM
            enable_data_processor: Habilitar processador de dados
        """
        super().__init__(
            name="orchestrator",
            description="Coordenador central do sistema multiagente de IA para análise de dados"
        )
        
        # Inicializar agentes especializados
        self.agents = {}
        self.conversation_history = []
        self.current_data_context = {}
        
        # Inicializar agentes com tratamento de erro gracioso
        initialization_errors = []
        
        # CSV Agent (sempre disponível - sem dependências externas)
        if enable_csv_agent:
            try:
                self.agents["csv"] = CSVAnalysisAgent()
                self.logger.info("✅ Agente CSV inicializado")
            except Exception as e:
                error_msg = f"CSV Agent: {str(e)}"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")
        
        # RAG Agent (requer Supabase configurado)
        if enable_rag_agent and RAG_AGENT_AVAILABLE:
            try:
                self.agents["rag"] = RAGAgent()
                self.logger.info("✅ Agente RAG inicializado")
            except Exception as e:
                error_msg = f"RAG Agent: {str(e)}"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")
        elif enable_rag_agent and not RAG_AGENT_AVAILABLE:
            error_msg = "RAG Agent: Dependências não disponíveis (Supabase não configurado)"
            initialization_errors.append(error_msg)
            self.logger.warning(f"⚠️ {error_msg}")

        # Google LLM Agent (requer Google API Key configurada)
        if enable_google_llm_agent and GOOGLE_LLM_AGENT_AVAILABLE:
            try:
                self.agents["llm"] = GoogleLLMAgent()
                self.logger.info("✅ Agente Google LLM inicializado")
            except Exception as e:
                error_msg = f"Google LLM Agent: {str(e)}"
                initialization_errors.append(error_msg)
                self.logger.warning(f"⚠️ {error_msg}")
        elif enable_google_llm_agent and not GOOGLE_LLM_AGENT_AVAILABLE:
            error_msg = "Google LLM Agent: Dependências não disponíveis (Google AI não instalado)"
            initialization_errors.append(error_msg)
            self.logger.warning(f"⚠️ {error_msg}")
        
        # Data Processor (sempre disponível - sem dependências externas)  
        if enable_data_processor:
            try:
                self.data_processor = DataProcessor()
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
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa consulta determinando agente(s) apropriado(s).
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional (file_path, dados, configurações)
        
        Returns:
            Resposta consolidada do sistema
        """
        self.logger.info(f"🎯 Processando consulta: '{query[:50]}...'")
        
        try:
            # 1. Adicionar à história da conversa
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
    
    def _classify_query(self, query: str, context: Optional[Dict[str, Any]]) -> QueryType:
        """Classifica o tipo de consulta para roteamento adequado.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
        
        Returns:
            Tipo da consulta identificado
        """
        query_lower = query.lower()
        
        # Palavras-chave para cada tipo de consulta
        csv_keywords = [
            'csv', 'tabela', 'dados', 'análise', 'estatística', 'correlação',
            'gráfico', 'plot', 'visualização', 'resumo', 'describe', 'dataset',
            'colunas', 'linhas', 'média', 'mediana', 'fraude', 'outlier'
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
        
        # Classificar baseado em palavras-chave e contexto
        csv_score = sum(1 for kw in csv_keywords if kw in query_lower)
        rag_score = sum(1 for kw in rag_keywords if kw in query_lower)
        data_score = sum(1 for kw in data_keywords if kw in query_lower)
        llm_score = sum(3 for kw in llm_keywords if kw in query_lower)  # Peso triplicado para LLM
        general_score = sum(1 for kw in general_keywords if kw in query_lower)
        
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
            # Verificar se foi fornecido um arquivo
            if context and 'file_path' in context:
                file_path = context['file_path']
                
                # Carregar dados usando DataProcessor
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
        """Processa análises via Google LLM."""
        if "llm" not in self.agents:
            return self._build_response(
                "❌ Agente Google LLM não está disponível",
                metadata={"error": True, "agents_used": []}
            )
        
        self.logger.info("🤖 Delegando para agente Google LLM")
        
        # Preparar contexto para o LLM
        llm_context = context or {}
        
        # Se há dados carregados, incluir informações básicas
        if hasattr(self, 'current_data_context') and self.current_data_context:
            llm_context.update(self.current_data_context)
        
        try:
            result = self.agents["llm"].process(query, llm_context)
            return self._enhance_response(result, ["llm"])
        except Exception as e:
            self.logger.error(f"Erro no agente LLM: {str(e)}")
            return self._build_response(
                f"❌ Erro na análise LLM: {str(e)}",
                metadata={"error": True, "agents_used": ["llm"]}
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
        
        # Usar LLM para resposta geral se disponível
        elif "llm" in self.agents:
            try:
                result = self.agents["llm"].process(query, context)
                return self._enhance_response(result, ["llm"])
            except Exception as e:
                self.logger.warning(f"Erro ao usar LLM para consulta geral: {str(e)}")
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
        
        enhanced["metadata"]["orchestrator"] = {
            "agents_used": agents_used,
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
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retorna histórico completo da conversa."""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> Dict[str, Any]:
        """Limpa histórico da conversa."""
        count = len(self.conversation_history)
        self.conversation_history.clear()
        self.logger.info(f"Histórico limpo: {count} interações removidas")
        
        return self._build_response(
            f"✅ Histórico limpo: {count} interações removidas",
            metadata={"cleared_count": count}
        )
    
    def clear_data_context(self) -> Dict[str, Any]:
        """Limpa contexto de dados carregados."""
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