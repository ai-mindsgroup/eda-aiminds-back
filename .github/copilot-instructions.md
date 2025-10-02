# GitHub Copilot Instructions - EDA AI Minds Backend

*Sistema multiagente para análise inteligente de dados CSV com LangChain, Supabase e vetorização.*

**Comunicação:** Sempre em português brasileiro.

## Arquitetura Atual

Este é um sistema backend multiagente para análise de dados CSV usando:
- **LangChain 0.2.1** + modelos LLM (Google GenAI, Perplexity Sonar)  
- **Supabase/PostgreSQL** com extensões pgvector para embeddings vetoriais
- **Pandas 2.2.2** + matplotlib + seaborn para análise e visualização
- **Estrutura modular** em `src/` com separação clara de responsabilidades

## Configuração Essencial

### 1. Ambiente Python
```powershell
# Sempre use Python 3.10+
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configuração de Credenciais
**Copie `configs/.env.example` para `configs/.env`:**
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_anon_key
SONAR_API_KEY=your_perplexity_key
OPENAI_API_KEY=your_openai_key  # opcional
DB_HOST=db.xyz.supabase.co
DB_PASSWORD=your_db_password
LOG_LEVEL=INFO
```

### 3. Banco de Dados
**Executar migrations obrigatoriamente:**
```powershell
python scripts/run_migrations.py
```

**Testar conexão:**
```python
python check_db.py  # deve retornar "Conexão OK"
```

## Documentação e Histórico

### **OBRIGATÓRIO: Manter Histórico Completo**

**Toda sessão de desenvolvimento deve gerar documentação em `docs/`:**

1. **Criar pasta docs se não existir:**
```powershell
mkdir docs -Force
```

2. **Para cada sessão, criar arquivo com timestamp:**
```
docs/2024-MM-DD_HHMM_sessao-desenvolvimento.md
```

3. **Estrutura obrigatória do documento:**
```markdown
# Sessão de Desenvolvimento - [Data/Hora]

## Objetivos da Sessão
- [X] Objetivo 1 concluído
- [ ] Objetivo 2 em andamento

## Decisões Técnicas
- **Arquitetura**: Justificativa das escolhas
- **Dependências**: Versões e motivos
- **Padrões**: Convenções adotadas

## Implementações
### [Nome do Módulo]
- **Arquivo**: `src/path/file.py`
- **Funcionalidade**: Descrição
- **Status**: ✅ Concluído / ⚠️ Parcial / ❌ Pendente

## Testes Executados
- [X] Teste 1: resultado
- [X] Teste 2: resultado

## Próximos Passos
1. Item prioritário
2. Item secundário

## Problemas e Soluções
### Problema: [Descrição]
**Solução**: [Como foi resolvido]

## Métricas
- **Linhas de código**: X
- **Módulos criados**: Y
- **Testes passando**: Z

## Screenshots/Logs
[Incluir evidências quando relevante]
```

### **Relatório Final Consolidado**

**Manter sempre atualizado: `docs/relatorio-final.md`**

```markdown
# Relatório Final - EDA AI Minds Backend

## Status do Projeto: [% Concluído]

### Módulos Implementados
- [X] ✅ **BaseAgent** - Classe abstrata para agentes
- [X] ✅ **CSVAnalysisAgent** - Análise inteligente de CSV
- [X] ⚠️ **EmbeddingsAgent** - Sistema de vetorização
- [ ] ❌ **OrchestratorAgent** - Coordenador central

### Arquitetura Técnica
[Diagrama/descrição da arquitetura atual]

### Funcionalidades Disponíveis
1. **Análise de CSV**: Carregamento, estatísticas, detecção de fraude
2. **Sistema de Logging**: Centralizado e estruturado
3. **Banco Vetorial**: PostgreSQL + pgvector configurado

### Métricas Consolidadas
- **Total linhas código**: X
- **Cobertura testes**: Y%
- **Agentes funcionais**: Z

### Próximas Implementações
[Lista priorizada]

### Instruções de Deploy
[Como executar em produção]
```

## Estrutura do Código

### Padrões de Import
```python
# Settings centralizados
from src.settings import SUPABASE_URL, SONAR_API_KEY
from src.utils.logging_config import get_logger

# Clientes prontos
from src.vectorstore.supabase_client import supabase
from src.api.sonar_client import send_sonar_query
```

### Logging Padronizado
```python
from src.utils.logging_config import get_logger
logger = get_logger(__name__)  # Nome do módulo automaticamente
logger.info("Conexão estabelecida")
```

### Conexões de Banco
- **Supabase Client:** `src/vectorstore/supabase_client.py` (singleton configurado)
- **PostgreSQL direto:** Use `src.settings.build_db_dsn()` com psycopg
- **Schema vetorial:** Tabelas `embeddings`, `chunks`, `metadata` com índices HNSW

