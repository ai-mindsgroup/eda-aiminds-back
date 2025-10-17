# Auditoria Completa - EDA AI Minds Backend

## Objetivos da Sessão
- [X] Auditar todo o workspace em busca de referências hardcoded a colunas, nomes de datasets, variáveis ou estruturas específicas (ex: V1-V28, Time, Amount, Class, creditcard.csv, features, etc).
- [X] Documentar todos os achados, classificando como dinâmico ou hardcoded.
- [X] Recomendar correções e registrar status de cada trecho.

## Metodologia
- Busca automatizada por termos: V1, V28, Time, Amount, Class, colunas, variáveis, columns, features, creditcard, fraud, chunk_text, header, dataset, hardcode, csv antigo, csv atual, numéricas, categóricas.
- Análise dos scripts, agentes, prompts e fluxos de ingestão, síntese e resposta.
- Classificação dos achados: Dinâmico (adaptável ao dataset carregado) ou Hardcoded (fixo, dependente de estrutura específica).

## Achados

### 1. src/agent/rag_agent.py
- Detecção de colunas: Dinâmico (parse do header do CSV, identifica colunas presentes no arquivo carregado).
- Tipologia e estrutura: Dinâmico (detecta colunas numéricas, categóricas e temporais via Pandas).
- Análise de chunks: Dinâmico (gera chunks com base nas colunas do dataset ativo).

### 2. src/agent/rag_synthesis_agent.py
- Prompt e fallback: Corrigido (antes hardcoded, agora dinâmico, lista apenas colunas presentes no dataset atual).

### 3. api_completa.py
- Análise de fraude: Parcialmente dinâmico (busca por colunas com nomes 'fraud', 'class', 'amount', 'time' de forma genérica, mas depende de nomenclatura padrão; não é hardcoded, mas pode falhar em datasets com nomes diferentes).
- Análise de colunas numéricas/categóricas: Dinâmico (usa Pandas para detectar tipos).

### 4. add_chunks_oficial.py, add_metadata_chunks.py, add_metadata_chunks_safe.py
- Referências explícitas a 'creditcard.csv' e 'creditcard_full': Hardcoded (scripts voltados para dataset específico, não genéricos).
- Geração de chunks: Hardcoded (nome do dataset e caminho fixos).

### 5. .github/copilot-instructions.md
- Instruções e exemplos: Referências ao dataset de cartão de crédito e colunas típicas, mas apenas para documentação.

## Recomendações
- Refatorar scripts de ingestão (add_chunks_oficial.py, add_metadata_chunks.py, add_metadata_chunks_safe.py) para aceitar qualquer arquivo CSV e nome de dataset, tornando-os genéricos.
- Validar se prompts e fluxos de análise na API lidam corretamente com datasets que não possuem colunas padrão ('fraud', 'class', etc). Adicionar fallback dinâmico.
- Manter agentes de síntese e análise sempre dinâmicos, extraindo colunas do dataset carregado.
- Documentar toda refatoração e registrar status dos trechos corrigidos.

## Status dos Trechos
| Arquivo                        | Trecho/Referência         | Status      | Observação |
|-------------------------------|---------------------------|-------------|------------|
| src/agent/rag_agent.py        | Detecção de colunas       | Dinâmico    | OK         |
| src/agent/rag_synthesis_agent.py | Prompt/fallback         | Dinâmico    | Corrigido  |
| api_completa.py               | Análise de fraude         | Parcial     | Melhorar   |
| add_chunks_oficial.py         | creditcard.csv            | Hardcoded   | Refatorar  |
| add_metadata_chunks.py        | creditcard.csv            | Hardcoded   | Refatorar  |
| add_metadata_chunks_safe.py   | creditcard.csv            | Hardcoded   | Refatorar  |

## Plano de Correção
1. Refatorar scripts de ingestão para aceitar qualquer arquivo/nome de dataset.
2. Revisar análise de fraude na API para fallback dinâmico.
3. Validar agentes em datasets sem colunas padrão.
4. Documentar todas as correções em docs/.

## Logs e Evidências
- Auditoria realizada em 15/10/2025.
- Logs de busca e análise disponíveis mediante solicitação.

---
