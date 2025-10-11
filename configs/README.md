# 🔧 Guia de Configuração - EDA AI Minds

Este guia te ajuda a configurar corretamente o ambiente para o sistema multiagente.

## 📋 Configuração Inicial (5 minutos)

### 1. **Copiar Template de Configuração**
```bash
# Na pasta do projeto
cp configs/.env.example configs/.env
```

### 2. **Configurar Supabase (Obrigatório)**
```bash
# Edite configs/.env e preencha:
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_anonima_aqui
```

### 3. **Configurar pelo menos 1 LLM**

#### **🥇 Opção 1: Google Gemini (Recomendado)**
- 🔗 **Link:** https://makersuite.google.com/app/apikey
- 💰 **Custo:** Gratuito até certo limite, depois pago
- ⚡ **Velocidade:** Rápido
- 🎯 **Qualidade:** Excelente

```bash
GOOGLE_API_KEY=sua_chave_google_aqui
```

#### **🥈 Opção 2: Groq (Ideal para Dev)**
- 🔗 **Link:** https://console.groq.com/keys
- 💰 **Custo:** Gratuito
- ⚡ **Velocidade:** Muito rápido
- 🎯 **Qualidade:** Boa

```bash
GROQ_API_KEY=sua_chave_groq_aqui
```

#### **🥉 Opção 3: OpenAI (Mais caro)**
- 🔗 **Link:** https://platform.openai.com/api-keys
- 💰 **Custo:** Pago
- ⚡ **Velocidade:** Médio
- 🎯 **Qualidade:** Excelente

```bash
OPENAI_API_KEY=sua_chave_openai_aqui
```

## ✅ Testar Configuração

### **Teste Básico:**
```bash
python -c "from src.settings import *; print('✅ Configuração OK!')"
```

### **Teste Banco de Dados:**
```bash
python tools/check_db.py
```

### **Teste API:**
```bash
python api_simple.py
# Acesse: http://localhost:8000/health
```

### **Teste Sistema Multiagente:**
```bash
python examples/exemplo_orchestrator.py
```

## 🎛️ Configurações Avançadas

### **Níveis de Log:**
```bash
LOG_LEVEL=DEBUG    # Desenvolvimento (muitos detalhes)
LOG_LEVEL=INFO     # Produção (informações importantes)
LOG_LEVEL=WARNING  # Apenas avisos e erros
LOG_LEVEL=ERROR    # Apenas erros críticos
```

### **Conexão PostgreSQL Direta (Opcional):**
```bash
# Para operações avançadas no banco
DB_HOST=sua-instancia.pooler.supabase.com
DB_PORT=6543  # Pooler: 6543, Direto: 5432
DB_NAME=postgres
DB_USER=postgres.sua_referencia
DB_PASSWORD=sua_senha_postgres
```

## 🚀 Configurações por Ambiente

### **👨‍💻 Desenvolvimento:**
```bash
# Configuração mínima para desenvolver
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_anonima
GROQ_API_KEY=sua_chave_groq  # Gratuito e rápido
LOG_LEVEL=DEBUG
```

### **🧪 Teste/QA:**
```bash
# Configuração para ambiente de testes
SUPABASE_URL=https://seu-projeto-qa.supabase.co
SUPABASE_KEY=chave_qa
GOOGLE_API_KEY=chave_google
GROQ_API_KEY=chave_groq_backup
LOG_LEVEL=INFO
```

### **🏭 Produção:**
```bash
# Configuração robusta para produção
SUPABASE_URL=https://seu-projeto-prod.supabase.co
SUPABASE_KEY=chave_producao_segura
GOOGLE_API_KEY=chave_google_prod
OPENAI_API_KEY=chave_openai_backup
GROQ_API_KEY=chave_groq_backup
LOG_LEVEL=WARNING
```

## 🔒 Segurança

### **✅ Boas Práticas:**
- ✅ Nunca comitar arquivos `.env` no Git
- ✅ Usar chaves diferentes para cada ambiente
- ✅ Rotacionar chaves periodicamente
- ✅ Limitar permissões das chaves de API
- ✅ Monitorar uso das APIs

### **❌ Não Faça:**
- ❌ Compartilhar chaves em mensagens/emails
- ❌ Usar chaves de produção em desenvolvimento
- ❌ Deixar chaves em código-fonte
- ❌ Usar senhas fracas no banco

## 🛠️ Resolução de Problemas

### **Erro: "SUPABASE_URL não configurado"**
```bash
# Verifique se o arquivo .env existe
ls configs/.env

# Verifique se a variável está definida
grep SUPABASE_URL configs/.env
```

### **Erro: "Nenhum provedor LLM disponível"**
```bash
# Configure pelo menos uma chave de LLM
grep -E "GOOGLE_API_KEY|GROQ_API_KEY|OPENAI_API_KEY" configs/.env
```

### **Erro: "Falha na conexão com Supabase"**
```bash
# Teste a conexão diretamente
python -c "from src.vectorstore.supabase_client import supabase; print(supabase.table('embeddings').select('id').limit(1).execute())"
```

### **Erro: "Modelo LLM não encontrado"**
```bash
# Atualize o modelo padrão no código
# src/llm/manager.py -> _get_default_model()
# Mude "gemini-pro" para "gemini-1.5-flash"
```

## 📚 Links Úteis

- 📖 **Documentação Supabase:** https://supabase.com/docs
- 🤖 **Google AI Studio:** https://makersuite.google.com/
- ⚡ **Groq Console:** https://console.groq.com/
- 🧠 **OpenAI Platform:** https://platform.openai.com/
- 🐍 **Python dotenv:** https://pypi.org/project/python-dotenv/

## 📞 Suporte

Se precisar de ajuda:
1. 📋 Verifique este guia primeiro
2. 🧪 Execute os testes básicos
3. 📝 Confira os logs em `LOG_LEVEL=DEBUG`
4. 🔍 Procure por erros similares na documentação

---

**Configuração atualizada:** 03/10/2025  
**Branch:** feature/refactore-langchain  
**Status:** ✅ Validado e testado