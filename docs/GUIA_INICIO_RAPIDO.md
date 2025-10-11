# 🚀 Guia de Início Rápido - Para Equipe Paralela
**Entenda as mudanças da API em 15 minutos**

---

## ⏱️ TL;DR - 2 Minutos

### **O que mudou?**
✅ Criadas 2 APIs REST completas:
- `api_simple.py` (porta 8000) - Básica para testes
- `api_completa.py` (porta 8001) ⭐ - Produção com IA

### **Qual usar?**
✨ **api_completa.py (porta 8001)** - Sistema multiagente completo

### **Como iniciar?**
```bash
# Configure .env
GOOGLE_API_KEY=sua_chave
SUPABASE_URL=sua_url
SUPABASE_KEY=sua_chave

# Instale dependências
pip install -r requirements.txt

# Execute
python api_completa.py

# Acesse
http://localhost:8001/docs
```

---

## 📋 Checklist de 5 Minutos

### **Passo 1: Verificar Arquivos** (1 min)
```bash
# Verifique se os arquivos existem
ls api_simple.py      # 720 linhas
ls api_completa.py    # 997 linhas
```

### **Passo 2: Configurar Ambiente** (2 min)
```bash
# Copie .env.example para .env
cp configs/.env.example configs/.env

# Edite com suas credenciais
# GOOGLE_API_KEY=...
# SUPABASE_URL=...
# SUPABASE_KEY=...
```

### **Passo 3: Instalar Dependências** (1 min)
```bash
pip install -r requirements.txt
```

### **Passo 4: Testar** (1 min)
```bash
# Teste API simples
python api_simple.py
# Ctrl+C para parar

# Teste API completa (recomendado)
python api_completa.py
# Acesse: http://localhost:8001/docs
```

✅ **Pronto!** API rodando em 5 minutos.

---

## 🎯 Guia de 15 Minutos

### **Parte 1: Entender o Contexto** (5 min)

#### **Situação Anterior:**
- Sem APIs REST
- Apenas scripts Python
- Sem endpoints HTTP

#### **Situação Atual:**
- 2 APIs REST completas
- 12 endpoints disponíveis
- Sistema multiagente operacional
- Upload de CSV até 999MB
- Detecção de fraude com IA

#### **Quando foi criado?**
- **03/10/2025**: Criação das APIs
- **04/10/2025**: Melhorias e LLM Router

---

### **Parte 2: Principais Diferenças** (5 min)

#### **api_simple.py vs api_completa.py:**

| Característica | Simple | Completa |
|----------------|--------|----------|
| **Propósito** | Testes | Produção |
| **Porta** | 8000 | 8001 |
| **Linhas** | 720 | 997 |
| **Multiagente** | ❌ | ✅ |
| **LLM Router** | ❌ | ✅ |
| **Fraude IA** | ❌ | ✅ |

#### **Endpoints Principais:**

**Ambas APIs:**
```
GET  /health          → Status
POST /chat            → Chat
POST /csv/upload      → Upload CSV
GET  /csv/files       → Lista arquivos
GET  /dashboard/metrics → Métricas
```

**Apenas api_completa.py:**
```
POST /fraud/detect    → Detecção fraude IA
GET  /agents/status   → Status agentes
POST /agents/reload   → Recarregar agentes
```

---

### **Parte 3: Como Usar** (5 min)

#### **Exemplo 1: Upload CSV**
```bash
curl -X POST "http://localhost:8001/csv/upload" \
  -F "file=@dados.csv"

# Resposta:
{
  "file_id": "file_abc123",
  "filename": "dados.csv",
  "rows": 10000,
  "columns": 15,
  "message": "Arquivo processado com sucesso"
}
```

#### **Exemplo 2: Chat Contextual**
```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analise os dados",
    "file_id": "file_abc123"
  }'

# Resposta:
{
  "response": "Análise detalhada dos dados...",
  "agent_used": "OrchestratorAgent",
  "llm_model": "gemini-1.5-pro",
  "complexity_level": "COMPLEX"
}
```

#### **Exemplo 3: Detecção de Fraude**
```bash
curl -X POST "http://localhost:8001/fraud/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "file_abc123",
    "analysis_depth": "comprehensive"
  }'

# Resposta:
{
  "fraud_score": 0.87,
  "risk_level": "high",
  "patterns_detected": [
    "Multiple transactions same merchant",
    "Unusual amounts"
  ],
  "recommendations": [...]
}
```

---

## 📊 Decisão Rápida: Qual API Usar?

### **Use api_simple.py quando:**
```
✅ Você precisa testar rapidamente
✅ Não tem credenciais de LLM configuradas
✅ Quer análise básica de CSV
✅ Velocidade é mais importante que funcionalidades
```

### **Use api_completa.py quando:** ⭐
```
✅ Está em produção
✅ Precisa de detecção de fraude
✅ Quer análises complexas com IA
✅ Tem credenciais de LLM (Google Gemini)
✅ Qualidade > Velocidade
```

**Recomendação:** 🎯 **api_completa.py**

---

## 🔧 Troubleshooting Rápido

### **Problema 1: API não inicia**
```bash
# Verifique Python
python --version  # Deve ser 3.10+

# Verifique dependências
pip install -r requirements.txt

# Verifique .env
cat configs/.env  # Ou: type configs\.env (Windows)
```

### **Problema 2: "GOOGLE_API_KEY não configurado"**
```bash
# Edite o arquivo .env
# Adicione: GOOGLE_API_KEY=sua_chave_aqui
```

### **Problema 3: Porta já em uso**
```bash
# api_simple.py usa porta 8000
# api_completa.py usa porta 8001
# Verifique se já tem algo rodando nessas portas
```

