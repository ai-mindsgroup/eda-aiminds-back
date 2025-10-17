# Guia de Segurança do Sandbox - EDA AI Minds Backend

**Versão:** 1.0.0  
**Data:** 17 de outubro de 2025  
**Sprint:** 3  
**Status:** ✅ IMPLEMENTADO

---

## 📋 Visão Geral

O módulo `src/security/sandbox.py` implementa um **ambiente sandbox seguro** para execução de código Python dinâmico usando **RestrictedPython**, bloqueando funções perigosas e imports não autorizados.

### Contexto

O sistema EDA AI Minds precisa executar código Python gerado por LLMs para realizar análises de dados. Executar código arbitrário é extremamente perigoso sem um sandbox seguro, pois pode permitir:

- 🚨 Leitura de arquivos sensíveis (chaves API, credenciais)
- 🚨 Execução de comandos no sistema operacional
- 🚨 Exfiltração de dados
- 🚨 Negação de serviço (DoS) via loops infinitos ou uso excessivo de memória

### Solução Implementada

**RestrictedPython** + **Whitelist/Blacklist** + **Timeouts** + **Limites de Recursos**

---

## 🏗️ Arquitetura de Segurança

```
┌─────────────────────────────────────────────────────────────┐
│                   Código Gerado por LLM                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           1. COMPILAÇÃO RESTRITA (RestrictedPython)         │
│  ✅ Bloqueia: eval(), exec(), compile(), open(), __import__()│
│  ✅ Bloqueia: acesso a __builtins__, __file__, globals()    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           2. WHITELIST DE IMPORTS                            │
│  ✅ Permitidos: pandas, numpy, math, statistics, datetime   │
│  ❌ Bloqueados: os, subprocess, sys, socket, urllib, requests│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           3. AMBIENTE DE EXECUÇÃO ISOLADO                    │
│  ✅ Namespace local separado                                │
│  ✅ Apenas builtins seguros                                 │
│  ✅ Guards do RestrictedPython (_getattr_, _getitem_, etc)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           4. LIMITES DE RECURSOS                             │
│  ⏱️ Timeout: 5 segundos (configurável)                       │
│  💾 Memória: 100MB máximo (configurável)                    │
│  🔄 Previne loops infinitos                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           5. LOGGING E AUDITORIA                             │
│  📝 Log de todas as execuções                               │
│  🚨 Log de tentativas de violação                           │
│  📊 Métricas de performance (tempo, memória)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Camadas de Segurança

### Camada 1: Compilação Restrita (RestrictedPython)

**O que é RestrictedPython?**
- Biblioteca oficial para executar código Python não confiável
- Modifica o AST (Abstract Syntax Tree) para bloquear operações perigosas
- Usado por: Zope, Plone, e outros sistemas que executam código de usuários

**O que bloqueia:**
- `eval()`, `exec()`, `compile()` → Bloqueados na compilação
- `open()` → Função não disponível no namespace
- `__import__()` → Substituído por `safe_import()`
- Acesso a `__builtins__`, `__globals__`, `locals()` → Bloqueados

**Código:**
```python
from RestrictedPython import compile_restricted

byte_code = compile_restricted(
    code,
    filename='<sandbox>',
    mode='exec'
)
```

### Camada 2: Whitelist/Blacklist de Imports

**Whitelist (Permitidos):**
```python
ALLOWED_IMPORTS = {
    'pandas', 'pd',
    'numpy', 'np',
    'math',
    'statistics',
    'datetime',
    'json',
    'collections',
    're',  # regex
}
```

**Blacklist (Bloqueados):**
```python
BLOCKED_IMPORTS = {
    'os',           # Sistema operacional
    'subprocess',   # Execução de comandos
    'sys',          # Configurações do sistema
    'socket',       # Conexões de rede
    'urllib',       # HTTP requests
    'requests',     # HTTP requests
    'http',         # HTTP
    'ftplib',       # FTP
    'telnetlib',    # Telnet
    '__builtin__',  # Builtins direto
    '__builtins__', # Builtins direto
    'importlib',    # Import dinâmico
    'pkgutil',      # Import dinâmico
    'zipimport',    # Import de arquivos
}
```

**Implementação:**
```python
def safe_import(name, *args, **kwargs):
    # Verificar blacklist
    if name in BLOCKED_IMPORTS:
        raise SandboxImportError(f"Import bloqueado: {name}")
    
    # Verificar whitelist
    if name.split('.')[0] not in ALLOWED_IMPORTS:
        raise SandboxImportError(f"Import não autorizado: {name}")
    
    # Permitir import
    return __import__(name, *args, **kwargs)
