-- Remove constraint NOT NULL da coluna key da tabela metadata
-- para permitir inserções sem essa informação

-- Remover constraint NOT NULL se existir
ALTER TABLE public.metadata ALTER COLUMN key DROP NOT NULL;