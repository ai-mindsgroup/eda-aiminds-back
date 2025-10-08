# QueryRefiner - Implementação (2025-10-06)

Resumo
------
Este documento descreve a nova pipeline `QueryRefiner` que valida e refina queries para busca vetorial usando embeddings.

Arquivos principais
------------------
- `src/router/query_refiner.py` - Pipeline iterativo que gera embedding da query, compara com histórico via `VectorStore.search_similar` e gera refinamentos heurísticos usando `src/router/semantic_ontology.py`.
- `src/router/semantic_ontology.py` - Ontologia estatística e utilitários de expansão/variações simples.
- `src/router/semantic_router.py` - Atualizado para chamar `QueryRefiner` em `search_with_expansion` quando a busca inicial não retorna resultados.

Como funciona
-------------
1. `search_with_expansion` tenta a busca com a query original.
2. Se nenhum resultado, chama `QueryRefiner.refine_query`.
3. `QueryRefiner` gera embedding, consulta `VectorStore.search_similar` por histórico e, se necessário, aplica heurísticas de refinamento (até `max_iterations`).
4. Se obtiver resultados satisfatórios (similaridade >= `similarity_threshold`), retorna os resultados ao roteador.

Parâmetros configuráveis
------------------------
- `similarity_threshold` (default 0.72)
- `max_iterations` (default 3)

Logs e monitoramento
--------------------
- `QueryRefiner.refine_query` registra `best_historical_similarity`, número de iterações e status de sucesso.
- Recomenda-se adicionar métricas de contagem de refinamentos e taxa de sucesso para monitoramento contínuo.

Boas práticas
------------
- Persistir explicitamente queries bem-sucedidas usando `VectorStore.store_embedding` com metadados `embedding_type='query_success'` melhora a qualidade do histórico.
- Para históricos por sessão, considerar converter `QueryRefiner` para async e usar `SupabaseMemory.search_similar`.

Compatibilidade
---------------
- Preserva LangChain e memória Supabase; `QueryRefiner` usa `VectorStore` (síncrono) por simplicidade e estabilidade no roteador.

Próximos passos recomendados
---------------------------
1. Salvar queries bem-sucedidas explicitamente (melhora histórico).
2. Implementar variações via LLM (paraphrase) para refinamentos mais robustos.
3. Adicionar métricas/telemetria (Prometheus/DB) e testes end-to-end mais abrangentes.
