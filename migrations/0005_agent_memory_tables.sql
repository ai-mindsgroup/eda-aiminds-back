-- ============================================================================
-- Migration 0005: Agent Memory Tables
-- Criação de tabelas para sistema de memória persistente dos agentes
-- Autor: Sistema Multiagente EDA AI Minds
-- Data: 2025-01-28
-- ============================================================================

-- ############################################################################
-- 1. TABELA DE SESSÕES DOS AGENTES
-- ############################################################################

-- Tabela principal para gerenciar sessões de usuários/agentes
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    agent_name VARCHAR(100),
    session_type VARCHAR(50) DEFAULT 'interactive', -- 'interactive', 'batch', 'api'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'expired', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_session_type CHECK (session_type IN ('interactive', 'batch', 'api', 'system')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'expired', 'archived', 'terminated'))
);

-- Comentários da tabela
COMMENT ON TABLE agent_sessions IS 'Gerencia sessões de usuários e agentes com metadados e controle de expiração';
COMMENT ON COLUMN agent_sessions.session_id IS 'Identificador único da sessão (string legível)';
COMMENT ON COLUMN agent_sessions.user_id IS 'Identificador do usuário associado à sessão';
COMMENT ON COLUMN agent_sessions.agent_name IS 'Nome do agente principal da sessão';
COMMENT ON COLUMN agent_sessions.session_type IS 'Tipo da sessão: interactive, batch, api, system';
COMMENT ON COLUMN agent_sessions.status IS 'Status atual: active, expired, archived, terminated';
COMMENT ON COLUMN agent_sessions.expires_at IS 'Data/hora de expiração automática da sessão';
COMMENT ON COLUMN agent_sessions.metadata IS 'Metadados adicionais da sessão em formato JSON';

-- ############################################################################
-- 2. TABELA DE CONVERSAÇÕES DOS AGENTES
-- ############################################################################

-- Tabela para armazenar histórico completo de conversações
CREATE TABLE IF NOT EXISTS agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    conversation_turn INTEGER NOT NULL DEFAULT 1,
    message_type VARCHAR(20) NOT NULL, -- 'query', 'response', 'system', 'error'
    content TEXT NOT NULL,
    content_format VARCHAR(20) DEFAULT 'text', -- 'text', 'json', 'html', 'markdown'
    processing_time_ms INTEGER,
    token_count INTEGER,
    model_used VARCHAR(100),
    confidence_score DECIMAL(3,2), -- 0.00 a 1.00
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_message_type CHECK (message_type IN ('query', 'response', 'system', 'error', 'debug')),
    CONSTRAINT valid_content_format CHECK (content_format IN ('text', 'json', 'html', 'markdown', 'code')),
    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0.00 AND confidence_score <= 1.00)),
    CONSTRAINT positive_processing_time CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0),
    CONSTRAINT positive_token_count CHECK (token_count IS NULL OR token_count >= 0)
);

-- Comentários da tabela
COMMENT ON TABLE agent_conversations IS 'Histórico completo de conversações entre usuários e agentes';
COMMENT ON COLUMN agent_conversations.conversation_turn IS 'Número sequencial do turno na conversação';
COMMENT ON COLUMN agent_conversations.message_type IS 'Tipo da mensagem: query, response, system, error, debug';
COMMENT ON COLUMN agent_conversations.content IS 'Conteúdo principal da mensagem';
COMMENT ON COLUMN agent_conversations.content_format IS 'Formato do conteúdo: text, json, html, markdown, code';
COMMENT ON COLUMN agent_conversations.processing_time_ms IS 'Tempo de processamento em milissegundos';
COMMENT ON COLUMN agent_conversations.confidence_score IS 'Score de confiança da resposta (0.00-1.00)';

-- ############################################################################
-- 3. TABELA DE CONTEXTO DOS AGENTES
-- ############################################################################