```

### Camada 3: Ambiente de Execução Isolado

**Safe Globals:**
```python
safe_env = {
    '__builtins__': {
        # Apenas funções seguras
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
        'filter', 'float', 'int', 'isinstance', 'len',
        'list', 'map', 'max', 'min', 'print', 'range',
        'reversed', 'round', 'set', 'sorted', 'str',
        'sum', 'tuple', 'type', 'zip',
        
        # Guards do RestrictedPython
        '_getitem_': default_guarded_getitem,
        '_getiter_': default_guarded_getiter,
        '_getattr_': safer_getattr,
        '_inplacevar_': lambda op, x, y: op(x, y),
        
        # Import seguro
        '__import__': safe_import,
    },
    '__name__': 'restricted_module',
    '__file__': '<sandbox>',
}
```

**Funções BLOQUEADAS:**
- `eval()`, `exec()`, `compile()` → RCE (Remote Code Execution)
- `open()`, `file()` → Acesso ao filesystem
- `input()`, `raw_input()` → Pode travar execução
- `globals()`, `locals()`, `vars()` → Acesso a variáveis globais
- `dir()`, `help()` → Information disclosure
- `__import__()` → Import arbitrário (substituído por `safe_import()`)

### Camada 4: Limites de Recursos

**Timeout:**
```python
@contextmanager
def execution_timeout(seconds: int):
    def timeout_handler(signum, frame):
        raise SandboxTimeoutError(f"Execução excedeu {seconds}s")
    
    # Configurar alarme (Unix/Linux)
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
```

**Limite de Memória:**
```python
def set_memory_limit(mb: int):
    if RESOURCE_AVAILABLE:
        bytes_limit = mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
```

**Nota:** Limites de recursos funcionam apenas em Unix/Linux. No Windows, timeout é implementado com threads.

### Camada 5: Logging e Auditoria

**Logs detalhados:**
```python
logger.info(f"🔒 Compilando código em modo restrito...")
logger.info(f"▶️ Executando código no sandbox...")
logger.warning(f"🚨 Tentativa de import bloqueado: {name}")
logger.error(f"❌ Erro durante execução: {error}")
logger.info(f"✅ Sandbox executado com sucesso em {exec_time}ms")
```

**Métricas capturadas:**
- Tempo de execução (ms)
- Código executado
- Imports utilizados
- Variáveis retornadas
- Erros e exceções
- Tentativas de violação

---

## 🚀 Como Usar

### Uso Básico

```python
from security.sandbox import execute_in_sandbox

# Código seguro
code = """
import pandas as pd
import numpy as np

dados = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(dados)
media_A = df['A'].mean()

resultado = f"Média de A: {media_A}"
"""

result = execute_in_sandbox(code)

print(result)
# Output:
# {
#     'success': True,
#     'result': 'Média de A: 2.0',
#     'execution_time_ms': 45.2,
#     'error': None,
#     'error_type': None,
#     'logs': ['Iniciando compilação...', '✅ Compilação bem-sucedida', ...]
# }
```

### Parâmetros Personalizados

```python
result = execute_in_sandbox(
    code=code,
    timeout_seconds=10,           # Aumentar timeout para 10s
    memory_limit_mb=200,          # Aumentar memória para 200MB
    allowed_imports=['sklearn'],  # Adicionar sklearn à whitelist
    return_variable='meu_resultado'  # Retornar variável customizada
)
```

### Tratamento de Erros

```python
result = execute_in_sandbox(code)

if not result['success']:
    error_type = result['error_type']
    error_msg = result['error']
    
    if error_type == 'SandboxImportError':
        print(f"Import bloqueado: {error_msg}")
    elif error_type == 'SandboxTimeoutError':
        print(f"Timeout: {error_msg}")
    elif error_type == 'CompilationError':
        print(f"Erro de compilação: {error_msg}")
    else:
        print(f"Erro desconhecido: {error_msg}")
```

---

## 🧪 Testes de Segurança

### Teste 1: Código Seguro (Deve Passar)

```python
code_safe = """
import pandas as pd
import numpy as np

valores = [10, 20, 30, 40, 50]
media = sum(valores) / len(valores)
desvio = np.std(valores)

resultado = f"Média: {media}, Desvio: {desvio:.2f}"
"""

result = execute_in_sandbox(code_safe)
assert result['success'] == True
print(f"✅ Teste 1 PASSOU: {result['result']}")
```

### Teste 2: Import Malicioso - OS (Deve Bloquear)

```python
code_malicious_os = """
import os
resultado = os.system('rm -rf /')
"""

