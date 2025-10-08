-- Corrige função match_embeddings para usar distância cosseno corretamente
-- O operador <=> retorna distância cosseno de 0 (idêntico) a 2 (oposto)
-- Fórmula de similaridade: 1 - (distância / 2), resultando em valores de -1 a 1
-- onde 1 = idêntico, 0 = ortogonal, -1 = oposto

DROP FUNCTION IF EXISTS match_embeddings(vector, float, int);

CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(384),
    similarity_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    chunk_text text,
    embedding vector(384),
    metadata jsonb,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        embeddings.id,
        embeddings.chunk_text,
        embeddings.embedding,
        embeddings.metadata,
        1 - (embeddings.embedding <=> query_embedding) / 2 AS similarity
    FROM embeddings
    WHERE 1 - (embeddings.embedding <=> query_embedding) / 2 > similarity_threshold
    ORDER BY embeddings.embedding <=> query_embedding ASC
    LIMIT match_count;
$$;

COMMENT ON FUNCTION match_embeddings IS 
'Busca embeddings similares usando distância cosseno.
O operador <=> retorna distância cosseno (0 = idêntico, 2 = oposto).
Similaridade = 1 - (distância / 2), onde 1 = idêntico, 0 = ortogonal, -1 = oposto.
Threshold padrão 0.5 significa que vetores devem ter pelo menos 50% de similaridade.';
