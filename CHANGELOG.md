# 📋 Changelog - EDA AI Minds Backend

Histórico completo de alterações, melhorias e correções no sistema multiagente.

> **Convenção:** Mantemos formato [Keep a Changelog](https://keepachangelog.com/)  
> **Versionamento:** [Semantic Versioning](https://semver.org/)

---

## 📑 Índice Rápido

- [Última Versão (2.1.0)](#version-210---2025-10-22)
- [Versão 2.0.1](#version-201---2025-10-04)
- [Versão 2.0.0](#version-200---2025-10-03)
- [Como Usar Este Changelog](#como-usar-este-changelog)

---

## [Version 2.1.0] - 2025-10-22

### 🔥 Limpeza Profunda de Arquivos/Módulos Obsoletos
**Data:** 2025-10-22  
**Documentação:** [`docs/2025-10-22_limpeza_obsoletos.md`](docs/2025-10-22_limpeza_obsoletos.md)  
**Resumo:** [`docs/documentacao_atual/chat_perplexity/2025-10-22-relatorio-limpeza-obsoletos.md`](docs/documentacao_atual/chat_perplexity/2025-10-22-relatorio-limpeza-obsoletos.md)

**Arquivos Removidos:**
- src/agent/rag_data_agent_v1_backup.py (backup obsoleto)
- src/agent/rag_data_agent_v2.py (versão intermediária obsoleta)
- src/agent/rag_data_agent_backup_20251018.py (backup obsoleto)
- src/agent/rag_agent.py.backup_dual_chunking (backup obsoleto)
- src/agent/grok_llm_agent.py (anterior à camada de abstração LangChain)
- src/agent/google_llm_agent.py (anterior à camada de abstração LangChain)
- src/agent/groq_llm_agent.py (anterior à camada de abstração LangChain)
- src/agent/hybrid_query_processor.py (substituído por hybrid_query_processor_v2.py)
- scripts/setup_and_run_interface_interativa.py (substituído por _v3.py)
- scripts/setup_and_run_fastapi.py (substituído por _v3.py)

**Arquivos Mantidos (Essenciais):**
- src/agent/rag_data_agent.py (classe base para RAGDataAgentV4)
- src/agent/rag_data_agent_v4.py (extensão V4 com melhorias)
- src/agent/rag_agent.py (agente de ingestão RAG)
- src/agent/hybrid_query_processor_v2.py (processador híbrido atual)

**Justificativa:**
- Não utilizados no pipeline principal
- Risco de uso de código legado
- Padronização da integração de LLMs via LangChain
- Melhoria na segurança e manutenção
- rag_data_agent.py mantido por ser classe base do V4

---

## [Version 2.0.1] - 2025-10-04

### ✨ Novidades

#### 🧠 Sistema de Roteamento Inteligente de LLM
**Data:** 2025-10-04 03:20  
**Documentação:** [`docs/changelog/2025-10-04_0320_llm-router-sistema-inteligente.md`](docs/changelog/2025-10-04_0320_llm-router-sistema-inteligente.md)

Sistema de seleção automática de modelos LLM baseado na complexidade da query:

**Arquivos:**


### 🔧 Correções
**Data:** 2025-10-04 03:30  
**Documentação:** 
- Completa: [`docs/troubleshooting/2025-10-04_0330_correcao-timeout-30s.md`](docs/troubleshooting/2025-10-04_0330_correcao-timeout-30s.md)
- Resumo: [`docs/changelog/2025-10-04_0335_resumo-solucao-timeout.md`](docs/changelog/2025-10-04_0335_resumo-solucao-timeout.md)
- Frontend: [`docs/guides/FRONTEND_TIMEOUT_CONFIG.md`](docs/guides/FRONTEND_TIMEOUT_CONFIG.md)

**Problema:** Frontend apresentava timeout de 30s na primeira requisição  
**Causa:** Lazy loading de agentes demora 60-90s  
**Solução:**
- Timeout aumentado para 120s no backend
- Endpoint `/health/detailed` para verificar status sem carregar agentes
- Cache global do orquestrador
- Documentação para configurar frontend

**Performance:**
| Requisição | Antes | Depois |
|------------|-------|--------|
| Primeira | ❌ Timeout 30s | ✅ 51-90s |
| Subsequentes | ❌ Timeout 30s | ✅ 2-10s |

**Arquivos Modificados:**
- `api_completa.py` - API_TIMEOUT = 120, endpoint /health/detailed

---

#### 🐛 Variável fraud_col Não Inicializada
**Data:** 2025-10-04 03:45  
**Documentação:** [`docs/troubleshooting/2025-10-04_0345_fix-fraud-col-error.md`](docs/troubleshooting/2025-10-04_0345_fix-fraud-col-error.md)

**Erro:** `cannot access local variable 'fraud_col' where it is not associated with a value`  
**Causa:** Variável definida apenas dentro de bloco condicional  
**Solução:** Inicializar `fraud_col`, `fraud_count`, `fraud_rate` antes do bloco

**Cenário que causava erro:**
- Dataset sem palavras-chave de fraude (ex: CardPhrase.csv)
- Query sobre fraude → UnboundLocalError

**Arquivos Modificados:**
- `api_completa.py` - Função `analyze_csv_data()`

---

### 🚀 Melhorias

#### 📂 Sistema de file_id para Análise Contextual
**Data:** 2025-10-04 03:00-03:15  
**Documentação:**
- API Completa: [`docs/changelog/2025-10-04_0300_implementacao-file-id-api-completa.md`](docs/changelog/2025-10-04_0300_implementacao-file-id-api-completa.md)
- API Simple: [`docs/changelog/2025-10-04_0305_file-id-completo-api-simple.md`](docs/changelog/2025-10-04_0305_file-id-completo-api-simple.md)

Sistema para referenciar arquivos CSV carregados em conversas subsequentes:

**Funcionalidades:**
- Upload retorna `file_id` único
- Endpoint `/chat` aceita `file_id` para análise contextual
- Endpoint `/csv/files` lista todos os arquivos carregados
- Cache em memória para acesso rápido

**Exemplo de Uso:**
```json
// 1. Upload
POST /csv/upload → { "file_id": "csv_123456_creditcard" }

// 2. Análise
POST /chat {
  "message": "Quantas fraudes?",
  "file_id": "csv_123456_creditcard"
}
```

**Arquivos Modificados:**
- `api_completa.py` - Sistema completo de file_id
- `api_simple.py` - Sistema básico de file_id

---

#### 📊 Limite de Upload Aumentado para 999MB
**Data:** 2025-10-04 03:07  
**Documentação:** [`docs/changelog/2025-10-04_0307_aumento-limite-999mb.md`](docs/changelog/2025-10-04_0307_aumento-limite-999mb.md)

Limite de upload CSV aumentado de 100MB para **999MB** em ambas as APIs.

**Arquivos Modificados:**
- `api_completa.py` - MAX_FILE_SIZE = 999MB
- `api_simple.py` - MAX_FILE_SIZE = 999MB

---

#### 🤖 Sistema Multiagente Totalmente Operacional
**Data:** 2025-10-04 03:12-03:15  
**Documentação:**
- [`docs/changelog/2025-10-04_0312_api-completa-operacional.md`](docs/changelog/2025-10-04_0312_api-completa-operacional.md)
- [`docs/changelog/2025-10-04_0315_sistema-multiagente-ativado.md`](docs/changelog/2025-10-04_0315_sistema-multiagente-ativado.md)

Sistema multiagente com lazy loading para evitar erros de importação circular:

**Componentes:**
- ✅ Orchestrator Agent (coordenador central)
- ✅ CSV Analysis Agent
- ✅ Embeddings Agent
- ✅ RAG Agent
- ✅ LLM Manager (Google Gemini)
- ✅ Memory System (Supabase + LangChain)

**Carregamento:**
- Lazy loading na primeira requisição (60-90s)
- Cache em memória para requisições subsequentes (2-10s)

**Arquivos:**
- `api_completa.py` - Integração com lazy loading
- `src/agent/orchestrator_agent.py` - Coordenador
- `src/llm/manager.py` - Gerenciador de LLMs

---

## [Version 2.0.0] - 2025-10-03

### ✨ Novidades Principais

#### 🔄 Migração para API Completa como Padrão
**Data:** 2025-10-03  
**Documentação:** [`docs/changelog/2025-10-03_migracao-api-completa.md`](docs/changelog/2025-10-03_migracao-api-completa.md)

Estabelecida `api_completa.py` como API principal do projeto:
- **Porta:** 8001 (api_simple.py permanece na 8000 para testes)
- **Funcionalidades:** Sistema multiagente completo
- **Endpoints:** /csv/upload, /chat, /health, /dashboard/metrics

---

- [`docs/changelog/2025-10-03_correcao-hard-coding-csv-generico.md`](docs/changelog/2025-10-03_correcao-hard-coding-csv-generico.md)
- [`docs/changelog/2025-10-03_correcoes-sistema-generico-csv.md`](docs/changelog/2025-10-03_correcoes-sistema-generico-csv.md)

Sistema agora suporta **qualquer tipo de CSV**, não apenas dados de fraude:

**Depois:**
- Genérico para qualquer dataset
- Análise adaptativa baseada nas colunas disponíveis
- Detecção automática de tipos de dados

---

**Data:** 2025-10-03  

Relatório completo de compatibilidade entre api_simple.py e api_completa.py.
 Removidos arquivos de agentes obsoletos e backups não utilizados (rag_agent.py.backup_dual_chunking, rag_data_agent_backup_20251018.py, rag_data_agent_v1_backup.py)
 Atualizada documentação para refletir uso exclusivo do RAGAgent
 Motivo: Organização, redução de riscos e alinhamento ao pipeline principal

---

### 🧪 Testes

#### Relatório de Testes Completo
**Data:** 2025-10-03  
**Documentação:** [`docs/changelog/2025-10-03_relatorio-testes-completo.md`](docs/changelog/2025-10-03_relatorio-testes-completo.md)

Suite completa de testes implementada e executada:
- Upload de CSV genérico
- Análise multiagente
- Sistema de memória
- Detecção de fraude

---

## [Version 1.x] - Desenvolvimento Inicial

### Sessões de Desenvolvimento Anteriores

Documentação completa do desenvolvimento inicial disponível em:
- [`docs/archive/2025-10-02_1700_sessao-desenvolvimento.md`](docs/archive/2025-10-02_1700_sessao-desenvolvimento.md)
- Relatórios de auditoria em [`docs/auditoria/`](docs/auditoria/)
- Relatórios para professor em [`docs/relatorio-professor/`](docs/relatorio-professor/)

---

## 📚 Documentação Arquivada

Documentos importantes do histórico do projeto:

### Análises e Conformidade
- [`docs/architecture/ANALISE-CONFORMIDADE-REQUISITOS.md`](docs/architecture/ANALISE-CONFORMIDADE-REQUISITOS.md)
- [`docs/architecture/STATUS-COMPLETO-PROJETO.md`](docs/architecture/STATUS-COMPLETO-PROJETO.md)
- [`docs/architecture/RELATORIO-AGENTES-PROMPTS-GUARDRAILS.md`](docs/architecture/RELATORIO-AGENTES-PROMPTS-GUARDRAILS.md)

### Guias Técnicos
- [`docs/guides/GUIA-CORRECAO-SEGURANCA.md`](docs/guides/GUIA-CORRECAO-SEGURANCA.md)
- [`docs/guides/guia-recarga-completa.md`](docs/guides/guia-recarga-completa.md)
- [`docs/guides/FRONTEND_TIMEOUT_CONFIG.md`](docs/guides/FRONTEND_TIMEOUT_CONFIG.md)

### Diagnósticos
- [`docs/troubleshooting/analise-limitacao-carga.md`](docs/troubleshooting/analise-limitacao-carga.md)
- [`docs/archive/diagnostico/`](docs/archive/diagnostico/) - Diagnósticos antigos

---

## 🎯 Como Usar Este Changelog

### Por Data
Procure por `2025-10-04` para ver todas as mudanças de um dia específico.

### Por Funcionalidade
- **LLM Router:** Busque por "🧠 Sistema de Roteamento"
- **Timeout:** Busque por "⏰ Timeout"
- **file_id:** Busque por "📂 Sistema de file_id"
- **Bugs:** Busque por "🐛" ou seção "Correções"

### Links Diretos
Cada item tem link para documentação detalhada com:
- Problema/motivação
- Solução implementada
- Código modificado
- Testes realizados
- Exemplos de uso

---

## 🔄 Convenções Usadas

### Tipos de Mudança
- **✨ Novidades** - Novas funcionalidades
- **🔧 Correções** - Bug fixes
- **🚀 Melhorias** - Enhancements
- **🗑️ Removido** - Funcionalidades removidas
- **⚠️ Deprecated** - Em desuso
- **🔒 Segurança** - Correções de segurança

### Emoji Guide
- 🧠 Inteligência artificial / LLM
- ⏰ Performance / Timeout
- 📂 Arquivos / Storage
- 🐛 Bug fix
- 🤖 Multiagente
- 📊 Dashboard / Métricas
- 🧪 Testes
- 📝 Documentação

---

## 📞 Suporte

- **Documentação Técnica:** [`docs/guides/`](docs/guides/)
- **Troubleshooting:** [`docs/troubleshooting/`](docs/troubleshooting/)
- **Arquitetura:** [`docs/architecture/`](docs/architecture/)
- **Issues:** [GitHub Issues](https://github.com/ai-mindsgroup/eda-aiminds-back/issues)

---

**Última Atualização:** 2025-10-04  
**Versão Atual:** 2.0.1  
**Mantido por:** Sistema Multiagente EDA AI Minds
