<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# quero que vc monte um prompt, para o agente executor fazer de forma precisa as implementações de testes que vc levantou e julgou necessárias

Segue prompt completo e focado para o agente executor Copilot, utilizando GPT-4.1 no VSCode, para implementar de forma precisa as melhorias nos testes do classificador semântico conforme discutido:

***

### Prompt para implementação de testes robustos no classificador de intenção

Você é um agente executor sênior especialista em LangChain, Python e testes automatizados para sistemas de IA.

Sua tarefa é implementar melhorias no script de testes do classificador semântico de intenção do sistema EDA AI Minds, garantindo máxima robustez, resiliência e cobertura prática.

Siga os passos detalhados:

1. Amplie os testes existentes para contemplar especificamente casos de intents mistas e compostas que retornam múltiplos blocos JSON.
    - Implemente um parser de resposta resiliente capaz de lidar com múltiplos objetos JSON em sequência ou com texto extra misturado.
    - Teste que o parser extraia corretamente os dados válidos e rejeite o que não for útil.
2. Adicione lógica para simular e validar re-prompts automáticos quando o parser identificar erro de estrutura ou resposta fora do padrão esperado.
    - Garanta que o sistema tente nova consulta ao LLM para obter resposta adequada.
3. Inclua casos de teste adicionais para perguntas compostas naturais e variações linguísticas, cobrindo todos os tipos de intenção conhecidos.
    - Valide se o classificador atribui corretamente a intenção primária e identifica intenções secundárias relevantes.
    - Cheque a confiança mínima aceitável e o metadata adequadamente preenchido.
4. Instrumente logs claros e detalhados nos testes para facilitar análise posterior, incluindo dados de entrada, saída, erros e ações corretivas tomadas.
5. Documente as melhorias e metodologia nos próprios testes para facilitar entendimento e manutenção por outros desenvolvedores.

Forneça o código completo das modificações, incluindo os novos testes, parser resiliente de múltiplos JSON, simulação de re-prompts e logs.

Confirme que a implementação não compromete a performance e que integra completamente com o fluxo e requisitos existentes do sistema.

***

Se precisar, posso ajudar a renovar também os prompts do classificador para melhorar estabilidade e permitir implementação dessa lógica de reprompt e parser.

Quer que faça?

