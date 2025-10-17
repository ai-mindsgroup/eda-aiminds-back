-- ═══════════════════════════════════════════════════════════════════════════
-- MIGRATION: Sandbox Monitoring Schema
-- Description: Cria tabelas e índices para sistema de monitoramento do sandbox
-- Version: 1.0.0
-- Date: 2025-10-17
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- 1. TABELA: sandbox_metrics
-- Armazena métricas de execução do sandbox
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sandbox_metrics (
    -- Identificadores
    id BIGSERIAL PRIMARY KEY,
    execution_id TEXT NOT NULL UNIQUE,
    
    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Código
    code_hash TEXT NOT NULL,
    code_length INTEGER NOT NULL DEFAULT 0,
    
    -- Status e Resultado
    status TEXT NOT NULL CHECK (
        status IN (
            'SUCCESS', 'success',
            'FAILURE', 'failure',
            'TIMEOUT', 'timeout',
            'MEMORY_EXCEEDED', 'memory_exceeded',
            'COMPILATION_ERROR', 'compilation_error',
            'RUNTIME_ERROR', 'runtime_error'
        )
    ),
    success BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Performance
    execution_time_ms DOUBLE PRECISION NOT NULL,
    memory_used_mb DOUBLE PRECISION NOT NULL DEFAULT 0,
    memory_peak_mb DOUBLE PRECISION NOT NULL DEFAULT 0,
    
    -- Limites
    timeout_limit_s INTEGER NOT NULL DEFAULT 5,
    memory_limit_mb INTEGER NOT NULL DEFAULT 100,
    
    -- Erros
    error_type TEXT,
    error_message TEXT,
    
    -- Metadata adicional (JSON)
    metadata JSONB,
    
    -- Índices de auditoria
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE sandbox_metrics IS 'Métricas de execução do sandbox seguro';
COMMENT ON COLUMN sandbox_metrics.execution_id IS 'ID único da execução (UUID)';
COMMENT ON COLUMN sandbox_metrics.code_hash IS 'SHA-256 hash do código executado';
COMMENT ON COLUMN sandbox_metrics.status IS 'Status da execução';
COMMENT ON COLUMN sandbox_metrics.execution_time_ms IS 'Tempo de execução em milissegundos';
COMMENT ON COLUMN sandbox_metrics.memory_used_mb IS 'Memória utilizada em MB';
COMMENT ON COLUMN sandbox_metrics.error_type IS 'Tipo de erro (se houver)';
COMMENT ON COLUMN sandbox_metrics.metadata IS 'Metadados adicionais em formato JSON';

-- ═══════════════════════════════════════════════════════════════════════════
-- 2. ÍNDICES: sandbox_metrics
-- Otimização para queries frequentes
-- ═══════════════════════════════════════════════════════════════════════════

-- Índice por timestamp (queries temporais)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_timestamp 
ON sandbox_metrics(timestamp DESC);

-- Índice por status (filtrar por tipo de resultado)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_status 
ON sandbox_metrics(status);

-- Índice composto: timestamp + status (queries comuns)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_timestamp_status 
ON sandbox_metrics(timestamp DESC, status);

-- Índice por code_hash (identificar códigos repetidos)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_code_hash 
ON sandbox_metrics(code_hash);

-- Índice por success (filtrar sucesso/falha rápido)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_success 
ON sandbox_metrics(success, timestamp DESC);

-- Índice por error_type (agrupar erros)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_error_type 
ON sandbox_metrics(error_type) 
WHERE error_type IS NOT NULL;

-- Índice GIN para metadata (busca em JSON)
CREATE INDEX IF NOT EXISTS idx_sandbox_metrics_metadata 
ON sandbox_metrics USING GIN(metadata);

-- ═══════════════════════════════════════════════════════════════════════════
-- 3. TABELA: sandbox_alerts
-- Armazena alertas gerados pelo sistema de monitoramento
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sandbox_alerts (
    -- Identificadores
    id BIGSERIAL PRIMARY KEY,
    alert_id TEXT NOT NULL UNIQUE,
    
    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Tipo e Severidade
    alert_type TEXT NOT NULL CHECK (
        alert_type IN (
            'HIGH_FAILURE_RATE',
            'EXCESSIVE_TIMEOUTS',
            'MEMORY_EXCEEDED',
            'SUSPICIOUS_PATTERN',
            'SYSTEM_DEGRADATION'
        )
    ),
    level TEXT NOT NULL CHECK (
        level IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    
    -- Conteúdo do Alerta
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    
    -- Dados Relacionados
    value DOUBLE PRECISION,
    threshold DOUBLE PRECISION,
    period_hours INTEGER,
    
    -- Métricas Associadas (JSON)
    metrics JSONB,
    
    -- Recomendações (Array de strings)
    recommendations TEXT[],
    
    -- Status
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    
    -- Auditoria
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE sandbox_alerts IS 'Alertas do sistema de monitoramento do sandbox';
COMMENT ON COLUMN sandbox_alerts.alert_id IS 'ID único do alerta';
COMMENT ON COLUMN sandbox_alerts.alert_type IS 'Tipo de alerta detectado';
COMMENT ON COLUMN sandbox_alerts.level IS 'Nível de severidade do alerta';
COMMENT ON COLUMN sandbox_alerts.value IS 'Valor observado que disparou o alerta';
COMMENT ON COLUMN sandbox_alerts.threshold IS 'Limite configurado da regra';
COMMENT ON COLUMN sandbox_alerts.metrics IS 'Métricas associadas ao alerta';
COMMENT ON COLUMN sandbox_alerts.recommendations IS 'Recomendações automáticas';
COMMENT ON COLUMN sandbox_alerts.acknowledged IS 'Se o alerta foi reconhecido';
COMMENT ON COLUMN sandbox_alerts.resolved IS 'Se o alerta foi resolvido';

-- ═══════════════════════════════════════════════════════════════════════════
-- 4. ÍNDICES: sandbox_alerts
-- Otimização para queries de alertas
-- ═══════════════════════════════════════════════════════════════════════════

-- Índice por timestamp (alertas recentes)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_timestamp 
ON sandbox_alerts(timestamp DESC);

-- Índice por alert_type (filtrar por tipo)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_type 
ON sandbox_alerts(alert_type);

-- Índice por level (filtrar por severidade)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_level 
ON sandbox_alerts(level);

-- Índice composto: timestamp + level (alertas críticos recentes)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_timestamp_level 
ON sandbox_alerts(timestamp DESC, level);

-- Índice por status (não resolvidos)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_resolved 
ON sandbox_alerts(resolved, timestamp DESC);

-- Índice por acknowledged (não reconhecidos)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_acknowledged 
ON sandbox_alerts(acknowledged, timestamp DESC);

-- Índice GIN para metrics (busca em JSON)
CREATE INDEX IF NOT EXISTS idx_sandbox_alerts_metrics 
ON sandbox_alerts USING GIN(metrics);

-- ═══════════════════════════════════════════════════════════════════════════
-- 5. FUNÇÃO: Cleanup de métricas antigas
-- Remove métricas com mais de 90 dias (manutenção)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION cleanup_old_sandbox_metrics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sandbox_metrics
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_sandbox_metrics() IS 
'Remove métricas do sandbox com mais de 90 dias';

-- ═══════════════════════════════════════════════════════════════════════════
-- 6. FUNÇÃO: Cleanup de alertas antigos
-- Remove alertas resolvidos com mais de 30 dias
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION cleanup_old_sandbox_alerts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sandbox_alerts
    WHERE resolved = TRUE 
    AND resolved_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_sandbox_alerts() IS 
'Remove alertas resolvidos com mais de 30 dias';

-- ═══════════════════════════════════════════════════════════════════════════
-- 7. VIEW: Estatísticas Recentes (24h)
-- Visão agregada das últimas 24 horas
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW sandbox_metrics_24h AS
SELECT
    COUNT(*) as total_executions,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_executions,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_executions,
    ROUND(
        (COUNT(*) FILTER (WHERE success = TRUE)::NUMERIC / COUNT(*)::NUMERIC * 100),
        2
    ) as success_rate,
    ROUND(AVG(execution_time_ms)::NUMERIC, 2) as avg_execution_time_ms,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms)::NUMERIC, 2) as median_execution_time_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms)::NUMERIC, 2) as p95_execution_time_ms,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms)::NUMERIC, 2) as p99_execution_time_ms,
    ROUND(MAX(execution_time_ms)::NUMERIC, 2) as max_execution_time_ms,
    ROUND(AVG(memory_used_mb)::NUMERIC, 2) as avg_memory_used_mb,
    ROUND(MAX(memory_used_mb)::NUMERIC, 2) as max_memory_used_mb,
    MIN(timestamp) as period_start,
    MAX(timestamp) as period_end