-- Tabela para armazenar contexto específico de cada agente
CREATE TABLE IF NOT EXISTS agent_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    context_type VARCHAR(50) NOT NULL, -- 'data', 'preferences', 'state', 'cache', 'learning'
    context_key VARCHAR(255) NOT NULL,
    context_data JSONB NOT NULL,
    data_size_bytes INTEGER,
    access_count INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    expires_at TIMESTAMP WITH TIME ZONE, -- NULL = never expires
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_context_type CHECK (context_type IN ('data', 'preferences', 'state', 'cache', 'learning', 'embeddings', 'analysis')),
    CONSTRAINT positive_data_size CHECK (data_size_bytes IS NULL OR data_size_bytes >= 0),
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 10),
    CONSTRAINT positive_access_count CHECK (access_count >= 0),
    
    -- Unique constraint para evitar duplicatas
    UNIQUE(session_id, agent_name, context_type, context_key)
);

-- Comentários da tabela
COMMENT ON TABLE agent_context IS 'Contexto e estado específico de cada agente por sessão';
COMMENT ON COLUMN agent_context.context_type IS 'Tipo do contexto: data, preferences, state, cache, learning, embeddings, analysis';
COMMENT ON COLUMN agent_context.context_key IS 'Chave única para identificar o contexto específico';
COMMENT ON COLUMN agent_context.context_data IS 'Dados do contexto em formato JSON';
COMMENT ON COLUMN agent_context.data_size_bytes IS 'Tamanho dos dados em bytes para monitoramento';
COMMENT ON COLUMN agent_context.access_count IS 'Contador de acessos para análise de uso';
COMMENT ON COLUMN agent_context.priority IS 'Prioridade do contexto (1=alta, 10=baixa)';

-- ############################################################################
-- 4. TABELA DE EMBEDDINGS DE MEMÓRIA
-- ############################################################################

-- Tabela para armazenar embeddings relacionados à memória dos agentes
CREATE TABLE IF NOT EXISTS agent_memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE SET NULL,
    context_id UUID REFERENCES agent_context(id) ON DELETE SET NULL,
    embedding_type VARCHAR(50) NOT NULL, -- 'query', 'response', 'context', 'summary'
    source_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL, -- OpenAI embedding dimension
    similarity_threshold DECIMAL(4,3) DEFAULT 0.800, -- Threshold para similarity search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_embedding_type CHECK (embedding_type IN ('query', 'response', 'context', 'summary', 'learning')),
    CONSTRAINT valid_similarity_threshold CHECK (similarity_threshold >= 0.000 AND similarity_threshold <= 1.000)
);

-- Comentários da tabela
COMMENT ON TABLE agent_memory_embeddings IS 'Embeddings vetoriais para busca semântica em memória dos agentes';
COMMENT ON COLUMN agent_memory_embeddings.embedding_type IS 'Tipo do embedding: query, response, context, summary, learning';
COMMENT ON COLUMN agent_memory_embeddings.source_text IS 'Texto original que gerou o embedding';
COMMENT ON COLUMN agent_memory_embeddings.similarity_threshold IS 'Threshold mínimo para similarity search';

-- ############################################################################
-- 5. ÍNDICES PARA PERFORMANCE
-- ############################################################################

-- Índices para agent_sessions
CREATE INDEX IF NOT EXISTS idx_agent_sessions_session_id ON agent_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_expires_at ON agent_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_name ON agent_sessions(agent_name);

