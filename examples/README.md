# 🎯 Exemplos e Demonstrações EDA AI Minds

Esta pasta contém exemplos práticos, demonstrações e casos de uso do sistema.

## 📁 Organização dos Exemplos

### **Demonstrações Principais**
- `exemplo_orchestrator.py` - Demonstração completa do orquestrador multiagente
- `demo_csv_agent.py` - Demonstração do agente de análise CSV
- `demo_data_loading.py` - Demonstração do sistema de carregamento

### **Exemplos Práticos**
- `exemplo_pratico_carregamento.py` - Caso de uso prático do carregamento
- `exemplo_csv.py` - Exemplo básico de análise CSV

### **Dados de Exemplo**
- `dados_exemplo.csv` - Arquivo CSV para testes e demonstrações

## 🚀 Como Executar

### **Exemplos Básicos (sem dependências):**
```powershell
# Demonstração do orquestrador
python examples\exemplo_orchestrator.py

# Demo rápido
python examples\exemplo_orchestrator.py --quick

# Carregamento de dados
python examples\demo_data_loading.py

# Análise CSV
python examples\demo_csv_agent.py
```

### **Exemplos Avançados (requerem configuração):**
```powershell
# Configure configs/.env primeiro, depois:
python examples\exemplo_orchestrator.py    # Versão completa
```

## 📚 Casos de Uso Demonstrados

### **1. Sistema Orquestrador** (`exemplo_orchestrator.py`)
- ✅ Inicialização do sistema multiagente
- ✅ Carregamento automático de dados
- ✅ Roteamento inteligente de consultas
- ✅ Coordenação de múltiplos agentes
- ✅ Análises contextualizadas

### **2. Análise de Dados** (`demo_csv_agent.py`)
- ✅ Carregamento de CSV
- ✅ Análise exploratória automática
- ✅ Detecção de padrões de fraude
- ✅ Correlações e estatísticas
- ✅ Sugestões de visualização

### **3. Carregamento Multi-fonte** (`demo_data_loading.py`)
- ✅ Carregamento de arquivos locais
- ✅ Carregamento de URLs
- ✅ Dados sintéticos
- ✅ Validação automática
- ✅ Relatórios de qualidade

## 🎯 Fluxos de Trabalho Demonstrados

### **Fluxo Completo via Orquestrador:**
```python
# 1. Inicializar
orchestrator = OrchestratorAgent()

# 2. Carregar dados
context = {"file_path": "dados.csv"}
orchestrator.process("carregar dados", context)

# 3. Análises automáticas
orchestrator.process("faça um resumo dos dados")
orchestrator.process("identifique padrões suspeitos")
orchestrator.process("busque informações relevantes")

# 4. Status e histórico
orchestrator.process("status do sistema")
```

### **Análise Direta:**
```python
# Sistema tradicional
from src.data.data_processor import DataProcessor

processor = DataProcessor()
result = processor.load_from_file("dados.csv")
analysis = processor.quick_analysis()
```

## 🔧 Requisitos por Exemplo

### **Sem Dependências Externas:**
- ✅ `exemplo_orchestrator.py --quick`
- ✅ `demo_data_loading.py`
- ✅ `demo_csv_agent.py`
- ✅ `exemplo_pratico_carregamento.py`

### **Requer Supabase Configurado:**
- ⚠️ `exemplo_orchestrator.py` (versão completa com RAG)

### **Dados Necessários:**
- Alguns exemplos usam `dados_exemplo.csv` (incluído)
- Outros geram dados sintéticos automaticamente
- URLs de exemplo funcionam sem configuração adicional

## 💡 Dicas de Uso

1. **Comece pelos exemplos básicos** para entender o sistema
2. **Use `--quick`** nos exemplos para versões rápidas
3. **Configure `.env`** para funcionalidades completas
4. **Verifique logs** para entender o funcionamento interno
5. **Modifique exemplos** para seus casos de uso específicos

## 📊 Tipos de Dados Suportados

Os exemplos demonstram:
- **CSV**: Dados tabulares tradicionais
- **Dados sintéticos**: Fraude, vendas, clientes
- **URLs remotas**: Carregamento de datasets online
- **Base64**: Upload simulado via APIs

---

**Explore os exemplos para entender todo o potencial do sistema EDA AI Minds!**