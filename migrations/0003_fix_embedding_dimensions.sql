-- Alterar dimensões do embedding de 1536 para 384 (all-MiniLM-L6-v2)

-- Primeiro, limpar todos os embeddings existentes (se houver)
truncate table public.embeddings cascade;

-- Remover índice HNSW antigo
drop index if exists idx_embeddings_embedding_hnsw;

-- Alterar tipo da coluna embedding
alter table public.embeddings alter column embedding type vector(384);

-- Recriar índice HNSW com novas dimensões
create index idx_embeddings_embedding_hnsw on public.embeddings using hnsw (embedding vector_cosine_ops);

-- Recriar função match_embeddings com novas dimensões
create or replace function match_embeddings(
    query_embedding vector(384),
    similarity_threshold float default 0.5,
    match_count int default 10
)
returns table (
    id uuid,
    chunk_text text,
    metadata jsonb,
    similarity float
)
language sql stable
as $$
    select
        embeddings.id,
        embeddings.chunk_text,
        embeddings.metadata,
        1 - (embeddings.embedding <=> query_embedding) as similarity
    from embeddings
    where 1 - (embeddings.embedding <=> query_embedding) > similarity_threshold
    order by similarity desc
    limit match_count;
$$;