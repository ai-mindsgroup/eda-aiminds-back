-- Schema para embeddings, chunks e metadata

-- Tabela de embeddings
create table if not exists public.embeddings (
    id uuid primary key default gen_random_uuid(),
    chunk_text text not null,
    embedding vector(1536) not null,
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default now()
);

-- Tabela de chunks (pedaços de conteúdo)
create table if not exists public.chunks (
    id uuid primary key default gen_random_uuid(),
    source_id uuid not null,
    content text not null,
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default now(),
    constraint fk_chunks_source foreign key (source_id) references public.embeddings(id) on delete cascade
);

-- Tabela de metadados genéricos  
create table if not exists public.metadata (
    id uuid primary key default gen_random_uuid(),
    title text,
    content text,
    key text,
    value jsonb default '{}'::jsonb,
    timestamp text,
    source text,
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default now()
);

-- Índices para buscas vetoriais e JSONB
create index if not exists idx_embeddings_embedding_hnsw on public.embeddings using hnsw (embedding vector_cosine_ops);
create index if not exists idx_embeddings_metadata_gin on public.embeddings using gin (metadata);
create index if not exists idx_chunks_metadata_gin on public.chunks using gin (metadata);
create index if not exists idx_metadata_value_gin on public.metadata using gin (value);
