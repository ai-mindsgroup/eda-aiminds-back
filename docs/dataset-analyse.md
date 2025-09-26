# Análise do Dataset `creditcard.csv`

Este documento consolida todo o conteúdo discutido na nossa iteração sobre o dataset de fraude em cartões de crédito (comumente conhecido do Kaggle: `creditcard.csv`). Ele orienta seu uso dentro da arquitetura RAG/multiagente planejada para o projeto.

---
## 1. Visão Geral do Dataset
- Origem típica: Competição/dataset público (Kaggle) de transações com fraude.
- Linhas aproximadas: ~284.807 registros.
- Colunas: 31 ao todo (caso completo):
  - `Time`
  - `V1` a `V28` (componentes PCA previamente anonimizados)
  - `Amount`
  - `Class` (0 = legítima, 1 = fraude)
- Natureza: Dados numéricos (features já transformadas via PCA), altamente desbalanceados.

### 1.1 Desbalanceamento
- Fraudes ~0,172% (cerca de 492 casos em 284k linhas)
- Implicações:
  - Não usar apenas acurácia como métrica (preferir AUC-ROC, Precision-Recall, F1 para classe positiva, MCC).
  - Necessidade de técnicas de reamostragem (SMOTE, undersampling) ou ajuste de threshold dependendo do objetivo.
  - Para embeddings ou clustering, tratar separadamente outliers (fraudes) pode evitar distorção do espaço vetorial.

---
## 2. Objetivos de Uso no Projeto
Dentro da nossa arquitetura (RAG + Agentes):
1. Geração de resumos estatísticos por feature e agrupamentos.
2. Construção de uma camada de contexto para perguntas analíticas em linguagem natural (ex: "Quais variáveis mais correlacionam com a fraudes?").
3. Possível suporte a um agente de "profiling" que sintetiza padrões e anomalias.
4. Criação de embeddings sobre descrições derivadas (não diretamente sobre os vetores PCA crus, que são numéricos e já transformados) para permitir busca semântica baseada em descrições interpretáveis.

---
## 3. Estratégia de Engenharia de Atributos para Contexto Semântico
As colunas `V1`..`V28` não têm significado direto. Portanto, em vez de embutir valores numéricos brutos, geraremos descrições textuais compactas:
- Estatísticas resumidas (min, max, mean, std) por feature.
- Ranking de importância (via feature importance de um modelo baseline ou SHAP) agregada em texto.
- Agrupamento KMeans ou HDBSCAN em subset de transações → para cada cluster: tamanho, média das features principais, proporção de fraudes.
- Perfis de fraude: médias condicionais das features para transações fraudulentas vs legítimas.

Cada unidade textual (chunk) será armazenada em `chunks`/`embeddings` no Postgres (pgvector) seguindo o schema já criado.

---
## 4. Formato de Chunks Proposto
Exemplo de chunk textual (pseudo):
```
CLUSTER 3 (n=12.540, fraudes=0.21%)
Top deviations vs global mean: V4(+1.2σ), V12(-0.8σ), V17(+0.6σ)
Mean Amount: 92.13 (global: 88.35)
Comment: Cluster levemente acima da média em V4 e V17; baixa variabilidade em V12.
```

Outro exemplo (importância de features):
```
FEATURE IMPORTANCE SNAPSHOT:
1. V17 (fraud separation: KS=0.42)
2. V14 (KS=0.39)
3. V12 (KS=0.33)
High-separation features show heavier right tails for fraud class.
```

Esses textos são então embeddados com modelo (ex: `text-embedding-3-small`, dim=1536) → vetores armazenados em `embeddings.embedding`.

---
## 5. Estimativa de Tokens e Custo
### 5.1 Heurística de Tokens
- `creditcard.csv` original (numérico) não é diretamente útil para embeddings textuais.
- Após conversão em resumos, cada chunk esperado: 50–180 tokens.
- Se gerarmos, por exemplo:
  - 30 clusters + 1 resumo global + 1 importância de features + 5 perfis de fraude segmentados por faixas de `Amount` = ~37 chunks.
  - Média 120 tokens/chunk → ~4.440 tokens totais para embedding.

### 5.2 Comparação com Abordagem Ingênua
- Embedding linha a linha (não recomendado):
  - 284.807 linhas * (~150 tokens se textualizados) ≈ >42 milhões tokens (custos altos, sem ganho real para consulta semântica de alto nível).
- Nossa abordagem reduz a ordem de grandeza de milhões → poucos milhares.

### 5.3 Cálculo Aproximado
Tokens estimados T ≈ N_chunks * tokens_médios
Para reajustar: aumentar granularidade só quando necessário (ex: clusters com alta entropia → subdividir).

---
## 6. Pipeline Proposto (Futuro)
1. Leitura segura do CSV (pandas) em agente de ingestão.
2. Profiling estatístico:
   - Distribuições
   - Correlações (Pearson/Spearman) filtrando |r| > 0.25
   - KS-test entre classes para priorizar features.