-- Índices para agent_conversations
CREATE INDEX IF NOT EXISTS idx_agent_conversations_session_id ON agent_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_agent_name ON agent_conversations(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_timestamp ON agent_conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_message_type ON agent_conversations(message_type);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_session_agent ON agent_conversations(session_id, agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_turn ON agent_conversations(session_id, conversation_turn);

-- Índices para agent_context
CREATE INDEX IF NOT EXISTS idx_agent_context_session_id ON agent_context(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_context_agent_name ON agent_context(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_context_type ON agent_context(context_type);
CREATE INDEX IF NOT EXISTS idx_agent_context_session_agent ON agent_context(session_id, agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_context_expires_at ON agent_context(expires_at);
CREATE INDEX IF NOT EXISTS idx_agent_context_priority ON agent_context(priority);
CREATE INDEX IF NOT EXISTS idx_agent_context_last_accessed ON agent_context(last_accessed_at);

-- Índices para agent_memory_embeddings
CREATE INDEX IF NOT EXISTS idx_agent_memory_embeddings_session_id ON agent_memory_embeddings(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_embeddings_agent_name ON agent_memory_embeddings(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_memory_embeddings_type ON agent_memory_embeddings(embedding_type);

-- Índice HNSW para similarity search (requer extensão pgvector)
CREATE INDEX IF NOT EXISTS idx_agent_memory_embeddings_vector 
ON agent_memory_embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- ############################################################################
-- 6. FUNÇÕES UTILITÁRIAS
-- ############################################################################

-- Função para limpeza automática de sessões expiradas
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Marcar sessões expiradas
    UPDATE agent_sessions 
    SET status = 'expired', updated_at = NOW()
    WHERE expires_at < NOW() AND status = 'active';
    
    -- Deletar contextos de sessões muito antigas (mais de 7 dias expiradas)
    DELETE FROM agent_context 
    WHERE session_id IN (
        SELECT id FROM agent_sessions 
        WHERE status = 'expired' 
        AND expires_at < NOW() - INTERVAL '7 days'
    );
    
    -- Deletar conversações muito antigas
    DELETE FROM agent_conversations 
    WHERE session_id IN (
        SELECT id FROM agent_sessions 
        WHERE status = 'expired' 
        AND expires_at < NOW() - INTERVAL '30 days'
    );
    
    -- Deletar sessões muito antigas
    DELETE FROM agent_sessions 
    WHERE status = 'expired' 
    AND expires_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Função para busca de similarity em memória
CREATE OR REPLACE FUNCTION search_memory_similarity(
    p_agent_name VARCHAR(100),
    p_session_id UUID,
    p_query_embedding vector(1536),
    p_similarity_threshold DECIMAL(4,3) DEFAULT 0.800,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    source_text TEXT,
    similarity DECIMAL(4,3),
    embedding_type VARCHAR(50),
    conversation_id UUID,
    context_id UUID,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ame.id,
        ame.source_text,
        (1 - (ame.embedding <=> p_query_embedding))::DECIMAL(4,3) as similarity,
        ame.embedding_type,
        ame.conversation_id,
        ame.context_id,
        ame.metadata
    FROM agent_memory_embeddings ame
    WHERE ame.agent_name = p_agent_name
      AND (p_session_id IS NULL OR ame.session_id = p_session_id)
      AND (1 - (ame.embedding <=> p_query_embedding)) >= p_similarity_threshold
    ORDER BY ame.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$;

-- ############################################################################
-- 7. TRIGGERS PARA MANUTENÇÃO AUTOMÁTICA
-- ############################################################################

-- Trigger para atualizar updated_at em agent_sessions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_sessions_updated_at 
    BEFORE UPDATE ON agent_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_context_updated_at 
    BEFORE UPDATE ON agent_context 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para atualizar last_accessed_at em agent_context
CREATE OR REPLACE FUNCTION update_last_accessed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at = NOW();
    NEW.access_count = COALESCE(OLD.access_count, 0) + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger apenas em SELECTs que atualizam o campo
-- (implementação específica será feita na aplicação)

-- ############################################################################
-- 8. COMENTÁRIOS FINAIS E VERIFICAÇÕES
-- ############################################################################

-- Verificar se as extensões necessárias estão instaladas
DO $$
BEGIN
    -- Verificar pgvector
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE 'AVISO: Extensão pgvector não está instalada. Execute: CREATE EXTENSION vector;';
    END IF;
    
    -- Verificar se as tabelas foram criadas com sucesso
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agent_sessions') THEN
        RAISE NOTICE 'SUCCESS: Tabelas de memória dos agentes criadas com sucesso!';
        RAISE NOTICE 'INFO: Use a função cleanup_expired_sessions() para manutenção automática';
        RAISE NOTICE 'INFO: Use a função search_memory_similarity() para busca semântica na memória';
    END IF;
END $$;

-- ============================================================================
-- FIM DA MIGRATION 0005: Agent Memory Tables
-- Total de tabelas criadas: 4 (agent_sessions, agent_conversations, agent_context, agent_memory_embeddings)
-- Total de índices criados: 16
-- Total de funções criadas: 3 (cleanup_expired_sessions, search_memory_similarity, triggers)
-- ============================================================================