# 📂 Estrutura do Projeto - EDA AI Minds Backend

**Data de Criação:** 2025-10-04  
**Versão:** 2.0.1  
**Status:** ✅ Organizado e Padronizado

---

## 🎯 Objetivo

Este documento descreve a estrutura completa do projeto após organização e padronização, seguindo as melhores práticas de desenvolvimento Python e arquitetura de sistemas multiagente.

---

## 📁 Estrutura de Diretórios

```
eda-aiminds-back/
│
├── 📄 README.md                    # Visão geral do projeto
├── 📄 CHANGELOG.md                 # Histórico de versões
├── 📄 LICENSE                      # Licença MIT
├── 📄 requirements.txt             # Dependências Python
│
├── 🚀 api_completa.py              # API principal (porta 8001)
├── 🚀 api_simple.py                # API de testes (porta 8000)
│
├── ⚙️ .gitignore                   # Arquivos ignorados pelo Git
├── 📁 .github/                     # Workflows e configs GitHub
│   └── copilot-instructions.md    # Instruções para GitHub Copilot
│
├── 📁 configs/                     # Configurações
│   ├── .env.example               # Template de variáveis de ambiente
│   ├── .env                       # Variáveis de ambiente (não versionado)
│   ├── requirements-api.txt       # Deps específicas para API
│   ├── requirements-dev.txt       # Deps de desenvolvimento
│   └── requirements-minimal.txt   # Deps mínimas
│
├── 📁 src/                         # Código fonte principal
│   ├── 📁 agent/                  # Agentes inteligentes
│   │   ├── base_agent.py          # Classe base para agentes
│   │   ├── orchestrator_agent.py  # Coordenador central
│   │   ├── csv_analysis_agent.py  # Análise de CSV
│   │   ├── rag_agent.py           # Busca vetorial RAG
│   │   └── embeddings_agent.py    # Geração de embeddings
│   │
│   ├── 📁 data/                   # Processamento de dados
│   │   ├── data_loader.py         # Carregamento de arquivos
│   │   ├── data_processor.py      # Processamento e limpeza
│   │   └── data_validator.py      # Validação de dados
│   │
│   ├── 📁 vectorstore/            # Banco vetorial
│   │   ├── supabase_client.py     # Cliente Supabase
│   │   └── embeddings_store.py    # Armazenamento de embeddings
│   │
│   ├── 📁 memory/                 # Sistema de memória
│   │   ├── memory_manager.py      # Gerenciador de memória
│   │   └── conversation_store.py  # Armazenamento de conversas
│   │
│   ├── 📁 api/                    # Integrações de API
│   │   ├── llm_router.py          # Roteamento inteligente de LLM
│   │   └── sonar_client.py        # Cliente Perplexity Sonar
│   │
│   ├── 📁 utils/                  # Utilitários
│   │   ├── logging_config.py      # Configuração de logs
│   │   ├── helpers.py             # Funções auxiliares
│   │   └── validators.py          # Validadores genéricos
│   │
│   └── settings.py                # Configurações centralizadas
│
├── 📁 data/                        # Arquivos de dados
│   ├── creditcard_test_500.csv    # Dataset de teste (500 linhas)
│   ├── demo_transacoes.csv        # Dataset de demonstração
│   └── README.md                  # Descrição dos datasets
│
├── 📁 examples/                    # Scripts de exemplo
│   ├── exemplo_orchestrator.py    # Uso do orquestrador
│   ├── exemplo_csv_interativo.py  # Análise interativa de CSV
│   ├── interface_interativa.py    # Interface de console
│   ├── demo_data_loading.py       # Demonstração de carregamento
│   └── README_CREDITCARD_ANALYSIS.md
│
├── 📁 tests/                       # Testes automatizados
│   ├── test_agent/                # Testes de agentes
│   ├── test_data/                 # Testes de processamento
│   ├── test_api/                  # Testes de API
│   └── conftest.py                # Configuração do pytest
│
├── 📁 scripts/                     # Scripts de utilidade
│   ├── run_migrations.py          # Executar migrations
│   ├── setup_database.py          # Setup do banco de dados
│   └── check_env.py               # Verificar variáveis de ambiente
│
├── 📁 migrations/                  # Migrations do banco
│   ├── 0000_create_embeddings.sql
│   ├── 0001_create_memory.sql
│   └── README.md
│
├── 📁 debug/                       # Arquivos de debug (não versionados)
│   └── (arquivos temporários de debug)
│
├── 📁 outputs/                     # Saídas geradas (não versionados)
│   └── histogramas/               # Gráficos gerados
│
└── 📁 docs/                        # Documentação
    ├── INDEX.md                   # Índice geral da documentação
    │
    ├── 📁 changelog/              # Histórico de mudanças
    │   ├── 2025-10-04_0300_correcao-erro-413.md
    │   ├── 2025-10-04_0315_aumentar-limite-csv.md
    │   └── ...
    │
    ├── 📁 troubleshooting/        # Resolução de problemas
    │   ├── 2025-10-04_0325_limitacoes-tecnicas.md
    │   ├── 2025-10-04_0330_correcao-timeout-30s.md
    │   └── 2025-10-04_0335_correcao-fraud-col.md
    │
    ├── 📁 guides/                 # Guias de uso
    │   ├── 2025-10-04_0310_configuracao-frontend.md
    │   ├── 2025-10-04_0315_guia-commits.md
    │   ├── 2025-10-04_0320_guia-recarregar-agentes.md
    │   ├── GUIA_USO_API_COMPLETA.md
    │   └── guia-desenvolvimento-memoria.md
    │
    ├── 📁 architecture/           # Arquitetura técnica
    │   ├── 2025-10-04_0305_status-sistema.md
    │   ├── CONFORMIDADE_ARQUITETURAL_IMPLEMENTADA.md
    │   ├── agente-orquestrador-documentacao.md
    │   ├── sistema-memoria-arquitetura.md
    │   └── resumo-implementacao-orquestrador.md
    │
    ├── 📁 archive/                # Documentos antigos
    │   ├── api_simple_backup_20251003_1942.py
    │   ├── api_completa_simples.py
    │   ├── README_BROKEN_BACKUP.md
    │   └── (outros documentos históricos)
    │
    ├── 📁 auditoria/              # Auditorias técnicas
    ├── 📁 diagnostico/            # Diagnósticos do sistema
    ├── 📁 langchain/              # Docs específicos LangChain
    ├── 📁 relatorio-professor/    # Relatórios acadêmicos
    │
    ├── API_DOCUMENTATION.md       # Referência completa da API
    ├── CONFIGURACAO_SUPABASE.md   # Setup do Supabase
    ├── DEPENDENCIES.md            # Documentação de dependências
    ├── relatorio-final.md         # Relatório final do projeto
    ├── analise-questao-02.md      # Análise de questão específica
    ├── PROMPT_LOVABLE_MVP.md      # Prompts para MVP
    ├── SOLUCAO_DETECCAO_FRAUDE.md # Solução de detecção de fraude
    └── ESTRUTURA_PROJETO.md       # Este arquivo
```

