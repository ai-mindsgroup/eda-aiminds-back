# Plano de Expansão LangChain - Sistema EDA AI Minds

**Data:** 05/10/2025  
**Objetivo:** Expandir uso consistente da LangChain em todo o sistema  
**Abordagem:** Gradual, modular, com testes e fallback robusto  

---

## 1. Mapeamento Atual

### 1.1 Agentes e Status LangChain

| Agente | Status Atual | API Direta | Oportunidade LangChain |
|--------|-------------|------------|------------------------|
| **RAGDataAgent** | ✅ LangChain integrado | - | Já conforme |
| **GroqLLMAgent** | ❌ API Groq direta | `groq.Groq()` | `ChatGroq` do LangChain |
| **GoogleLLMAgent** | ❌ API Gemini direta | `genai.GenerativeModel()` | `ChatGoogleGenerativeAI` |
| **GrokLLMAgent** | ❌ API xAI direta | HTTP requests | Wrapper customizado |
| **RAGAgent** | ⚠️ LLM Manager | Via manager | Usar LangChain chains |
| **EmbeddingsAnalysisAgent** | ⚠️ LLM Manager | Via manager | Usar LangChain chains |
| **OrchestratorAgent** | ✅ Delega | - | Já conforme |

### 1.2 LLM Manager

**Status:** Usa APIs diretas com fallback manual

**Oportunidades:**
- Converter para `ChatOpenAI`, `ChatGoogleGenerativeAI`, `ChatGroq`
- Usar `LangChain Router` para seleção automática de provider
- Implementar `ConversationChain` para gerenciamento de contexto

### 1.3 Funções Críticas para Conversão

```python
# GroqLLMAgent
def _call_groq_api(messages, temperature, max_tokens)  # → ChatGroq
def _format_response(raw_response)                     # → Usar .invoke()

# GoogleLLMAgent  
def _call_gemini_api(prompt, config)                   # → ChatGoogleGenerativeAI
def _process_response(raw)                             # → Usar .invoke()

# LLM Manager
def _call_groq(prompt, config)                         # → ChatGroq
def _call_google(prompt, config)                       # → ChatGoogleGenerativeAI
def _call_openai(prompt, config)                       # → ChatOpenAI
def chat(messages, fallback=True)                      # → ConversationChain
```

---

## 2. Arquitetura Proposta

### 2.1 Camada de Abstração LangChain

```
┌─────────────────────────────────────────────────────┐
│           LangChain Wrapper Layer                    │
│  (Unified interface para todos os LLMs)              │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
    ┌────▼─────┐              ┌─────▼────┐
    │ ChatGroq │              │ChatGoogleGen│
    │          │              │   AI        │
    └────┬─────┘              └─────┬────┘
         │                          │
         │    ┌──────────────┐      │
         └────►  ChatOpenAI  ◄──────┘
              └──────┬───────┘
                     │
              ┌──────▼───────┐
              │ Fallback &   │
              │ Router Chain │
              └──────────────┘
```

### 2.2 Integração com Memória

```python
# Todos os agentes usarão:
from langchain.memory import ConversationBufferMemory
from src.memory.langchain_supabase_memory import LangChainSupabaseMemory

# Configuração unificada
memory = LangChainSupabaseMemory(
    agent_name=agent_name,
    session_id=session_id,
    supabase_manager=SupabaseMemoryManager(agent_name)
)

conversation_chain = ConversationChain(
    llm=langchain_llm,
    memory=memory,
    verbose=True
)
```

---

## 3. Implementação Gradual

### Fase 1: LLM Manager com LangChain (PRIORIDADE ALTA)

**Objetivo:** Converter núcleo do sistema

**Arquivos:**
- `src/llm/manager.py` → `src/llm/langchain_manager.py`

**Mudanças:**
```python
class LangChainManager:
    """Gerenciador LLM usando LangChain nativamente."""
    
    def __init__(self):
        self.providers = {
            LLMProvider.GROQ: ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-8b-instant"),
            LLMProvider.GOOGLE: ChatGoogleGenerativeAI(api_key=GOOGLE_API_KEY, model="gemini-pro"),
            LLMProvider.OPENAI: ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")
        }
        
        # Router automático com fallback
        self.router = RouterChain(
            llms=self.providers,
            fallback_order=[LLMProvider.GROQ, LLMProvider.GOOGLE, LLMProvider.OPENAI]
        )
    
    def chat(self, messages: List[BaseMessage], config: LLMConfig) -> LLMResponse:
        """Usa LangChain chain com fallback automático."""
        try:
            response = self.router.invoke(messages)
            return self._parse_response(response)
        except Exception as e:
            return self._handle_error(e)
```

### Fase 2: GroqLLMAgent com ChatGroq (PRIORIDADE ALTA)

**Arquivo:** `src/agent/groq_llm_agent.py`