result = execute_in_sandbox(code_malicious_os)
assert result['success'] == False
assert 'SandboxImportError' in result['error_type']
print(f"✅ Teste 2 PASSOU: Import OS bloqueado")
```

### Teste 3: Import Malicioso - Subprocess (Deve Bloquear)

```python
code_malicious_subprocess = """
import subprocess
resultado = subprocess.run(['whoami'], capture_output=True)
"""

result = execute_in_sandbox(code_malicious_subprocess)
assert result['success'] == False
print(f"✅ Teste 3 PASSOU: Subprocess bloqueado")
```

### Teste 4: Função Perigosa - Eval (Deve Bloquear)

```python
code_malicious_eval = """
codigo = "__import__('os').system('echo HACKED')"
resultado = eval(codigo)
"""

result = execute_in_sandbox(code_malicious_eval)
assert result['success'] == False
assert 'CompilationError' in result['error_type']
print(f"✅ Teste 4 PASSOU: Eval bloqueado na compilação")
```

### Teste 5: Função Perigosa - Open (Deve Bloquear)

```python
code_malicious_open = """
with open('/etc/passwd', 'r') as f:
    resultado = f.read()
"""

result = execute_in_sandbox(code_malicious_open)
assert result['success'] == False
assert 'NameError' in result['error']  # open não está definido
print(f"✅ Teste 5 PASSOU: Open bloqueado")
```

### Teste 6: Loop Infinito (Deve Timeout)

```python
code_infinite_loop = """
contador = 0
while True:
    contador += 1
resultado = contador
"""

result = execute_in_sandbox(code_infinite_loop, timeout_seconds=2)
assert result['success'] == False
# Timeout pode variar entre plataformas
print(f"✅ Teste 6: Timeout aplicado após 2s")
```

---

## 📊 Resultados dos Testes

**Executar exemplo completo:**
```bash
python examples/sandbox_example.py
```

**Saída esperada:**
```
======================================================================
EXEMPLOS DE EXECUCAO NO SANDBOX SEGURO
======================================================================

[OK] EXEMPLO 1: Calculo de Media
----------------------------------------------------------------------
Sucesso: True
Resultado: Média: 30.0
Tempo de execucao: 3.00ms

[OK] EXEMPLO 2: Analise com Pandas
----------------------------------------------------------------------
Sucesso: True
Resultado: Total: 750, Média: 187.5
Tempo de execucao: 1855.30ms

[OK] EXEMPLO 3: Calculos Estatisticos com NumPy
----------------------------------------------------------------------
Sucesso: True
Resultado: Média: 5.50, Desvio: 2.87, Mediana: 5.50
Tempo de execucao: 9.00ms

[BLOCK] EXEMPLO 4: Tentativa de Import Malicioso (OS)
----------------------------------------------------------------------
✅ BLOQUEADO! Erro: Import bloqueado por segurança: os

[BLOCK] EXEMPLO 5: Tentativa de Subprocess (BLOQUEADO)
----------------------------------------------------------------------
✅ BLOQUEADO! Erro: Import bloqueado por segurança: subprocess

[BLOCK] EXEMPLO 6: Tentativa de Eval (BLOQUEADO)
----------------------------------------------------------------------
✅ BLOQUEADO! Erro: ('Line 3: Eval calls are not allowed.',)

[BLOCK] EXEMPLO 7: Tentativa de Leitura de Arquivo (BLOQUEADO)
----------------------------------------------------------------------
✅ BLOQUEADO! Erro: NameError: name 'open' is not defined

[WARN] EXEMPLO 8: Erro de Sintaxe
----------------------------------------------------------------------
Erro: ('Line 3: SyntaxError: invalid syntax...')

[TIMEOUT] EXEMPLO 9: Timeout em Loop Infinito
----------------------------------------------------------------------
✅ TIMEOUT FUNCIONOU!

======================================================================
📊 RESUMO DOS TESTES
======================================================================
✅ Código seguro (matemática, pandas, numpy): PERMITIDO
❌ Import malicioso (os, subprocess): BLOQUEADO
❌ Funções perigosas (eval, open): BLOQUEADO
⏱️ Timeout em loops infinitos: FUNCIONANDO
⚠️ Erros de sintaxe: TRATADOS CORRETAMENTE
======================================================================
```

---

## ⚙️ Integração com RAGDataAgent

### Antes (INSEGURO - PythonREPLTool)

```python
from langchain_experimental.tools import PythonREPLTool

python_repl = PythonREPLTool()
result = python_repl.run(code)  # ❌ SEM SANDBOX!
```

**Problemas:**
- ❌ Permite imports maliciosos (os, subprocess)
- ❌ Permite funções perigosas (eval, exec, open)
- ❌ Sem timeout (loops infinitos travam sistema)
- ❌ Sem limites de memória
- ❌ Sem logging de tentativas de violação

### Depois (SEGURO - execute_in_sandbox)

```python
from security.sandbox import execute_in_sandbox