---

## 🎯 Diretórios Principais

### 📁 `src/` - Código Fonte

**Responsabilidade:** Todo o código de produção do sistema multiagente.

- **`agent/`**: Implementação dos agentes especializados
- **`data/`**: Carregamento, processamento e validação de dados
- **`vectorstore/`**: Integração com Supabase e pgvector
- **`memory/`**: Sistema de memória persistente
- **`api/`**: Integrações com APIs externas (LLMs, etc.)
- **`utils/`**: Utilitários compartilhados

### 📁 `docs/` - Documentação

**Responsabilidade:** Toda a documentação técnica, guias e histórico.

**Organização por categoria:**
- **`changelog/`**: Mudanças, correções e melhorias por versão
- **`troubleshooting/`**: Problemas conhecidos e soluções
- **`guides/`**: Tutoriais e guias de uso
- **`architecture/`**: Documentação de arquitetura e design
- **`archive/`**: Documentos históricos e backups

### 📁 `examples/` - Exemplos de Uso

**Responsabilidade:** Scripts de demonstração e tutoriais práticos.

Todos os arquivos são executáveis e demonstram funcionalidades específicas do sistema.

### 📁 `tests/` - Testes Automatizados

**Responsabilidade:** Testes unitários e de integração.

Estrutura espelha `src/` para facilitar navegação.

### 📁 `data/` - Datasets

**Responsabilidade:** Arquivos CSV de teste e demonstração.

⚠️ **Atenção:** Datasets grandes devem estar no `.gitignore`

### 📁 `configs/` - Configurações

**Responsabilidade:** Variáveis de ambiente e configurações de dependências.

⚠️ **Importante:** `.env` nunca deve ser versionado!

---

## 🚫 Arquivos Não Versionados

Conforme `.gitignore`, os seguintes arquivos/pastas **NÃO** são versionados:

- `__pycache__/` - Cache Python
- `.pytest_cache/` - Cache pytest
- `.venv/` - Ambiente virtual
- `.env` - Variáveis de ambiente
- `outputs/` - Saídas temporárias
- `debug/` - Arquivos de debug
- `*_backup.*` - Backups temporários
- `data/creditcard.csv` - Dataset grande original

---

## 📝 Arquivos na Raiz (Essenciais)

Apenas arquivos essenciais permanecem na raiz:

| Arquivo | Descrição |
|---------|-----------|
| `README.md` | Visão geral e quick start |
| `CHANGELOG.md` | Histórico de versões |
| `LICENSE` | Licença MIT |
| `requirements.txt` | Dependências Python |
| `api_completa.py` | API principal (8001) |
| `api_simple.py` | API de testes (8000) |
| `.gitignore` | Arquivos ignorados |

