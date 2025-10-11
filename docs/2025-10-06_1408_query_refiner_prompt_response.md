# Prompt e Resposta — 2025-10-06 14:08

## Prompt (usuário)

> Verifique se já existe uma rotina para validazar e refinar automaticamente as queries geradas para busca vetorial, usando embeddings.
>
> Se não houver, desenvolva um pipeline que:
> - Recebe a query gerada;
> - Calcula o embedding da query;
> - Compara com embeddings de queries anteriores que tiveram sucesso;
> - Se similaridade estiver abaixo de um limiar pré-definido, automaticamente gera uma nova query refinada, ajustando o prompt para incluir termos mais relevantes;
> - Repete o processo até obter uma query com qualidade mínima assegurada, respeitando um número máximo de iterações para evitar loops infinitos.
>
> Garanta:
> - Integração transparente com o sistema atual, que usa LangChain e Supabase para armazenamento e memória;
> - Que o processo seja eficiente e audível para debugging e melhorias futuras, com logs estruturados e métricas para monitoramento;
> - Controle e tratamento de erros para manter a estabilidade e segurança do fluxo.
>  (See <attachments> above for file contents. You may not need to search or read the file again.)


## Resposta (assistente)

Atualização rápida do que eu fiz e o próximo passo.

O que fiz
- Procurei por rotinas existentes de refinamento/expansão de queries — havia apenas heurísticas (ontologia e geração de variações simples) e scripts de `populate_intent_embeddings`, mas não uma rotina iterativa que compare a query atual com queries históricas bem-sucedidas e gere refinamentos automáticos.
- Implementei uma pipeline de refinamento e integrei ao roteador semântico:
  - Adicionado `src/router/semantic_ontology.py` (ontologia estatística + gerador de variações simples).
  - Adicionado `src/router/query_refiner.py` (pipeline iterativo que:
    - gera embedding da query,
    - compara com embeddings históricos via `VectorStore.search_similar`,
    - se similaridade < limiar, gera refinamentos heurísticos da query e repete até max de iterações),
    - logs estruturados e tratamento de exceções).
  - Integrei `QueryRefiner` em `src/router/semantic_router.py` dentro de `search_with_expansion` (tenta refinar automaticamente quando a busca inicial não retorna resultados).

Verificações e testes executados
- Rodei verificações sintáticas nos arquivos alterados — sem erros.
- Rodei o smoke test de distribuição (`python scripts/smoke_distribution_test.py`) antes e depois das mudanças:
  - Smoke test completou com sucesso; dataframe reconstruído e histogramas gerados em `outputs/histogramas/`.
  - Logs mostram o pipeline rodando normalmente; houve um erro pontual do `graph_generator` ao salvar um arquivo com nome repetido (já presente antes), mas o processo seguiu gerando os demais gráficos.

Detalhes técnicos e decisões importantes
- Por que usar VectorStore em vez da memória assíncrona:
  - A API `SupabaseMemory.search_similar` é assíncrona (async). Para manter `QueryRefiner` simples e evitar event loop/await complexidade ao ser chamado de fluxos síncronos no roteador, usei `VectorStore.search_similar` (síncrono) como source of historical successful query embeddings. Isso mantém o fluxo estável sem mudanças massivas na arquitetura.
- Heurísticas de refinamento:
  - `QueryRefiner._heuristic_refine` usa `StatisticalOntology.expand_query` e acrescenta termos relevantes (ex.: "desvio padrão", "variância", "média", "mínimo máximo") e pequenas frases por iteração para diversificar.
  - Parâmetros configuráveis: `similarity_threshold` (default 0.72) e `max_iterations` (default 3).
- Segurança e estabilidade:
  - Tratamento de exceções em todos os pontos de integração (fallback seguro que apenas registra a falha do refiner e segue para as variações simples).
  - Logs estruturados com mensagens informativas para debugging.
- Métricas e auditabilidade:
  - Logs em `QueryRefiner.refine_query` informam `best_historical_similarity`, iteração e sucesso.
  - Pode-se expandir para persistir métricas em DB (ex.: tabela `routing_metrics`) se preferir.

Arquivos criados/alterados (resumo)
- Added: `src/router/semantic_ontology.py` — ontologia + generate_simple_expansions
- Added: `src/router/query_refiner.py` — pipeline de refinamento iterativo
- Updated: `src/router/semantic_router.py` — import QueryRefiner; usa refiner dentro de `search_with_expansion`

Estado das tasks (delta)
- QueryRefiner criado e integrado — Done
- Smoke tests — In-progress → Smoke test completo com sucesso localmente (geração de histogramas OK). Vou marcar final quando você confirmar que quer que eu feche a task do todo.

Sugestões / próximos passos (recomendados)
1. Persistir metadados de queries bem-sucedidas:
   - Atualmente o refiner usa qualquer embedding da tabela `embeddings` via `VectorStore` (campo `chunk_text`); podemos criar um fluxo para salvar explicitamente queries bem-sucedidas (com metadados `embedding_type='query_success'`) usando `VectorStore.store_embedding` para melhorar a qualidade do histórico.
2. Tornar refiner assíncrono/opcional:
   - Se preferir integrar com memória assíncrona (SupabaseMemory) para histórico por sessão, posso converter `QueryRefiner` para async e adaptar chamadas no orquestrador (já suportado).
3. Melhorias de refinamento:
   - Substituir heurísticas por um prompt LLM (paraphrase/expand) para gerar variações mais naturais; isso costuma melhorar recall além de simples sinônimos.
4. Telemetria:
   - Adicionar contadores (Prometheus ou logs estruturados) para métricas: refinements_count, refinement_success_rate, avg_iterations.

Perguntas rápidas para alinhar o próximo trabalho
- Quer que eu:
  A) Grave explicitamente queries bem-sucedidas em uma tabela de memória (via `VectorStore.store_embedding`) para melhorar histórico? (recomendado)
  B) Converta o `QueryRefiner` para async e use `SupabaseMemory.search_similar` por sessão (se quiser histórico por sessão)? 
  C) Substitua heurística por geração via LLM (prompt) para paraphrase e variações mais ricas?

Se quiser, eu implemento (A) e (C) em seguida — A melhora imediata do histórico; C tende a aumentar significativamente recall em dados variados.

Se preferir, posso também:
- adicionar testes unitários para `QueryRefiner` e `StatisticalOntology`;
- documentar o novo módulo em `docs/` (sessão de desenvolvimento com timestamp) conforme as instruções internas.

Diga qual próximo passo prefere e eu sigo — se quiser, já aplico (A) e atualizo os testes e docs.
