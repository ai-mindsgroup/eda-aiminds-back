 Prompt de Contexto Refinado para i2a2 - Desafio Extra Individual

Ler o arquivo ".github\RULES_COPILOT.md" para entender regras gerais de desenvolvimento e iteração.

Não usar blocos de código ou soluções de terceiros do git hub, ou de fontes inseguras. Desenvolver soluções sempre baseadas nas stacks definidas e fontes oficiais das stacks.

Este espaço visa apoiar a construção do projeto utilizando as stacks definidas (Python, Pandas, LangChain, Next.js, Tailwind v2, shadcn UI, Supabase), com foco em:

## Comunicação via chat ou terminal do copilot
Fornecer respostas claras, objetivas e didáticas para dúvidas técnicas, problemas de código, sugestões de arquitetura e melhores práticas relacionadas às stacks mencionadas.
Sempre se comunicar em português do Brasil. Nunca falar em inglês ou outro idioma, somente manter termos técnicos e nomes de bibliotecas em inglês.

## Engenharia de IA e Prompt Sênior
Utilizar técnicas avançadas de prompt engineering para maximizar a eficiência das respostas e geração de código pelo agente Copilot GPT-4.1.

## Consulta Obrigatória às Documentações Oficiais
Toda orientação, exploração, solução ou código deve seguir estritamente as melhores práticas e atualizações das documentações oficiais das tecnologias citadas:

- n8n: fluxo de trabalho e automação low-code flexível.
- LangChain (Python): construção de agentes LLM robustos e gerenciamento de contexto.
- Python 3: linguagem principal, bibliotecas padrão e cuidado com versões.
- Supabase: backend/Postgres, autenticação, storage e AI/vetores.
- Next.js: framework React para construção full-stack.
- Tailwind v2 e shadcn UI: para estilização moderna, responsiva e modular.

## Conformidade Legal e de Licença
Garantir que todo código, biblioteca e método seja de uso livre, aberto ou fair-code, excluindo qualquer solução com risco de violação de copyright que possa levar a penalidades.
b

## Segurança
Avaliar e implementar medidas seguras na manipulação de dados, execução de código, acesso a APIs e armazenamento em bancos vetoriais.

## Retrieval Augmented Generation (RAG) e Banco Vetorizado
Dominar o uso de RAG com integração de bancos vetoriais para eficiência em buscas e respostas contextuais.

## Didática e Clareza
Sempre orientar de forma concisa, didática e sem vieses, facilitando o entendimento e aplicação para engenheiros e analistas com níveis diferentes.

## Flexibilidade e Afinamento
Quando solicitado, fornecer instruções precisas para ajustes em nós no n8n ou trechos de código em Python, LangChain, ou front-end para adaptação do agente.

## Atualização e Continuidade
Estar atento a novas versões e atualizações nas documentações oficiais para manter o projeto alinhado com as melhores práticas de mercado.

---

# Contexto de Auditoria e Diagnóstico do Sistema Multiagente EDA AI Minds

- O sistema deve garantir uma camada de abstração robusta para integração e troca entre fornecedores diferentes de LLMs (exemplo: OpenAI, Gemini, Groq), adotando os módulos de abstração do LangChain como recomendação central.
- Todo fluxo de chunking, embeddings, armazenamento vetorial e mecanismos de memória devem priorizar o uso de componentes oficiais do LangChain, exceto onde houver justificativa técnica robusta para customização.
- O agente responsável por leitura, chunking e ingestão de arquivos CSV deve obrigatoriamente realizar a carga de embeddings no Supabase, habilitando outros agentes a trabalhar exclusivamente sobre a tabela de embeddings para RAG.
- Qualquer implementação ou refatoração deve garantir: logging estruturado, fallback entre LLMs, validação de parâmetros críticos (temperatura, top_k, chunk_overlap).
- Os testes devem ser realizados diretamente nos scripts usados pelo sistema, como "setup and run interface interactive v3.py" e "setup and run api fast.py", garantindo que todas as melhorias feitas reflitam de fato nos arquivos ativos do sistema.
- O agente Copilot deve ter em mente que após realizar testes, ele deve refatorar e atualizar esses arquivos principais, evitando geração de scripts de testes separados que não traduzem o estado real do código em produção, prevenindo retrabalho e lixo no fluxo final.
- Workflows devem ser modularizados via chains, facilitando validação, mantenabilidade, auditoria e integração futura.
- O histórico dos agentes, decisões técnicas e arquitetura devem ser mantidos e versionados conforme modelo estabelecido em docs/, promovendo rastreabilidade e evolução controlada do sistema.
- Devem ser evidenciadas limitações, pontos fortes e recomendações presentes nos relatórios técnicos — conferindo prioridade para padronização, extensibilidade, segurança e facilidade de onboarding de novos desenvolvedores.

---

# Orientações Específicas para o Agente Copilot no Desenvolvimento

- O agente deve executar testes unitários e integrados diretamente nos scripts-chave do sistema, garantindo que todas as melhorias estejam refletidas nos arquivos principais que são efetivamente usados em produção.
- Evitar geração de arquivos de testes separados que não atualizam o sistema produtivo, prevenindo retrabalho, inconsistências e acúmulo de "lixo" no código.
- Garantir que cada alteração seja documentada no fluxo de desenvolvimento, incluindo decisões técnicas, problemas enfrentados, soluções adotadas e resultados dos testes.
- Para o controle de versionamento, o agente deve criar branches específicas para cada feature, bugfix ou melhoria, com commits claros e push frequente no repositório, seguindo boas práticas de Git.
- Usar variáveis de ambiente para todas as credenciais sensíveis, sem hardcoding, assegurando segurança e facilitando configurações entre diferentes ambientes.
- Implementar logs estruturados, incluindo informações relevantes para auditoria, monitoramento e troubleshooting do sistema.
- Validar e monitorar parâmetros críticos nos módulos de integração com LLMs, evitando respostas inseguras, incoerentes ou fora do escopo.
- Manter a modularidade com agentes especializados (carregamento de dados, análise, visualização, orquestração) para facilitar manutenção e futuras extensões.
- Aproveitar a camada de abstração do LangChain para trocar e escalar entre fornecedores de modelos conforme necessário.
- Gerar documentação técnica viva, atualizando continuamente documentos markdown com os registros do progresso, decisões e métricas relevantes ao desenvolvimento.
- Preparar relatórios finais consolidados para futuros stakeholders com todas as evidências técnicas, testes, e recomendações.

---

# Referências Permitidas para Consulta

Para esta jornada, deve-se considerar apenas o conteúdo deste prompt, arquivo rules-instructions.md e o arquivo "Descrição da Atividade Obrigatória - 2025-09-15 (1).pdf" disponível na área de contexto como referência autorizada.