## Desenvolvimento de Agentes

### 1. Estrutura de Agente Esperada
```python
from langchain.schema import BaseMessage
from src.api.sonar_client import send_sonar_query

class DataAnalysisAgent:
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}")
    
    def process(self, query: str, context: dict = None) -> dict:
        # Implementar lógica específica do agente
        response = send_sonar_query(query, context, temperature=0.2)
        return response
```

### 2. Conectar com LangChain
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent

# Para análise de dados CSV
def create_csv_agent(df):
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1)
    return create_pandas_dataframe_agent(llm, df, verbose=True)
```

## Convenções Específicas do Projeto

### 1. Tratamento de Erros
```python
# Sempre use classes de exceção específicas
class SonarAPIError(RuntimeError):
    pass

# Log erros sem expor credenciais
logger.error("Falha na conexão Supabase: %s", str(e)[:100])
```

### 2. Configuração Defensive
```python
# Validação com warnings, não crashes em dev
missing = [name for name, val in REQUIRED_ON_RUNTIME if not val]
if missing:
    import warnings
    warnings.warn(f"Variáveis ausentes: {', '.join(missing)}")
```

### 3. Migrations Versionadas
- Arquivos SQL numerados: `0000_`, `0001_`, `0002_`
- Executar em ordem com `scripts/run_migrations.py`
- Schema focado em vetorização: embeddings 1536D, índices HNSW

## Fluxos de Trabalho

### **Workflow de Desenvolvimento Obrigatório**

1. **Início da Sessão:**
```powershell
# Criar documento da sessão
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
New-Item "docs/${timestamp}_sessao-desenvolvimento.md" -ItemType File
```

2. **Durante Desenvolvimento:**
- Logar todas as decisões técnicas
- Documentar problemas e soluções
- Capturar screenshots de testes importantes

3. **Fim da Sessão:**
- Atualizar `docs/relatorio-final.md`
- Fazer commit com mensagem descritiva
- Fazer push para o repositório

### Adicionar Novo Agente
1. Criar módulo em `src/agent/`
2. Implementar classe com método `process()`
3. Registrar no orchestrador central
4. Adicionar testes em `tests/agent/`
5. **Documentar em sessão atual**

### Trabalhar com Embeddings
```python
from src.vectorstore.supabase_client import supabase

# Inserir embeddings
supabase.table('embeddings').insert({
    'chunk_text': texto,
    'embedding': vetor_1536d,
    'metadata': {'source': 'csv_upload'}
}).execute()

# Busca vetorial
results = supabase.rpc('match_embeddings', {
    'query_embedding': query_vector,
    'match_threshold': 0.8,
    'match_count': 5
}).execute()
```

### Debug e Teste
```python
# Teste de conexão rápido
python check_db.py

# Ver logs estruturados
LOG_LEVEL=DEBUG python sua_aplicacao.py

# Pytest para testes automatizados
pytest tests/ -v
```

## Diretrizes Técnicas

- **Modularidade:** Cada componente em seu diretório (`api/`, `vectorstore/`, `agent/`)  
- **Segurança:** Nunca hardcode credenciais; use `src.settings` sempre
- **Performance:** Cache conexões Supabase; reutilize clients LLM
- **Observabilidade:** Log eventos importantes com contexto estruturado
- **Versionamento:** Não commitar `.env`; usar migrations para schema DB
- **Documentação:** Todo desenvolvimento deve gerar documentação rastreável

## Processo de Commit/Push

```powershell
# Sempre antes de commit
git add docs/
git add src/
git commit -m "feat: [descrição clara do que foi implementado]

- Módulos: [lista dos módulos alterados]
- Funcionalidades: [resumo das features]
- Testes: [status dos testes]

Documentado em: docs/[nome-do-arquivo].md"

