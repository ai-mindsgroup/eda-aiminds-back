# Análise de Memória do Sistema Multiagente - Supabase

## 📋 **ANÁLISE ATUAL DA IMPLEMENTAÇÃO DE MEMÓRIA**

### ✅ **MEMÓRIA EXISTENTE - AGENTES COM IMPLEMENTAÇÃO:**

#### 1. **OrchestratorAgent** - Memória Local Parcial
- **Localização:** `src/agent/orchestrator_agent.py`
- **Implementação Atual:**
  ```python
  self.conversation_history = []        # Lista local na instância
  self.current_data_context = {}       # Contexto de dados na memória
  ```
- **Funcionalidades:**
  - ✅ Histórico de conversação em memória (local)
  - ✅ Contexto de dados carregados
  - ✅ Métodos: `get_conversation_history()`, `clear_conversation_history()`
- **Limitações:** 
  - ❌ **Não persistente** - perdida ao reiniciar o agente
  - ❌ **Não integrada com Supabase**
  - ❌ Apenas em RAM local da instância

#### 2. **Sessões de API** - Memória Temporária (Detectada no código)
- **Localização:** Referenciado nos exemplos e semantic search
- **Implementação Detectada:**
  ```python
  # Em app.py e backend_api_example.py (arquivo não encontrado mas referenciado)
  sessions = {}  # Dicionário local temporário
  ```
- **Funcionalidades:**
  - ✅ Sessões por ID único
  - ✅ Histórico de conversação por sessão
  - ✅ Contexto de dados associado à sessão
- **Limitações:**
  - ❌ **Não persistente** - perdida ao reiniciar servidor
  - ❌ **Não integrada com Supabase**

### ❌ **AGENTES SEM MEMÓRIA IMPLEMENTADA:**

#### 1. **EmbeddingsAnalysisAgent** (ex-CSVAnalysisAgent)
- **Localização:** `src/agent/csv_analysis_agent.py`
- **Estado Atual:** **SEM MEMÓRIA**
- **Necessidade:** 🔴 **ALTA** - Essencial para análises contextuais

#### 2. **RAGAgent** 
- **Localização:** `src/agent/rag_agent.py`
- **Estado Atual:** **SEM MEMÓRIA**
- **Necessidade:** 🔴 **ALTA** - Crítico para busca contextual melhorada

#### 3. **BaseAgent**
- **Localização:** `src/agent/base_agent.py`
- **Estado Atual:** **SEM SISTEMA DE MEMÓRIA**
- **Necessidade:** 🟡 **MÉDIA** - Base para todos os agentes

---

## 🗄️ **INFRAESTRUTURA SUPABASE DISPONÍVEL**

### **Tabelas Existentes para Memória:**

1. **`embeddings`** - Para dados vetoriais
2. **`chunks`** - Para conteúdo segmentado
3. **`metadata`** - Para metadados genéricos ✅ **PODE SER EXPANDIDA PARA MEMÓRIA**

### **Infraestrutura Necessária para Memória:**
- ❌ Tabela específica para conversações
- ❌ Tabela para contexto de agentes
- ❌ Tabela para sessões persistentes
- ❌ Índices para busca eficiente de memória

---

## 🎯 **PLANO DE IMPLEMENTAÇÃO DE MEMÓRIA**

### **PRIORIDADE 1: Sistema Base de Memória (Supabase)**

#### **1.1 Criar Estrutura de Tabelas**
```sql
-- Tabela de sessões de usuário
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Tabela de conversações
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    message_type VARCHAR(20) NOT NULL, -- 'query', 'response'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de contexto de agentes
CREATE TABLE agent_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    context_type VARCHAR(50) NOT NULL, -- 'data', 'preference', 'state'
    context_data JSONB NOT NULL,
    expiry_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_agent_conversations_session ON agent_conversations(session_id);
CREATE INDEX idx_agent_conversations_agent ON agent_conversations(agent_name);
CREATE INDEX idx_agent_context_session_agent ON agent_context(session_id, agent_name);
CREATE INDEX idx_agent_context_type ON agent_context(context_type);
```

#### **1.2 Criar Módulo Base de Memória**
```python
# src/memory/base_memory.py
class AgentMemoryManager:
    def save_conversation(self, session_id, agent_name, message_type, content, metadata)
    def get_conversation_history(self, session_id, agent_name, limit)
    def save_context(self, session_id, agent_name, context_type, context_data, expiry)
    def get_context(self, session_id, agent_name, context_type)
    def clear_session(self, session_id)
```

