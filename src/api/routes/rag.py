"""
Rotas para Sistema RAG (Retrieval Augmented Generation)
======================================================

Endpoints para consultas semânticas, chat inteligente e busca no banco vetorial.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.agent.orchestrator_agent import OrchestratorAgent
from src.api.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DocumentChunk,
    PaginatedResponse,
    PaginationParams,
    QueryType,
    RAGQuery,
    RAGResponse,
    SchemaExamples,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Cache de sessões de chat (em produção usar Redis)
_chat_sessions: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/search",
    response_model=RAGResponse,
    summary="Busca semântica",
    description="Busca documentos similares no banco vetorial usando embeddings",
    responses={
        200: {"description": "Busca realizada com sucesso", "model": RAGResponse},
        400: {"description": "Query inválida"},
        500: {"description": "Erro interno no sistema RAG"},
    },
)
async def semantic_search(request: RAGQuery):
    """
    Busca semântica no banco vetorial.
    
    **Tipos de busca:**
    - **semantic_search**: Busca por similaridade semântica
    - **document_query**: Consulta específica em documentos
    - **analysis_query**: Busca relacionada a análises anteriores
    
    **Parâmetros:**
    - **query**: Pergunta ou termo de busca
    - **max_results**: Número máximo de resultados (1-20)
    - **similarity_threshold**: Limiar de similaridade (0.0-1.0)
    - **include_sources**: Incluir informações das fontes
    """
    start_time = time.time()
    
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query não pode estar vazia"
            )
        
        logger.info(f"🔍 Busca semântica: '{request.query[:50]}...' (tipo: {request.query_type})")
        
        # Inicializar orquestrador com RAG habilitado
        orchestrator = OrchestratorAgent(
            enable_csv_agent=False,
            enable_rag_agent=True,
            enable_google_llm=True,
        )
        
        # Preparar contexto para busca RAG
        context = {
            'query_type': request.query_type,
            'max_results': request.max_results,
            'similarity_threshold': request.similarity_threshold,
            'include_sources': request.include_sources,
            'session_id': request.session_id,
            'additional_context': request.context,
        }
        
        # Executar busca via orquestrador
        result = orchestrator.process(request.query, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Processar resultados da busca
        search_results = _process_rag_results(result, request)
        
        logger.info(
            f"✅ Busca concluída: {len(search_results['sources'])} resultados - {processing_time}ms"
        )
        
        return RAGResponse(
            success=True,
            message=f"Busca concluída com {len(search_results['sources'])} resultados",
            answer=search_results['answer'],
            sources=search_results['sources'],
            confidence_score=search_results['confidence_score'],
            processing_time_ms=processing_time,
            query_type=request.query_type,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na busca semântica: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno no sistema de busca"
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat inteligente",
    description="Conversa com o assistente AI usando contexto e memória",
)
async def chat_with_ai(request: ChatRequest):
    """
    Chat inteligente com contexto e memória.
    
    **Funcionalidades:**
    - Memória de conversa por sessão
    - Busca automática no banco vetorial quando necessário
    - Respostas contextualizadas baseadas em dados
    - Suporte a múltiplas sessões simultâneas
    
    **Parâmetros:**
    - **message**: Mensagem do usuário
    - **session_id**: ID da sessão (para manter contexto)
    - **include_memory**: Usar histórico da conversa
    - **temperature**: Criatividade das respostas (0.0 = determinística, 2.0 = criativa)
    """
    start_time = time.time()
    
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Mensagem não pode estar vazia"
            )
        
        logger.info(f"💬 Chat: '{request.message[:50]}...' (sessão: {request.session_id})")
        
        # Gerenciar sessão de chat
        session = _get_or_create_chat_session(request.session_id)
        
        # Adicionar mensagem do usuário ao histórico
        user_message = ChatMessage(
            role="user",
            content=request.message,
            metadata={"session_id": request.session_id}
        )
        
        if request.include_memory:
            session['messages'].append(user_message.dict())
        
        # Preparar contexto para o chat
        context = {
            'chat_mode': True,
            'session_id': request.session_id,
            'temperature': request.temperature,
            'include_memory': request.include_memory,
            'chat_history': session['messages'] if request.include_memory else [],
            'additional_context': request.context,
        }
        
        # Inicializar orquestrador
        orchestrator = OrchestratorAgent(
            enable_csv_agent=True,   # Para responder sobre dados
            enable_rag_agent=True,   # Para buscar contexto
            enable_google_llm=True,  # Para gerar respostas
        )
        
        # Processar mensagem
        result = orchestrator.process(request.message, context)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Processar resposta do assistente
        assistant_response = _process_chat_response(result, request)
        
        # Adicionar resposta do assistente ao histórico
        assistant_message = ChatMessage(
            role="assistant",
            content=assistant_response['message'],
            metadata={
                "session_id": request.session_id,
                "message_id": assistant_response['message_id'],
                "confidence_score": assistant_response['confidence_score'],
            }
        )
        
        if request.include_memory:
            session['messages'].append(assistant_message.dict())
            session['last_activity'] = time.time()
        
        logger.info(
            f"✅ Chat respondido: {assistant_response['message_id']} - {processing_time}ms"
        )
        
        return ChatResponse(
            success=True,
            message=assistant_response['message'],
            session_id=request.session_id,
            message_id=assistant_response['message_id'],
            sources=assistant_response.get('sources'),
            confidence_score=assistant_response['confidence_score'],
            processing_time_ms=processing_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno no sistema de chat"
        )


@router.get(
    "/chat/{session_id}/history",
    summary="Histórico do chat",
    description="Recupera histórico de mensagens de uma sessão",
)
async def get_chat_history(
    session_id: str,
    pagination: PaginationParams = Query(),
):
    """
    Recupera histórico de mensagens de uma sessão de chat.
    
    **Parâmetros:**
    - **session_id**: ID da sessão
    - **page**: Página do histórico (mais recente primeiro)
    - **page_size**: Mensagens por página
    """
    try:
        if session_id not in _chat_sessions:
            raise HTTPException(
                status_code=404,
                detail="Sessão de chat não encontrada"
            )
        
        session = _chat_sessions[session_id]
        messages = session['messages']
        
        # Paginação
        total_messages = len(messages)
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        
        # Reverter ordem (mais recente primeiro)
        messages_reversed = list(reversed(messages))
        page_messages = messages_reversed[start_idx:end_idx]
        
        pagination_info = {
            'current_page': pagination.page,
            'page_size': pagination.page_size,
            'total_messages': total_messages,
            'total_pages': (total_messages + pagination.page_size - 1) // pagination.page_size,
            'has_next': end_idx < total_messages,
            'has_previous': pagination.page > 1,
        }
        
        return PaginatedResponse(
            success=True,
            message=f"Histórico da sessão {session_id}",
            data=page_messages,
            pagination=pagination_info,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro recuperando histórico: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno recuperando histórico"
        )


@router.delete(
    "/chat/{session_id}",
    summary="Limpar sessão de chat",
    description="Remove histórico e dados de uma sessão",
)
async def clear_chat_session(session_id: str):
    """
    Limpa dados de uma sessão de chat.
    
    Remove todo o histórico de mensagens e contexto da sessão.
    """
    try:
        if session_id not in _chat_sessions:
            raise HTTPException(
                status_code=404,
                detail="Sessão de chat não encontrada"
            )
        
        del _chat_sessions[session_id]
        
        logger.info(f"🗑️ Sessão de chat removida: {session_id}")
        
        return {
            'success': True,
            'message': f'Sessão {session_id} removida com sucesso',
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro removendo sessão: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno removendo sessão"
        )


@router.get(
    "/documents",
    summary="Listar documentos no banco vetorial",
    description="Lista documentos armazenados no banco vetorial",
)
async def list_documents(
    source: Optional[str] = Query(None, description="Filtrar por fonte"),
    pagination: PaginationParams = Query(),
):
    """
    Lista documentos armazenados no banco vetorial.
    
    **Filtros:**
    - **source**: Filtrar documentos por fonte específica
    """
    try:
        # Consultar banco vetorial via Supabase
        from src.vectorstore.supabase_client import supabase
        
        # Preparar query
        query = supabase.table('metadata').select('*')
        
        if source:
            query = query.eq('source', source)
        
        # Aplicar paginação
        offset = (pagination.page - 1) * pagination.page_size
        query = query.range(offset, offset + pagination.page_size - 1)
        
        # Executar query
        result = query.execute()
        documents = result.data
        
        # Contar total (para paginação)
        count_query = supabase.table('metadata').select('id', count='exact')
        if source:
            count_query = count_query.eq('source', source)
        
        count_result = count_query.execute()
        total_documents = count_result.count or 0
        
        pagination_info = {
            'current_page': pagination.page,
            'page_size': pagination.page_size,
            'total_documents': total_documents,
            'total_pages': (total_documents + pagination.page_size - 1) // pagination.page_size,
            'has_next': offset + pagination.page_size < total_documents,
            'has_previous': pagination.page > 1,
        }
        
        return PaginatedResponse(
            success=True,
            message=f"{len(documents)} documento(s) encontrado(s)",
            data=documents,
            pagination=pagination_info,
        )
        
    except Exception as e:
        logger.error(f"❌ Erro listando documentos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno listando documentos"
        )


@router.get(
    "/sessions",
    summary="Listar sessões ativas",
    description="Lista sessões de chat ativas",
)
async def list_active_sessions():
    """Lista sessões de chat ativas."""
    try:
        current_time = time.time()
        active_sessions = []
        
        for session_id, session_data in _chat_sessions.items():
            last_activity = session_data.get('last_activity', session_data['created_at'])
            inactive_time = current_time - last_activity
            
            # Considerar ativas as sessões com atividade nas últimas 24h
            if inactive_time < 24 * 60 * 60:
                active_sessions.append({
                    'session_id': session_id,
                    'created_at': session_data['created_at'],
                    'last_activity': last_activity,
                    'message_count': len(session_data['messages']),
                    'inactive_seconds': int(inactive_time),
                })
        
        return {
            'success': True,
            'message': f'{len(active_sessions)} sessão(ões) ativa(s)',
            'sessions': active_sessions,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro listando sessões: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno listando sessões"
        )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _get_or_create_chat_session(session_id: str) -> Dict[str, Any]:
    """Obtém ou cria uma sessão de chat."""
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = {
            'session_id': session_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'messages': [],
            'context': {},
        }
        logger.info(f"📝 Nova sessão de chat criada: {session_id}")
    
    return _chat_sessions[session_id]


def _process_rag_results(result: Dict[str, Any], request: RAGQuery) -> Dict[str, Any]:
    """Processa resultados da busca RAG."""
    
    # Extrair conteúdo da resposta
    answer = result.get('content', 'Busca realizada, mas nenhum resultado específico encontrado.')
    
    # Simular fontes encontradas (em implementação real, vem do banco vetorial)
    sources = []
    
    # Se há contexto de busca, criar chunks simulados
    if 'sources' in result:
        for i, source in enumerate(result['sources'][:request.max_results]):
            sources.append(DocumentChunk(
                chunk_id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=source.get('content', 'Conteúdo do documento...'),
                source=source.get('source', 'documento_desconhecido'),
                similarity_score=source.get('similarity', 0.8),
                metadata=source.get('metadata', {}),
            ))
    
    # Se não há fontes específicas, criar uma fonte genérica
    if not sources and request.include_sources:
        sources.append(DocumentChunk(
            chunk_id=f"chunk_{uuid.uuid4().hex[:8]}",
            content="Informação baseada no conhecimento do sistema",
            source="sistema_interno",
            similarity_score=0.7,
            metadata={
                'query_type': request.query_type,
                'generated': True,
            },
        ))
    
    confidence_score = result.get('confidence_score', 0.8)
    
    return {
        'answer': answer,
        'sources': sources,
        'confidence_score': confidence_score,
    }


def _process_chat_response(result: Dict[str, Any], request: ChatRequest) -> Dict[str, Any]:
    """Processa resposta do chat."""
    
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    message = result.get('content', 'Desculpe, não consegui processar sua mensagem.')
    
    # Extrair fontes se houver busca RAG
    sources = None
    if 'sources' in result:
        sources = []
        for source in result['sources'][:5]:  # Máximo 5 fontes no chat
            sources.append(DocumentChunk(
                chunk_id=f"chunk_{uuid.uuid4().hex[:8]}",
                content=source.get('content', ''),
                source=source.get('source', 'sistema'),
                similarity_score=source.get('similarity', 0.8),
                metadata=source.get('metadata', {}),
            ))
    
    confidence_score = result.get('confidence_score', 0.8)
    
    return {
        'message': message,
        'message_id': message_id,
        'sources': sources,
        'confidence_score': confidence_score,
    }