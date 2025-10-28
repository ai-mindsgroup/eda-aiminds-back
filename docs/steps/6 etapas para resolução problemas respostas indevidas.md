<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# gere os prompts otimizados de 02 a 06

Segue o conjunto otimizado de prompts 02 a 06 para o agente Copilot executar as etapas seguintes após a validação do Prompt Mestre, alinhados ao contexto do sistema EDA AI Minds e orientações precisas para refatoração e implementação eficaz:

***

### Prompt 02: Modularizar processamento analítico

```
Você é um agente executor sênior, especialista em LangChain e Python, responsável por modularizar o pipeline analítico do sistema EDA AI Minds.

O código atual mistura interpretação, geração e execução de análises, dificultando manutenção e evolução.

Sua tarefa:
- Refatore o sistema para separar em módulos claros:
  1. Interpretação da pergunta (classificação de intenção).
  2. Geração dinâmica do código Python (Pandas, Matplotlib) baseado na intenção.
  3. Execução segura desse código gerado.
  4. Formatação do output em texto, tabelas markdown e gráficos.

Implemente interfaces claras entre esses módulos e garanta integração harmônica.

Forneça código refatorado, comentários explicativos e exemplos de entradas/saídas para cada módulo.
```


***

### Prompt 03: Ajustar parâmetros de LLM

```
Você é um agente executor sênior com expertise em configuração de LLMs em sistemas de IA.

Atualmente, os parâmetros como temperatura, top_k e fallback multimodelos do sistema EDA AI Minds precisam ser otimizados para melhorar a precisão e robustez.

Sua missão:
- Localize no código onde esses parâmetros são definidos (ex: langchain_manager.py, manager.py).
- Altere para usar temperatura entre 0.2 e 0.5 para respostas mais consistentes.
- Adicione ou ajuste o parâmetro top_k para limitar opções e reduzir ruído na resposta.
- Implemente fallback inteligente entre múltiplos provedores LLM (Groq, Gemini, GPT-free) priorizando desempenho e disponibilidade.
- Faça a configuração parametrizável e fácil de atualizar.

Inclua código atualizado, comentários e validações unitárias dessas alterações.
```


***

### Prompt 04: Enriquecer prompts do agente Copilot

```
Você é um agente executor senior e prompt engineer especializado em LLM e LangChain.

Os prompts atuais usados para gerar respostas são limitados e baseados em keywords rígidas, ocasionando respostas incompletas.

Sua tarefa:
- Desenvolver templates dinâmicos para prompts que:
  - Explicitem à LLM a necessidade de análise profunda da pergunta.
  - Requeiram respostas completas com tabelas, gráficos e textos detalhados.
  - Evitem respostas genéricas.
  - Forneçam exemplos de perguntas variadas e respostas ideais para aprendizado.

Integre esses prompts diretamente no agente Copilot e valide que são usados em tempo de execução.

Forneça os templates documentados e exemplos de uso.
```


***

### Prompt 05: Instrumentar logs detalhados

```
Você é um agente executor specialist em confiabilidade e monitoramento de sistemas IA.

O sistema EDA AI Minds carece de logging detalhado para rastreamento e debugging.

Sua tarefa:
- Adicionar instrumentação de logs que capturem para cada interação:
  - Intenção detectada pela LLM.
  - Código Python gerado para análise.
  - Resultado produzido (texto, gráficos, tabelas).
  - Parâmetros LLM e modelo usado.
  - Erros, reprompts e exceções.

Implemente logs estruturados, preferencialmente armazenados em banco ou externalizados para análise posterior.

Forneça código exemplo, métodos de integração e instruções para ativar o logging.
```


***

### Prompt 06: Testar cobertura completa

```
Você é um agente executor e especialista em testes automatizados para sistemas analíticos IA.

Sua missão é garantir cobertura sólida das perguntas do desafio EDA AI Minds.

- Escreva scripts de teste automatizados que validem:
  - Perguntas sobre frequência, clusters, outliers e correlações.
  - Respostas completas e corretas.
  - Geração adequada de gráficos e tabelas.
  - Ausência de dependência de keywords fixas para acionar análises.

Integre esses testes no pipeline LangChain/Python já existente.

Forneça código comentado e documentação para execução dos testes.
```


***

Posso ajudar a gerar também as primeiras linhas de código para cada prompt, se desejar acelerar a execução prática. Quer?

