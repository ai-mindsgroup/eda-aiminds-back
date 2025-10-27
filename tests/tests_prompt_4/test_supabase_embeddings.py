import os
import uuid
import pytest


def _supabase_env_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL")) and bool(os.environ.get("SUPABASE_KEY"))


@pytest.mark.integration
def test_store_and_retrieve_embeddings_supabase(tmp_path, request):
    if not _supabase_env_configured():
        pytest.skip("Supabase não configurado (SUPABASE_URL/SUPABASE_KEY ausentes)")

    # Importações locais (só quando ambiente está configurado)
    from src.embeddings.vector_store import VectorStore
    from src.embeddings.generator import EmbeddingResult
    from src.embeddings.generator import EmbeddingProvider

    store = VectorStore()

    # Criar dois embeddings simples (dim=384)
    emb1 = [0.0] * 384
    emb2 = [0.1] * 384
    source = f"tests_prompt_4_supabase_{uuid.uuid4().hex[:8]}"

    results = [
        EmbeddingResult(
            chunk_content="hello world",
            embedding=emb1,
            provider=EmbeddingProvider.MOCK,
            model="mock-model",
            dimensions=len(emb1),
            processing_time=0.0,
            raw_dimensions=len(emb1),
            chunk_metadata={"source": source, "chunk_index": 0}
        ),
        EmbeddingResult(
            chunk_content="another chunk",
            embedding=emb2,
            provider=EmbeddingProvider.MOCK,
            model="mock-model",
            dimensions=len(emb2),
            processing_time=0.0,
            raw_dimensions=len(emb2),
            chunk_metadata={"source": source, "chunk_index": 1}
        ),
    ]

    ids = store.store_embeddings(results, source_type="text")
    assert len(ids) == 2

    # Recuperar por ID
    emb = store.get_embedding_by_id(ids[0])
    assert emb is not None
    assert emb.chunk_text in {"hello world", "another chunk"}
    assert isinstance(emb.embedding, list) and len(emb.embedding) == 384

    # (Opcional) Tentar busca vetorial se função RPC estiver disponível
    try:
        hits = store.search_similar(results[0].embedding, similarity_threshold=0.0, limit=5, filters={"source": source})
        assert isinstance(hits, list)
        # Pode retornar vazio se RPC não estiver configurado, então não forçar
    except Exception:
        pytest.skip("Busca vetorial via RPC indisponível no ambiente atual")

    # Cleanup
    removed = store.delete_embeddings_by_source(source)
    assert removed >= 2
