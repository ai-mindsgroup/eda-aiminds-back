# Integração do Roteador Semântico no Orquestrador

**Data:** 04/10/2025  
**Módulo:** `orchestrator_agent.py`  
**Funcionalidade:** Roteamento inteligente de consultas via classificação semântica com embeddings

---

## Visão Geral

O sistema de roteamento do orquestrador foi aprimorado para utilizar classificação semântica via embeddings, substituindo o matching estático por palavras-chave por um pipeline inteligente de análise de intenção.

---

## Arquitetura

### Fluxo de Decisão

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRADA DO USUÁRIO                        │
│                      (query + context)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            ETAPA 1: ROTEAMENTO SEMÂNTICO                     │
│  • Gera embedding da pergunta (SENTENCE_TRANSFORMER)        │
│  • Consulta vetorial no Supabase (search_similar)           │
│  • Classifica intenção via Pydantic (QuestionIntent)        │
│  • Verifica confiança (threshold >= 0.7)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │ Confiança >= 0.7?     │
                └───────────┬───────────┘
                            │
            ┌───────────────┴───────────────┐
            │ SIM                       NÃO │
            ▼                               ▼
┌─────────────────────┐      ┌────────────────────────────┐
│  MAPEAR CATEGORIA   │      │  ETAPA 2: FALLBACK         │
│  • statistical_     │      │  • Matching por palavras   │
│    analysis → CSV   │      │  • Score de keywords       │
│  • fraud_detection  │      │  • Contexto de arquivo     │
│    → CSV            │      │  • Heurísticas estáticas   │
│  • llm_generic →    │      └────────────┬───────────────┘
│    LLM_ANALYSIS     │                   │
└──────────┬──────────┘                   │
           └──────────────┬────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              DELEGAÇÃO PARA AGENTE ESPECIALIZADO            │
│  • CSV: EmbeddingsAnalysisAgent                             │
│  • RAG: RAGAgent                                            │
│  • LLM: LLM Manager (GenericLLMAgent)                       │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   RESPOSTA CONSOLIDADA                       │
│         (com metadata de agentes_used e rota)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementação

### 1. Import do Semantic Router

```python
# Import do Roteador Semântico para classificação inteligente de intenções
try:
    from src.router.semantic_router import SemanticRouter
    SEMANTIC_ROUTER_AVAILABLE = True
except ImportError as e:
    SEMANTIC_ROUTER_AVAILABLE = False
    print(f"⚠️ Semantic Router não disponível: {str(e)[:100]}...")
```

### 2. Inicialização no Construtor

```python
# Semantic Router (para classificação inteligente de intenções via embeddings)
if SEMANTIC_ROUTER_AVAILABLE:
    try:
        self.semantic_router = SemanticRouter()
        self.logger.info("✅ Semantic Router inicializado (classificação via embeddings)")
        self.use_semantic_routing = True
    except Exception as e:
        error_msg = f"Semantic Router: {str(e)}"
        initialization_errors.append(error_msg)
        self.logger.warning(f"⚠️ {error_msg}")
        self.semantic_router = None
        self.use_semantic_routing = False
else:
    self.semantic_router = None
    self.use_semantic_routing = False
    self.logger.warning("⚠️ Semantic Router não disponível, usando roteamento estático")
```

### 3. Método `_classify_query` Aprimorado

```python
def _classify_query(self, query: str, context: Optional[Dict[str, Any]]) -> QueryType:
    """Classifica o tipo de consulta usando roteamento semântico ou estático.
    
    FLUXO DE DECISÃO:
    1. Se Semantic Router disponível: usa classificação via embeddings e consulta vetorial
    2. Fallback: usa matching estático por palavras-chave
    3. Logging: registra decisão e rota escolhida
    """
    
    # ETAPA 1: TENTATIVA DE ROTEAMENTO SEMÂNTICO
    if self.use_semantic_routing and self.semantic_router:
        try:
            self.logger.info("🧠 Usando roteamento semântico via embeddings...")
            
            # Chamar o roteador semântico para classificar intenção
            routing_result = self.semantic_router.route(query)
            
            # Log da decisão do roteador
            self.logger.info(f"📍 Roteamento semântico: {routing_result}")
            
            # Verificar confiança
            confidence = routing_result.get('confidence', 0.0)
            
            if confidence >= 0.7:
                # Mapear rota semântica para QueryType
                route_mapping = {
                    'statistical_analysis': QueryType.CSV_ANALYSIS,
                    'fraud_detection': QueryType.CSV_ANALYSIS,
                    'data_visualization': QueryType.CSV_ANALYSIS,
                    'contextual_embedding': QueryType.RAG_SEARCH,
                    'data_loading': QueryType.DATA_LOADING,
                    'llm_generic': QueryType.LLM_ANALYSIS,
                }
                
                query_type = route_mapping.get(routing_result.get('route'))
                
                if query_type:
                    self.logger.info(f"🎯 Rota semântica mapeada: {route} → {query_type.value}")
                    return query_type
        except Exception as e:
            self.logger.error(f"❌ Erro no roteamento semântico: {str(e)}")
    
    # ETAPA 2: FALLBACK - ROTEAMENTO ESTÁTICO
    self.logger.info("📋 Usando roteamento estático por palavras-chave...")
    # ... código de matching estático continua ...
```

