# 🔄 Comparativo Visual: api_simple.py vs api_completa.py

## 📊 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        APLICAÇÃO FRONTEND                         │
│                    (React, Angular, etc.)                        │
└────────────────────┬────────────────┬───────────────────────────┘
                     │                │
                     │                │
        ┌────────────▼─────┐    ┌────▼──────────────┐
        │  api_simple.py   │    │ api_completa.py   │
        │   Porta 8000     │    │   Porta 8001      │
        │   720 linhas     │    │   997 linhas      │
        └────────┬─────────┘    └─────┬─────────────┘
                 │                    │
                 │                    │
     ┌───────────▼──────────┐    ┌────▼──────────────────────┐
     │   Análise Básica     │    │  Sistema Multiagente      │
     │   • Pandas           │    │  • OrchestratorAgent      │
     │   • Estatísticas     │    │  • EmbeddingsAgent        │
     │   • Regras fixas     │    │  • GoogleLLMAgent         │
     └──────────────────────┘    │  • FraudDetectionAgent    │
                                 └───┬───────────────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │   LLM Router            │
                        │   • gemini-1.5-flash    │
                        │   • gemini-1.5-pro      │
                        │   • gemini-2.0-flash    │
                        └────────┬────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Supabase + PostgreSQL │
                    │   • Embeddings          │
                    │   • RAG                 │
                    │   • Vector Store        │
                    └─────────────────────────┘
```

---

## 🎯 Fluxo de Requisições

### **api_simple.py** - Fluxo Direto

```
Cliente → FastAPI → Pandas → Resposta
   ↓         ↓         ↓         ↓
Upload → Validação → Análise → JSON
   1s      0.5s        2s      Total: 3.5s
```

### **api_completa.py** - Fluxo Inteligente

```
Cliente → FastAPI → LLM Router → Complexidade → Agente → LLM → RAG → Resposta
   ↓         ↓          ↓            ↓            ↓       ↓     ↓       ↓
Upload → Validação → Análise → SIMPLE/COMPLEX → Orq. → Gemini → DB → JSON
   1s      0.5s       0.5s          1s          2s     5s    2s   Total: 12s

* Tempo varia conforme complexidade
* Cache pode reduzir significativamente
```

---

## 📋 Matriz de Funcionalidades

```
┌──────────────────────────┬─────────────┬──────────────┐
│      Funcionalidade      │   Simple    │   Completa   │
├──────────────────────────┼─────────────┼──────────────┤
│ Upload CSV               │     ✅      │      ✅      │
│ Análise Pandas           │     ✅      │      ✅      │
│ Chat Básico              │     ✅      │      ✅      │
│ file_id System           │     ✅      │      ✅      │
│ Limite 999MB             │     ✅      │      ✅      │
├──────────────────────────┼─────────────┼──────────────┤
│ Orquestrador IA          │     ❌      │      ✅      │
│ LLM Router               │     ❌      │      ✅      │
│ Sistema Multiagente      │     ❌      │      ✅      │
│ Detecção Fraude IA       │     ❌      │      ✅      │
│ Embeddings + RAG         │     ❌      │      ✅      │
│ Memória Persistente      │     ❌      │      ✅      │
│ Lazy Loading             │     ❌      │      ✅      │
│ Análise Complexa         │     ❌      │      ✅      │
└──────────────────────────┴─────────────┴──────────────┘
```

---

## 🚦 Níveis de Complexidade (LLM Router)

```
┌─────────────────────────────────────────────────────────┐
│                    LLM ROUTER                           │
│            (Apenas api_completa.py)                     │
└───┬─────────────────────────────────────────────────────┘
    │
    ├─► SIMPLE ──────► gemini-1.5-flash
    │                  • Saudações, help
    │                  • Temp: 0.3 | Tokens: 500
    │                  • Custo: $
    │
    ├─► MEDIUM ──────► gemini-1.5-flash
    │                  • Estatísticas básicas
    │                  • Datasets < 10k linhas
    │                  • Temp: 0.5 | Tokens: 1500
    │                  • Custo: $$
    │
    ├─► COMPLEX ─────► gemini-1.5-pro
    │                  • Detecção fraude
    │                  • Datasets 10k-100k
    │                  • Temp: 0.7 | Tokens: 3000
    │                  • Custo: $$$
    │
    └─► ADVANCED ────► gemini-2.0-flash-exp
                       • Análise massiva > 100k
                       • ML complexo
                       • Temp: 0.8 | Tokens: 4000
                       • Custo: $$$$
