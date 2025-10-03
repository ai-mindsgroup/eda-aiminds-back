# 🤖 LLMs Suportados

## ✅ Sim! A aplicação aceita Gemini e outros LLMs

### **Provedores Integrados**:

| Provedor | Status | Modelo Padrão | Gratuito? |
|----------|--------|---------------|-----------|
| 🧠 **Google Gemini** | ✅ Integrado | `gemini-pro` | ✅ Sim |
| 🚀 **Groq** | ✅ Integrado | `llama-3.1-8b-instant` | ✅ Sim |
| 💬 **OpenAI** | ✅ Integrado | `gpt-3.5-turbo` | ❌ Pago |

---

## 🔧 Configuração Rápida

### **1. Obter API Keys**:

- **Gemini**: https://makersuite.google.com/app/apikey
- **Groq**: https://console.groq.com/keys
- **OpenAI**: https://platform.openai.com/api-keys

### **2. Adicionar no `.env`**:

Edite `configs/.env`:

```env
# Recomendado: Configure pelo menos um ✅
GOOGLE_API_KEY=sua_chave_google
GROQ_API_KEY=sua_chave_groq
OPENAI_API_KEY=sua_chave_openai  # Opcional
```

### **3. Testar**:

```powershell
# Teste rápido do Gemini
python test_gemini.py

# Iniciar API completa
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📊 Comparação

| Critério | Gemini | Groq | OpenAI |
|----------|--------|------|--------|
| **Qualidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Velocidade** | ⚡⚡ | ⚡⚡⚡ | ⚡⚡ |
| **Limite Gratuito** | 1.500/dia | 14.400/dia | Pago |
| **Melhor Para** | Análises complexas | Respostas rápidas | Produção |

---

## 🎯 Recomendação

### **Desenvolvimento**:
```env
GROQ_API_KEY=xxx  # Rápido para testes
```

### **Produção**:
```env
GOOGLE_API_KEY=xxx  # Melhor qualidade
GROQ_API_KEY=xxx    # Backup rápido
```

---

## 📚 Documentação Completa

- 📖 **Detalhes do Gemini**: `SUPORTE_GEMINI.md`
- 🧪 **Script de Teste**: `test_gemini.py`
- ⚙️ **Configurações**: `configs/.env`

---

**✅ Sistema pronto para usar qualquer LLM com fallback automático!**