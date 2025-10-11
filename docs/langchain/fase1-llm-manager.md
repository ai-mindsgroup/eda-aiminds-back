# Fase 1: Integração LangChain - LLM Manager

**Data:** 02/10/2025  
**Status:** ✅ Implementado

---

## Objetivo

Refatorar o LLM Manager para usar LangChain como backend principal, mantendo fallback customizado e garantindo estabilidade durante a migração.

---

## Implementação

### Arquivo: `src/llm/langchain_manager.py`

Novo módulo que integra LangChain para gerenciamento de múltiplos provedores LLM:

- **ChatOpenAI** (OpenAI GPT)
- **ChatGoogleGenerativeAI** (Google Gemini)
- **ChatGroq** (Groq)

### Funcionalidades

1. **Suporte a múltiplos provedores**
   - Ordem de preferência configurável
   - Detecção automática de disponibilidade
   - Fallback automático quando um provedor falha

2. **Configuração completa de hiperparâmetros**
   ```python
   config = LLMConfig(
       temperature=0.2,    # Criatividade (0.0-1.0)
       max_tokens=1024,    # Limite de tokens
       top_p=0.9          # Nucleus sampling
   )
   ```

3. **Interface padronizada**
   ```python
   from src.llm.langchain_manager import get_langchain_llm_manager
   
   manager = get_langchain_llm_manager()
   response = manager.chat("Sua pergunta aqui")
   ```

4. **Sistema de cache**
   - Clientes LangChain são reutilizados
   - Otimização de performance

5. **Logging estruturado**
   - Rastreamento de provedores
   - Monitoramento de fallbacks
   - Métricas de tempo de processamento

### Resposta Padronizada

```python
@dataclass
class LLMResponse:
    content: str              # Conteúdo da resposta
    provider: LLMProvider     # Provedor utilizado
    model: str               # Modelo específico
    tokens_used: int         # Tokens consumidos
    processing_time: float   # Tempo de processamento
    error: str               # Erro (se houver)
    success: bool            # Status da chamada
```

---

## Testes

### Arquivo: `tests/langchain/test_langchain_manager.py`

Testes implementados:

1. **Testes unitários**
   - ✅ Inicialização do manager
   - ✅ Verificação de status dos provedores
   - ✅ Chamadas básicas de chat
   - ✅ Configuração personalizada
   - ✅ System prompts
   - ✅ Modelos padrão
   - ✅ Metadados de resposta

2. **Testes de integração**
   - ✅ Provedor Groq
   - ✅ Provedor Google
   - ✅ Provedor OpenAI

### Executar testes

```bash
# Todos os testes
pytest tests/langchain/test_langchain_manager.py -v

# Apenas testes unitários
pytest tests/langchain/test_langchain_manager.py -v -m "not integration"

# Apenas testes de integração
pytest tests/langchain/test_langchain_manager.py -v -m integration
```

---

## Uso

### Exemplo básico

```python
from src.llm.langchain_manager import get_langchain_llm_manager

manager = get_langchain_llm_manager()
response = manager.chat("Analise estes dados de fraude...")

print(response.content)
print(f"Provedor: {response.provider.value}")
print(f"Tempo: {response.processing_time:.2f}s")
```

### Exemplo com configuração

```python
from src.llm.langchain_manager import get_langchain_llm_manager, LLMConfig

manager = get_langchain_llm_manager()

config = LLMConfig(
    temperature=0.1,  # Mais determinístico
    max_tokens=2048,
    top_p=0.95
)

response = manager.chat(
    "Gere um relatório detalhado...",
    config=config,
    system_prompt="Você é um analista de dados experiente."
)
```

### Exemplo com provedor específico

```python
from src.llm.langchain_manager import get_langchain_llm_manager, LLMProvider

manager = get_langchain_llm_manager()

# Forçar uso do Groq
response = manager.chat(
    "Sua pergunta",
    provider=LLMProvider.GROQ
)
```

---

## Configuração de API Keys

Certifique-se de que as seguintes variáveis estão configuradas em `configs/.env`:

```env
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
```

---

## Migração do Sistema Legado

### Compatibilidade

O novo LangChain Manager é **compatível** com o manager legado:

- Mesma interface de resposta (`LLMResponse`)
- Mesmos enums (`LLMProvider`)
- Mesma configuração (`LLMConfig`)

### Plano de Migração

1. **Fase Atual**: Novo manager disponível em paralelo
2. **Próxima Fase**: Atualizar agentes para usar `get_langchain_llm_manager()`
3. **Fase Final**: Deprecar manager legado

### Exemplo de Migração em Agentes

**Antes:**
```python
from src.llm.manager import get_llm_manager

manager = get_llm_manager()
response = manager.chat("...")
```

**Depois:**
```python
from src.llm.langchain_manager import get_langchain_llm_manager

manager = get_langchain_llm_manager()
response = manager.chat("...")
```

---

## Próximos Passos

- [ ] Fase 2: Sistema de Memória LangChain
- [ ] Fase 3: Chunking com TextSplitters
- [ ] Fase 4: Retrieval com LangChain
- [ ] Fase 5: Chains e Workflows

---

## Dependências Adicionais

Certifique-se de instalar as dependências LangChain:

```bash
pip install langchain langchain-openai langchain-google-genai langchain-groq
```

---

## Referências

- [LangChain Documentation](https://python.langchain.com/)
- [ChatOpenAI](https://python.langchain.com/docs/integrations/chat/openai)
- [ChatGoogleGenerativeAI](https://python.langchain.com/docs/integrations/chat/google_generative_ai)
- [ChatGroq](https://python.langchain.com/docs/integrations/chat/groq)
