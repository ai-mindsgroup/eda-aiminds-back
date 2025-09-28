-- Atualizar schema da tabela metadata para suportar documentos RAG
-- Adiciona as colunas necessárias caso ainda não existam

-- Adicionar colunas se não existirem
DO $$ 
BEGIN
    -- Adicionar coluna title se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'metadata' AND column_name = 'title') THEN
        ALTER TABLE public.metadata ADD COLUMN title TEXT;
    END IF;

    -- Adicionar coluna content se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'metadata' AND column_name = 'content') THEN
        ALTER TABLE public.metadata ADD COLUMN content TEXT;
    END IF;

    -- Adicionar coluna timestamp se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'metadata' AND column_name = 'timestamp') THEN
        ALTER TABLE public.metadata ADD COLUMN timestamp TEXT;
    END IF;

    -- Adicionar coluna source se não existir  
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'metadata' AND column_name = 'source') THEN
        ALTER TABLE public.metadata ADD COLUMN source TEXT;
    END IF;

    -- Adicionar coluna metadata se não existir
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'metadata' AND column_name = 'metadata') THEN
        ALTER TABLE public.metadata ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_metadata_source ON public.metadata(source);
CREATE INDEX IF NOT EXISTS idx_metadata_timestamp ON public.metadata(timestamp);
CREATE INDEX IF NOT EXISTS idx_metadata_title ON public.metadata USING gin(to_tsvector('portuguese', title));
CREATE INDEX IF NOT EXISTS idx_metadata_content ON public.metadata USING gin(to_tsvector('portuguese', content));