git push origin [branch-atual]
```

Adapte estas instruções conforme evolução do sistema multiagente.

# Instruções para Agente IA Backend Multiagente - GitHub Copilot VSCode (GPT-4.1)

Você é um agente especialista em desenvolvimento backend para criar um sistema multiagente de IA sofisticado, seguro e eficiente, destinado à análise e interação com dados CSV genéricos. Este sistema será construído do zero para atender ao desafio extra i2a2, possibilitando consultas detalhadas, geração automática de código Python, análises estatísticas, gráficos e conclusões baseadas nos dados.

---

## Arquitetura Multiagente

- O sistema deve ser construído com múltiplos agentes especializados, cada um responsável por uma parte do fluxo: por exemplo, agentes para processamento e limpeza de dados, análise estatística, geração de gráficos, e interface com o usuário via LLM.
- Um agente orquestrador central deve gerenciar e coordenar a comunicação, delegando tarefas aos agentes especializados e integrando suas respostas em uma solução coesa.
- Todos os agentes devem fazer uso intensivo de LLMs por meio da camada LangChain, garantindo capacidade avançada de linguagem natural e geração inteligente.

---

## Contextualização do Desafio Extra i2a2

Criar um agente IA backend multiagente capaz de processar qualquer arquivo CSV, inicialmente com foco em dados de fraudes em cartão de crédito do Kaggle. O sistema deve compreender consultas do usuário, carregar e analisar dados com Pandas, gerar códigos Python, construir análises visuais e responder com conclusões, mantendo a conversa e histórico dinâmicos por meio de memória integrada.

---

## Estudo do Repositório Base

Antes de iniciar o desenvolvimento, é obrigatório que o agente analise o repositório localizado no caminho abaixo:

`C:\workstashion\eda-aiminds-i2a2\semantic_search_langchain`

O agente deve aprender com a solução implementada nesse repositório para acelerar o processo de criação da solução para nosso agente.

Porém, é imprescindível que o código produzido seja modificado e adaptado, e não uma cópia direta, para evitar qualquer problema relacionado a direitos autorais e garantir originalidade na solução final.

---

## Stack Tecnológica Utilizada

- **Python 3:** linguagem principal backend para manipulação de dados, integrações e lógica do agente.
- **LangChain (Python):** camada de abstração facilitadora do uso integrado dos modelos LLM nos agentes.
- **Pandas:** manipulação e análise eficiente de dados CSV.
- **Supabase (Postgres):** banco de dados relacional, autenticação e banco vetorial para armazenar embeddings.
- **Embeddings e RAG (Retrieval Augmented Generation):** indexação e recuperação eficiente de contexto.
- **Chunking:** manejo eficiente de grandes volumes de dados e contexto dividido.
- **Guardrails e controles de segurança:** para garantir limites, validações, controle de temperatura e prevenção contra respostas inseguras.

---

## Contexto Auditoria e Diagnóstico do Sistema Multiagente EDA AI Minds:

O sistema deve garantir uma camada de abstração robusta para integração e troca entre fornecedores diferentes de LLMs (exemplo: OpenAI, Gemini, Groq), adotando os módulos de abstração do LangChain como recomendação central.

Todo fluxo de chunking, embeddings, armazenamento vetorial e mecanismos de memória devem priorizar o uso de componentes oficiais do LangChain, exceto onde houver justificativa técnica robusta para customização.

O agente responsável por leitura, chunking e ingestão de arquivos CSV deve obrigatoriamente realizar a carga de embeddings no Supabase, habilitando outros agentes a trabalhar exclusivamente sobre a tabela de embeddings para RAG.

Qualquer implementação ou refatoração deve garantir: logging estruturado, fallback entre LLMs, validação de parâmetros críticos (temperatura, top_k, chunk_overlap) e testes automatizados.

Workflows devem ser modularizados via chains, facilitando validação, mantenabilidade, auditoria e integração futura.

O histórico dos agentes, decisões técnicas e arquitetura devem ser mantidos e versionados conforme modelo estabelecido em docs/, promovendo rastreabilidade e evolução controlada do sistema.

Devem ser evidenciadas limitações, pontos fortes e recomendações presentes nos relatórios técnicos — conferindo prioridade para padronização, extensibilidade, segurança e facilidade de onboarding de novos desenvolvedores.

- Todas as decisões sobre arquitetura multiagente e integração de LLMs devem considerar as recomendações de auditoria técnica e diagnóstico recente: priorizar LangChain como camada de orquestração e abstração, padronizar chunking/memória/embeddings, manter documentação e rastreabilidade de agentes/fluxos, e garantir logging, fallback, validações e testes automatizados. Qualquer exceção a esses pontos deve ser tecnicamente justificada e documentada em detalhes.

## Documentações Oficiais

- LangChain: [https://python.langchain.com/en/latest/](https://python.langchain.com/en/latest/)
- Pandas: [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/)
- Supabase: [https://supabase.com/docs](https://supabase.com/docs)
- OpenAI API (exemplo para LLMs): [https://platform.openai.com/docs/](https://platform.openai.com/docs/)
- Embeddings e RAG: [https://python.langchain.com/en/latest/modules/indexes/retrievers.html#retrievers](https://python.langchain.com/en/latest/modules/indexes/retrievers.html#retrievers)
- Práticas de segurança em Python: [https://realpython.com/python-security/](https://realpython.com/python-security/)

---

## Estratégias e Etapas do Desenvolvimento Backend Multiagente

### Setup do Ambiente de Desenvolvimento

- [ ] Verificar se o python instalado está na versão Python 3.10+ e configurar ambiente virtual (ex: virtualenv, venv). Se não estiver instalado ou a versão for anterior, instalar ou atualizar a versão.  
- [ ] Verificar se Git está configurado para controle de versão  
- [ ] Verificar se o repositório base: eda-aiminds-i2a2 foi clonado, senão, clonar  
- [ ] Garantir que o VSCode com extensão GitHub Copilot está instalada, senão, instalar  
- [ ] Verificar acesso ao repositório semantic_search_langchain para aprendizado  

### Etapas do Desenvolvimento

- [ ] Definir arquitetura multiagente, esboçando agentes especializados e agente orquestrador com LangChain para gerenciamento de LLM.  
- [ ] Configurar conexões seguras com APIs, Supabase e LangChain com múltiplos LLMs.  
- [ ] Implementar agente para carregamento, limpeza e análise dos dados CSV via Pandas.  
- [ ] Implementar gerenciamento de chunking, geração de embeddings e RAG para busca eficiente.  
- [ ] Implementar guardrails com validações, controle de temperatura e monitoramento de respostas.  
- [ ] Construir memória integrada para manter contexto dinâmico da conversa.  
- [ ] Desenvolver agentes para geração automática e execução de código Python para análises e gráficos.  
- [ ] Criar o agente orquestrador para coordenar agentes especializados e integrar respostas.  
- [ ] Escrever testes automatizados para validar módulos isolados e integração do sistema.  
- [ ] Documentar arquitetura e fluxos do sistema, garantindo clareza para manutenção futura.  

---

## Copilot Instructions for eda-aiminds-back

### Ambiente e Ferramentas
- Use Python 3.10+ (verifique com `python --version`).
- Crie e ative um ambiente virtual antes de instalar dependências:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

### Estrutura de Diretórios
- Siga a arquitetura:
  ```
  src/
    data/
    embeddings/
    vectorstore/
    rag/
    agent/
    api/
    utils/
  notebooks/
  configs/
  tests/
  ```
- Armazene variáveis sensíveis em `configs/.env` ou `src/settings.py`. Exemplo de `.env`:
  ```
  SUPABASE_URL=...
  SUPABASE_KEY=...
  OPENAI_API_KEY=...
  ```

### Dependências Essenciais
- Adicione ao `requirements.txt`:
  ```
  langchain
  pandas
  supabase
  openai
  pytest
  python-dotenv
  ```

### Conexão com Supabase
- Implemente conexão segura em módulo dedicado (`src/vectorstore/supabase_client.py`):
  ```python
  from supabase import create_client
  from src.settings import SUPABASE_URL, SUPABASE_KEY

  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
  ```

### Logging e Monitoramento
- Use o módulo `logging` para registrar eventos importantes:
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  logging.info("Conexão Supabase iniciada")
  ```