3. Clustering nas features escaladas (`StandardScaler`).
4. Geração textual dos resumos (templates padronizados).
5. Embedding via modelo 1536-dim (compatível com schema atual) → inserir em `embeddings`.
6. Inserir chunks + metadados (tipo: cluster_summary, feature_importance, fraud_profile, global_summary) em `chunks`.
7. Indexação incremental: registrar data de geração em `metadata` JSONB.
8. Consulta RAG: usuário pergunta → retrieval top-k (HNSW) → montar contexto → LLM (Sonar/OpenAI) gera resposta.

---
## 7. Esquema de Banco (Resumo Relevante)
- `embeddings(id, embedding vector(1536), created_at)`
- `chunks(id, embedding_id FK, content text, created_at)`
- `metadata(id, chunk_id FK, key text, value jsonb)`
- Índices: HNSW em `embedding`, GIN em `metadata.value`.

---
## 8. Decisões Técnicas Relacionadas
| Decisão | Justificativa |
|---------|---------------|
| Não embutir todas as linhas | Custo e irrelevância semântica; foco em resumos. |
| Dimensão 1536 | Compatível com modelos populares (OpenAI small) e adequada para granularidade moderada. |
| Uso de descrições derivadas | Cria semântica interpretável para QA. |
| Clustering + perfis | Reduz ruído e permite contexto macro. |
| Metadados JSONB | Flexibilidade para evoluir tipos de chunks sem alterar schema. |

---
## 9. Métricas Sugeridas para Avaliar Qualidade do Contexto
- Cobertura: % de features mencionadas em pelo menos um chunk.
- Densidade Semântica: tokens médios / informação (heurístico qualitativo).
- Relevância de Retrieval: MRR / Recall@k em queries de teste definidas manualmente.
- Drift: Necessidade de regenerar embeddings se heurísticas mudam ou se novas estatísticas forem introduzidas.

---
## 10. Próximos Passos (Relacionados ao Dataset)
| Prioridade | Tarefa | Status |
|------------|--------|--------|
| Alta | Esqueleto do agente de profiling | Pendente |
| Alta | Função para gerar descrições de clusters | Pendente |
| Média | Implementar cálculo KS/feature importance | Pendente |
| Média | Módulo de geração de chunks + inserção no DB | Pendente |
| Média | Teste de fumaça (embedding + insert) | Pendente |
| Baixa | Métricas de avaliação de retrieval | Pendente |

---
## 11. Riscos e Mitigações
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Overfitting de clusters irrelevantes | Contexto ruidoso | Ajustar número de clusters via silhouette e inspeção manual inicial |
| Aumento de custo se granularidade explodir | Custo tokens | Limitar geração inicial a ~40 chunks e expandir sob demanda |
| Inconsistência de dimensão de embedding futura | Erro de inserção | Centralizar dimensão em config e validar antes de inserir |
| Queries ambíguas | Respostas genéricas | Expandir prompt com instruções para pedir clarificação |

---
## 12. Exemplos de Queries Alvo
- "Quais clusters concentram maior proporção de fraudes?"
- "Quais as 5 features mais discriminantes entre fraude e não fraude?"
- "Existe diferença relevante no `Amount` entre clusters principais?"
- "Qual o perfil estatístico da classe de fraude?"

---
## 13. Integração com Agentes
- Agente Ingestão: valida schema do CSV, aciona profiling.
- Agente Profiling: gera estatísticas, clusters, importância, perfis.
- Agente Indexação: transforma resumos em chunks + embeddings e persiste.
- Agente Orquestrador: recebe pergunta do usuário, chama retrieval e LLM.
- Guardrails: impedir perguntas que pedem dados de linha individual (risco de reidentificação) — responder com agregações.

---
## 14. Checklist de Implementação (Roadmap Incremental)
1. Criar módulo `profiling/loader.py` (carregar CSV com dtypes explícitos)
2. Implementar `profiling/stats.py` (estatísticas globais + KS)
3. Implementar `profiling/clustering.py`
4. Gerar descrições em `profiling/descriptions.py`
5. Módulo `indexer/chunk_builder.py` (templates + cortes de tamanho)
6. Módulo `indexer/embed_and_store.py` (usa cliente embeddings + inserts)
7. Testes: mocks para embeddings → validar pipeline de ponta a ponta sem custo externo

---
## 15. Considerações de Privacidade
Embora o dataset seja público e anonimizado, manter:
- Não reverter componentes PCA (impossível, mas registramos ética).
- Evitar reembutir todos os registros para não criar material redundante.
- Logs: não registrar conteúdo completo dos chunks em nível DEBUG em produção.

---
## 16. Resumo Executivo
Usaremos o dataset `creditcard.csv` apenas como fonte para construir um "knowledge layer" estatístico e semântico compacto (~40 chunks embeddados). Focaremos em resumos agregados (clusters, importância de features, perfis de fraude) para permitir consultas analíticas em linguagem natural com baixo custo de tokens e alta interpretabilidade. Próximo passo: criar esqueleto dos módulos de profiling e indexação.

---
*Documento gerado automaticamente a partir das decisões e discussões do histórico do projeto.*