**Mudanças:**
```python
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

class GroqLLMAgent(BaseAgent):
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        super().__init__(name="groq_llm", enable_memory=True)
        
        # LangChain native
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=model,
            temperature=0.3,
            max_tokens=2000
        )
        
        # Memory integration
        self.memory = ConversationBufferMemory(return_messages=True)
        
        # Conversation chain
        self.chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=True
        )
    
    async def process(self, query: str, context: dict = None) -> dict:
        """Usa LangChain chain ao invés de API direta."""
        # 1. Recuperar memória Supabase
        memory_context = await self.recall_conversation_context()
        
        # 2. Preparar mensagens
        messages = [
            SystemMessage(content=self._build_system_prompt(context)),
            HumanMessage(content=query)
        ]
        
        # 3. Invocar chain
        response = await asyncio.to_thread(self.chain.invoke, {"input": query})
        
        # 4. Salvar na memória
        await self.remember_interaction(query, response["response"], ...)
        
        return self._build_response(response["response"])
```

### Fase 3: GoogleLLMAgent com ChatGoogleGenerativeAI (PRIORIDADE ALTA)

**Arquivo:** `src/agent/google_llm_agent.py`

**Implementação similar ao GroqLLMAgent:**
```python
from langchain_google_genai import ChatGoogleGenerativeAI

class GoogleLLMAgent(BaseAgent):
    def __init__(self, model: str = "gemini-2.0-flash"):
        super().__init__(name="google_llm", enable_memory=True)
        
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=GOOGLE_API_KEY,
            model=model,
            temperature=0.3,
            max_tokens=2000
        )
        
        self.memory = LangChainSupabaseMemory(
            agent_name=self.name,
            supabase_manager=SupabaseMemoryManager(self.name)
        )
        
        self.chain = ConversationChain(llm=self.llm, memory=self.memory)
```

### Fase 4: RAGAgent e EmbeddingsAnalysisAgent (PRIORIDADE MÉDIA)

**Objetivo:** Usar LangChain chains ao invés de LLM Manager

**Mudanças:**
```python
class RAGAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="rag_agent", enable_memory=True)
        
        # Usar LangChain native
        self.llm = ChatGroq(...)  # ou via LangChainManager
        
        # RAG Chain
        from langchain.chains import RetrievalQA
        self.rag_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(),
            memory=self.memory
        )
    
    async def process(self, query: str, context: dict = None):
        """Usa RetrievalQA chain."""
        result = await asyncio.to_thread(self.rag_chain.invoke, {"query": query})
        return self._build_response(result["result"])
```

### Fase 5: Otimizações e Caching (PRIORIDADE MÉDIA)

**Implementações:**

1. **Cache de Embeddings:**
```python
from langchain.embeddings.cache import CacheBackedEmbeddings
from langchain.storage import RedisStore

cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings=base_embeddings,
    document_embedding_cache=RedisStore(redis_url="redis://localhost:6379"),
    namespace="embeddings"
)
```

2. **Connection Pooling:**
```python
from langchain.llms import OpenAI

llm = OpenAI(
    model="gpt-3.5-turbo",
    max_retries=3,
    request_timeout=30,
    max_tokens=2000
)
```

3. **Caching de Respostas:**
```python
from langchain.cache import SQLiteCache
import langchain

langchain.llm_cache = SQLiteCache(database_path=".langchain.db")
```

---

## 4. Benefícios da Migração

### 4.1 Benefícios Técnicos

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Código** | APIs diferentes por provedor | Interface unificada |
| **Fallback** | Manual, hard-coded | Automático via RouterChain |
| **Memória** | Implementação customizada | LangChain Memory nativo |
| **Chains** | Fluxos manuais | Chains pré-construídas |
| **Retry** | Implementação manual | Nativo no LangChain |
| **Logging** | Customizado | LangChain callbacks |

### 4.2 Manutenibilidade

- ✅ Código 30-40% mais conciso
- ✅ Menos bugs (componentes testados)
- ✅ Documentação oficial disponível
- ✅ Comunidade ativa para suporte
- ✅ Atualizações automáticas de provedores

### 4.3 Performance

**Ganhos esperados:**
- Cache nativo: -50% chamadas LLM repetidas
- Connection pooling: -30% latência
- Retry automático: +20% confiabilidade

**Overhead:**
- +10-15ms por chamada (aceitável)

---

## 5. Estratégia de Testes

### 5.1 Testes Unitários

```python
# tests/agent/test_groq_langchain.py
async def test_groq_agent_with_langchain():
    agent = GroqLLMAgent()
    
    # Testar resposta básica
    response = await agent.process("Teste LangChain")
    assert response["success"] == True
    assert "content" in response
    
    # Testar memória
    response2 = await agent.process("Continue", session_id=session_id)
    assert response2["metadata"]["previous_interactions"] > 0
```