FROM sandbox_metrics
WHERE timestamp >= NOW() - INTERVAL '24 hours';

COMMENT ON VIEW sandbox_metrics_24h IS 
'Estatísticas agregadas das últimas 24 horas de execuções do sandbox';

-- ═══════════════════════════════════════════════════════════════════════════
-- 8. VIEW: Alertas Ativos
-- Alertas não resolvidos
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW sandbox_alerts_active AS
SELECT
    alert_id,
    timestamp,
    alert_type,
    level,
    title,
    message,
    value,
    threshold,
    acknowledged,
    acknowledged_at,
    recommendations
FROM sandbox_alerts
WHERE resolved = FALSE
ORDER BY 
    CASE level
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        WHEN 'INFO' THEN 5
    END,
    timestamp DESC;

COMMENT ON VIEW sandbox_alerts_active IS 
'Alertas ativos (não resolvidos) ordenados por severidade e timestamp';

-- ═══════════════════════════════════════════════════════════════════════════
-- 9. RLS (Row Level Security) - Opcional
-- Descomente se precisar de segurança em nível de linha
-- ═══════════════════════════════════════════════════════════════════════════

-- ALTER TABLE sandbox_metrics ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sandbox_alerts ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Public read access for sandbox_metrics"
-- ON sandbox_metrics FOR SELECT
-- USING (true);

-- CREATE POLICY "Public read access for sandbox_alerts"
-- ON sandbox_alerts FOR SELECT
-- USING (true);

-- ═══════════════════════════════════════════════════════════════════════════
-- 10. GRANTS - Permissões
-- ═══════════════════════════════════════════════════════════════════════════

-- Grant para authenticated users (Supabase)
GRANT SELECT, INSERT ON sandbox_metrics TO authenticated;
GRANT SELECT, INSERT, UPDATE ON sandbox_alerts TO authenticated;

-- Grant para anon users (leitura apenas de views)
GRANT SELECT ON sandbox_metrics_24h TO anon;
GRANT SELECT ON sandbox_alerts_active TO anon;

-- ═══════════════════════════════════════════════════════════════════════════
-- FIM DA MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════

-- Verificação final
DO $$
BEGIN
    RAISE NOTICE '✅ Migration sandbox_monitoring_schema.sql aplicada com sucesso!';
    RAISE NOTICE '📊 Tabelas criadas: sandbox_metrics, sandbox_alerts';
    RAISE NOTICE '🔍 Views criadas: sandbox_metrics_24h, sandbox_alerts_active';
    RAISE NOTICE '🧹 Funções criadas: cleanup_old_sandbox_metrics, cleanup_old_sandbox_alerts';
END $$;
