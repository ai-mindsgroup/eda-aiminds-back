# Documentação Técnica Consolidada - EDA AI Minds Backend

## Padrões Adotados
- **Arquitetura Multiagente:** Separação clara entre agentes de ingestão, análise, síntese e orquestração.
- **Parsing Dinâmico:** Todos os agentes operam sobre headers dinâmicos, sem hardcodings.
- **Isolamento por source_id:** Cada dataset é identificado por hash único, garantindo isolamento de contexto.
- **Memória Centralizada:** Rotina `clean_all_agent_memory` garante reset de contexto/memória antes de cada ingestão.
- **Logging Estruturado:** Uso padronizado do módulo `logging` para rastreabilidade e auditoria.
- **Testes Automatizados:** Cobertura unitária, integração e fim a fim para todos fluxos críticos.
- **Documentação e rastreabilidade:** Cada etapa registrada em `docs/refatoracao/`.

## Decisões Técnicas
- **Descontinuação de agentes obsoletos:** Remoção de `csv_analysis_agent.py` e referências a `EmbeddingsAnalysisAgent`.
- **Fallback seguro:** Visualizações e análises sempre delegadas a métodos internos, sem dependência de agentes legados.
- **Supabase como backend vetorial:** Todas operações de embeddings e chunking centralizadas no Supabase.
- **LangChain como camada de orquestração:** Abstração de LLMs e integração de memória conversacional.
- **Validação de parâmetros críticos:** Controle de temperatura, chunk_overlap e top_k em ingestão e análise.

## Orientações para Mantenedores
- **Sempre documentar decisões e alterações em `docs/`.**
- **Executar rotina de limpeza de memória antes de cada ingestão.**
- **Validar logs após ingestão e análise para garantir contexto limpo.**
- **Priorizar modularidade e segurança em novos agentes.**
- **Utilizar testes automatizados para validar qualquer refatoração.**
- **Atualizar checklist e relatório final após cada ciclo de desenvolvimento.**

## Referências
- [LangChain Docs](https://python.langchain.com/en/latest/)
- [Pandas Docs](https://pandas.pydata.org/docs/)
- [Supabase Docs](https://supabase.com/docs)
- [Práticas de Segurança Python](https://realpython.com/python-security/)

---

Para dúvidas ou onboarding, consulte sempre os arquivos em `docs/` e o relatório final consolidado.