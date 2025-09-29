# Scripts de Setup e Manutenção

Este diretório contém scripts para automatizar a configuração e manutenção do sistema EDA AI Minds Backend.

## 📋 Scripts Disponíveis

### 🚀 Setup Completo

#### `setup_environment.py`
**Setup automático completo do ambiente de desenvolvimento**

```powershell
python scripts/setup_environment.py
```

**O que faz:**
- ✅ Verifica Python 3.10+
- ✅ Atualiza pip
- ✅ Instala todas as dependências (`requirements.txt`)
- ✅ Copia `.env.example` → `.env`
- ✅ Executa migrations do banco
- ✅ Valida instalação completa

---

### 🗄️ Setup de Banco de Dados

#### `setup_database.py`
**Configuração específica do banco de dados**

```powershell
python scripts/setup_database.py
```

**O que faz:**
- ✅ Testa conexão com PostgreSQL/Supabase
- ✅ Aplica todas as migrations
- ✅ Verifica schema e extensões
- ✅ Valida funcionalidades do banco

#### `run_migrations.py`
**Aplica migrations SQL na ordem correta**

```powershell
python scripts/run_migrations.py
```

**O que faz:**
- ✅ Conecta ao banco usando configs/.env
- ✅ Executa arquivos SQL em `migrations/` em ordem
- ✅ Configura pgvector e schema vetorial

---

### 🔍 Validação e Diagnóstico

#### `validate_dependencies.py`
**Valida se todas as dependências estão funcionando**

```powershell
python scripts/validate_dependencies.py
```

**O que faz:**
- ✅ Verifica Python 3.10+
- ✅ Testa importação de todos os pacotes
- ✅ Mostra versões instaladas
- ✅ Gera relatório de saúde do sistema
- ✅ Taxa de sucesso da instalação

---

## 🎯 Fluxo Recomendado

### Para Primeira Instalação:

```powershell
# 1. Clonar repositório
git clone <repo-url>
cd eda-aiminds-i2a2-rb

# 2. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# 3. Setup completo automático
python scripts/setup_environment.py

# 4. Configurar chaves de API em configs/.env
# GROQ_API_KEY=seu_groq_key
# SUPABASE_URL=sua_supabase_url
# SUPABASE_KEY=sua_supabase_key

# 5. Validar tudo
python scripts/validate_dependencies.py

# 6. Testar sistema
python examples/teste_groq_completo.py
```

### Para Problemas de Banco:

```powershell
# Setup específico de banco
python scripts/setup_database.py

# Ou apenas migrations
python scripts/run_migrations.py

# Testar conexão
python check_db.py
```

### Para Verificar Saúde do Sistema:

```powershell
# Diagnóstico completo
python scripts/validate_dependencies.py

# Deve mostrar taxa de sucesso > 80%
```

---

## 📁 Estrutura de Migrations

```
migrations/
├── 0000_enable_pgcrypto.sql      # Habilita extensão de criptografia
├── 0001_init_pgvector.sql        # Instala pgvector
├── 0002_schema.sql               # Schema principal
├── 0003_fix_embedding_dimensions.sql  # Correções de dimensões
├── 0003_update_metadata_schema.sql    # Schema de metadados
├── 0003_vector_search_function.sql    # Função de busca vetorial
└── 0004_fix_metadata_key_constraint.sql  # Constraints
```

**Migrations são executadas em ordem alfabética/numérica.**

---

## 🔧 Solução de Problemas

### ❌ "Python 3.10+ é necessário"
```powershell
# Instalar Python mais recente
# Recriar ambiente virtual
```

### ❌ "GROQ_API_KEY não configurado"
```powershell
# Editar configs/.env
echo "GROQ_API_KEY=sua_chave_aqui" >> configs/.env
```

### ❌ "Erro de conexão com banco"
```powershell
# Verificar configs/.env
# DB_HOST, DB_PASSWORD, SUPABASE_URL, SUPABASE_KEY
python scripts/setup_database.py
```

### ❌ "Dependências faltando"
```powershell
# Reinstalar tudo
pip install -r requirements.txt
python scripts/validate_dependencies.py
```

---

## 📈 Métricas de Sucesso

- **Taxa de validação > 80%**: Sistema funcional
- **Taxa de validação > 95%**: Sistema completo
- **Migrations aplicadas**: Banco configurado
- **Groq API respondendo**: LLM funcional

Execute `python scripts/validate_dependencies.py` para ver as métricas atuais!