```

---

## 🎭 Casos de Uso

### **Cenário 1: Upload CSV Simples**

**api_simple.py:**
```
1. POST /csv/upload
2. Pandas lê arquivo
3. Estatísticas básicas
4. Retorna file_id + preview
⏱️ Tempo: ~3s
```

**api_completa.py:**
```
1. POST /csv/upload
2. Pandas + validação
3. Agente CSVAgent processa
4. Embeddings gerados
5. Armazenamento em Supabase
6. Retorna file_id + análise IA
⏱️ Tempo: ~15s (com processamento IA)
```

---

### **Cenário 2: Chat Sobre Dados**

**api_simple.py:**
```
POST /chat
{
  "message": "Quantas linhas tem?",
  "file_id": "file_123"
}

→ Regras fixas no código
→ df.shape[0]
→ Resposta: "O arquivo tem 10,000 linhas"
⏱️ Tempo: ~1s
```

**api_completa.py:**
```
POST /chat
{
  "message": "Analise padrões de fraude",
  "file_id": "file_123"
}

→ LLM Router detecta: COMPLEX
→ Orquestrador aciona FraudDetectionAgent
→ RAG busca contexto em embeddings
→ gemini-1.5-pro analisa
→ Resposta detalhada com insights IA
⏱️ Tempo: ~12s
```

---

### **Cenário 3: Detecção de Fraude**

**api_simple.py:**
```
❌ Não disponível
```

**api_completa.py:**
```
POST /fraud/detect
{
  "file_id": "file_123",
  "analysis_depth": "comprehensive"
}

→ FraudDetectionAgent ativado
→ Análise com gemini-2.0-flash-exp
→ Padrões detectados
→ Score de fraude calculado
→ Recomendações geradas

Response:
{
  "fraud_score": 0.87,
  "risk_level": "high",
  "patterns_detected": [
    "Multiple transactions same merchant",
    "Unusual transaction amounts",
    "Geographic inconsistencies"
  ],
  "recommendations": [...]
}
⏱️ Tempo: ~20s
```

---

## 📊 Performance Comparativa

```
┌────────────────────┬──────────┬──────────┬──────────┐
│    Operação        │  Simple  │ Completa │ Diferença│
├────────────────────┼──────────┼──────────┼──────────┤
│ Startup            │   2s     │   5s     │  +3s     │
│ Upload CSV (1MB)   │   3s     │   15s    │  +12s    │
│ Upload CSV (50MB)  │   10s    │   45s    │  +35s    │
│ Chat Simples       │   1s     │   3s     │  +2s     │
│ Chat Complexo      │   N/A    │   12s    │  N/A     │
│ Detecção Fraude    │   N/A    │   20s    │  N/A     │
└────────────────────┴──────────┴──────────┴──────────┘

* Simple: Mais rápida, menos funcionalidades
* Completa: Mais lenta, muito mais poderosa
```

---

## 💰 Custo de Processamento (Estimado)

### **api_simple.py:**
```
┌──────────────────┬─────────┐
│ Operação         │ Custo   │
├──────────────────┼─────────┤
│ Upload CSV       │ $0.00   │
│ Chat             │ $0.00   │
│ Total/1000 req   │ $0.00   │
└──────────────────┴─────────┘
Sem uso de LLMs externos
```

### **api_completa.py:**
```
┌──────────────────────┬─────────────┐
│ Operação             │ Custo/req   │
├──────────────────────┼─────────────┤
│ Upload + Embeddings  │ $0.02       │
│ Chat SIMPLE          │ $0.001      │
│ Chat MEDIUM          │ $0.005      │
│ Chat COMPLEX         │ $0.02       │
│ Chat ADVANCED        │ $0.05       │
│ Detecção Fraude      │ $0.03       │
├──────────────────────┼─────────────┤
│ Total/1000 req mix   │ ~$15-30     │
└──────────────────────┴─────────────┘
* Valores aproximados baseados em Google Gemini
```

---

## 🎯 Decisão: Qual API Usar?

### **Use api_simple.py SE:**
```
✅ Prototipagem rápida
✅ Ambiente de desenvolvimento
✅ Análise básica de CSV
✅ Orçamento zero para LLMs
✅ Velocidade é crítica
✅ Sem necessidade de IA avançada
```

### **Use api_completa.py SE:** ⭐
```
✅ Produção
✅ Detecção de fraude necessária
✅ Análises complexas e insights
✅ Sistema multiagente necessário
✅ Orçamento para LLMs disponível
✅ Qualidade > Velocidade
✅ RAG e embeddings necessários
```

---

## 🔀 Migração Entre APIs

### **De Simple → Completa:**

**Mudanças necessárias:**
```javascript
// Frontend: Apenas trocar a porta
// Antes:
const API_URL = "http://localhost:8000";

