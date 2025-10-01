"""
Implementação do gerenciador de memória usando Supabase.

Este módulo implementa a classe SupabaseMemoryManager que utiliza
Supabase (PostgreSQL + pgvector) como backend para armazenamento
persistente da memória dos agentes multiagente.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..settings import SUPABASE_URL, SUPABASE_KEY
from ..utils.logging_config import get_logger
from ..vectorstore.supabase_client import supabase
from .base_memory import BaseMemoryManager
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
    SessionType,
    SimilaritySearchResult,
    ContentFormat
)
from .memory_utils import (
    calculate_data_size,
    generate_session_id,
    sanitize_agent_name,
    validate_context_data
)


class SupabaseMemoryManager(BaseMemoryManager):
    """
    Gerenciador de memória usando Supabase como backend.
    
    Implementa armazenamento persistente utilizando PostgreSQL com pgvector
    para capacidades de busca semântica em embeddings.
    """
    
    def __init__(self, agent_name: str):
        """
        Inicializa o gerenciador Supabase.
        
        Args:
            agent_name: Nome do agente
        """
        super().__init__(agent_name)
        self.logger = get_logger(f"memory.supabase.{self.agent_name}")
        
        # Verifica conexão Supabase
        if not SUPABASE_URL or not SUPABASE_KEY:
            self.logger.warning("Credenciais Supabase não configuradas")
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados")
        
        self.logger.info(f"SupabaseMemoryManager inicializado para agente: {self.agent_name}")
    
    # ========================================================================
    # IMPLEMENTAÇÃO DOS MÉTODOS ABSTRATOS
    # ========================================================================
    
    async def create_session(self, session_id: Optional[str] = None,
                           user_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
        """
        Cria uma nova sessão no Supabase.
        
        Args:
            session_id: ID da sessão (gera se None)
            user_id: ID do usuário
            metadata: Metadados adicionais
            
        Returns:
            Informações da sessão criada
        """
        if not session_id:
            session_id = generate_session_id(prefix=self.agent_name)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'agent_name': self.agent_name,
            'session_type': SessionType.INTERACTIVE.value,
            'status': SessionStatus.ACTIVE.value,
            'expires_at': (datetime.now() + timedelta(hours=MemoryConfig.DEFAULT_SESSION_DURATION_HOURS)).isoformat(),
            'metadata': metadata or {}
        }
        
        try:
            result = supabase.table('agent_sessions').insert(session_data).execute()
            
            if result.data:
                session_info = self._parse_session_data(result.data[0])
                self.logger.info(f"Sessão criada: {session_id}")
                return session_info
            else:
                raise Exception("Falha ao criar sessão - sem dados retornados")
                
        except Exception as e:
            self.logger.error(f"Erro ao criar sessão {session_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Recupera informações de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Informações da sessão ou None
        """
        try:
            result = supabase.table('agent_sessions').select('*').eq('session_id', session_id).execute()
            
            if result.data:
                return self._parse_session_data(result.data[0])
            else:
                self.logger.debug(f"Sessão não encontrada: {session_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao recuperar sessão {session_id}: {e}")
            return None
    
    async def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Atualiza uma sessão existente.
        
        Args:
            session_id: ID da sessão
            **kwargs: Campos para atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        # Prepara dados para atualização
        update_data = {'updated_at': datetime.now().isoformat()}
        
        # Mapeia campos permitidos
        field_mapping = {
            'status': 'status',
            'expires_at': 'expires_at',
            'metadata': 'metadata',
            'user_id': 'user_id'
        }
        
        for key, value in kwargs.items():
            if key in field_mapping:
                if key == 'expires_at' and isinstance(value, datetime):
                    update_data[field_mapping[key]] = value.isoformat()
                else:
                    update_data[field_mapping[key]] = value
        
        try:
            result = supabase.table('agent_sessions').update(update_data).eq('session_id', session_id).execute()
            
            success = bool(result.data)
            if success:
                self.logger.debug(f"Sessão atualizada: {session_id}")
            else:
                self.logger.warning(f"Sessão não encontrada para atualização: {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar sessão {session_id}: {e}")
            return False
    
    async def save_conversation(self, session_id: str, message_type: MessageType,
                              content: str, **kwargs) -> ConversationMessage:
        """
        Salva uma mensagem de conversação.
        
        Args:
            session_id: ID da sessão
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            **kwargs: Campos adicionais
            
        Returns:
            Mensagem salva
        """
        # Busca o UUID da sessão
        session_uuid = await self._get_session_uuid(session_id)
        if not session_uuid:
            raise ValueError(f"Sessão não encontrada: {session_id}")
        
        # Busca próximo turn number
        conversation_turn = await self._get_next_conversation_turn(session_uuid)
        
        # Prepara dados da mensagem
        message_data = {
            'session_id': str(session_uuid),
            'agent_name': self.agent_name,
            'conversation_turn': conversation_turn,
            'message_type': message_type.value,
            'content': content,
            'content_format': kwargs.get('content_format', ContentFormat.TEXT.value),
            'processing_time_ms': kwargs.get('processing_time_ms'),
            'token_count': kwargs.get('token_count'),
            'model_used': kwargs.get('model_used'),
            'confidence_score': kwargs.get('confidence_score'),
            'metadata': kwargs.get('metadata', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            result = supabase.table('agent_conversations').insert(message_data).execute()
            
            if result.data:
                message = self._parse_conversation_data(result.data[0])
                self.logger.debug(f"Mensagem salva: {message_type.value} - turn {conversation_turn}")
                return message
            else:
                raise Exception("Falha ao salvar mensagem - sem dados retornados")
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar mensagem: {e}")
            raise
    
    async def get_conversation_history(self, session_id: str,
                                     limit: Optional[int] = None,
                                     since: Optional[datetime] = None) -> List[ConversationMessage]:
        """
        Recupera histórico de conversação.
        
        Args:
            session_id: ID da sessão
            limit: Limite de mensagens
            since: Data mínima das mensagens
            
        Returns:
            Lista de mensagens
        """
        session_uuid = await self._get_session_uuid(session_id)
        if not session_uuid:
            return []
        
        try:
            query = supabase.table('agent_conversations').select('*').eq('session_id', str(session_uuid)).order('conversation_turn')
            
            if since:
                query = query.gte('timestamp', since.isoformat())
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            messages = [self._parse_conversation_data(data) for data in result.data]
            self.logger.debug(f"Recuperadas {len(messages)} mensagens para sessão {session_id}")
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar conversação {session_id}: {e}")
            return []
    
    async def save_context(self, session_id: str, context_type: ContextType,
                         context_key: str, context_data: Dict[str, Any],
                         **kwargs) -> AgentContext:
        """
        Salva contexto do agente.
        
        Args:
            session_id: ID da sessão
            context_type: Tipo do contexto
            context_key: Chave do contexto
            context_data: Dados do contexto
            **kwargs: Campos adicionais
            
        Returns:
            Contexto salvo
        """
        # Validações
        is_valid, error_msg = validate_context_data(context_data)
        if not is_valid:
            raise ValueError(f"Dados de contexto inválidos: {error_msg}")
        
        session_uuid = await self._get_session_uuid(session_id)
        if not session_uuid:
            raise ValueError(f"Sessão não encontrada: {session_id}")
        
        # Calcula tamanho dos dados
        data_size = calculate_data_size(context_data)
        
        # Prepara dados do contexto
        context_record = {
            'session_id': str(session_uuid),
            'agent_name': self.agent_name,
            'context_type': context_type.value,
            'context_key': context_key,
            'context_data': context_data,
            'data_size_bytes': data_size,
            'priority': kwargs.get('priority', MemoryConfig.DEFAULT_CONTEXT_PRIORITY),
            'expires_at': kwargs.get('expires_at').isoformat() if kwargs.get('expires_at') else None,
            'metadata': kwargs.get('metadata', {}),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_accessed_at': datetime.now().isoformat()
        }
        
        try:
            # Tenta atualizar se já existe
            existing = await self.get_context(session_id, context_type, context_key)
            
            if existing:
                # Atualiza contexto existente
                update_data = {
                    'context_data': context_data,
                    'data_size_bytes': data_size,
                    'updated_at': datetime.now().isoformat(),
                    'access_count': existing.access_count + 1
                }
                
                if 'priority' in kwargs:
                    update_data['priority'] = kwargs['priority']
                if 'expires_at' in kwargs:
                    update_data['expires_at'] = kwargs['expires_at'].isoformat() if kwargs['expires_at'] else None
                if 'metadata' in kwargs:
                    update_data['metadata'] = kwargs['metadata']
                
                result = supabase.table('agent_context').update(update_data).eq('id', str(existing.id)).execute()
                
                if result.data:
                    context = self._parse_context_data(result.data[0])
                    self.logger.debug(f"Contexto atualizado: {context_type.value}/{context_key}")
                    return context
            else:
                # Insere novo contexto
                result = supabase.table('agent_context').insert(context_record).execute()
                
                if result.data:
                    context = self._parse_context_data(result.data[0])
                    self.logger.debug(f"Contexto criado: {context_type.value}/{context_key}")
                    return context
            
            raise Exception("Falha ao salvar contexto - sem dados retornados")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar contexto {context_type.value}/{context_key}: {e}")
            raise
    
    async def get_context(self, session_id: str, context_type: ContextType,
                        context_key: str) -> Optional[AgentContext]:
        """
        Recupera contexto específico.
        
        Args:
            session_id: ID da sessão
            context_type: Tipo do contexto
            context_key: Chave do contexto
            
        Returns:
            Contexto encontrado ou None
        """
        session_uuid = await self._get_session_uuid(session_id)
        if not session_uuid:
            return None
        
        try:
            result = supabase.table('agent_context').select('*').eq('session_id', str(session_uuid)).eq('agent_name', self.agent_name).eq('context_type', context_type.value).eq('context_key', context_key).execute()
            
            if result.data:
                context = self._parse_context_data(result.data[0])
                
                # Atualiza last_accessed_at
                await self._update_context_access(context.id)
                
                return context
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao recuperar contexto {context_type.value}/{context_key}: {e}")
            return None
    
    async def list_contexts(self, session_id: str,
                          context_type: Optional[ContextType] = None) -> List[AgentContext]:
        """
        Lista contextos de uma sessão.
        
        Args:
            session_id: ID da sessão
            context_type: Tipo específico (opcional)
            
        Returns:
            Lista de contextos
        """
        session_uuid = await self._get_session_uuid(session_id)
        if not session_uuid:
            return []
        
        try:
            query = supabase.table('agent_context').select('*').eq('session_id', str(session_uuid)).eq('agent_name', self.agent_name)
            
            if context_type:
                query = query.eq('context_type', context_type.value)
            
            result = query.order('created_at').execute()
            
            contexts = [self._parse_context_data(data) for data in result.data]
            self.logger.debug(f"Recuperados {len(contexts)} contextos para sessão {session_id}")
            
            return contexts
            
        except Exception as e:
            self.logger.error(f"Erro ao listar contextos: {e}")
            return []
    
    async def delete_context(self, session_id: str, context_type: ContextType,
                           context_key: str) -> bool:
        """
        Remove contexto específico.
        
        Args:
            session_id: ID da sessão
            context_type: Tipo do contexto
            context_key: Chave do contexto
            
        Returns:
            True se removido com sucesso
        """
        session_uuid = await self._get_session_uuid(session_id)
        if not session_uuid:
            return False
        
        try:
            result = supabase.table('agent_context').delete().eq('session_id', str(session_uuid)).eq('agent_name', self.agent_name).eq('context_type', context_type.value).eq('context_key', context_key).execute()
            
            success = bool(result.data)
            if success:
                self.logger.debug(f"Contexto removido: {context_type.value}/{context_key}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao remover contexto {context_type.value}/{context_key}: {e}")
            return False
    
    async def save_embedding(self, embedding: MemoryEmbedding) -> bool:
        """
        Salva embedding para busca semântica.
        
        Args:
            embedding: Objeto de embedding
            
        Returns:
            True se salvo com sucesso
        """
        if len(embedding.embedding) != MemoryConfig.EMBEDDING_DIMENSION:
            raise ValueError(f"Embedding deve ter {MemoryConfig.EMBEDDING_DIMENSION} dimensões")
        
        # Prepara dados do embedding
        embedding_data = {
            'session_id': str(embedding.session_id) if embedding.session_id else None,
            'agent_name': embedding.agent_name or self.agent_name,
            'conversation_id': str(embedding.conversation_id) if embedding.conversation_id else None,
            'context_id': str(embedding.context_id) if embedding.context_id else None,
            'embedding_type': embedding.embedding_type.value,
            'source_text': embedding.source_text,
            'embedding': embedding.embedding,
            'similarity_threshold': embedding.similarity_threshold,
            'created_at': embedding.created_at.isoformat(),
            'metadata': embedding.metadata
        }
        
        try:
            result = supabase.table('agent_memory_embeddings').insert(embedding_data).execute()
            
            success = bool(result.data)
            if success:
                self.logger.debug(f"Embedding salvo: {embedding.embedding_type.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar embedding: {e}")
            return False
    
    async def search_similar(self, query_embedding: List[float],
                           similarity_threshold: float = 0.8,
                           limit: int = 10,
                           session_id: Optional[str] = None) -> List[SimilaritySearchResult]:
        """
        Busca por similaridade semântica.
        
        Args:
            query_embedding: Embedding da consulta
            similarity_threshold: Threshold mínimo
            limit: Limite de resultados
            session_id: ID da sessão (opcional)
            
        Returns:
            Lista de resultados similares
        """
        if len(query_embedding) != MemoryConfig.EMBEDDING_DIMENSION:
            raise ValueError(f"Query embedding deve ter {MemoryConfig.EMBEDDING_DIMENSION} dimensões")
        
        session_uuid = None
        if session_id:
            session_uuid = await self._get_session_uuid(session_id)
        
        try:
            # Usa função SQL customizada para busca de similaridade
            result = supabase.rpc('search_memory_similarity', {
                'p_agent_name': self.agent_name,
                'p_session_id': str(session_uuid) if session_uuid else None,
                'p_query_embedding': query_embedding,
                'p_similarity_threshold': similarity_threshold,
                'p_limit': limit
            }).execute()
            
            similarities = []
            for data in result.data:
                similarity_result = SimilaritySearchResult(
                    id=UUID(data['id']),
                    source_text=data['source_text'],
                    similarity=float(data['similarity']),
                    embedding_type=EmbeddingType(data['embedding_type']),
                    conversation_id=UUID(data['conversation_id']) if data['conversation_id'] else None,
                    context_id=UUID(data['context_id']) if data['context_id'] else None,
                    metadata=data['metadata'] or {}
                )
                similarities.append(similarity_result)
            
            self.logger.debug(f"Encontrados {len(similarities)} resultados similares")
            return similarities
            
        except Exception as e:
            self.logger.error(f"Erro na busca por similaridade: {e}")
            return []
    
    async def cleanup_expired(self) -> Dict[str, int]:
        """
        Limpa dados expirados.
        
        Returns:
            Dicionário com contagem de itens removidos
        """
        stats = {
            'expired_sessions': 0,
            'expired_contexts': 0,
            'old_conversations': 0,
            'old_embeddings': 0
        }
        
        try:
            # Chama função SQL de limpeza
            result = supabase.rpc('cleanup_expired_sessions').execute()
            
            if result.data:
                stats['expired_sessions'] = result.data
            
            # Limpa contextos expirados específicos do agente
            cutoff_date = datetime.now() - timedelta(days=MemoryConfig.EXPIRED_SESSION_RETENTION_DAYS)
            
            contexts_result = supabase.table('agent_context').delete().eq('agent_name', self.agent_name).lt('expires_at', cutoff_date.isoformat()).execute()
            
            if contexts_result.data:
                stats['expired_contexts'] = len(contexts_result.data)
            
            self.logger.info(f"Limpeza concluída: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")
            return stats
    
    # ========================================================================
    # MÉTODOS AUXILIARES PRIVADOS
    # ========================================================================
    
    async def _get_session_uuid(self, session_id: str) -> Optional[UUID]:
        """Recupera UUID da sessão pelo session_id."""
        try:
            result = supabase.table('agent_sessions').select('id').eq('session_id', session_id).execute()
            
            if result.data:
                return UUID(result.data[0]['id'])
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar UUID da sessão {session_id}: {e}")
            return None
    
    async def _get_next_conversation_turn(self, session_uuid: UUID) -> int:
        """Calcula próximo número de turno na conversação."""
        try:
            result = supabase.table('agent_conversations').select('conversation_turn').eq('session_id', str(session_uuid)).order('conversation_turn', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]['conversation_turn'] + 1
            else:
                return 1
                
        except Exception as e:
            self.logger.error(f"Erro ao calcular próximo turno: {e}")
            return 1
    
    async def _update_context_access(self, context_id: UUID) -> None:
        """Atualiza timestamp de último acesso do contexto."""
        try:
            update_data = {
                'last_accessed_at': datetime.now().isoformat(),
                'access_count': supabase.table('agent_context').select('access_count').eq('id', str(context_id)).execute().data[0]['access_count'] + 1
            }
            
            supabase.table('agent_context').update(update_data).eq('id', str(context_id)).execute()
            
        except Exception as e:
            self.logger.debug(f"Erro ao atualizar acesso do contexto: {e}")
    
    def _parse_session_data(self, data: Dict[str, Any]) -> SessionInfo:
        """Converte dados do Supabase para SessionInfo."""
        return SessionInfo(
            id=UUID(data['id']),
            session_id=data['session_id'],
            user_id=data.get('user_id'),
            agent_name=data.get('agent_name'),
            session_type=SessionType(data.get('session_type', 'interactive')),
            status=SessionStatus(data.get('status', 'active')),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            expires_at=datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00')),
            metadata=data.get('metadata', {})
        )
    
    def _parse_conversation_data(self, data: Dict[str, Any]) -> ConversationMessage:
        """Converte dados do Supabase para ConversationMessage."""
        return ConversationMessage(
            id=UUID(data['id']),
            session_id=UUID(data['session_id']),
            agent_name=data['agent_name'],
            conversation_turn=data['conversation_turn'],
            message_type=MessageType(data['message_type']),
            content=data['content'],
            content_format=ContentFormat(data.get('content_format', 'text')),
            processing_time_ms=data.get('processing_time_ms'),
            token_count=data.get('token_count'),
            model_used=data.get('model_used'),
            confidence_score=data.get('confidence_score'),
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        )
    
    def _parse_context_data(self, data: Dict[str, Any]) -> AgentContext:
        """Converte dados do Supabase para AgentContext."""
        expires_at = None
        if data.get('expires_at'):
            expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        
        return AgentContext(
            id=UUID(data['id']),
            session_id=UUID(data['session_id']),
            agent_name=data['agent_name'],
            context_type=ContextType(data['context_type']),
            context_key=data['context_key'],
            context_data=data['context_data'],
            data_size_bytes=data.get('data_size_bytes'),
            access_count=data.get('access_count', 0),
            priority=data.get('priority', 5),
            expires_at=expires_at,
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            last_accessed_at=datetime.fromisoformat(data['last_accessed_at'].replace('Z', '+00:00')),
            metadata=data.get('metadata', {})
        )