# Relatório de Funcionamento do Sistema Multiagente EDA AI Minds

## 1. Objetivo do Projeto
O sistema desenvolvido tem como objetivo realizar análise inteligente de dados CSV, especialmente voltado para detecção de fraudes em cartão de crédito, utilizando técnicas modernas de IA, multiagentes, LLMs e banco vetorial. O projeto foi desenhado para ser genérico, modular e escalável, podendo ser adaptado para outros tipos de dados e análises.

## 2. Principais Técnicas e Tecnologias Utilizadas
- **Python 3.10+**: Linguagem principal para backend e manipulação de dados
- **LangChain**: Orquestração de agentes LLM e integração com modelos de linguagem
- **Pandas**: Manipulação, limpeza e análise de dados CSV
- **Matplotlib + Seaborn + Plotly**: Sistema de visualização gráfica com 5 tipos de gráficos 🎨 **NOVO!**
- **Supabase/PostgreSQL**: Banco relacional e vetorial para armazenamento de embeddings
- **pgvector**: Extensão para busca vetorial eficiente
- **Embeddings & RAG**: Vetorização de dados e recuperação aumentada por geração
- **Chunking**: Divisão de dados em partes menores para processamento eficiente
- **Guardrails**: Controle de segurança, validação e limites de respostas
- **Logging estruturado**: Monitoramento e rastreabilidade

## 3. Estrutura do Sistema
- **src/agent/**: Agentes especializados (análise CSV, geração de embeddings, orquestrador)
- **src/data/**: Carregamento e processamento de dados
- **src/embeddings/**: Geração e manipulação de embeddings
- **src/vectorstore/**: Integração com Supabase
- **src/memory/**: Memória integrada para contexto dinâmico
- **src/tools/**: Guardrails, análise de código Python, visualização gráfica (GraphGenerator) 🎨 **NOVO!**
- **tests/**: Testes automatizados de integração e unidade
- **docs/**: Documentação técnica e relatórios
- **examples/**: Scripts demonstrativos (incluindo exemplos de visualização)

## 4. Instalação e Configuração
### Pré-requisitos
- Python 3.10 ou superior
- Git
- Conta e projeto no Supabase

### Passos de Instalação
1. Clone o repositório:
   ```powershell
   git clone https://github.com/roberto-fgv/eda-aiminds-back.git
   cd eda-aiminds-back
   ```
2. Crie e ative o ambiente virtual:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure as credenciais em `configs/.env` (baseado em `configs/.env.example`)
5. Execute as migrations do banco:
   ```powershell
   python scripts/run_migrations.py
   ```
6. Teste a conexão:
   ```powershell
   python check_db.py
   ```

## 5. Como Startar o Projeto
- Para iniciar o sistema multiagente:
   ```powershell
   python src/agent/orchestrator_agent.py
   ```
- Para rodar exemplos e testes:
   ```powershell
   python tests/test_workflow_completo.py
   ```

## 6. Funcionamento Geral
- O sistema carrega dados CSV, realiza limpeza e análise estatística com Pandas
- Gera embeddings dos dados e armazena no Supabase
- Utiliza agentes LLM via LangChain para responder perguntas, gerar código Python, criar gráficos e análises
- **Sistema de Visualização**: Gera automaticamente 5 tipos de gráficos (histogramas, scatter plots, boxplots, barras, heatmaps) com detecção automática de necessidade 🎨 **NOVO!**
- O agente orquestrador coordena os agentes especializados e integra as respostas
- Memória integrada permite manter contexto de conversas e análises
- Guardrails garantem segurança e qualidade das respostas

### Exemplo de Uso do Sistema de Visualização
```powershell
# Executar exemplos completos de visualização
python examples/exemplo_visualizacao_graficos.py
```
O sistema detecta automaticamente quando o usuário solicita gráficos usando palavras-chave como:
- "mostre um histograma"
- "gráfico de dispersão"
- "boxplot para outliers"
- "gráfico de barras"
- "heatmap de correlação"

## 7. Observações Finais
- O sistema é modular e pode ser expandido para outros tipos de dados
- Toda sessão de desenvolvimento é documentada em `docs/`
- Recomenda-se não versionar arquivos sensíveis ou grandes (ex: CSVs originais)
- Para dúvidas ou problemas, consulte os arquivos de documentação e exemplos em `docs/` e `examples/`

---
Relatório gerado por GitHub Copilot em 01/10/2025.
