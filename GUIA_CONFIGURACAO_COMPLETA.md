# 🚀 Guia de Configuração Completa - Sistema RAG + LLM

## ✅ Status: Sistema Backend Operacional!

O sistema multiagente de IA para análise de dados CSV está **totalmente funcional** com:
- ✅ Banco de dados PostgreSQL + pgvector 
- ✅ Sistema de embeddings vetoriais
- ✅ Agentes especializados (CSV, RAG, orquestrador)
- ✅ Persistência de análises e documentos
- ✅ Interface interativa para usuários

## 📋 Configuração Final: Google API Key

Para habilitar análises LLM avançadas, configure sua chave da Google:

### 1. Obtenha a API Key do Google AI Studio
1. Acesse: https://aistudio.google.com/
2. Faça login com sua conta Google
3. Vá em "Get API Key" → "Create API Key"
4. Copie a chave gerada

### 2. Configure no arquivo .env
Edite o arquivo `configs/.env`:
```env
# Configurações obrigatórias (já configuradas)
SUPABASE_URL=https://dfwcihzctkbxtaarhcxf.supabase.co
SUPABASE_KEY=eyJhbGciOi... (sua chave atual)
SONAR_API_KEY=pplx-... (sua chave atual)
DB_HOST=db.dfwcihzctkbxtaarhcxf.supabase.co
DB_PASSWORD=(sua senha atual)
LOG_LEVEL=INFO

# ADICIONE ESTA LINHA:
GOOGLE_API_KEY=AIzaSy... (sua chave do Google AI Studio)
```

### 3. Teste a configuração
```powershell
# Ative o ambiente virtual
.venv\Scripts\Activate.ps1

# Teste o sistema completo
python examples/exemplo_database_rag.py

# Teste a interface interativa
python examples/exemplo_csv_interativo.py
```

## 🎯 Como usar o Sistema

### Interface Interativa (Recomendado)
```powershell
python examples/exemplo_csv_interativo.py
```
- Upload de qualquer arquivo CSV
- Análises automáticas de fraude, padrões, correlações
- Conversação natural com o sistema
- Geração de gráficos e insights

### Programaticamente
```python
from src.agent.orchestrator_agent import OrchestratorAgent

# Inicializar sistema
orchestrator = OrchestratorAgent()

# Analisar CSV
result = orchestrator.process(
    "analise este arquivo CSV",
    context={"file_path": "dados.csv"}
)

# Consulta RAG
result = orchestrator.process(
    "busque informações sobre detecção de fraudes"
)
```

## 🔧 Funcionalidades Disponíveis

### 1. Análise Automática de CSV
- ✅ Detecção de fraudes em cartões de crédito
- ✅ Análise estatística descritiva
- ✅ Identificação de padrões e anomalias
- ✅ Geração de visualizações
- ✅ Correlações entre variáveis

### 2. Sistema RAG (Retrieval Augmented Generation)
- ✅ Busca semântica em documentos
- ✅ Contextualização de respostas
- ✅ Embeddings vetoriais
- ✅ Persistência de conhecimento

### 3. Multiagente Inteligente
- ✅ Orquestrador central
- ✅ Agente especialista em CSV
- ✅ Agente RAG para contexto
- ✅ Classificação automática de consultas

## 🗄️ Banco de Dados

### Estrutura
- `embeddings`: Vetores semânticos (1536 dimensões)
- `chunks`: Fragmentos de documentos
- `metadata`: Análises e documentos persistidos

### Consultas úteis
```sql
-- Ver análises armazenadas
SELECT title, source, created_at 
FROM metadata 
ORDER BY created_at DESC;

-- Ver embeddings
SELECT id, source, created_at 
FROM embeddings 
LIMIT 10;
```

## 🚀 Próximos Passos Sugeridos

1. **Configurar GOOGLE_API_KEY** (principal)
2. **Testar com seus próprios CSVs**
3. **Explorar análises avançadas**
4. **Integrar com API REST** (FastAPI)
5. **Adicionar novos tipos de análise**

## 🏗️ Arquitetura Implementada

```
Sistema Multiagente
├── OrchestratorAgent (Coordenador central)
├── CSVAnalyzerAgent (Especialista em dados)
├── RAGAgent (Busca contextualizada)
├── DataProcessor (Processamento)
└── EmbeddingsGenerator (Vetorização)

Banco Vetorial PostgreSQL
├── Tabela embeddings (vetores semânticos)
├── Tabela chunks (fragmentos)
└── Tabela metadata (análises persistidas)

Interface
├── exemplo_csv_interativo.py (Interface usuário)
├── exemplo_database_rag.py (Demo completo)
└── teste_deteccao_fraude.py (Validação)
```

## ✅ Verificação Final

Execute este comando para validar tudo:
```powershell
python check_db.py
```
Deve retornar: "Conexão OK"

## 🎉 Sistema Pronto para Uso!

Seu sistema backend multiagente está **100% operacional**. Para usar todas as funcionalidades avançadas, apenas configure a `GOOGLE_API_KEY` seguindo as instruções acima.

---
*Documentação gerada automaticamente - EDA AI Minds Backend*
*Data: 2025-09-28*