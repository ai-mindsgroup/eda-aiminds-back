-- Função RPC para busca vetorial de similaridade
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    chunk_text text,
    metadata jsonb,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        embeddings.id,
        embeddings.chunk_text,
        embeddings.metadata,
        1 - (embeddings.embedding <=> query_embedding) AS similarity
    FROM embeddings
    WHERE 1 - (embeddings.embedding <=> query_embedding) > similarity_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;