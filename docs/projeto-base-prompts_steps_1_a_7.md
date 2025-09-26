## Prompt 1: Setup Inicial do Ambiente e Projeto

python
"""
Objetivo: Configurar o ambiente inicial do projeto backend para agente IA multiagente usando Python 3.10+, LangChain, Pandas e Supabase.

- Verificar versão do Python e presença de ambiente virtual; se necessário, configurar virtualenv.
- Criar estrutura básica de diretórios conforme arquitetura definida.
- Criar arquivos iniciais como requirements.txt com dependências essenciais: langchain, pandas, supabase-py, openai, pytest.
- Criar arquivo de configuração (.env ou settings.py) para armazenar variáveis sensíveis (chaves API).
- Implementar setup inicial para conexão segura com Supabase (Postgres e banco vetorial).
- Registrar logs básicos para debug e monitoramento.

Siga as melhores práticas de modularidade, segurança, documentação e clean code.
"""


## Prompt 2: Definir a Arquitetura Multiagente (esqueleto)
python
"""
Objetivo: Criar o esqueleto da arquitetura multiagente backend com agentes especialistas e agente orquestrador, utilizando LangChain para LLM.

- Definir classes ou módulos para agentes especializados:
  - Agente para processamento e limpeza de dados CSV.
  - Agente para análise estatística e geração de insights.
  - Agente para gráficos e visualização.
  - Agente de interface de linguagem natural (LLM).
- Criar classe AgenteOrquestrador que gerencia e coordena a comunicação e delegação de tarefas.
- Esboçar interface de comunicação entre agentes (mensagens, chamadas de método, troca de contexto).
- Garantir que todos os agentes utilizem LangChain para interagir com LLMs.
- Documentar a arquitetura e responsabilidades.

Implemente de forma que o código seja facilmente extensível e testável.
"""


## Prompt 3: Implementar Agente para Carregamento e Limpeza de Dados CSV
python
"""
Objetivo: Implementar um agente especializado para carregar arquivos CSV genéricos e realizar limpeza básica dos dados usando Pandas.

- Função para receber caminho do arquivo CSV.
- Ler CSV e validar formato e integridade.
- Tratar valores nulos, duplicados e tipos de dados incorretos.
- Documentar os passos de limpeza.
- Preparar dados para análise subsequente por outros agentes.

O agente deve ser confiável, eficiente e fácil de integrar com a arquitetura multiagente.
"""


## Prompt 4: Gerenciamento de Contexto via Chunking e Embeddings
python
"""
Objetivo: Implementar mecanismos para dividir dados e textos em chunks apropriados e gerar embeddings para recuperação eficiente.

- Desenvolver função para segmentar datasets ou textos longos em partes menores (chunks).
- Utilizar LangChain para gerar embeddings vetoriais para cada chunk.
- Armazenar embeddings no banco vetorial via Supabase.
- Garantir compatibilidade do gerenciamento de contexto com limites de tokens de LLMs.
- Preparar infra para query e recuperação dos chunks relevantes conforme contexto da conversa.

Documente a abordagem e testes básicos para validação.
"""


## Prompt 5: Implementar Guardrails e Controle de Temperatura no Agente
python
"""
Objetivo: Introduzir validações, limites e parâmetros de controle, incluindo controle de temperatura no uso de LLMs.

- Definir guardrails para sanitização de entradas e validação de outputs.
- Implementar mecanismos para controlar parâmetros como temperatura, max tokens, top-p.
- Monitorar consistência e segurança das respostas geradas.
- Criar logs de auditoria para respostas do agente.
- Permitir ajustes dinâmicos nos controles conforme demanda.

Documente e teste esses controles para assegurar robustez e segurança.
"""


## Prompt 6: Desenvolvimento do Agente Orquestrador
python
"""
Objetivo: Implementar o agente orquestrador que gerencia a comunicação e sequência de tarefas entre agentes especializados.

- Receber consultas do usuário e interpretar intenção.
- Delegar partes do processamento para agentes especialistas.
- Coletar, agregar e formatar respostas dos agentes.
- Manter estado e memória do contexto da conversa.
- Garantir performance e integridade durante operações multitarefa.

Projete o orquestrador para ser escalável e resiliente a falhas.
"""

## Prompt 7: Testes Automatizados e Documentação Técnica
python
"""
Objetivo: Criar testes unitários e de integração para todos agentes e para o sistema multiagente completo.

- Testar carregamento e limpeza de dados.
- Validar geração e recuperação de embeddings.
- Testar comunicação e delegação do agente orquestrador.
- Garantir conformidade e segurança das respostas.
- Documentar arquitetura, processos e APIs.

Utilize frameworks como pytest e prática de TDD quando possível.
"""

Estes prompts podem ser usados sequencialmente para orientar o GitHub Copilot a criar código incrementalmente, seguindo a arquitetura e boas práticas planejadas.