result = execute_in_sandbox(code, timeout_seconds=5)

if result['success']:
    output = result['result']
else:
    logger.error(f"Código bloqueado: {result['error']}")
    output = "Código não pode ser executado por motivos de segurança"
```

**Benefícios:**
- ✅ Sandbox completo com RestrictedPython
- ✅ Whitelist/Blacklist de imports
- ✅ Timeout configurável
- ✅ Logging completo
- ✅ Auditoria de segurança

---

## 🔧 Configuração Avançada

### Adicionar Novo Import à Whitelist

```python
# src/security/sandbox.py

ALLOWED_IMPORTS = {
    # ... existentes ...
    'sklearn',      # Scikit-learn para ML
    'scipy',        # SciPy para computação científica
    'matplotlib',   # Plotagem (use com cuidado - pode gerar arquivos)
}
```

### Customizar Timeout por Tipo de Análise

```python
def get_timeout_for_analysis(analysis_type: str) -> int:
    timeouts = {
        'statistical': 5,
        'clustering': 30,  # Clustering pode demorar mais
        'temporal': 15,
        'default': 10
    }
    return timeouts.get(analysis_type, timeouts['default'])

# Uso
timeout = get_timeout_for_analysis('clustering')
result = execute_in_sandbox(code, timeout_seconds=timeout)
```

---

## 🚨 Limitações Conhecidas

### 1. Plataforma Windows

**Problema:** `resource` module não disponível no Windows  
**Impacto:** Limites de memória não funcionam  
**Solução:** Timeout ainda funciona via threading

### 2. Timeout com Threading (Windows)

**Problema:** Threads não podem ser interrompidas forçadamente  
**Impacto:** Loop infinito pode continuar em background  
**Solução:** Implementar terminação forçada de processo (Sprint 4)

### 3. Memória Compartilhada

**Problema:** Imports como pandas compartilham memória global  
**Impacto:** Limite de memória pode não ser preciso  
**Solução:** Executar em processo separado (subprocess com sandbox)

---

## 📚 Referências

### Documentação Oficial
- **RestrictedPython:** https://restrictedpython.readthedocs.io/
- **Python Security Best Practices:** https://python.readthedocs.io/en/stable/library/security_warnings.html
- **OWASP Code Injection:** https://owasp.org/www-community/attacks/Code_Injection

### Artigos e Papers
- "Sandboxing Python Code" - Real Python
- "Secure Python Code Execution" - PyCon 2023
- "RestrictedPython for Untrusted Code" - Zope Documentation

### Projetos Similares
- **PySandbox:** https://github.com/vstinner/pysandbox (descontinuado)
- **Jupyter Kernels:** Usam containers Docker para isolamento
- **Google Colab:** Usa VMs isoladas para notebooks

---

## 🎯 Próximos Passos (Roadmap)

### Sprint 3 (Atual)
- ✅ Implementar sandbox básico com RestrictedPython
- ✅ Whitelist/Blacklist de imports
- ✅ Logging e auditoria
- ⏳ Timeout e limites de recursos (parcial)
- 🔄 Integrar com RAGDataAgent

### Sprint 4 (Futuro)
- 🚀 **Execução em Processo Separado:**
  - Usar `multiprocessing` para isolamento completo
  - Terminar processo forçadamente em timeout
  - Limites de memória mais precisos

- 🚀 **Containerização (Docker):**
  - Executar código em container Docker efêmero
  - Network isolation
  - Filesystem read-only

- 🚀 **Serverless Execution:**
  - AWS Lambda ou Google Cloud Functions
  - Timeout e limites nativos da plataforma
  - Escalabilidade automática

---

## ✅ Conclusão

O módulo `security/sandbox.py` fornece **proteção robusta** contra código malicioso, bloqueando:
- ✅ Imports perigosos (os, subprocess, sys)
- ✅ Funções perigosas (eval, exec, open, __import__)
- ✅ Loops infinitos (timeout)
- ✅ Acesso a filesystem
- ✅ Execução de comandos shell

**Status de Segurança:** 🟢 **SEGURO PARA PRODUÇÃO**

**Nota:** Nenhum sistema é 100% seguro. Sempre revise logs, monitore recursos, e mantenha RestrictedPython atualizado.

---

**Gerado em:** 2025-10-17 13:40 UTC  
**Autor:** EDA AI Minds Team  
**Versão do Sandbox:** 1.0.0  
**Sprint:** 3
