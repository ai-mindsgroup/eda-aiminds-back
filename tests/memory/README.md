# Testes do Sistema de Memória

Este diretório contém a suíte completa de testes para o sistema de memória persistente dos agentes multiagente.

## 📁 Estrutura dos Testes

```
tests/memory/
├── test_memory_system.py        # Testes unitários básicos
├── test_memory_integration.py   # Testes de integração com agentes
├── test_memory_performance.py   # Testes de performance e stress
└── run_memory_tests.py         # Script de execução e relatórios
```

## 🧪 Tipos de Teste

### 1. Testes Unitários (`test_memory_system.py`)
- **TestMemoryTypes**: Testa criação e validação de tipos de dados
- **TestMemoryUtils**: Testa funções utilitárias
- **TestSupabaseMemoryManager**: Testa manager de memória com mocks
- **TestMemoryMixin**: Testa integração de memória com agentes

### 2. Testes de Integração (`test_memory_integration.py`)
- **TestOrchestratorMemoryIntegration**: Integração com OrchestratorAgent
- **TestCSVAnalysisMemoryIntegration**: Integração com EmbeddingsAnalysisAgent  
- **TestRAGMemoryIntegration**: Integração com RAGAgent
- **TestMemorySystemIntegration**: Testes de workflow completo

### 3. Testes de Performance (`test_memory_performance.py`)
- **TestMemoryPerformance**: Performance básica de operações
- **TestMemoryStress**: Testes de stress com alta carga
- **TestMemoryOptimization**: Validação de otimizações
- **TestMemoryCleanup**: Testes de limpeza automática

## 🚀 Execução dos Testes

### Execução Rápida
```bash
# Todos os testes
python tests/memory/run_memory_tests.py

# Apenas testes unitários
python -m pytest tests/memory/test_memory_system.py -v

# Apenas testes de integração
python -m pytest tests/memory/test_memory_integration.py -v

# Apenas testes de performance
python -m pytest tests/memory/test_memory_performance.py -v
```

### Execução com Relatório Completo
```bash
python tests/memory/run_memory_tests.py
```
- Gera relatório JSON com timestamp
- Valida integridade do sistema
- Executa todos os tipos de teste
- Análise de cobertura de código

### Execução por Tipo
```python
from tests.memory.run_memory_tests import run_memory_tests

# Executar apenas testes unitários
result = run_memory_tests("unit")

# Executar apenas testes de integração
result = run_memory_tests("integration")

# Executar apenas testes de performance
result = run_memory_tests("performance")
```

## 📊 Análise de Cobertura

```bash
# Instalar dependência se necessário
pip install pytest-cov

# Executar com cobertura
python -m pytest tests/memory/ --cov=src.memory --cov-report=html --cov-report=term-missing

# Ver relatório HTML
open tests/memory/coverage_html/index.html
```

## 🔧 Configuração de Ambiente

### Dependências Necessárias
```bash
pip install pytest pytest-asyncio pytest-cov pandas supabase python-dotenv
```

### Variáveis de Ambiente (Opcional)
```env
# Para testes com Supabase real (não recomendado para CI)
SUPABASE_URL=your_test_supabase_url
SUPABASE_KEY=your_test_supabase_key
```

**Nota**: Os testes usam mocks por padrão, não requerendo Supabase real.

## 📋 Validações Incluídas

### Estrutura do Sistema
- ✅ Todos os arquivos de memória existem
- ✅ Migration de banco configurada
- ✅ Integração com agentes implementada
- ✅ Testes cobrindo funcionalidades principais

### Funcionalidades Testadas
- ✅ Criação e gerenciamento de sessões
- ✅ Persistência de conversações
- ✅ Armazenamento de contexto
- ✅ Sistema de embeddings
- ✅ Cache e otimizações
- ✅ Limpeza automática
- ✅ Performance sob carga

### Cenários de Integração
- ✅ Workflow completo multiagente
- ✅ Continuidade de conversação
- ✅ Cache de análises CSV
- ✅ Aprendizado de padrões
- ✅ Busca RAG otimizada
- ✅ Threshold adaptativo

## 🐛 Debugging e Troubleshooting

### Executar Teste Específico
```bash
# Teste específico por nome
python -m pytest tests/memory/test_memory_system.py::TestMemoryTypes::test_session_info_creation -v

# Com output detalhado
python -m pytest tests/memory/test_memory_system.py -v -s --tb=long
```

### Verificar Importações
```python
# Verificar se módulos de memória estão disponíveis
python -c "from src.memory import SupabaseMemoryManager; print('✅ Memória OK')"

# Verificar se agentes estão disponíveis
python -c "from src.agent.orchestrator_agent import OrchestratorAgent; print('✅ Agentes OK')"
```

### Logs de Teste
```bash
# Executar com logs detalhados
LOG_LEVEL=DEBUG python -m pytest tests/memory/ -v -s
```

## 📈 Métricas de Performance

### Benchmarks Esperados
- **Criação de sessão**: < 10ms
- **Salvamento de conversação**: < 50ms
- **Recuperação de contexto**: < 100ms
- **Busca de embedding**: < 200ms
- **50 sessões concorrentes**: < 10s
- **200 conversações**: < 15s

### Limites de Sistema
- **Tamanho máximo de contexto**: 1MB
- **Dimensão de embedding**: 1536
- **Duração padrão de sessão**: 24h
- **Threshold de similaridade**: 0.800
- **Compressão de conversação**: 50 turnos

## 🔍 Interpretação de Resultados

### Status de Sucesso
```
✅ Sistema de memória está completamente implementado!
🎉 SISTEMA DE MEMÓRIA COMPLETAMENTE FUNCIONAL!
```

### Problemas Comuns
```
❌ Pacotes faltando: pytest-asyncio
💡 Execute: pip install pytest-asyncio

⚠️ 2 verificações falharam
❌ Integração de memória em base_agent.py
```

### Relatório JSON
```json
{
  "timestamp": "2024-01-28T10:30:00",
  "system_validation": {
    "passed": true,
    "details": [...]
  },
  "test_results": {
    "unit": {"success": true, "duration_seconds": 2.5},
    "integration": {"success": true, "duration_seconds": 5.2},
    "performance": {"success": true, "duration_seconds": 8.1}
  },
  "summary": {
    "total_test_types": 3,
    "passed_test_types": 3,
    "system_complete": true,
    "total_duration": 15.8
  }
}
```

## 🚀 Execução em CI/CD

### GitHub Actions
```yaml
- name: Test Memory System
  run: |
    pip install pytest pytest-asyncio pytest-cov
    python tests/memory/run_memory_tests.py
```

### Docker
```dockerfile
RUN pip install pytest pytest-asyncio pytest-cov
CMD ["python", "tests/memory/run_memory_tests.py"]
```

---

## 📚 Documentação Adicional

- **Arquitetura de Memória**: `docs/sistema-memoria-arquitetura.md`
- **Guia de Desenvolvimento**: `docs/guia-desenvolvimento-memoria.md`
- **API Reference**: `src/memory/__init__.py`

Para dúvidas ou problemas, consulte a documentação completa ou execute:
```bash
python tests/memory/run_memory_tests.py --help
```