**Total:** 7 arquivos + pastas organizadas

---

## 🔄 Mudanças Recentes (2025-10-04)

### ✅ Movimentos Realizados

1. **Backups → `docs/archive/`**
   - `api_simple_backup_20251003_1942.py`
   - `README_BROKEN_BACKUP.md`
   - `api_completa_simples.py`

2. **Documentos → `docs/` ou subpastas**
   - `GUIA_USO_API_COMPLETA.md` → `docs/guides/`
   - `analise-questao-02.md` → `docs/`
   - `SOLUCAO_DETECCAO_FRAUDE.md` → `docs/`
   - `PROMPT_LOVABLE_MVP.md` → `docs/`

3. **Dados → `data/`**
   - `demo_transacoes.csv` → `data/`

4. **Scripts → `examples/`**
   - `interface_interativa.py` → `examples/`

5. **Limpeza de cache**
   - Removido `__pycache__/`
   - Removido `.pytest_cache/`
   - Removido `temp_scripts/` (vazio)

6. **`.gitignore` atualizado**
   - Adicionadas regras para outputs/
   - Adicionadas regras para backups
   - Organizado por categorias

---

## 📊 Estatísticas

### Antes da Organização
- **Arquivos na raiz:** ~20 arquivos
- **Documentação:** Desorganizada
- **Backups:** Na raiz
- **Cache:** Versionado

### Após Organização
- **Arquivos na raiz:** 7 arquivos essenciais
- **Documentação:** 4 categorias estruturadas
- **Backups:** Arquivados em `docs/archive/`
- **Cache:** Ignorado e removido

---

## 🎯 Boas Práticas Implementadas

### ✅ Estrutura Clara
- Cada pasta tem responsabilidade única
- Nomes descritivos e padronizados
- Hierarquia lógica de diretórios

### ✅ Separação de Responsabilidades
- Código (`src/`)
- Testes (`tests/`)
- Documentação (`docs/`)
- Exemplos (`examples/`)
- Configuração (`configs/`)

### ✅ Versionamento Controlado
- `.gitignore` completo e organizado
- Arquivos sensíveis protegidos (`.env`)
- Cache e temporários não versionados

### ✅ Documentação Organizada
- Categorização por tipo (changelog, guides, etc.)
- Índice central (`docs/INDEX.md`)
- Histórico preservado (`docs/archive/`)

### ✅ Manutenibilidade
- Estrutura espelhada entre `src/` e `tests/`
- README claro com quick start
- CHANGELOG com links para detalhes

---

## 🚀 Como Navegar no Projeto

### Para Desenvolvedores
1. **Iniciar:** Leia `README.md`
2. **Configurar:** Siga `docs/guides/`
3. **Código:** Explore `src/` por funcionalidade
4. **Exemplos:** Execute scripts em `examples/`
5. **Testes:** Rode `pytest tests/`

### Para Usuários
1. **Quick Start:** `README.md`
2. **API Docs:** `docs/API_DOCUMENTATION.md`
3. **Problemas:** `docs/troubleshooting/`
4. **Mudanças:** `CHANGELOG.md`

### Para Contribuidores
1. **Estrutura:** Este arquivo (`ESTRUTURA_PROJETO.md`)
2. **Commits:** `docs/guides/2025-10-04_0315_guia-commits.md`
3. **Arquitetura:** `docs/architecture/`

---

## 📋 Checklist de Manutenção

Ao adicionar novos arquivos, verifique:

- [ ] Arquivo está na pasta correta?
- [ ] Nome segue o padrão (snake_case para Python)?
- [ ] Documentação foi criada/atualizada?
- [ ] `.gitignore` cobre arquivos sensíveis?
- [ ] README menciona nova funcionalidade?
- [ ] CHANGELOG foi atualizado?
- [ ] Testes foram criados em `tests/`?

---

## 🔗 Links Úteis

- **Índice Geral:** [docs/INDEX.md](INDEX.md)
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **API Docs:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **README Principal:** [README.md](../README.md)
- **Conformidade:** [architecture/CONFORMIDADE_ARQUITETURAL_IMPLEMENTADA.md](architecture/CONFORMIDADE_ARQUITETURAL_IMPLEMENTADA.md)

---

## 📝 Observações Finais

Esta estrutura foi desenhada para:

1. **Escalabilidade** - Fácil adicionar novos agentes e funcionalidades
2. **Manutenibilidade** - Código organizado e bem documentado
3. **Colaboração** - Estrutura clara para trabalho em equipe
4. **Profissionalismo** - Segue padrões da indústria

**Última atualização:** 2025-10-04  
**Responsável:** Equipe EDA AI Minds  
**Versão do projeto:** 2.0.1
