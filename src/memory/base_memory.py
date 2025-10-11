"""
Módulo base para gerenciamento de memória dos agentes.

Este módulo define as interfaces e classes base para o sistema de memória
persistente dos agentes multiagente. Fornece abstrações para diferentes
implementações de armazenamento (Supabase, local, etc.).
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..utils.logging_config import get_logger
from .memory_types import (
    AgentContext,
    ContextType,
    ConversationMessage,
    EmbeddingType,
    MemoryConfig,
    MemoryEmbedding,
    MessageType,
    SessionInfo,
    SessionStatus,
    SimilaritySearchResult
)
from .memory_utils import (
    calculate_data_size,
    generate_session_id,
    sanitize_agent_name,
    validate_context_data
)


class BaseMemoryManager(ABC):
    """
    Classe base abstrata para gerenciamento de memória dos agentes.
    
    Define a interface comum que deve ser implementada por diferentes
    backends de armazenamento (Supabase, SQLite, MongoDB, etc.).
    """
    
    def __init__(self, agent_name: str):
        """
        Inicializa o gerenciador de memória.
        
        Args:
            agent_name: Nome do agente que utilizará este gerenciador
        """
        self.agent_name = sanitize_agent_name(agent_name)
        self.logger = get_logger(f"memory.{self.agent_name}")
        self._current_session_id: Optional[UUID] = None
    
    # ========================================================================
    # MÉTODOS ABSTRATOS - DEVEM SER IMPLEMENTADOS NAS SUBCLASSES
    # ========================================================================
    
    @abstractmethod
    async def create_session(self, session_id: Optional[str] = None, 
                           user_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
        """Cria uma nova sessão."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Recupera informações de uma sessão."""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, **kwargs) -> bool:
        """Atualiza uma sessão existente."""
        pass
    
    @abstractmethod
    async def save_conversation(self, session_id: str, message_type: MessageType,
                              content: str, **kwargs) -> ConversationMessage:
        """Salva uma mensagem de conversação."""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, session_id: str, 
                                     limit: Optional[int] = None,
                                     since: Optional[datetime] = None) -> List[ConversationMessage]:
        """Recupera histórico de conversação."""
        pass
    
    @abstractmethod
    async def save_context(self, session_id: str, context_type: ContextType,
                         context_key: str, context_data: Dict[str, Any],
                         **kwargs) -> AgentContext:
        """Salva contexto do agente."""
        pass
    
    @abstractmethod
    async def get_context(self, session_id: str, context_type: ContextType,
                        context_key: str) -> Optional[AgentContext]:
        """Recupera contexto específico."""
        pass
    
    @abstractmethod
    async def list_contexts(self, session_id: str, 
                          context_type: Optional[ContextType] = None) -> List[AgentContext]:
        """Lista contextos de uma sessão."""
        pass
    
    @abstractmethod
    async def delete_context(self, session_id: str, context_type: ContextType,
                           context_key: str) -> bool:
        """Remove contexto específico."""
        pass
    
    @abstractmethod
    async def save_embedding(self, embedding: MemoryEmbedding) -> bool:
        """Salva embedding para busca semântica."""
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float],
                           similarity_threshold: float = 0.8,
                           limit: int = 10,
                           session_id: Optional[str] = None) -> List[SimilaritySearchResult]:
        """Busca por similaridade semântica."""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> Dict[str, int]:
        """Limpa dados expirados."""
        pass
    
    # ========================================================================
    # MÉTODOS PÚBLICOS - INTERFACE COMUM
    # ========================================================================
    
    async def initialize_session(self, session_id: Optional[str] = None,
                                user_id: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Inicializa uma nova sessão ou recupera uma existente.
        
        Args:
            session_id: ID da sessão (se None, gera um novo)
            user_id: ID do usuário
            metadata: Metadados adicionais
            
        Returns:
            ID da sessão criada/recuperada
        """
        if session_id:
            # Tenta recuperar sessão existente
            existing_session = await self.get_session(session_id)
            if existing_session and existing_session.status == SessionStatus.ACTIVE:
                self._current_session_id = existing_session.id
                self.logger.info(f"Sessão existente recuperada: {session_id}")
                return session_id
        
        # Cria nova sessão
        if not session_id:
            session_id = generate_session_id(prefix=self.agent_name)
        
        session = await self.create_session(session_id, user_id, metadata)
        self._current_session_id = session.id
        
        self.logger.info(f"Nova sessão criada: {session_id}")
        return session_id
    
    async def add_user_query(self, query: str, session_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Adiciona uma consulta do usuário ao histórico.
        
        Args:
            query: Consulta do usuário
            session_id: ID da sessão
            metadata: Metadados adicionais
            
        Returns:
            Mensagem de conversação salva
        """
        if not session_id:
            session_id = await self.initialize_session()
        
        return await self.save_conversation(
            session_id=session_id,
            message_type=MessageType.QUERY,
            content=query,
            metadata=metadata or {}
        )
    
    async def add_agent_response(self, response: str, session_id: str,
                               processing_time_ms: Optional[int] = None,
                               confidence_score: Optional[float] = None,
                               model_used: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Adiciona uma resposta do agente ao histórico.
        
        Args:
            response: Resposta do agente
            session_id: ID da sessão
            processing_time_ms: Tempo de processamento
            confidence_score: Score de confiança
            model_used: Modelo LLM utilizado
            metadata: Metadados adicionais
            
        Returns:
            Mensagem de conversação salva
        """
        return await self.save_conversation(
            session_id=session_id,
            message_type=MessageType.RESPONSE,
            content=response,
            processing_time_ms=processing_time_ms,
            confidence_score=confidence_score,
            model_used=model_used,
            metadata=metadata or {}
        )
    
    async def store_data_context(self, session_id: str, data_info: Dict[str, Any],
                               context_key: str = "current_data") -> AgentContext:
        """
        Armazena contexto de dados carregados.
        
        Args:
            session_id: ID da sessão
            data_info: Informações dos dados
            context_key: Chave do contexto
            
        Returns:
            Contexto salvo
        """
        return await self.save_context(
            session_id=session_id,
            context_type=ContextType.DATA,
            context_key=context_key,
            context_data=data_info,
            priority=1  # Alta prioridade para dados
        )
    
    async def store_preferences(self, session_id: str, preferences: Dict[str, Any],
                              context_key: str = "user_preferences") -> AgentContext:
        """
        Armazena preferências do usuário.
        
        Args:
            session_id: ID da sessão
            preferences: Preferências do usuário
            context_key: Chave do contexto
            
        Returns:
            Contexto salvo
        """
        return await self.save_context(
            session_id=session_id,
            context_type=ContextType.PREFERENCES,
            context_key=context_key,
            context_data=preferences,
            priority=2  # Alta prioridade para preferências
        )
    
    async def cache_analysis_result(self, session_id: str, analysis_key: str,
                                  result: Dict[str, Any],
                                  expiry_hours: int = 24) -> AgentContext:
        """
        Faz cache de resultado de análise.
        
        Args:
            session_id: ID da sessão
            analysis_key: Chave única da análise
            result: Resultado da análise
            expiry_hours: Horas até expirar
            
        Returns:
            Contexto salvo
        """
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        return await self.save_context(
            session_id=session_id,
            context_type=ContextType.CACHE,
            context_key=analysis_key,
            context_data=result,
            priority=7,  # Prioridade média para cache
            expires_at=expires_at
        )
    
    async def get_cached_analysis(self, session_id: str, analysis_key: str) -> Optional[Dict[str, Any]]:
        """
        Recupera resultado de análise do cache.
        
        Args:
            session_id: ID da sessão
            analysis_key: Chave da análise
            
        Returns:
            Resultado da análise ou None se não encontrado/expirado
        """
        context = await self.get_context(session_id, ContextType.CACHE, analysis_key)
        
        if context and not context.is_expired():
            context.access()  # Registra acesso
            return context.context_data
        
        return None
    
    async def get_recent_context(self, session_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Recupera contexto recente para fornecer ao agente.
        
        Args:
            session_id: ID da sessão
            hours: Horas de contexto recente
            
        Returns:
            Dicionário com contexto agregado
        """
        # Recupera conversações recentes
        since = datetime.now() - timedelta(hours=hours)
        conversations = await self.get_conversation_history(session_id, limit=50, since=since)
        
        # Recupera contextos ativos
        contexts = await self.list_contexts(session_id)
        
        # Organiza contexto
        context_summary = {
            'recent_conversations': [
                {
                    'type': msg.message_type.value,
                    'content': msg.content[:500],  # Trunca para resumo
                    'timestamp': msg.timestamp.isoformat()
                }
                for msg in conversations[-10:]  # Últimas 10 mensagens
            ],
            'data_context': {},
            'preferences': {},
            'cached_analyses': []
        }
        
        # Organiza contextos por tipo
        for ctx in contexts:
            if ctx.is_expired():
                continue
                
            if ctx.context_type == ContextType.DATA:
                context_summary['data_context'][ctx.context_key] = ctx.context_data
            elif ctx.context_type == ContextType.PREFERENCES:
                context_summary['preferences'][ctx.context_key] = ctx.context_data
            elif ctx.context_type == ContextType.CACHE:
                context_summary['cached_analyses'].append({
                    'key': ctx.context_key,
                    'created_at': ctx.created_at.isoformat(),
                    'access_count': ctx.access_count
                })
        
        return context_summary
    
    # ========================================================================
    # MÉTODOS UTILITÁRIOS
    # ========================================================================
    
    async def validate_session(self, session_id: str) -> bool:
        """
        Valida se uma sessão existe e está ativa.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se válida e ativa
        """
        session = await self.get_session(session_id)
        return (session is not None and 
                session.status == SessionStatus.ACTIVE and 
                not session.is_expired())
    
    def calculate_context_size(self, context_data: Dict[str, Any]) -> int:
        """
        Calcula tamanho de dados de contexto.
        
        Args:
            context_data: Dados do contexto
            
        Returns:
            Tamanho em bytes
        """
        return calculate_data_size(context_data)
    
    def validate_context_data_size(self, context_data: Dict[str, Any]) -> bool:
        """
        Valida se dados de contexto não excedem limite.
        
        Args:
            context_data: Dados do contexto
            
        Returns:
            True se dentro do limite
        """
        size = self.calculate_context_size(context_data)
        return size <= MemoryConfig.MAX_CONTEXT_SIZE_BYTES
    
    async def get_memory_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Recupera estatísticas de uso de memória.
        
        Args:
            session_id: ID da sessão (None para todas)
            
        Returns:
            Dicionário com estatísticas
        """
        # Implementação base - pode ser sobrescrita
        if session_id:
            contexts = await self.list_contexts(session_id)
            conversations = await self.get_conversation_history(session_id)
            
            return {
                'session_id': session_id,
                'contexts_count': len(contexts),
                'conversations_count': len(conversations),
                'total_context_size': sum(
                    ctx.data_size_bytes or 0 for ctx in contexts
                ),
                'agent_name': self.agent_name
            }
        else:
            return {
                'agent_name': self.agent_name,
                'message': 'Estatísticas globais não implementadas na classe base'
            }


class MemoryMixin:
    """
    Mixin para adicionar capacidades de memória aos agentes.
    
    Esta classe fornece uma interface simples para agentes utilizarem
    o sistema de memória sem precisar conhecer os detalhes de implementação.
    """
    
    def __init__(self, memory_manager: Optional[BaseMemoryManager] = None):
        """
        Inicializa o mixin de memória.
        
        Args:
            memory_manager: Gerenciador de memória a utilizar
        """
        self._memory_manager = memory_manager
        self._current_session_id: Optional[str] = None
    
    @property
    def has_memory(self) -> bool:
        """Verifica se o agente tem sistema de memória configurado."""
        return self._memory_manager is not None
    
    @property
    def current_session(self) -> Optional[str]:
        """Retorna ID da sessão atual."""
        return self._current_session_id
    
    async def init_memory(self, session_id: Optional[str] = None,
                         user_id: Optional[str] = None) -> Optional[str]:
        """
        Inicializa sistema de memória.
        
        Args:
            session_id: ID da sessão
            user_id: ID do usuário
            
        Returns:
            ID da sessão ou None se não há memória
        """
        if not self.has_memory:
            return None
        
        self._current_session_id = await self._memory_manager.initialize_session(
            session_id, user_id
        )
        return self._current_session_id
    
    async def remember_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Lembra uma consulta do usuário.
        
        Args:
            query: Consulta do usuário
            metadata: Metadados adicionais
            
        Returns:
            True se salvo com sucesso
        """
        if not self.has_memory or not self._current_session_id:
            return False
        
        try:
            await self._memory_manager.add_user_query(
                query, self._current_session_id, metadata
            )
            return True
        except Exception as e:
            self._memory_manager.logger.error(f"Erro ao salvar query: {e}")
            return False
    
    async def remember_response(self, response: str, 
                              processing_time_ms: Optional[int] = None,
                              confidence: Optional[float] = None,
                              model: Optional[str] = None) -> bool:
        """
        Lembra uma resposta do agente.
        
        Args:
            response: Resposta do agente
            processing_time_ms: Tempo de processamento
            confidence: Score de confiança
            model: Modelo utilizado
            
        Returns:
            True se salvo com sucesso
        """
        if not self.has_memory or not self._current_session_id:
            return False
        
        try:
            await self._memory_manager.add_agent_response(
                response, self._current_session_id, processing_time_ms, confidence, model
            )
            return True
        except Exception as e:
            self._memory_manager.logger.error(f"Erro ao salvar resposta: {e}")
            return False
    
    async def remember_data(self, data_info: Dict[str, Any], key: str = "current_data") -> bool:
        """
        Lembra informações de dados carregados.
        
        Args:
            data_info: Informações dos dados
            key: Chave do contexto
            
        Returns:
            True se salvo com sucesso
        """
        if not self.has_memory or not self._current_session_id:
            return False
        
        try:
            await self._memory_manager.store_data_context(
                self._current_session_id, data_info, key
            )
            return True
        except Exception as e:
            self._memory_manager.logger.error(f"Erro ao salvar dados: {e}")
            return False
    
    async def recall_context(self, hours: int = 24) -> Dict[str, Any]:
        """
        Recupera contexto recente.
        
        Args:
            hours: Horas de contexto
            
        Returns:
            Contexto recuperado
        """
        if not self.has_memory or not self._current_session_id:
            return {}
        
        try:
            return await self._memory_manager.get_recent_context(
                self._current_session_id, hours
            )
        except Exception as e:
            self._memory_manager.logger.error(f"Erro ao recuperar contexto: {e}")
            return {}
    
    async def recall_conversation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera histórico de conversação.
        
        Args:
            limit: Limite de mensagens
            
        Returns:
            Lista de mensagens
        """
        if not self.has_memory or not self._current_session_id:
            return []
        
        try:
            messages = await self._memory_manager.get_conversation_history(
                self._current_session_id, limit
            )
            return [msg.to_dict() for msg in messages]
        except Exception as e:
            self._memory_manager.logger.error(f"Erro ao recuperar conversação: {e}")
            return []