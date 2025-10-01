"""Classe base para agentes do sistema multiagente.

Esta classe fornece a estrutura comum para todos os agentes especializados:
- Logging centralizado
- Interface padronizada de comunicação
- Integração com LLM Manager (abstração para múltiplos provedores)
- Sistema de memória persistente
- Tratamento de erros
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.utils.logging_config import get_logger

# Import do LLM Manager para abstração de provedores
try:
    from src.llm.manager import get_llm_manager, LLMConfig, LLMResponse
    LLM_MANAGER_AVAILABLE = True
except ImportError:
    LLM_MANAGER_AVAILABLE = False
    get_llm_manager = None
    LLMConfig = None
    LLMResponse = None

# Import do sistema de memória
try:
    from src.memory import MemoryMixin, SupabaseMemoryManager, MemoryConfig
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryMixin = None
    SupabaseMemoryManager = None
    MemoryConfig = None

class AgentError(Exception):
    """Exceção específica para erros em agentes."""
    pass


class BaseAgent(ABC):
    """Classe base abstrata para todos os agentes do sistema."""
    
    def __init__(self, name: str, description: str = "", enable_memory: bool = True):
        """Inicializa o agente base.
        
        Args:
            name: Nome único do agente
            description: Descrição das responsabilidades do agente
            enable_memory: Se deve habilitar sistema de memória
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f"agent.{name}")
        
        # Inicializa sistema de memória se disponível e habilitado
        self._memory_manager = None
        self._current_session_id = None
        self._memory_enabled = enable_memory and MEMORY_AVAILABLE
        
        if self._memory_enabled:
            try:
                self._memory_manager = SupabaseMemoryManager(self.name)
                self.logger.info(f"Sistema de memória habilitado para agente {name}")
            except Exception as e:
                self.logger.warning(f"Falha ao inicializar memória: {e}")
                self._memory_enabled = False
        
        self.logger.info(f"Agente {name} inicializado: {description}")
    
    # ========================================================================
    # PROPRIEDADES DE MEMÓRIA
    # ========================================================================
    
    @property
    def has_memory(self) -> bool:
        """Verifica se o agente tem sistema de memória habilitado."""
        return self._memory_enabled and self._memory_manager is not None
    
    @property
    def current_session(self) -> Optional[str]:
        """Retorna ID da sessão atual."""
        return self._current_session_id
    
    # ========================================================================
    # MÉTODOS DE MEMÓRIA
    # ========================================================================
    
    async def init_memory_session(self, session_id: Optional[str] = None, 
                                user_id: Optional[str] = None) -> Optional[str]:
        """
        Inicializa uma sessão de memória.
        
        Args:
            session_id: ID da sessão (gera novo se None)
            user_id: ID do usuário
            
        Returns:
            ID da sessão criada ou None se memória não disponível
        """
        if not self.has_memory:
            self.logger.debug("Sistema de memória não disponível")
            return None
        
        try:
            self._current_session_id = await self._memory_manager.initialize_session(
                session_id, user_id, {'agent_name': self.name}
            )
            self.logger.info(f"Sessão de memória iniciada: {self._current_session_id}")
            return self._current_session_id
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sessão de memória: {e}")
            return None
    
    async def remember_interaction(self, query: str, response: str, 
                                 processing_time_ms: Optional[int] = None,
                                 confidence: Optional[float] = None,
                                 model_used: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Salva uma interação completa (query + response) na memória.
        
        Args:
            query: Consulta do usuário
            response: Resposta do agente
            processing_time_ms: Tempo de processamento
            confidence: Score de confiança
            model_used: Modelo LLM utilizado
            metadata: Metadados adicionais
            
        Returns:
            True se salvo com sucesso
        """
        if not self.has_memory or not self._current_session_id:
            return False
        
        try:
            # Salva query
            await self._memory_manager.add_user_query(
                query, self._current_session_id, metadata
            )
            
            # Salva response
            await self._memory_manager.add_agent_response(
                response, self._current_session_id, 
                processing_time_ms, confidence, model_used, metadata
            )
            
            self.logger.debug("Interação salva na memória")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar interação: {e}")
            return False
    
    async def remember_data_context(self, data_info: Dict[str, Any], 
                                  context_key: str = "current_data") -> bool:
        """
        Salva contexto de dados na memória.
        
        Args:
            data_info: Informações dos dados
            context_key: Chave do contexto
            
        Returns:
            True se salvo com sucesso
        """
        if not self.has_memory or not self._current_session_id:
            return False
        
        try:
            await self._memory_manager.store_data_context(
                self._current_session_id, data_info, context_key
            )
            self.logger.debug(f"Contexto de dados salvo: {context_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar contexto de dados: {e}")
            return False
    
    async def remember_analysis_result(self, analysis_key: str, result: Dict[str, Any],
                                     expiry_hours: int = 24) -> bool:
        """
        Faz cache de resultado de análise.
        
        Args:
            analysis_key: Chave única da análise
            result: Resultado da análise
            expiry_hours: Horas até expirar
            
        Returns:
            True se salvo com sucesso
        """
        if not self.has_memory or not self._current_session_id:
            return False
        
        try:
            await self._memory_manager.cache_analysis_result(
                self._current_session_id, analysis_key, result, expiry_hours
            )
            self.logger.debug(f"Resultado de análise cacheado: {analysis_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear análise: {e}")
            return False
    
    async def recall_cached_analysis(self, analysis_key: str) -> Optional[Dict[str, Any]]:
        """
        Recupera resultado de análise do cache.
        
        Args:
            analysis_key: Chave da análise
            
        Returns:
            Resultado da análise ou None
        """
        if not self.has_memory or not self._current_session_id:
            return None
        
        try:
            result = await self._memory_manager.get_cached_analysis(
                self._current_session_id, analysis_key
            )
            if result:
                self.logger.debug(f"Análise recuperada do cache: {analysis_key}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar análise cacheada: {e}")
            return None
    
    async def recall_conversation_context(self, hours: int = 24) -> Dict[str, Any]:
        """
        Recupera contexto de conversação recente.
        
        Args:
            hours: Horas de contexto para recuperar
            
        Returns:
            Contexto agregado da conversação
        """
        if not self.has_memory or not self._current_session_id:
            return {}
        
        try:
            context = await self._memory_manager.get_recent_context(
                self._current_session_id, hours
            )
            self.logger.debug(f"Contexto recuperado: {hours}h de histórico")
            return context
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar contexto: {e}")
            return {}
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Recupera estatísticas de uso da memória.
        
        Returns:
            Estatísticas de memória
        """
        if not self.has_memory or not self._current_session_id:
            return {'memory_available': False}
        
        try:
            stats = await self._memory_manager.get_memory_stats(self._current_session_id)
            stats['memory_available'] = True
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar estatísticas: {e}")
            return {'memory_available': False, 'error': str(e)}
    
    # ========================================================================
    # MÉTODOS DE VISUALIZAÇÃO
    # ========================================================================
    
    def generate_visualization(self, data: Any, viz_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Gera visualização gráfica usando GraphGenerator.
        
        Args:
            data: Dados para visualizar (DataFrame, Series, etc.)
            viz_type: Tipo de visualização ('histogram', 'scatter', 'boxplot', 'bar', 'heatmap')
            **kwargs: Parâmetros específicos para o tipo de gráfico
            
        Returns:
            Dict com imagem (base64 ou caminho) e estatísticas, ou None se erro
        """
        try:
            from src.tools.graph_generator import GraphGenerator
            
            generator = GraphGenerator()
            
            if viz_type == 'histogram':
                img, stats = generator.histogram(data, **kwargs)
            elif viz_type == 'scatter':
                img, stats = generator.scatter_plot(data, **kwargs)
            elif viz_type == 'boxplot':
                img, stats = generator.boxplot(data, **kwargs)
            elif viz_type == 'bar':
                img, stats = generator.bar_chart(data, **kwargs)
            elif viz_type == 'heatmap':
                img, stats = generator.correlation_heatmap(data, **kwargs)
            else:
                self.logger.warning(f"Tipo de visualização não suportado: {viz_type}")
                return None
            
            self.logger.info(f"Visualização '{viz_type}' gerada com sucesso")
            return {
                'image': img,
                'statistics': stats,
                'type': viz_type
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar visualização: {e}")
            return None
    
    # ========================================================================
    # MÉTODOS ABSTRATOS
    # ========================================================================
    
    @abstractmethod
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Processa uma consulta e retorna uma resposta.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional (dados, histórico, etc.)
        
        Returns:
            Dict com resposta processada e metadados
        """
        pass
    
    # ========================================================================
    # MÉTODOS DE PROCESSAMENTO COM MEMÓRIA
    # ========================================================================
    
    async def process_with_memory(self, query: str, context: Optional[Dict[str, Any]] = None,
                                session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa consulta utilizando sistema de memória.
        
        Args:
            query: Consulta do usuário
            context: Contexto adicional
            session_id: ID da sessão (inicializa se None)
            
        Returns:
            Resposta processada com metadados de memória
        """
        start_time = None
        
        try:
            import time
            start_time = time.time()
            
            # Inicializa sessão se necessário
            if session_id and self.has_memory:
                if not self._current_session_id or self._current_session_id != session_id:
                    await self.init_memory_session(session_id)
            elif not self._current_session_id and self.has_memory:
                await self.init_memory_session()
            
            # Recupera contexto de memória se disponível
            memory_context = {}
            if self.has_memory and self._current_session_id:
                memory_context = await self.recall_conversation_context()
                if context:
                    context.update({"memory_context": memory_context})
                else:
                    context = {"memory_context": memory_context}
            
            # Processa a consulta (método abstrato implementado pelas subclasses)
            response = self.process(query, context)
            
            # Calcula tempo de processamento
            processing_time_ms = None
            if start_time:
                processing_time_ms = int((time.time() - start_time) * 1000)
                response.setdefault('metadata', {})['processing_time_ms'] = processing_time_ms
            
            # Salva interação na memória
            if self.has_memory and self._current_session_id:
                await self.remember_interaction(
                    query=query,
                    response=response.get('content', str(response)),
                    processing_time_ms=processing_time_ms,
                    confidence=response.get('metadata', {}).get('confidence'),
                    model_used=response.get('metadata', {}).get('model_used'),
                    metadata=response.get('metadata', {})
                )
            
            # Adiciona informações de memória à resposta
            if self.has_memory:
                response.setdefault('metadata', {})['session_id'] = self._current_session_id
                response.setdefault('metadata', {})['memory_enabled'] = True
            else:
                response.setdefault('metadata', {})['memory_enabled'] = False
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento com memória: {e}")
            # Fallback para processamento sem memória
            return self.process(query, context)
    
    # ========================================================================
    # MÉTODOS LLM
    # ========================================================================
    
    def _call_llm(self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Chama LLM via LLM Manager com fallback automático entre provedores.
        
        Args:
            prompt: Prompt para o LLM
            context: Contexto adicional
            **kwargs: Parâmetros extras para configuração
        
        Returns:
            Resposta do LLM padronizada
        """
        try:
            if not LLM_MANAGER_AVAILABLE:
                raise ImportError("LLM Manager não disponível. Verifique imports.")
            
            # Configuração padrão para agentes
            config = LLMConfig(
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 1024),
                top_p=kwargs.get("top_p", 0.9),
                model=kwargs.get("model", None)
            )
            
            # Obter manager e fazer chamada
            llm_manager = get_llm_manager()
            self.logger.debug(f"Chamando LLM via manager para agente {self.name}")
            
            response = llm_manager.chat(prompt, config)
            
            if not response.success:
                raise RuntimeError(f"Falha em todos os provedores LLM: {response.error}")
            
            self.logger.debug(f"LLM respondeu via {response.provider.value} em {response.processing_time:.2f}s")
            
            # Converter para formato compatível com código existente
            return {
                "choices": [
                    {
                        "message": {
                            "content": response.content
                        }
                    }
                ],
                "usage": {
                    "total_tokens": response.tokens_used or 0
                },
                "provider": response.provider.value,
                "model": response.model,
                "processing_time": response.processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Erro na chamada LLM: {str(e)}")
            raise AgentError(f"Falha na comunicação com LLM: {str(e)}")
    
    def _build_response(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Constrói resposta padronizada do agente.
        
        Args:
            content: Conteúdo principal da resposta
            metadata: Metadados adicionais
        
        Returns:
            Resposta estruturada
        """
        response = {
            "agent": self.name,
            "content": content,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        }
        return response
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual em formato ISO."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"


class AgentError(Exception):
    """Exceção específica para erros de agentes."""
    
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        self.message = message
        super().__init__(f"[{agent_name}] {message}")