# Documentação: Resposta Adaptativa, Humanizada e Fallback Inteligente

## Objetivo
Garantir que o agente multiagente do EDA I2A2 Mind responda perguntas de forma completa, clara e contextual, usando inteligência para decidir entre análise via chunks ou fallback para o dataset original.

## Comportamento Implementado
- O agente interpreta dinamicamente a pergunta recebida, identificando o tipo de análise ou insight solicitado (ex: intervalo, média, desvio padrão, estatísticas gerais).
- Avalia se os chunks analíticos disponíveis contêm informação suficiente para responder. Caso contrário, ativa fallback para leitura e análise do arquivo CSV original.
- O nome/caminho do CSV é extraído dinamicamente do contexto, dos chunks ou, se ausente, busca o arquivo mais recente na pasta processados.
- A resposta gerada:
  - Mantém a ordem original das colunas do CSV.
  - Inclui texto introdutório humanizado e contextual.
  - Adapta o formato e conteúdo conforme a pergunta (intervalo, média, desvio, resumo estatístico, etc).
  - É flexível para qualquer análise, sem engessamento em formatos ou estatísticas específicas.

## Exemplo de Resposta
```
Análise completa do dataset `data/processado/dataset.csv` conforme solicitado:

Abaixo estão os valores mínimos e máximos de cada variável:

|   | Mínimo | Máximo |
|---|--------|--------|
| A | ...    | ...    |
| B | ...    | ...    |
| C | ...    | ...    |
```

## Testes Automatizados
- `test_humanizacao_ordenacao_adaptativa.py`: Valida que o agente gera respostas humanizadas, ordenadas e adaptativas para diferentes perguntas.
- `test_intervalo_todas_colunas.py`: Garante que todas as variáveis do CSV são consideradas na resposta.

## Garantias
- Não há hardcode de nomes de arquivos CSV.
- O agente decide de forma inteligente quando ativar fallback para análise global.
- Respostas são sempre completas, claras e contextualizadas, respeitando o dataset original.

## Orientações para Mantenedores
- Priorize sempre a flexibilidade e adaptabilidade do agente.
- Amplie os testes para novos tipos de perguntas e datasets.
- Documente qualquer ajuste ou evolução do mecanismo de fallback e resposta adaptativa.

---

Para dúvidas, consulte este documento e os testes em `tests/`.