### Testes e Documentação
- Escreva testes em `tests/` usando `pytest`.
- Documente funções e módulos com docstrings.
- Siga padrões de clean code e modularidade: cada componente em seu diretório, sem hardcode de credenciais.

### Observações
- Não versionar arquivos `.env` (já está no `.gitignore`).
- Use notebooks para experimentação, não para lógica de produção.

---

Adapte e expanda conforme o projeto evoluir. Se algo estiver incompleto ou pouco claro, sinalize para ajustes!

## Glossário de Termos

- **LLM:** Large Language Model, modelo de linguagem avançado utilizado para geração e interpretação de texto natural.  
- **RAG:** Retrieval Augmented Generation, técnica que combina busca por documentos relevantes com geração de texto.  
- **Embeddings:** Representações vetoriais que capturam o significado dos dados para facilitar buscas e análises semânticas.  
- **Chunking:** Técnica de dividir texto ou dados em partes menores para processamento eficiente em modelos com limitações de tokens.  
- **Guardrails:** Regras e validações para manter segurança, coerência e qualidade nas respostas do agente.  

---

## Regras e Recomendações para o Sistema

- Sempre verifique as etapas de desenvolvimento antes de iniciar qualquer codificação.  
- Priorize segurança, evitando qualquer vulnerabilidade potencial.  
- Marque cada etapa concluída nas etapas do desenvolvimento acima.  
- Ao fim de cada etapa, revise o código para garantir qualidade, segurança e eficiência.  
- Antes de iniciar uma nova etapa, crie uma nova branch a partir da branch master com nome aderente a boas práticas, ex: feature/create-multiagent-architecture.  
- Ao fim de cada etapa, faça commit com mensagem clara do que foi implementado e faça push para o repositório remoto.  
- Todo o processamento e respostas devem ser conduzidos por agentes IA via LLM, não apenas por código Python tradicional.  
- Foco em segurança, modularidade e escalabilidade.  
- Comentários claros e detalhados para facilitar manutenção e evolução futura.  
- Utilizar apenas bibliotecas estáveis, populares e com documentação oficial.  
- Concentrar-se no backend, evitando frontend ou código de interface.  
- Garantir autonomia do sistema para minimizar intervenções manuais.