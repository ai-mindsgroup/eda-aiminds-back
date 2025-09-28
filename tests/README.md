# 🧪 Testes do Sistema EDA AI Minds

Esta pasta contém todos os testes automatizados e manuais do sistema.

## 📁 Organização dos Testes

### **Testes de Componentes Principais**
- `test_csv_agent.py` - Testes do agente de análise CSV
- `test_orchestrator_basic.py` - Testes básicos do orquestrador (sem dependências)
- `test_orchestrator.py` - Testes completos do orquestrador (requer Supabase)

### **Testes do Sistema de Dados**
- `test_data_loading_system.py` - Testes do sistema de carregamento completo

### **Testes RAG/Embeddings**
- `test_rag_system.py` - Testes do sistema RAG completo
- `test_rag_mock.py` - Testes RAG com mocks (sem dependências)

### **Testes Utilitários**
- `test_simple.py` - Teste simples de funcionamento básico

## 🚀 Como Executar

### **Testes Individuais:**
```powershell
# Teste básico (sem dependências externas)
python tests\test_orchestrator_basic.py

# Teste do sistema de dados
python tests\test_data_loading_system.py

# Teste do agente CSV
python tests\test_csv_agent.py
```

### **Testes que Requerem Configuração:**
```powershell
# Configure .env primeiro, depois:
python tests\test_orchestrator.py
python tests\test_rag_system.py
```

### **Executar Todos os Testes:**
```powershell
# Opção 1: pytest (se instalado)
pytest tests/

# Opção 2: Executar um por um
Get-ChildItem tests\test_*.py | ForEach-Object { python $_.FullName }
```

## ✅ Status dos Testes

- ✅ `test_orchestrator_basic.py` - 100% funcional
- ✅ `test_data_loading_system.py` - 10/10 testes passando
- ✅ `test_csv_agent.py` - Funcional
- ⚠️ `test_orchestrator.py` - Requer Supabase configurado
- ⚠️ `test_rag_system.py` - Requer Supabase configurado
- ✅ `test_rag_mock.py` - Funcional com mocks

## 🔧 Configuração para Testes Completos

Para executar todos os testes, configure o arquivo `configs/.env`:

```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
SONAR_API_KEY=your_perplexity_key  # opcional
```

## 📊 Cobertura de Testes

Os testes cobrem:
- 🤖 **Agentes**: Orquestrador, CSV, RAG
- 📁 **Sistema de Dados**: Carregamento, validação, processamento
- 🔍 **Sistema RAG**: Embeddings, busca vetorial
- 🛠️ **Utilitários**: Logging, configurações
- 🔄 **Integração**: Coordenação entre componentes

---

**Nota:** Execute testes regularmente durante o desenvolvimento para garantir que mudanças não quebrem funcionalidades existentes.