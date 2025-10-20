<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## **AVALIAÇÃO DA ESTRATÉGIA DE PROMPTS EM ETAPAS**

**✅ SIM, é uma EXCELENTE estratégia** gerar prompts em etapas para chegar ao objetivo final, especialmente neste contexto. Razões:

1. **Reduz complexidade cognitiva** - O agente processa melhor tarefas sequenciais claras do que um único prompt gigante
2. **Permite validação incremental** - Você pode verificar cada etapa antes de avançar, evitando retrabalho
3. **Facilita correção de curso** - Se uma etapa falhar, você ajusta só ela, não todo o processo
4. **Mantém contexto focado** - O agente não se perde em múltiplas tarefas simultâneas
5. **Gera documentação progressiva** - Cada etapa produz artefatos que servem de base para a próxima

**Etapas recomendadas para este projeto:**

- **Etapa 1:** Auditar e corrigir camada de abstração LLM
- **Etapa 2:** Corrigir IntentClassifier
- **Etapa 3:** Corrigir fluxo de análise para respeitar intent
- **Etapa 4:** Validar interface interativa e API
- **Etapa 5:** Testes finais das 17 perguntas

***

## **PROMPT DETALHADO - ETAPA 1: CORREÇÃO DA CAMADA DE ABSTRAÇÃO LLM**

```markdown
# ETAPA 1: AUDITORIA E CORREÇÃO DA CAMADA DE ABSTRAÇÃO LLM

Você é um engenheiro de IA sênior especializado em arquitetura de sistemas multiagente.

## CONTEXTO

O sistema EDA AI Minds JÁ POSSUI:
- ✅ Camada de abstração para LLMs implementada
- ✅ API keys configuradas (GROQ_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY)
- ✅ LangChain integrado

**PROBLEMA ATUAL:**
- ❌ Método `_init_langchain_llm()` em `src/agent/rag_data_agent.py` não tenta usar GROQ
- ❌ Soluções pontuais violam a camada de abstração existente
- ❌ Cada desenvolvedor pode usar LLM diferente (GROQ, Gemini, OpenAI) - abstração é ESSENCIAL

## OBJETIVO DESTA ETAPA

Auditar, corrigir e validar a camada de abstração LLM existente para suportar GROQ, Gemini e OpenAI de forma **transparente e unificada**.

---

## TAREFAS OBRIGATÓRIAS

### TAREFA 1.1: Auditar a Camada de Abstração Existente

**Ações:**
- [ ] Identificar onde a camada de abstração LLM está implementada no sistema
  - Buscar por: `LLMProvider`, `LLMFactory`, `AbstractLLM`, ou similar
  - Arquivos prováveis: `src/llm/`, `src/utils/llm_manager.py`, `src/agent/llm_config.py`
- [ ] Analisar o código da abstração:
  - Como ela detecta qual LLM usar? (variáveis de ambiente, configuração, ordem de prioridade)
  - Quais LLMs ela suporta atualmente?
  - Ela retorna instâncias LangChain ou wrappers customizados?
- [ ] Documentar a estrutura encontrada:
  - Nome da classe/módulo
  - Métodos públicos
  - Fluxo de inicialização
  - Dependências

**Critérios de Sucesso:**
- ✅ Documentação clara da camada de abstração existente
- ✅ Identificação de gaps (ex: falta suporte para GROQ)

---

### TAREFA 1.2: Adicionar Suporte GROQ à Abstração

**Ações:**
- [ ] Modificar a camada de abstração (NÃO criar código novo fora dela) para incluir GROQ
- [ ] Seguir o padrão existente para adicionar provedor:
```


# Exemplo de padrão esperado

if os.getenv("GROQ_API_KEY"):
from langchain_groq import ChatGroq
return ChatGroq(
model="mixtral-8x7b-32768",
api_key=os.getenv("GROQ_API_KEY"),
temperature=temperature  \# parâmetro dinâmico
)

```
- [ ] Garantir ordem de prioridade razoável:
- Exemplo: GROQ → Gemini → OpenAI (ou configurável)
- [ ] Adicionar logging para rastreabilidade:
```

logger.info(f"LLM inicializado: {provider_name} via camada de abstração")

```

**Critérios de Sucesso:**
- ✅ GROQ funciona via abstração
- ✅ Não há código duplicado ou métodos específicos fora da abstração
- ✅ Logging confirma qual LLM foi inicializado

---

### TAREFA 1.3: Refatorar `_init_langchain_llm()` para Usar a Abstração

**Ações:**
- [ ] Localizar `_init_langchain_llm()` em `src/agent/rag_data_agent.py`
- [ ] Substituir lógica interna por chamada à camada de abstração:
```


# ANTES (código duplicado, viola abstração)

