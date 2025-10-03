# ⚡ GUIA RÁPIDO - Qual API Executar?

**Atualizado**: 01/10/2025

---

## 🎯 Resposta Rápida

### Você está desenvolvendo FRONTEND?
👉 **Use: `api_simple.py`**
```powershell
uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload
```

### Você precisa de ANÁLISE COM IA?
👉 **Use: `src/api/main.py`**
```powershell
.\start_api_completa.ps1
```

---

## 🔍 Entenda a Diferença em 30 Segundos

### `api_simple.py` = Backend Básico
- ✅ Upload CSV
- ✅ Preview dados
- ✅ Estatísticas básicas (Pandas)
- ❌ **SEM** Inteligência Artificial
- ❌ **SEM** Orquestrador
- ❌ **SEM** LLMs (Gemini/Groq)
- ❌ **SEM** Sistema RAG
- ⚡ **RÁPIDO** (~100ms)
- 🪶 **LEVE** (~150MB RAM)

**Perfeito para**: Testar interface do frontend

### `src/api/main.py` = Sistema Multiagente Completo
- ✅ Upload CSV
- ✅ Preview dados
- ✅ Estatísticas avançadas
- ✅ **COM** Inteligência Artificial
- ✅ **COM** Orquestrador Central
- ✅ **COM** LLMs (Gemini/Groq/OpenAI)
- ✅ **COM** Sistema RAG + Busca Semântica
- ✅ Detecção de Fraudes
- ✅ Insights Automáticos
- ✅ Chat Contextual Avançado
- 🐢 **MAIS LENTO** (~2000ms) - mas mais inteligente!
- 🐘 **PESADO** (~800MB RAM)

**Perfeito para**: Demo completa, produção, análises reais

---

## 📋 Checklist: Qual API Devo Usar?

Marque as afirmações verdadeiras:

- [ ] Preciso apenas testar upload de CSV no frontend
- [ ] Não tenho credenciais de Supabase/LLMs
- [ ] Quero respostas rápidas (sem IA)
- [ ] Estou apenas desenvolvendo a interface

**Se marcou ALGUMA** → Use `api_simple.py`

---

- [ ] Preciso detectar fraudes com IA
- [ ] Quero insights automáticos dos dados
- [ ] Preciso de chat inteligente que entende contexto
- [ ] Vou fazer uma demo completa do sistema
- [ ] Vou para produção

**Se marcou ALGUMA** → Use `src/api/main.py`

---

## 🚀 Como Executar (Copy & Paste)

### Opção 1: API Simples (Frontend Dev)

```powershell
# 1. Ativar ambiente
.\.venv\Scripts\Activate.ps1

# 2. Iniciar
uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload

# Pronto! ✅
# Acesse: http://localhost:8000/docs
```

**Requisitos**: Apenas Python + FastAPI + Pandas

---

### Opção 2: API Completa (Sistema IA)

```powershell
# 1. Ativar ambiente
.\.venv\Scripts\Activate.ps1

# 2. Verificar .env configurado
cat configs\.env

# 3. Iniciar (script automático)
.\start_api_completa.ps1

# OU manualmente:
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Pronto! ✅
# Acesse: http://localhost:8000/docs
```

**Requisitos**: Python + todas dependências + .env configurado

---

## 🆚 Comparação Visual Rápida

```
┌─────────────────────────────┬─────────────────────────────┐
│      api_simple.py          │      src/api/main.py        │
├─────────────────────────────┼─────────────────────────────┤
│ 🪶 Leve (150MB)             │ 🐘 Pesado (800MB)           │
│ ⚡ Rápido (100ms)           │ 🐢 Lento (2000ms)           │
│ 🎯 Foco: Frontend           │ 🧠 Foco: Análise IA         │
│ ❌ Sem IA                   │ ✅ Com IA Completa          │
│ 💰 Barato ($0/mês APIs)     │ 💰 Caro ($50-200/mês APIs)  │
│ 🛠️ Dev: Rápido             │ 🛠️ Dev: Complexo            │
│ ✅ Upload CSV               │ ✅ Upload CSV               │
│ ✅ Estatísticas             │ ✅ Estatísticas Avançadas   │
│ ⚠️ Chat Fixo               │ ✅ Chat IA Contextual       │
│ ❌ Sem Fraudes              │ ✅ Detecção Fraudes         │
│ ❌ Sem RAG                  │ ✅ Sistema RAG              │
│ ❌ Sem Embeddings           │ ✅ Embeddings + Vetores     │
│ ❌ Sem Orquestrador         │ ✅ Orquestrador Central     │
└─────────────────────────────┴─────────────────────────────┘
```

---

## 🎓 Exemplos de Uso Real

### Cenário 1: Dev Frontend Criando Tela Upload
**Problema**: "Preciso testar o formulário de upload"  
**Solução**: `api_simple.py`  
**Motivo**: Rápido, simples, não precisa configurar LLMs

### Cenário 2: Demo para Cliente
**Problema**: "Vou mostrar detecção de fraudes"  
**Solução**: `src/api/main.py`  
**Motivo**: Cliente quer ver IA em ação

### Cenário 3: Teste de Performance Frontend
**Problema**: "Testar se UI carrega CSV de 10MB"  
**Solução**: `api_simple.py`  
**Motivo**: Foco é performance de upload, não análise

### Cenário 4: Integração com Chatbot
**Problema**: "Chat precisa responder perguntas sobre dados"  
**Solução**: `src/api/main.py`  
**Motivo**: Precisa de LLM + contexto dos dados

---

## 📞 Ainda em Dúvida?

### Pergunte-se:

**"Estou APENAS testando a interface do frontend?"**  
→ Sim? Use `api_simple.py`  
→ Não? Use `src/api/main.py`

**"Preciso que o sistema PENSE e ANALISE?"**  
→ Sim? Use `src/api/main.py`  
→ Não? Use `api_simple.py`

**"Tenho credenciais Supabase + LLMs configuradas?"**  
→ Não? Use `api_simple.py`  
→ Sim? Pode usar qualquer uma (escolha pela funcionalidade)

---

## 🎯 Recomendação Final

```
DESENVOLVIMENTO FRONTEND
  ↓
api_simple.py (desenvolvimento rápido)
  ↓
src/api/main.py (quando precisar testar integração com IA)
  ↓
PRODUÇÃO (sempre src/api/main.py)
```

---

## 📚 Documentação Completa

- **Guia Completo**: `COMO_INICIAR_API_COMPLETA.md`
- **Comparação Detalhada**: `COMPARATIVO_APIS.md`
- **Frontend**: `INSTRUCOES_FRONTEND_CORRIGIR_DETECCAO.md`

---

## ✅ TL;DR (Ultra Rápido)

**Frontend dev** → `api_simple.py`  
**Sistema IA completo** → `src/api/main.py`  

**Comando rápido**:
```powershell
# Simples
uvicorn api_simple:app --reload

# Completa
.\start_api_completa.ps1
```

**FIM** ✅

---

**Criado**: 01/10/2025  
**Autor**: GitHub Copilot