### 5.2 Testes de Integração

```python
# tests/integration/test_langchain_system.py
async def test_full_system_with_langchain():
    # 1. Testar LangChainManager
    manager = LangChainManager()
    response = manager.chat([HumanMessage(content="Test")])
    assert response.success
    
    # 2. Testar fallback
    with patch.object(manager.providers[LLMProvider.GROQ], 'invoke', side_effect=Exception):
        response = manager.chat([HumanMessage(content="Test fallback")])
        assert response.provider == LLMProvider.GOOGLE
    
    # 3. Testar memória persistente
    agent = GroqLLMAgent()
    session_id = str(uuid4())
    
    await agent.process("Primeira pergunta", session_id=session_id)
    response2 = await agent.process("Segunda pergunta", session_id=session_id)
    
    # Verificar no Supabase
    conversations = supabase.table('agent_conversations').select('*').eq('session_id', session_id).execute()
    assert len(conversations.data) >= 2
```

### 5.3 Testes de Performance

```python
# tests/performance/test_langchain_performance.py
import time

async def test_langchain_performance():
    agent = GroqLLMAgent()
    
    # Teste sem cache
    start = time.time()
    response1 = await agent.process("Query complexa para teste")
    time_no_cache = time.time() - start
    
    # Teste com cache (mesma query)
    start = time.time()
    response2 = await agent.process("Query complexa para teste")
    time_with_cache = time.time() - start
    
    # Cache deve ser significativamente mais rápido
    assert time_with_cache < time_no_cache * 0.5
    
    print(f"Sem cache: {time_no_cache:.2f}s")
    print(f"Com cache: {time_with_cache:.2f}s")
    print(f"Ganho: {((time_no_cache - time_with_cache) / time_no_cache * 100):.1f}%")
```

---

## 6. Cronograma de Implementação

| Fase | Componente | Esforço | Prioridade | Status |
|------|-----------|---------|-----------|--------|
| 1 | LangChainManager | 8h | 🔴 Alta | 📋 Planejado |
| 2 | GroqLLMAgent | 4h | 🔴 Alta | 📋 Planejado |
| 3 | GoogleLLMAgent | 4h | 🔴 Alta | 📋 Planejado |
| 4 | RAGAgent | 6h | 🟡 Média | 📋 Planejado |
| 5 | EmbeddingsAnalysisAgent | 6h | 🟡 Média | 📋 Planejado |
| 6 | Testes unitários | 6h | 🔴 Alta | 📋 Planejado |
| 7 | Testes integração | 8h | 🔴 Alta | 📋 Planejado |
| 8 | Otimizações (cache) | 4h | 🟡 Média | 📋 Planejado |
| 9 | Documentação | 4h | 🟡 Média | 📋 Planejado |
| **TOTAL** | | **50h** | | |

**Estimativa:** 1-2 semanas com desenvolvedor full-time

---

## 7. Critérios de Aceitação

### 7.1 Funcional

- ✅ Todos os agentes usam LangChain nativamente
- ✅ Fallback automático funciona entre provedores
- ✅ Memória persistente integrada via LangChain Memory
- ✅ Chains funcionam corretamente (ConversationChain, RetrievalQA)
- ✅ Respostas mantêm mesma qualidade

### 7.2 Performance

- ✅ Latência ≤ 15% maior que APIs diretas
- ✅ Cache reduz ≥ 40% chamadas repetidas
- ✅ Fallback automático em < 2s
- ✅ Memória persistente em < 500ms

### 7.3 Qualidade

- ✅ Cobertura de testes ≥ 80%
- ✅ Zero regressões funcionais
- ✅ Documentação atualizada
- ✅ Logs estruturados e claros

---

## 8. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|--------------|-----------|
| LangChain overhead | Médio | Alta | Testes de performance, otimizações |
| Breaking changes | Alto | Baixa | Testes extensivos, feature flags |
| Dependências extras | Baixo | Alta | Documentar requirements, Docker |
| Curva de aprendizado | Médio | Média | Documentação interna, exemplos |
| Bugs LangChain | Médio | Média | Fallback para APIs diretas |

---

## 9. Próximos Passos Imediatos

1. ✅ **Criar branch:** `feature/expand-langchain`
2. 📋 **Implementar:** `LangChainManager` (núcleo)
3. 📋 **Refatorar:** `GroqLLMAgent` (primeiro agente)
4. 📋 **Testar:** Testes unitários + integração
5. 📋 **Validar:** Performance e funcionalidade
6. 📋 **Expandir:** Demais agentes gradualmente
7. 📋 **Documentar:** Gerar relatório final

---

**Documento criado em:** 05/10/2025  
**Autor:** Sistema Multiagente EDA AI Minds  
**Status:** 📋 Plano Aprovado - Aguardando Implementação
