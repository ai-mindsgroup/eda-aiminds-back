# 🚀 Solução: Sair do Modo Demonstração

## 📊 Situação Atual

Você está rodando: `api_simple.py` (modo demonstração)  
**Mensagem do frontend**: "Modo Demonstração Detectado"

## ✅ Solução: Rodar API Completa

Você já tem **Supabase configurado**! Vamos usar a API completa.

---

## 🔑 Configurar API Keys

### **1. Obter Google API Key** (para LLM Gemini)

1. Acesse: https://makersuite.google.com/app/apikey
2. Clique em "Create API Key"
3. Copie a chave

### **2. Atualizar `.env`**

Edite `configs/.env` e adicione:

```env
# Já configurado ✅
SUPABASE_URL=https://ncefmfiulpwssaajybtl.supabase.co
SUPABASE_KEY=eyJhbGc...
DB_HOST=aws-1-sa-east-1.pooler.supabase.com
DB_PASSWORD=Alder1310

# ADICIONAR ESTAS ⬇️
GOOGLE_API_KEY=sua_chave_aqui
GROQ_API_KEY=opcional_mas_recomendado

# Opcional (Perplexity Sonar)
SONAR_API_KEY=opcional
```

---

## 🚀 Iniciar API Completa

### **Opção 1: Com Script** (RECOMENDADO)
```powershell
python start_api.py
```

### **Opção 2: Direto com uvicorn**
```powershell
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ⚡ Quick Fix (Se não tiver API keys agora)

Posso modificar o `api_simple.py` para remover o aviso de "modo demonstração" e torná-lo mais funcional:

### **Opção A: Melhorar api_simple.py**
- ✅ Remove mensagem de "modo demonstração"
- ✅ Adiciona funcionalidades completas de CSV
- ✅ Mantém tudo em memória (sem Supabase)
- ⚠️ Sem LLM/IA avançada

### **Opção B: API Completa** (Recomendado)
- ✅ Sistema multiagente completo
- ✅ LLMs (Gemini, Groq)
- ✅ Supabase + RAG
- ✅ Todas as funcionalidades
- ⚠️ Requer API keys

---

## 🎯 Recomendação

**Para desenvolvimento rápido do frontend**: Use Opção A (melhorar api_simple)  
**Para sistema completo/produção**: Use Opção B (API completa)

Qual prefere? Posso implementar qualquer uma agora! 🚀