# Documentação Técnica: Roteador Semântico EDA AI Minds

## Visão Geral
O roteador semântico é responsável por classificar perguntas do usuário, identificar intenções e delegar para agentes especializados. Utiliza embeddings, busca vetorial, validação Pydantic, fallback contextual e logging estruturado.

## Pipeline do Roteador

1. **Normalização**
   - Limpa e padroniza a pergunta do usuário.
   - Método: `normalize(question: str)`

2. **Geração de Embedding**
   - Converte a pergunta em vetor semântico usando o modelo configurado (ex: SentenceTransformer).
   - Método: `embed_question(question: str)`

3. **Classificação de Intenção**
   - Busca vetorial no VectorStore/Supabase para identificar categoria/intenção.
   - Valida entidades e confiança via Pydantic.
   - Método: `classify_intent(question: str)`

4. **Fallback Contextual**
   - Se não houver correspondência semântica, busca resposta contextualizada via embeddings.
   - Método: `fallback_contextual(question: str)`

5. **Logging Estruturado**
   - Todos os passos e decisões são logados para auditoria e debugging.

6. **Roteamento Final**
   - Retorna dicionário com rota, entidades, confiança e fonte.
   - Método: `route(question: str)`

## Integração com VectorStore
- O VectorStore gerencia armazenamento e busca de embeddings no Supabase.
- Embeddings de intenções são inseridos via scripts dedicados e expandidos dinamicamente.
- Busca vetorial retorna categoria, entidades e score de similaridade.

## Fallback e Robustez
- Se a classificação não atingir o threshold de confiança, o sistema tenta buscar contexto relevante.
- Se ainda assim não houver resposta, delega para LLM genérica.

## Exemplo de Uso
```python
from src.router.semantic_router import SemanticRouter
router = SemanticRouter()
resultado = router.route("Qual a média de Amount?")
print(resultado)
```

## Expansão Dinâmica
- Novas categorias podem ser detectadas e inseridas sem downtime.
- Basta rodar o script de expansão com exemplos reais e feedback.

## Auditoria e Logging
- Todas decisões são registradas via logger estruturado.
- Auditoria técnica disponível em docs/auditoria/.

## Referências
- src/router/semantic_router.py
- src/embeddings/vector_store.py
- scripts/populate_intent_embeddings.py
- scripts/expand_intent_categories.py

---
Equipe EDA AI Minds