### **Problema 4: Timeout em uploads**
```bash
# api_completa.py tem timeout de 120 segundos
# Para arquivos muito grandes, considere aumentar:
# API_TIMEOUT = 180  # 3 minutos
```

### **Problema 5: "Agentes não disponíveis"**
```bash
# Normal! API usa lazy loading
# Agentes são carregados quando necessário
# Verifique logs para detalhes
```

---

## 📚 Documentação Completa

### **3 Documentos Principais:**

1. **[RESUMO_ALTERACOES_API.md](RESUMO_ALTERACOES_API.md)** 📄
   - Resumo executivo
   - Timeline das alterações
   - Checklist de integração
   - **Tempo de leitura: 10 min**

2. **[COMPARATIVO_VISUAL_API.md](COMPARATIVO_VISUAL_API.md)** 📊
   - Diagramas de arquitetura
   - Fluxos de requisições
   - Casos de uso práticos
   - **Tempo de leitura: 15 min**

3. **[RELATORIO_ALTERACOES_API.md](RELATORIO_ALTERACOES_API.md)** 📋
   - Documento completo e detalhado
   - Todas as alterações commit-by-commit
   - Funcionalidades implementadas
   - **Tempo de leitura: 45 min**

### **Ordem de Leitura Recomendada:**
```
1. Este arquivo (15 min)       ← Você está aqui
2. RESUMO_ALTERACOES_API.md (10 min)
3. COMPARATIVO_VISUAL_API.md (15 min)
4. RELATORIO_ALTERACOES_API.md (45 min) - Opcional
```

**Total:** ~1h30min para entender tudo completamente.

---

## 🎯 Próximos Passos

### **Agora (15 min):**
- [x] Ler este guia
- [ ] Configurar ambiente
- [ ] Testar api_completa.py
- [ ] Fazer upload de um CSV
- [ ] Testar endpoint /chat

### **Hoje (1 hora):**
- [ ] Ler RESUMO_ALTERACOES_API.md
- [ ] Ler COMPARATIVO_VISUAL_API.md
- [ ] Testar todos os endpoints
- [ ] Validar com seus dados

### **Esta Semana:**
- [ ] Ler RELATORIO_ALTERACOES_API.md (completo)
- [ ] Integrar com seu frontend
- [ ] Testes de carga
- [ ] Deploy em staging

---

## 💡 Dicas Importantes

### **1. Use sempre o Swagger UI:**
```
http://localhost:8000/docs  # api_simple.py
http://localhost:8001/docs  # api_completa.py
```
**Por quê?** Documentação interativa, testa endpoints sem curl.

### **2. Ative logs detalhados:**
```bash
# No arquivo da API, procure por:
logging.basicConfig(level=logging.INFO)

# Para debug mais detalhado:
logging.basicConfig(level=logging.DEBUG)
```

### **3. Use file_id sempre:**
```python
# Ao fazer upload, guarde o file_id
{
  "file_id": "file_abc123",  # ← Guarde isso!
  "filename": "dados.csv"
}

# Use no chat para análise contextual
{
  "message": "Analise os dados",
  "file_id": "file_abc123"  # ← Use aqui
}
```

### **4. LLM Router automático:**
```
# api_completa.py detecta automaticamente:
"Olá" → SIMPLE → gemini-1.5-flash
"Estatísticas" → MEDIUM → gemini-1.5-flash
"Detecte fraudes" → COMPLEX → gemini-1.5-pro
"Análise massiva" → ADVANCED → gemini-2.0-flash-exp
```

### **5. Timeout configurável:**
```python
# api_completa.py tem timeout de 120 segundos
# Se precisar de mais tempo:
API_TIMEOUT = 180  # 3 minutos
```

---

## 🆘 Precisa de Ajuda?

### **Documentação:**
- 📄 [`RESUMO_ALTERACOES_API.md`](RESUMO_ALTERACOES_API.md)
- 📊 [`COMPARATIVO_VISUAL_API.md`](COMPARATIVO_VISUAL_API.md)
- 📋 [`RELATORIO_ALTERACOES_API.md`](RELATORIO_ALTERACOES_API.md)

### **Changelogs:**
- `docs/changelog/` - Histórico de mudanças

### **Guias:**
- `docs/guides/` - Guias de uso

### **Troubleshooting:**
- `docs/troubleshooting/` - Soluções de problemas

### **Testes:**
- `debug/test_api_completo.py` - Testes completos
- `debug/test_api_unitario.py` - Testes unitários

---

## ✅ Resumo Final

### **O que você aprendeu:**
✅ Existem 2 APIs: simple (8000) e completa (8001)  
✅ api_completa.py é recomendada para produção  
✅ Sistema multiagente com LLM Router inteligente  
✅ Suporte a CSV até 999MB  
✅ Detecção de fraude com IA  
✅ file_id para análise contextual  

### **Próximas ações:**
1. ✅ Configure .env
2. ✅ Instale dependências
3. ✅ Execute api_completa.py
4. ✅ Teste no Swagger UI
5. ✅ Leia documentação completa

### **Arquivos importantes:**
```
api_completa.py              ← API principal (use esta)
requirements.txt             ← Dependências
configs/.env                 ← Configurações
docs/RESUMO_ALTERACOES_API.md ← Próxima leitura
```

---

## 🎉 Conclusão

**Em 15 minutos você aprendeu:**
- ✅ O que mudou nas APIs
- ✅ Qual API usar e quando
- ✅ Como configurar e executar
- ✅ Como fazer upload e chat
- ✅ Onde encontrar mais informações

**Próximo passo:** 🚀 Execute a API e teste!

```bash
python api_completa.py
# Acesse: http://localhost:8001/docs
```

---

**Criado em:** 08/10/2025  
**Tempo estimado:** 15 minutos  
**Status:** ✅ Pronto para uso

**Boa sorte! 🚀**
