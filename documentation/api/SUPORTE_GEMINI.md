# ✅ SIM! A Aplicação Aceita Gemini (Google)

**Resposta rápida**: ✅ **SIM, totalmente integrado!**

---

## 🎯 Suporte a LLMs na Aplicação

A aplicação tem **suporte nativo** para 3 provedores LLM com **fallback automático**:

### **Provedores Suportados**:

1. 🚀 **Groq** (Padrão - Mais rápido)
   - Modelo: `llama-3.1-8b-instant`
   - Velocidade: ⚡ Muito rápida
   - Gratuito até 14.400 requisições/dia

2. 🧠 **Google Gemini** (Recomendado - Melhor qualidade)
   - Modelo: `gemini-pro`
   - Qualidade: ⭐⭐⭐⭐⭐
   - Gratuito até 60 requisições/minuto

3. 💬 **OpenAI** (Fallback)
   - Modelo: `gpt-3.5-turbo`
   - Qualidade: ⭐⭐⭐⭐
   - Pago (requer créditos)

---

## 🔧 Como Configurar Gemini

### **Passo 1: Obter API Key do Google**

1. Acesse: https://makersuite.google.com/app/apikey
2. Clique em **"Create API Key"**
3. Selecione um projeto ou crie novo
4. Copie a chave gerada

### **Passo 2: Adicionar no `.env`**

Edite o arquivo `configs/.env`:

```env
# Já configurado ✅
SUPABASE_URL=https://ncefmfiulpwssaajybtl.supabase.co
SUPABASE_KEY=eyJhbGc...
DB_PASSWORD=Alder1310

# ADICIONE ESTA LINHA ⬇️
GOOGLE_API_KEY=AIzaSy...sua_chave_aqui...
```

### **Passo 3: Verificar Instalação**

A biblioteca já está instalada no `requirements.txt`:
```
langchain-google-genai==2.1.9
```

Para garantir:
```powershell
pip install langchain-google-genai
```

---

## 🚀 Como Usar

### **Opção 1: Automático (Recomendado)**

O sistema escolhe o melhor provedor disponível:

```python
from src.llm.manager import LLMManager

# Inicializa (prioriza: Groq → Google → OpenAI)
manager = LLMManager()

# Usa automaticamente
response = manager.chat("Analise estes dados de fraude...")
print(response.content)
print(f"Usado: {response.provider.value}")  # Ex: "google"
```

### **Opção 2: Forçar Google Gemini**

```python
from src.llm.manager import LLMManager, LLMProvider

# Força uso do Google Gemini
manager = LLMManager(preferred_providers=[LLMProvider.GOOGLE])

response = manager.chat("Sua pergunta aqui...")
```

### **Opção 3: Com Configurações Personalizadas**

```python
from src.llm.manager import LLMManager, LLMConfig

manager = LLMManager()

config = LLMConfig(
    temperature=0.7,  # Mais criativo
    max_tokens=2048,  # Resposta mais longa
    model="gemini-pro"
)

response = manager.chat("Explique análise de fraude", config=config)
```

---

## 📊 Prioridade de Fallback

Por padrão, o sistema tenta nesta ordem:

1. **Groq** (mais rápido) ⚡
   - Se falhar ou não configurado → 

2. **Google Gemini** (melhor qualidade) 🧠
   - Se falhar ou não configurado →

3. **OpenAI** (backup confiável) 💬

**Você pode mudar a ordem:**
```python
manager = LLMManager(preferred_providers=[
    LLMProvider.GOOGLE,  # Primeiro: Google
    LLMProvider.GROQ,    # Segundo: Groq
    LLMProvider.OPENAI   # Terceiro: OpenAI
])
```

---

## 🧪 Testar Gemini

### **Script de Teste Rápido**:

Crie `test_gemini.py`:

```python
from src.llm.manager import LLMManager, LLMProvider

# Força uso do Gemini
manager = LLMManager(preferred_providers=[LLMProvider.GOOGLE])

# Teste simples
response = manager.chat("Olá! Você é o Gemini?")
print(f"✅ Resposta do {response.provider.value}:")
print(response.content)
print(f"\n⏱️ Tempo: {response.processing_time:.2f}s")
print(f"🔤 Tokens: {response.tokens_used or 'N/A'}")
```

Execute:
```powershell
python test_gemini.py
```

**Saída esperada**:
```
✅ LLM Manager inicializado com provedor ativo: google
✅ Resposta do google:
Sim, sou o Gemini, um modelo de linguagem grande desenvolvido pelo Google...

⏱️ Tempo: 1.23s
🔤 Tokens: 42
```