### **PRIORIDADE 2: Implementação por Agente**

#### **2.1 OrchestratorAgent - Upgrade de Memória**
- ✅ **Converter memória local para Supabase**
- ✅ **Persistência de conversation_history**
- ✅ **Context de dados no Supabase**
- ✅ **Recuperação automática ao inicializar**

#### **2.2 EmbeddingsAnalysisAgent - Memória Nova**
- 🆕 **Contexto de consultas anteriores**
- 🆕 **Padrões de análise detectados**
- 🆕 **Preferências de formato de resposta**
- 🆕 **Cache de resultados de embeddings**

#### **2.3 RAGAgent - Memória Inteligente**
- 🆕 **Histórico de buscas vetoriais**
- 🆕 **Contexto de consultas relacionadas**
- 🆕 **Cache de embeddings de consultas**
- 🆕 **Aprendizado de relevância**

### **PRIORIDADE 3: Funcionalidades Avançadas**

#### **3.1 Gerenciamento Inteligente**
- 🔄 **Expiração automática de contexto**
- 🔄 **Compressão de histórico longo**
- 🔄 **Limpeza de memória órfã**

#### **3.2 Busca Semântica de Memória**
- 🔍 **Busca em conversações anteriores**
- 🔍 **Recuperação de contexto similar**
- 🔍 **Embeddings de memória**

---

## 💻 **IMPLEMENTAÇÃO TÉCNICA**

### **Estrutura de Arquivos:**
```
src/
  memory/
    __init__.py
    base_memory.py          # Classe base para memória
    supabase_memory.py      # Implementação Supabase
    memory_types.py         # Tipos e schemas
    memory_utils.py         # Utilitários
  agent/
    base_agent.py          # + Mixin de memória
    orchestrator_agent.py  # + Memória Supabase
    csv_analysis_agent.py  # + Memória contextual
    rag_agent.py           # + Memória de busca
migrations/
  0005_agent_memory_tables.sql  # Novas tabelas
tests/
  test_memory/           # Testes de memória
```

### **Exemplo de Uso:**
```python
# Agente com memória
class OrchestratorAgent(BaseAgent, MemoryMixin):
    def __init__(self, session_id=None):
        super().__init__("orchestrator", "Coordenador central")
        self.memory = SupabaseMemoryManager(session_id=session_id)
    
    def process(self, query, context=None):
        # Recuperar contexto da memória
        historical_context = self.memory.get_context("data_preferences")
        
        # Processar consulta
        result = self._process_with_memory(query, historical_context)
        
        # Salvar na memória
        self.memory.save_conversation("query", query, {"timestamp": now()})
        self.memory.save_conversation("response", result["content"], result["metadata"])
        
        return result
```

---

## 🧪 **CRITÉRIOS DE ENTREGA**

### **✅ Entregáveis Técnicos:**
1. **Migration SQL** para tabelas de memória
2. **Módulo `src/memory/`** completo
3. **Agentes atualizados** com memória integrada
4. **Testes automatizados** para todas as funcionalidades
5. **Documentação técnica** e exemplos de uso

### **✅ Validação Funcional:**
1. **Persistência** - Memória mantida após restart
2. **Performance** - Queries < 100ms para recuperação
3. **Integridade** - Limpeza automática e consistência
4. **Escalabilidade** - Suporte a múltiplas sessões simultâneas

---

## 📊 **CRONOGRAMA DE IMPLEMENTAÇÃO**

| Fase | Duração | Entregáveis |
|------|---------|-------------|
| **Fase 1** | 2-3 horas | Tabelas Supabase + Módulo base |
| **Fase 2** | 3-4 horas | OrchestratorAgent + EmbeddingsAnalysisAgent |
| **Fase 3** | 2-3 horas | RAGAgent + Funcionalidades avançadas |
| **Fase 4** | 1-2 horas | Testes + Documentação |

**Total Estimado: 8-12 horas de desenvolvimento**

---

## 🎯 **BENEFÍCIOS ESPERADOS**

1. **📈 Qualidade de Resposta:** Contexto histórico melhora relevância
2. **🔄 Continuidade:** Conversações mantêm contexto entre sessões  
3. **🎯 Personalização:** Agentes aprendem preferências do usuário
4. **⚡ Performance:** Cache de resultados reduz processamento
5. **🔍 Análise:** Histórico permite melhorias no sistema

**PRÓXIMO PASSO:** Iniciar implementação com Fase 1 - Estrutura base Supabase