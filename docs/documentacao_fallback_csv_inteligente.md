# Documentação: Fallback Inteligente e Detecção Dinâmica de CSV

## Causas do Problema
- Respostas incompletas ocorriam quando os chunks analíticos não continham todas as colunas/linhas do dataset.
- Em versões anteriores, o agente podia omitir variáveis ou depender de dados parciais, prejudicando a precisão.
- Hardcodings de nomes de arquivos CSV foram auditados e removidos dos agentes principais.

## Modificações Realizadas
- Implementado método `_should_use_global_csv` para detectar perguntas que exigem análise global e decidir pelo fallback.
- Adicionado método `_analisar_completo_csv` para executar análise completa do arquivo CSV, conforme a pergunta.
- O agente extrai dinamicamente o caminho do arquivo CSV dos chunks (`csv_path`), do contexto ou busca o arquivo mais recente na pasta de processados.
- Toda análise global é feita de forma flexível, sem hardcode de nomes de arquivos.
- Testes automatizados criados para validar que todas as variáveis são consideradas na resposta.

## Garantias do Novo Comportamento
- O agente responde perguntas sobre intervalos, estatísticas ou colunas considerando todos os dados do arquivo CSV quando necessário.
- Não há limitação arbitrária ou filtro que exclua colunas automaticamente.
- O sistema é robusto, adaptável e rastreável, com fallback inteligente e logs detalhados.

## Testes
- Teste `test_intervalo_todas_colunas.py` valida que o agente retorna o intervalo de todas as variáveis do CSV.
- Testes de integração garantem que o fallback é acionado apenas quando necessário.

## Orientações para Mantenedores
- Nunca hardcode nomes de arquivos CSV em agentes ou scripts.
- Sempre utilize métodos dinâmicos para extração do caminho do arquivo.
- Priorize a inteligência do agente para decidir entre análise via chunks ou via CSV completo.
- Mantenha e amplie os testes automatizados para cenários diversos.

---

Para dúvidas, consulte este documento e os testes em `tests/`.