---

## 🔍 Verificar Status dos Provedores

```python
from src.llm.manager import LLMManager

manager = LLMManager()

# Ver status de todos os provedores
for provider, status in manager._provider_status.items():
    print(f"{provider.value}: {'✅' if status['available'] else '❌'} - {status['message']}")
```

**Saída esperada (com Gemini configurado)**:
```
groq: ❌ - API key não configurada
google: ✅ - Google Gemini disponível
openai: ❌ - API key não configurada
```

---

## 📚 Onde o Gemini é Usado na Aplicação

### **1. Análise de CSV** (`src/agent/csv_analysis_agent.py`):
```python
# Análise inteligente de dados
llm_manager = LLMManager()
response = llm_manager.chat(f"Analise este CSV: {data_summary}")
```

### **2. Detecção de Fraude** (`src/agent/fraud_detection_agent.py`):
```python
# Detecção avançada com IA
llm = LLMManager()
analysis = llm.chat(f"Identifique padrões de fraude em: {transactions}")
```

### **3. Chat Inteligente** (API REST):
```python
# Endpoint /chat
llm_manager = LLMManager()
response = llm_manager.chat(user_message)
```

### **4. Sistema RAG** (`src/rag/pipeline.py`):
```python
# Busca semântica + geração de resposta
llm = LLMManager()
answer = llm.chat(f"Com base no contexto: {context}\nPergunta: {query}")
```

---

## 💰 Custos e Limites

### **Google Gemini (Gratuito)**:
- ✅ **60 requisições por minuto**
- ✅ **1.500 requisições por dia**
- ✅ Totalmente gratuito
- 📖 Documentação: https://ai.google.dev/pricing

### **Comparação**:
| Provedor | Limite Gratuito | Velocidade | Qualidade |
|----------|-----------------|------------|-----------|
| Groq | 14.400/dia | ⚡⚡⚡ | ⭐⭐⭐ |
| **Gemini** | **1.500/dia** | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| OpenAI | Pago | ⚡⚡ | ⭐⭐⭐⭐ |

---

## 🎯 Recomendação de Uso

### **Para Desenvolvimento**:
```env
# Use Groq (mais rápido para testes)
GROQ_API_KEY=sua_chave_groq
GOOGLE_API_KEY=sua_chave_google  # Fallback
```

### **Para Produção**:
```env
# Use Gemini (melhor qualidade)
GOOGLE_API_KEY=sua_chave_google  # Principal
GROQ_API_KEY=sua_chave_groq     # Backup
```

### **Para Máxima Confiabilidade**:
```env
# Configure os 3
GOOGLE_API_KEY=sua_chave_google
GROQ_API_KEY=sua_chave_groq
OPENAI_API_KEY=sua_chave_openai
```

---

## ✅ Checklist de Configuração

- [ ] Obter API Key do Google: https://makersuite.google.com/app/apikey
- [ ] Adicionar `GOOGLE_API_KEY` no `configs/.env`
- [ ] Verificar instalação: `pip install langchain-google-genai`
- [ ] Testar com script de teste
- [ ] Iniciar API completa: `uvicorn src.api.main:app --reload`
- [ ] Verificar logs: deve mostrar "✅ GOOGLE: Google Gemini disponível"

---

## 🚨 Solução de Problemas

### **Erro: "API key não configurada"**
✅ Adicione `GOOGLE_API_KEY` no `.env`

### **Erro: "Biblioteca não instalada"**
```powershell
pip install langchain-google-genai google-generativeai
```

### **Erro: "Rate limit exceeded"**
✅ Você atingiu 60 req/min. Aguarde 1 minuto ou configure fallback.

### **Erro: "Invalid API key"**
✅ Verifique se copiou a chave completa do Google AI Studio.

---

## 🎉 Resumo

**SIM! A aplicação aceita Gemini com:**
- ✅ Suporte nativo via `LLMManager`
- ✅ Fallback automático
- ✅ Configuração simples via `.env`
- ✅ Biblioteca já no `requirements.txt`
- ✅ Usado em toda a aplicação (CSV, Chat, RAG, Fraud Detection)

**Próximo passo**: 
1. Pegue sua API key em https://makersuite.google.com/app/apikey
2. Adicione no `.env`
3. Reinicie a aplicação
4. Aproveite o Gemini! 🚀

---

**🔗 Links Úteis**:
- Google AI Studio: https://makersuite.google.com/app/apikey
- Documentação Gemini: https://ai.google.dev/docs
- Pricing: https://ai.google.dev/pricing
- Modelos disponíveis: https://ai.google.dev/models/gemini