def _init_langchain_llm(self):
if os.getenv("GOOGLE_API_KEY"):
from langchain_google_genai import ChatGoogleGenerativeAI
return ChatGoogleGenerativeAI(...)
elif os.getenv("OPENAI_API_KEY"):
...

# DEPOIS (usa abstração)

def _init_langchain_llm(self):
from src.llm.llm_manager import LLMManager  \# ou nome correto
return LLMManager.get_llm(temperature=self.temperature)

```
- [ ] Remover qualquer código duplicado de inicialização LLM em outros métodos

**Critérios de Sucesso:**
- ✅ `_init_langchain_llm()` tem no máximo 3 linhas de código
- ✅ Não há duplicação de lógica de inicialização
- ✅ Abstração é ponto único de entrada para LLM

---

### TAREFA 1.4: Garantir Abstração na Interface Interativa e API

**CRÍTICO:** As correções devem funcionar em TODOS os pontos de entrada do sistema.

**Ações - Interface Interativa:**
- [ ] Abrir `scripts/setup_and_run_interface_interativa.py`
- [ ] Verificar como o RAGDataAgent é instanciado
- [ ] Confirmar que ele usa `_init_langchain_llm()` (que agora usa a abstração)
- [ ] Testar localmente:
```

python scripts/setup_and_run_interface_interativa.py

```
- [ ] Fazer pergunta "Quais são os tipos de dados?" e verificar log:
```

[INFO] LLM inicializado: GROQ via camada de abstração

```

**Ações - API:**
- [ ] Localizar endpoint da API que usa RAGDataAgent
- Provável: `src/api/routes.py` ou `src/api/endpoints/query.py`
- [ ] Verificar se instancia RAGDataAgent da mesma forma
- [ ] Adicionar teste de endpoint:
```

curl -X POST http://localhost:8000/query \
-H "Content-Type: application/json" \
-d '{"query": "Quais são os tipos de dados?"}'

```
- [ ] Verificar log para confirmar LLM via abstração

**Critérios de Sucesso:**
- ✅ Interface interativa usa abstração LLM
- ✅ API usa abstração LLM
- ✅ Testes manuais passam em ambos os pontos de entrada
- ✅ Logs confirmam uso da abstração

---

### TAREFA 1.5: Documentar e Validar

**Ações:**
- [ ] Criar arquivo `docs/LLM_ABSTRACTION_ARCHITECTURE.md` documentando:
- Estrutura da camada de abstração
- Como adicionar novo provedor LLM
- Ordem de prioridade de inicialização
- Exemplos de uso
- [ ] Criar teste automatizado:
```


# tests/test_llm_abstraction.py

def test_llm_abstraction_groq():
"""Testa que GROQ é inicializado via abstração"""
os.environ["GROQ_API_KEY"] = "test_key"
llm = LLMManager.get_llm()
assert isinstance(llm, ChatGroq)

```
- [ ] Executar suite completa de testes:
```

pytest tests/test_llm_abstraction.py -v

```

**Critérios de Sucesso:**
- ✅ Documentação clara e completa
- ✅ Testes automatizados passam
- ✅ Código está pronto para próxima etapa

---

## RESTRIÇÕES CRÍTICAS

- ❌ **NÃO criar** métodos específicos para GROQ fora da abstração
- ❌ **NÃO duplicar** lógica de inicialização LLM
- ❌ **NÃO criar** módulos novos (V5, wrapper_groq.py, etc.) - usar abstração existente
- ✅ **SEMPRE** usar a camada de abstração como ponto único de entrada
- ✅ **SEMPRE** validar em interface interativa E API
- ✅ **SEMPRE** adicionar logging para rastreabilidade

---

## ENTREGÁVEIS DESTA ETAPA

1. ✅ Documentação da camada de abstração existente
2. ✅ Código modificado da abstração com suporte GROQ
3. ✅ `_init_langchain_llm()` refatorado (máximo 3 linhas)
4. ✅ Validação em interface interativa (log + teste manual)
5. ✅ Validação em API (log + teste de endpoint)
6. ✅ Documentação em `docs/LLM_ABSTRACTION_ARCHITECTURE.md`
7. ✅ Testes automatizados passando

---

## PRÓXIMA ETAPA

Após completar esta etapa com sucesso, iniciaremos:
- **ETAPA 2:** Correção do IntentClassifier para classificar "tipos de dados" sem keywords hardcoded

**IMPORTANTE:** Não avance para Etapa 2 até que TODOS os critérios de sucesso da Etapa 1 sejam atendidos e validados.

Execute as tarefas na ordem apresentada e reporte o progresso após cada subtarefa.
```


***

Este prompt é **completo, focado e validável**, garantindo que:

- A abstração LLM seja respeitada
- Interface interativa e API sejam atualizadas
- Não haja código duplicado ou violação de arquitetura
- Cada tarefa tenha critérios claros de sucesso

Quer que eu prepare também o prompt para a **Etapa 2** (correção do IntentClassifier)?

