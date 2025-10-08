# Auditoria Técnica - Interface Interativa vs Teste RAG (07/10/2025)

## Objetivo
Analisar divergências entre o fluxo da interface_interativa.py e o teste_busca_intervalos.py, documentando por que a interface retorna estatísticas/outliers ao invés de apenas intervalos min/max, mesmo após correções.

---

## 1. Resumo dos Fluxos

### interface_interativa.py
- Sistema de chat via terminal, multiagente, com memória persistente (Supabase).
- Usuário digita perguntas, que são processadas pelo OrchestratorAgent.
- OrchestratorAgent faz roteamento da query, chama RAGDataAgent para perguntas de intervalo.
- Contexto passado inclui session_id, memória, histórico, dados do orquestrador.
- Resposta do agente exibida ao usuário, junto com metadados.

### teste_busca_intervalos.py
- Script de teste direto, sem contexto conversacional ou memória.
- Carrega CSV localmente, inicializa RAGAgent (versão simplificada).
- Chama rag_agent.process(pergunta) diretamente, sem contexto extra.
- Resposta é apenas o intervalo min/max, sem estatísticas ou outliers.

---

## 2. Principais Diferenças

| Aspecto                  | interface_interativa.py                | teste_busca_intervalos.py         |
|-------------------------|----------------------------------------|-----------------------------------|
| Agente principal        | OrchestratorAgent → RAGDataAgent       | RAGAgent direto                   |
| Contexto                | session_id, memória, histórico, dados  | Nenhum (apenas pergunta)          |
| Roteamento              | Multiagente, regras de classificação   | Direto para RAGAgent              |
| Prompt do agente        | Restritivo (min/max), mas pode poluir  | Restritivo (min/max), limpo       |
| Resposta                | Inclui estatísticas/outliers           | Apenas min/max                    |
| Persistência            | Supabase, memória conversacional       | Não aplicável                     |
| Possível poluição       | Sim, por contexto/histórico            | Não                               |

---

## 3. Diagnóstico do Problema

- O OrchestratorAgent está corretamente roteando queries de intervalo para o RAGDataAgent.
- O prompt do RAGDataAgent está restritivo, exigindo apenas min/max.
- No entanto, o contexto passado na interface pode incluir histórico, memória ou dados extras, poluindo a resposta do LLM e induzindo estatísticas/outliers.
- No teste, o contexto é limpo, garantindo resposta correta.
- Mesmo após patch para limpar contexto em queries de intervalo, o problema persiste, sugerindo que:
  - Algum dado residual do orquestrador/memória ainda está sendo passado.
  - O LLM pode estar ignorando parte do prompt devido ao excesso de contexto.

---

## 4. Recomendações Técnicas

1. **Forçar contexto absolutamente limpo para queries de intervalo:**
   - Garantir que nenhum campo de memória, histórico, dados extras ou contexto do orquestrador seja passado ao RAGDataAgent.
   - Passar apenas a pergunta e os chunks analíticos.
2. **Validar logs do agente:**
   - Verificar nos logs se o contexto está realmente limpo na chamada do agente.
3. **Testar interface com contexto zerado:**
   - Simular chamada igual ao teste, sem session_id, sem memória, apenas pergunta.
4. **Reforçar prompt do RAGDataAgent:**
   - Adicionar instrução para ignorar qualquer contexto extra e responder apenas ao que está nos chunks.

---

## 5. Evidências do Erro

### Resposta indevida do agente (interface_interativa.py):
```
OUTLIERS DETECTADOS (Método IQR):
  • V1: 7062 outliers (2.48%)
    Intervalo normal: [-4.27, 4.67]
  • V2: 13526 outliers (4.75%)
    Intervalo normal: [-2.70, 2.91]
  ...
```

### Resposta correta (teste_busca_intervalos.py):
```
| Variável | Mínimo | Máximo |
|----------|--------|--------|
| V1       | -56.0  | 2.45   |
| V2       | -72.0  | 3.12   |
...
```

---

## 6. Próximos Passos
- Refatorar interface_interativa.py para garantir contexto limpo nas queries de intervalo.
- Validar logs e outputs após correção.
- Documentar evolução e solução final neste arquivo.

---

## 7. Histórico
- Data: 07/10/2025
- Auditor: GitHub Copilot
- Status: Problema persiste após patch, contexto ainda poluído.
