# 🛠️ Tools - Scripts e Utilitários

Esta pasta contém scripts utilitários, ferramentas de desenvolvimento e testes do projeto EDA AI Minds Backend.

## 📁 Organização

### 🧪 Testes e Verificação
- `test_api.py` - Teste básico da API
- `test_api_production.ps1` - Teste de produção
- `test_api_upload.py` - Teste de upload de arquivos
- `test_gemini.py` - Teste do Google Gemini

### 🔧 Verificação de Sistema
- `check_api_dependencies.py` - Verifica dependências da API
- `check_api_quick.py` - Verificação rápida da API
- `check_db.py` - Verifica conexão com banco
- `check_full_chunk.py` - Verifica sistema de chunks

### 🐛 Debug e Depuração
- `debug_data_check.py` - Debug de dados
- `debug_enrichment_direct.py` - Debug de enriquecimento
- `debug_supabase_data.py` - Debug do Supabase

### 🚀 Inicialização
- `start_api.py` - Script de inicialização da API
- `start_api_simple.py` - Script API simples
- `start_api_completa.ps1` - PowerShell para API completa
- `start_api_verbose.ps1` - Inicialização com logs verbose
- `iniciar_api.ps1` - Script de inicialização alternativo

### 📊 Análise e Demonstração
- `analise_creditcard_dataset.py` - Análise do dataset de cartão
- `demonstracao_fluxo_supabase.py` - Demo do fluxo Supabase
- `demo_sistema_corrigido.py` - Demo do sistema corrigido

### 🧹 Utilitários
- `clear_embeddings.py` - Limpa embeddings do banco
- `resposta_perguntas_usuario.py` - Sistema de perguntas
- `interface_interativa.py` - Interface interativa

## 🚀 Como Usar

### Verificação Rápida
```bash
# Verificar se a API está funcionando
python tools/check_api_quick.py

# Testar conexão com banco
python tools/check_db.py

# Verificar dependências
python tools/check_api_dependencies.py
```

### Inicialização
```bash
# API simples
python tools/start_api_simple.py

# API completa
python tools/start_api.py

# PowerShell (Windows)
./tools/start_api_completa.ps1
```

### Testes
```bash
# Teste básico da API
python tools/test_api.py

# Teste de upload
python tools/test_api_upload.py

# Teste do Gemini
python tools/test_gemini.py
```

### Debug
```bash
# Debug geral
python tools/debug_data_check.py

# Debug Supabase
python tools/debug_supabase_data.py
```

### Análise
```bash
# Análise de dataset
python tools/analise_creditcard_dataset.py

# Interface interativa
python tools/interface_interativa.py
```

## 📋 Dependências

Os scripts nesta pasta assumem que você tem:
- Python 3.10+ configurado
- Ambiente virtual ativado
- Dependências do projeto instaladas
- Variáveis de ambiente configuradas

## ⚠️ Nota

Alguns scripts podem requerer configurações específicas ou dados de exemplo. Consulte a [documentação principal](../documentation/README.md) para mais detalhes.

---

**💡 Dica**: Use `python -h` ou `--help` em qualquer script para ver opções disponíveis.