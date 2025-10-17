# 🧪 Guia de Testes - Sandbox Segura

**Versão:** 1.0  
**Data:** 2025-10-17  
**Autor:** GitHub Copilot (GPT-4.1)

---

## 📚 Índice

1. [Introdução](#introdução)
2. [Setup Rápido](#setup-rápido)
3. [Estrutura dos Testes](#estrutura-dos-testes)
4. [Como Executar](#como-executar)
5. [Criando Novos Testes](#criando-novos-testes)
6. [Fixtures Disponíveis](#fixtures-disponíveis)
7. [Marcadores (Markers)](#marcadores-markers)
8. [Interpretando Resultados](#interpretando-resultados)
9. [Debugging](#debugging)
10. [CI/CD](#cicd)
11. [FAQ](#faq)

---

## 🎯 Introdução

Este guia explica como trabalhar com a suite de testes automatizados da **Sandbox Segura** do projeto EDA AI Minds.

**Objetivo dos testes:**
- ✅ Validar execução de código Python seguro (RestrictedPython)
- ✅ Garantir bloqueio de imports e funções maliciosas
- ✅ Verificar limites de timeout e memória
- ✅ Testar edge cases e carga paralela

---

## ⚡ Setup Rápido

### 1. Instalar Dependências

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Instalar pytest e extensões
pip install pytest pytest-cov pytest-timeout pytest-xdist pytest-benchmark
```

### 2. Verificar Instalação

```powershell
pytest --version
# Deve mostrar: pytest 8.4.2

pytest --cov --version
# Deve mostrar: pytest-cov 7.0.0
```

### 3. Executar Testes

```powershell
# Testes rápidos (sem --run-slow)
pytest tests/security/ -v

# Com cobertura
pytest tests/security/ --cov=src/security --cov-report=html

# Abrir relatório HTML
start htmlcov/index.html
```

---

## 📁 Estrutura dos Testes

```
tests/security/
├── conftest.py                        # Fixtures e configuração global
│   ├── execute_sandbox_helper()       # Helper principal de execução
│   ├── assert_success()               # Validar sucesso
│   ├── assert_failure()               # Validar falha
│   ├── small_dataframe()              # DataFrames de teste
│   └── default_execution_config()     # Configurações padrão
│
├── test_sandbox_valid_execution.py    # 38 testes - Código válido
│   ├── TestSimpleOperations           # Aritmética básica
│   ├── TestStringOperations           # Manipulação de strings
│   ├── TestDataStructures             # Listas, dicts, tuples
│   ├── TestPandasOperations           # DataFrame operations
│   ├── TestNumpyOperations            # Arrays e computação
│   ├── TestComplexCode                # Análises multi-step
│   ├── TestAllowedImports             # Whitelist validation
│   └── TestFunctionsAndClasses        # Funções e lambdas
│
├── test_sandbox_security.py           # 14 testes - Bloqueios
│   ├── TestBlockedImports             # os, subprocess, sys
│   ├── TestBlockedFunctions           # eval, exec, open
│   ├── TestWhitelistPermissions       # pandas, numpy permitidos
│   └── TestBypassAttempts             # __import__, __builtins__
│
├── test_sandbox_limits.py             # 13 testes - Limites
│   ├── TestTimeout                    # Loop infinito, slow code
│   ├── TestMemoryLimit                # Consumo excessivo
│   ├── TestExceptionHandling          # Try/except user code
│   └── TestIntegratedLimits           # Timeout + memória juntos
│
├── test_sandbox_edge_cases.py         # 10 testes - Casos extremos
│   └── TestEdgeCases                  # Empty, None, unicode, etc.
│
└── test_sandbox_load.py               # 5 testes - Performance
    └── TestLoad                       # Carga sequencial/paralela
```

---

## 🚀 Como Executar

### Comandos Básicos

```powershell
# Todos os testes (default)
pytest tests/security/

# Verbose (mostra cada teste)
pytest tests/security/ -v

# Quiet (só resumo)
pytest tests/security/ -q

# Parar na primeira falha
pytest tests/security/ -x

# Mostrar output de print()
pytest tests/security/ -s
```

### Filtros por Arquivo

```powershell
# Apenas execução válida
pytest tests/security/test_sandbox_valid_execution.py

# Apenas segurança
pytest tests/security/test_sandbox_security.py

# Apenas limites
pytest tests/security/test_sandbox_limits.py
```

### Filtros por Teste Específico

```powershell
# Um teste específico
pytest tests/security/test_sandbox_valid_execution.py::TestSimpleOperations::test_simple_addition

# Classe de testes
pytest tests/security/test_sandbox_security.py::TestBlockedImports

# Pattern matching
pytest tests/security/ -k "addition or multiplication"
pytest tests/security/ -k "not slow"
```

### Marcadores (Markers)

```powershell
# Apenas testes de segurança
pytest tests/security/ -m security

# Apenas testes lentos
pytest tests/security/ -m slow

# Excluir lentos
pytest tests/security/ -m "not slow"

# Apenas carga
pytest tests/security/ -m load

# Combinação
pytest tests/security/ -m "security and not slow"
```

### Cobertura

```powershell
# Relatório terminal
pytest tests/security/ --cov=src/security

# Terminal + missing lines
pytest tests/security/ --cov=src/security --cov-report=term-missing

# HTML (mais detalhado)
pytest tests/security/ --cov=src/security --cov-report=html
start htmlcov/index.html

# XML (para CI/CD)
pytest tests/security/ --cov=src/security --cov-report=xml

# Falhar se cobertura < 85%
pytest tests/security/ --cov=src/security --cov-fail-under=85
```

### Execução Paralela

```powershell
# 4 workers
pytest tests/security/ -n 4

# Auto-detect CPUs
pytest tests/security/ -n auto

# Com cobertura (requer pytest-cov)
pytest tests/security/ -n auto --cov=src/security
```

### Testes Lentos

```powershell
# Incluir testes marcados com @pytest.mark.slow
pytest tests/security/ --run-slow

# Ver os 10 testes mais lentos
pytest tests/security/ --durations=10
```

---

## ➕ Criando Novos Testes

### 1. Escolher o Arquivo Correto

| Tipo de Teste | Arquivo | Exemplo |
|---------------|---------|---------|
| Código válido (pandas, numpy) | `test_sandbox_valid_execution.py` | DataFrame operations |
| Bloqueio de imports | `test_sandbox_security.py` | `import os` deve falhar |
| Timeout/memória | `test_sandbox_limits.py` | Loop infinito |
| Edge cases | `test_sandbox_edge_cases.py` | Código vazio, None |
| Performance | `test_sandbox_load.py` | 100 execuções paralelas |

### 2. Template Básico

```python
import pytest

class TestMinhaFuncionalidade:
    """Descrição da classe de testes."""
    
    def test_caso_sucesso(self, execute_sandbox_helper, assert_success):
        """✅ Teste 99: Descrição clara do que testa."""
        # Arrange
        code = """
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3]})
resultado = df['A'].sum()
"""
        
        # Act
        result = execute_sandbox_helper(code)
        
        # Assert
        assert_success(result, expected_result=6)
    
    def test_caso_falha(self, execute_sandbox_helper, assert_failure):
        """✅ Teste 100: Import malicioso deve ser bloqueado."""
        # Arrange
        code = """
import os
resultado = os.listdir('/')
"""
        
        # Act
        result = execute_sandbox_helper(code)
        
        # Assert
        assert_failure(result, expected_error_type='CompilationError')
```

### 3. Usando Fixtures

```python
def test_com_dataframe(self, execute_sandbox_helper, small_dataframe, assert_success):
    """✅ Teste 101: Processar DataFrame injetado."""
    code = """
# small_dataframe já existe no namespace
resultado = df['A'].mean()
"""
    result = execute_sandbox_helper(
        code,
        custom_globals={'df': small_dataframe}
    )
    assert_success(result, expected_result=5.5)
```

### 4. Parametrização

```python
@pytest.mark.parametrize("expression,expected", [
    ("2 + 2", 4),
    ("10 * 5", 50),
    ("2 ** 8", 256),
])
def test_math_operations(self, execute_sandbox_helper, assert_success, expression, expected):
    """✅ Teste 102-104: Operações matemáticas parametrizadas."""
    code = f"resultado = {expression}"
    result = execute_sandbox_helper(code)
    assert_success(result, expected_result=expected)
```

### 5. Marcadores

```python
@pytest.mark.slow
def test_heavy_computation(self, execute_sandbox_helper, assert_success):
    """✅ Teste 105: Computação pesada (>5s)."""
    # Só executa com --run-slow
    code = "resultado = sum(range(10**8))"
    result = execute_sandbox_helper(code, timeout_seconds=30)
    assert_success(result)

@pytest.mark.security
def test_blocked_syscall(self, execute_sandbox_helper, assert_failure):
    """✅ Teste 106: Syscall bloqueada."""
    code = "import ctypes; resultado = ctypes.CDLL('libc.so.6')"
    result = execute_sandbox_helper(code)
    assert_failure(result)
```

---

## 🧰 Fixtures Disponíveis

### Fixtures de Execução

#### `execute_sandbox_helper(code, **kwargs)`
Helper principal para executar código no sandbox.

```python
def test_exemplo(self, execute_sandbox_helper):
    result = execute_sandbox_helper(
        code="resultado = 42",
        timeout_seconds=10,           # Default: 10s
        memory_limit_mb=200,          # Default: 200MB
        custom_globals={'x': 10},     # Injetar variáveis
        return_variable='resultado'   # Default: 'resultado'
    )
    # result = {
    #     'success': True,
    #     'result': 42,
    #     'execution_time_ms': 5.23,
    #     'error': None,
    #     'error_type': None,
    #     'logs': [...]
    # }
```

#### `assert_success(result, expected_result=None)`
Valida execução bem-sucedida.

```python
def test_success(self, execute_sandbox_helper, assert_success):
    result = execute_sandbox_helper("resultado = 100")
    assert_success(result, expected_result=100)
```

#### `assert_failure(result, expected_error_type=None)`
Valida execução falhada.

```python
def test_failure(self, execute_sandbox_helper, assert_failure):
    result = execute_sandbox_helper("import os")
    assert_failure(result, expected_error_type='CompilationError')
```

### Fixtures de Dados

#### DataFrames Pandas

```python
def test_com_dataframe(self, small_dataframe, medium_dataframe, large_dataframe):
    # small_dataframe: 10 linhas (A: 1-10, B: 11-20)
    # medium_dataframe: 1000 linhas
    # large_dataframe: 10000 linhas
    assert len(small_dataframe) == 10
```

#### Código de Teste

```python
def test_com_codigo_pronto(
    self,
    simple_valid_code,       # "resultado = 2 + 2"
    malicious_import_os,     # "import os\nresultado = ..."
    timeout_code,            # "while True: pass"
    memory_intensive_code    # "huge_list = [0] * (10**8)"
):
    # Usar fixtures de código
    result = execute_sandbox_helper(simple_valid_code)
```

### Fixtures de Configuração

```python
def test_com_config_custom(self, execute_sandbox_helper, strict_execution_config):
    # strict_execution_config = {
    #     'timeout_seconds': 5,
    #     'memory_limit_mb': 100,
    #     'return_variable': 'resultado'
    # }
    result = execute_sandbox_helper(
        "resultado = 42",
        **strict_execution_config
    )
```

---

## 🏷️ Marcadores (Markers)

### Marcadores Disponíveis

| Marcador | Uso | Comando |
|----------|-----|---------|
| `@pytest.mark.security` | Testes de segurança | `pytest -m security` |
| `@pytest.mark.slow` | Testes > 5s | `pytest --run-slow` |
| `@pytest.mark.load` | Testes de carga | `pytest -m load` |
| `@pytest.mark.integration` | Testes de integração | `pytest -m integration` |
| `@pytest.mark.skipif(...)` | Skip condicional | Automático |
| `@pytest.mark.xfail(...)` | Falha esperada | Automático |

### Exemplos de Uso

```python
@pytest.mark.security
def test_blocked_import(self, ...):
    """Teste de bloqueio de import."""
    pass

@pytest.mark.slow
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_timeout_unix(self, ...):
    """Teste de timeout Unix."""
    pass

@pytest.mark.xfail(reason="RestrictedPython não suporta classes")
def test_class_definition(self, ...):
    """Teste de definição de classe (esperado falhar)."""
    pass
```

---

## 📊 Interpretando Resultados

### Saída Típica

```
tests/security/test_sandbox_valid_execution.py::TestSimpleOperations::test_simple_addition PASSED
tests/security/test_sandbox_security.py::TestBlockedImports::test_blocked_import_os FAILED

=============================== FAILURES =======================================
_________________________ test_blocked_import_os _______________________________

tests\security\test_sandbox_security.py:42: in test_blocked_import_os
    assert_failure(result, expected_error_type='CompilationError')
E   AssertionError: Execution succeeded but should have failed

=============================== short test summary ==============================
FAILED tests/security/test_sandbox_security.py::TestBlockedImports::test_blocked_import_os
========================== 1 failed, 37 passed in 2.53s ========================
```

### Símbolos de Status

| Símbolo | Significado |
|---------|-------------|
| `.` | PASSED (teste passou) |
| `F` | FAILED (teste falhou) |
| `s` | SKIPPED (teste pulado) |
| `x` | XFAIL (falha esperada) |
| `X` | XPASS (passou quando esperado falhar) |
| `E` | ERROR (erro durante setup/teardown) |

### Relatório de Cobertura

```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
src\security\__init__.py       2      0   100%
src\security\sandbox.py      272    110    60%   79, 88-90, 104-109, ...
--------------------------------------------------------
TOTAL                        274    110    60%
```

- **Stmts:** Total de statements (linhas executáveis)
- **Miss:** Statements não cobertos
- **Cover:** Percentual de cobertura
- **Missing:** Números das linhas não cobertas

### HTML Report

Abrir `htmlcov/index.html` para visualização interativa:
- ✅ Verde: Linha coberta
- ❌ Vermelho: Linha não coberta
- ⚠️ Amarelo: Linha parcialmente coberta (branch)

---

## 🐛 Debugging

### 1. Print Debugging

```python
def test_com_debug(self, execute_sandbox_helper):
    result = execute_sandbox_helper("resultado = 42")
    
    # Ver resultado completo
    print(f"Result: {result}")
    
    # Ver logs do sandbox
    for log in result['logs']:
        print(f"LOG: {log}")
    
    assert result['success']
```

```powershell
# Executar com output visível
pytest tests/security/test_sandbox_valid_execution.py::test_com_debug -s
```

### 2. Pytest Debugger (pdb)

```python
def test_com_pdb(self, execute_sandbox_helper):
    result = execute_sandbox_helper("resultado = 42")
    
    # Breakpoint
    import pdb; pdb.set_trace()
    
    assert result['success']
```

```powershell
# Executar (pdb interativo)
pytest tests/security/test_sandbox_valid_execution.py::test_com_pdb -s
```

### 3. Logging Detalhado

```powershell
# Configurar log level DEBUG
$env:LOG_LEVEL="DEBUG"
pytest tests/security/ -v --log-cli-level=DEBUG
```

### 4. Inspecionar Falhas

```powershell
# Traceback completo
pytest tests/security/ --tb=long

# Traceback curto
pytest tests/security/ --tb=short

# Apenas linha da falha
pytest tests/security/ --tb=line

# Sem traceback
pytest tests/security/ --tb=no
```

### 5. Last Failed

```powershell
# Re-executar apenas testes que falharam
pytest tests/security/ --lf

# Re-executar falhas primeiro, depois o resto
pytest tests/security/ --ff
```

---

## 🔄 CI/CD

### GitHub Actions Workflow

Criar `.github/workflows/sandbox-tests.yml`:

```yaml
name: Sandbox Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests with coverage
        run: |
          pytest tests/security/ \
            --cov=src/security \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=test-results.xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.python-version }}
          path: |
            test-results.xml
            htmlcov/
```

### Pre-commit Hook

Criar `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-security
        name: Run security tests
        entry: pytest tests/security/test_sandbox_security.py -x
        language: system
        pass_filenames: false
        always_run: true
```

---

## ❓ FAQ

### P: Como pular testes no Windows?

```python
import sys
import pytest

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_timeout(self, ...):
    pass
```

### P: Como testar código que deveria falhar?

```python
def test_blocked_import(self, execute_sandbox_helper, assert_failure):
    result = execute_sandbox_helper("import os")
    assert_failure(result, expected_error_type='CompilationError')
```

### P: Como testar exceções de usuário?

```python
def test_user_exception(self, execute_sandbox_helper, assert_success):
    code = """
try:
    1 / 0
except ZeroDivisionError:
    resultado = "caught"
"""
    result = execute_sandbox_helper(code)
    assert_success(result, expected_result="caught")
```

### P: Como debugar timeout de teste?

```python
# Aumentar timeout do pytest (300s default)
@pytest.mark.timeout(600)  # 10 minutos
def test_heavy(self, ...):
    pass
```

### P: Como forçar re-execução de testes em cache?

```powershell
# Limpar cache
pytest --cache-clear tests/security/
```

### P: Por que alguns testes são pulados?

Motivos comuns:
- `@pytest.mark.slow` sem `--run-slow` flag
- `@pytest.mark.skipif(sys.platform == "win32")` no Windows
- Dependências não instaladas

### P: Como contribuir com novos testes?

1. Escolher arquivo apropriado (`test_sandbox_*.py`)
2. Seguir template de teste (ver seção [Criando Novos Testes](#criando-novos-testes))
3. Adicionar docstring descritiva
4. Testar localmente: `pytest tests/security/test_*.py -v`
5. Verificar cobertura: `pytest --cov=src/security --cov-report=html`
6. Abrir PR com descrição clara

---

## 📚 Recursos Adicionais

### Documentação Oficial
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- RestrictedPython: https://restrictedpython.readthedocs.io/

### Relatórios Internos
- [Relatório Completo Sprint 3](./SPRINT3_TESTES_AUTOMATIZADOS_RELATORIO.md)
- [Changelog do Projeto](../CHANGELOG.md)

### Contato
- Issues: https://github.com/seu-usuario/eda-aiminds-i2a2-rb/issues
- Documentação: `docs/`

---

**Última atualização:** 2025-10-17  
**Versão do guia:** 1.0  
**Autor:** GitHub Copilot (GPT-4.1)