// Depois:
const API_URL = "http://localhost:8001";
```

**Compatibilidade:**
- ✅ Todos os endpoints da Simple existem na Completa
- ✅ Mesmos modelos de request/response
- ✅ file_id funciona igual
- ✅ Adiciona novos campos nos responses (llm_model, complexity_level)

**Ganhos:**
- ✅ Sistema multiagente
- ✅ Respostas mais inteligentes
- ✅ Detecção de fraude
- ✅ Análises complexas

**Trade-offs:**
- ⚠️ Respostas mais lentas
- ⚠️ Custo de LLMs
- ⚠️ Mais complexidade

---

## 📈 Evolução da API (Timeline)

```
Outubro 2025
─────────────────────────────────────────────────────────────►

03/10 08:00
│ api_simple.py criada
│ • 507 linhas
│ • 7 endpoints
│ • Análise básica
│
03/10 14:00
│ Atualização LLM
│ • Gemini 2.0
│ • LangChain fixes
│
03/10 19:45
│ api_completa.py criada
│ • 997 linhas
│ • 12 endpoints
│ • Sistema multiagente
│
04/10 03:00
│ Limite 999MB
│ • Upload grande
│
04/10 03:15
│ Multiagente ativado
│ • Lazy loading
│ • Imports seguros
│
04/10 03:20
│ LLM Router
│ • 4 níveis complexidade
│ • Roteamento inteligente
│
04/10 03:30
│ Correções finais
│ • Timeout 120s
│ • Fixes críticos
│
│ ✅ ESTADO ATUAL
▼ Ambas operacionais e prontas
```

---

## 🧪 Como Testar

### **Teste Rápido - api_simple.py:**
```bash
# Terminal 1: Iniciar API
python api_simple.py

# Terminal 2: Testes
curl http://localhost:8000/health
curl -X POST http://localhost:8000/csv/upload -F "file=@test.csv"
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá"}'
```

### **Teste Completo - api_completa.py:**
```bash
# Terminal 1: Iniciar API
python api_completa.py

# Terminal 2: Testes
curl http://localhost:8001/health
curl http://localhost:8001/agents/status
curl -X POST http://localhost:8001/csv/upload -F "file=@fraud_data.csv"
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Detecte fraudes", "file_id": "file_123"}'
curl -X POST http://localhost:8001/fraud/detect \
  -H "Content-Type: application/json" \
  -d '{"file_id": "file_123"}'
```

---

## 📚 Documentação Relacionada

```
docs/
├── RELATORIO_ALTERACOES_API.md    ← Documento completo detalhado
├── RESUMO_ALTERACOES_API.md       ← Resumo executivo
├── COMPARATIVO_VISUAL_API.md      ← Este arquivo
│
├── changelog/
│   ├── 2025-10-04_0312_api-completa-operacional.md
│   ├── 2025-10-04_0320_llm-router-sistema-inteligente.md
│   └── 2025-10-04_0307_aumento-limite-999mb.md
│
├── guides/
│   ├── GUIA_USO_API_COMPLETA.md
│   └── FRONTEND_TIMEOUT_CONFIG.md
│
└── archive/
    ├── 2025-10-03_migracao-api-completa.md
    └── 2025-10-03_relatorio-compatibilidade-api.md
```

---

## ✅ Checklist Final

### **Para Equipe de Integração:**

**Preparação:**
- [ ] Ler `RELATORIO_ALTERACOES_API.md` (completo)
- [ ] Ler `RESUMO_ALTERACOES_API.md` (resumo)
- [ ] Ler este arquivo (visual)

**Ambiente:**
- [ ] Configurar `.env` com credenciais
- [ ] Instalar `requirements.txt`
- [ ] Validar Python 3.10+

**Testes:**
- [ ] Testar api_simple.py (porta 8000)
- [ ] Testar api_completa.py (porta 8001)
- [ ] Upload CSV de teste
- [ ] Chat sem file_id
- [ ] Chat com file_id
- [ ] Endpoint /health em ambas

**Decisão:**
- [ ] Escolher qual API usar (recomendado: completa)
- [ ] Atualizar frontend (porta + endpoints)
- [ ] Configurar timeout adequado
- [ ] Validar em staging

**Produção:**
- [ ] Deploy com variáveis corretas
- [ ] Monitoramento configurado
- [ ] Logs sendo coletados
- [ ] Testes de carga realizados

---

**Última atualização:** 08/10/2025  
**Versão:** 2.0.0  
**Status:** ✅ Documentação completa

---

**📖 Leitura Recomendada:**
1. Este arquivo (comparativo visual)
2. `RESUMO_ALTERACOES_API.md` (resumo executivo)
3. `RELATORIO_ALTERACOES_API.md` (detalhes completos)