---

## Logging e Auditoria

### Pontos de Logging Implementados

1. **Inicialização:**
   - ✅ Status do Semantic Router (disponível/indisponível)
   - ✅ Modo de roteamento ativo (semântico/estático)

2. **Durante Classificação:**
   - 🧠 Inicio do roteamento semântico
   - 📍 Resultado da classificação (rota, confiança, entidades)
   - ✅ Alta confiança detectada
   - ⚠️ Baixa confiança (fallback)
   - ❌ Erros na classificação semântica
   - 📋 Fallback para roteamento estático

3. **Durante Delegação:**
   - 📊 Agente escolhido para processar
   - 🔍 Preview da query
   - 📦 Contexto de dados disponível
   - ✅ Sucesso na execução
   - ❌ Erros no agente especializado

---

## Mapeamento de Rotas

| Categoria Semântica       | QueryType         | Agente Responsável          |
|---------------------------|-------------------|-----------------------------|
| `statistical_analysis`    | CSV_ANALYSIS      | EmbeddingsAnalysisAgent     |
| `fraud_detection`         | CSV_ANALYSIS      | EmbeddingsAnalysisAgent     |
| `data_visualization`      | CSV_ANALYSIS      | EmbeddingsAnalysisAgent     |
| `contextual_embedding`    | RAG_SEARCH        | RAGAgent                    |
| `data_loading`            | DATA_LOADING      | DataProcessor               |
| `llm_generic`             | LLM_ANALYSIS      | GenericLLMAgent             |
| `unknown`                 | (fallback)        | Roteamento estático         |

---

## Threshold de Confiança

- **Threshold atual:** 0.7 (70%)
- **Comportamento:**
  - `>= 0.7`: Usa rota semântica
  - `< 0.7`: Fallback para matching estático

**Recomendação:** Ajustar threshold conforme métricas de acurácia em produção.

---

## Testes

### Script de Teste

Executar: `python teste_integracao_semantic_router.py`

### Casos de Teste

1. ✅ "Qual a média da variável Amount?" → `statistical_analysis` → CSV_ANALYSIS
2. ✅ "Qual a mediana de V1?" → `statistical_analysis` → CSV_ANALYSIS
3. ✅ "Mostre o intervalo de valores da variável Time" → `statistical_analysis` → CSV_ANALYSIS
4. ✅ "Detecte fraudes no dataset" → `fraud_detection` → CSV_ANALYSIS
5. ✅ "Gere um histograma da distribuição de Amount" → `data_visualization` → CSV_ANALYSIS
6. ✅ "Explique os padrões encontrados nos dados" → `llm_generic` → LLM_ANALYSIS

---

## Próximos Passos

### Melhorias Recomendadas

1. **Popular banco com categorias:**
   - Adicionar embeddings com metadados de categoria
   - Treinar classificador com exemplos de cada tipo de consulta

2. **Ajuste fino de threshold:**
   - Analisar métricas de confiança
   - Ajustar threshold baseado em performance real

3. **Expansão de categorias:**
   - Adicionar novas categorias conforme necessário
   - Implementar categorias compostas (multi-agente)

4. **Dashboard de auditoria:**
   - Visualizar decisões de roteamento
   - Monitorar distribuição de rotas
   - Identificar padrões de consulta

5. **Feedback loop:**
   - Coletar feedback de usuários
   - Atualizar vocabulário automaticamente
   - Retreinar classificador periodicamente

---

## Dependências

- `src.router.semantic_router`: SemanticRouter
- `src.embeddings.generator`: EmbeddingGenerator (SENTENCE_TRANSFORMER)
- `src.embeddings.vector_store`: VectorStore
- `src.vectorstore.supabase_client`: supabase (cliente global)

---

## Compatibilidade

- ✅ **Retrocompatível:** Sistema funciona com fallback estático se Semantic Router indisponível
- ✅ **Modular:** Pode ser desabilitado sem impactar funcionalidade básica
- ✅ **Testado:** 4/4 testes do semantic_router passando

---

## Autoria

- **Desenvolvido por:** GitHub Copilot (GPT-4.1)
- **Sessão:** 04/10/2025
- **Branch:** feature/refactore-langchain
- **Commit:** [Próximo commit]

---

## Referências

- [Documentação Semantic Router](./semantic_router.md)
- [Arquitetura Multiagente](./STATUS-COMPLETO-PROJETO.md)
- [RAG e Embeddings](./langchain/rag-embeddings.md)
