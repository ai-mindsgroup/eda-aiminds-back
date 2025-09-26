# Estimativa de Custo de Uso de APIs LLM

Este documento consolida as iterações sobre dimensionamento de tokens e recomendação de modelos (GPT-4o mini vs Sonar/Perplexity) para o contexto acadêmico/multiagente do projeto.

---
## 1. Escopo
- Projeto acadêmico com arquitetura multiagente (ingestão, profiling, indexação RAG, orquestrador, QA).
- Dataset principal: `creditcard.csv` (resumido em ~40 chunks embeddados).
- Objetivo: Minimizar custo mantendo qualidade suficiente para respostas analíticas e explicativas.

---
## 2. Modelos Considerados
| Modelo | Tipo de Cobrança | Observação |
|--------|------------------|-----------|
| GPT-4o mini (OpenAI) | Pay-as-you-go por tokens | Alta relação custo/benefício para RAG acadêmico. |
| Sonar (Perplexity) | Assinatura / possível quota API | Página de pricing não capturada (Cloudflare); usar confirmação direta depois. |
| GPT-5 / Modelos maiores | Pay-as-you-go (mais caro) | Só necessário se surgir demanda de raciocínio avançado/código complexo. |

---
## 3. Parâmetros de Uso (Estimativas)
- Chunks de contexto RAG: ~40 (média 120 tokens cada) → selecione top-k (ex: 6) por query.
- Contexto efetivo incluído por query: ~1.200 tokens (resumo + system + instruções + pergunta).
- Pergunta do usuário: ~300 tokens (incluída no total acima).
- Overhead e formatação: ~300 tokens.
- Resposta média: ~500 tokens.
- Ingestão inicial embeddings: ~4.800–5.000 tokens (irrelevante em custo).

Tokens médios por query (input) adotados: 1.800 (inclui contexto + pergunta + overhead).
Tokens médios por resposta (output): 500.

---
## 4. Cenários de Volume
| Cenário | Queries/dia | Dias úteis | Queries/mês | Tokens Input | Tokens Output | Total Tokens (≈) |
|---------|-------------|-----------|-------------|--------------|---------------|------------------|
| A (Leve) | 10 | 20 | 200 | 360.000 | 100.000 | 460.000 + ~5K embeddings mês 1 |
| B (Moderado) | 25 | 20 | 500 | 900.000 | 250.000 | 1.150.000 + ~5K |
| C (Intenso) | 50 | 20 | 1.000 | 1.800.000 | 500.000 | 2.300.000 + ~5K |

---
## 5. Preços (OpenAI) - Referência Atual
GPT-4o mini (capturado via página de pricing):
- Input: US$ 0.60 / 1M tokens
- Cached input: US$ 0.30 / 1M tokens (se usar recurso de cache)
- Output: US$ 2.40 / 1M tokens

Embeddings (text-embedding-3-small) – valor público típico: ~US$ 0.02 / 1M tokens (confirmar no painel antes; custo aqui é desprezível dada a escala).

---
## 6. Cálculo de Custos (GPT-4o mini)
Fórmulas:
- Custo_input = (Tokens_input / 1e6) * 0.60
- Custo_output = (Tokens_output / 1e6) * 2.40
- Custo_embeddings (mês 1) ≈ (5.000 / 1e6) * 0.02 ≈ US$ 0.0001

| Cenário | Custo Input (US$) | Custo Output (US$) | Total (≈) |
|---------|-------------------|--------------------|-----------|
| A | 0.36 * 0.60 = 0.216 | 0.10 * 2.40 = 0.240 | ~0.46 |
| B | 0.90 * 0.60 = 0.54 | 0.25 * 2.40 = 0.60 | ~1.14 |
| C | 1.80 * 0.60 = 1.08 | 0.50 * 2.40 = 1.20 | ~2.28 |

Conclusão: Mesmo cenário intenso permanece abaixo de US$ 3/mês.

---
## 7. Sonar (Perplexity) - Suposições
Sem acesso direto à página neste momento (bloqueio Cloudflare). Dois modelos prováveis:
1. Assinatura Pro (~US$ 20–30/mês) com algum nível de acesso a recursos de modelo; API completa pode exigir plano específico.
2. Cobrança adicional por tokens similar a modelos "mini" (confirmar antes de produção).

Para planejamento conservador: assumir custo fixo de US$ 30/mês se optar por dependência da API Sonar. Custo efetivo por query melhora com mais volume, mas permanece superior ao pay-as-you-go do GPT-4o mini para baixo volume acadêmico.

---
## 8. Fórmula Geral (Reuso)
```
Custo_total = (Q * Tin / 1e6) * Pin + (Q * Tout / 1e6) * Pout + C_embed
onde:
  Q = queries/mês
  Tin = tokens input por query
  Tout = tokens output por query
  Pin = preço input / 1M tokens
  Pout = preço output / 1M tokens
  C_embed = custo embeddings (quase zero aqui)
```

---
## 9. Recomendações
| Ação | Justificativa |
|------|---------------|
| Usar GPT-4o mini como baseline | Atende qualidade + menor custo incremental. |
| Adiar migração para GPT-5 | Não há demanda de raciocínio extremo. |
| Aplicar retrieval enxuto (top-k ≤ 6) | Reduz tokens input sem perda relevante. |
| Cache de prompt (se aplicável) | Diminui custo de partes estáticas do system prompt. |
| Monitorar tokens diários | Projeção simples evita surpresas. |
| Validar pricing Sonar antes de integrar | Evita dependência de custo fixo desnecessário. |

---
## 10. Otimizações Futuras
- Compressão de histórico de conversa via resumos cumulativos.
- Classificador de intenção com modelo ainda menor antes de chamar GPT-4o mini.
- Restrições de formato de resposta para limitar tokens de saída.
- Fallback offline (modelo local) para operações triviais (ex: normalização de perguntas). 

---
## 11. Riscos e Mitigações
| Risco | Mitigação |
|-------|-----------|
| Mudança de pricing repentina | Script de recalculo + revisão mensal. |
| Crescimento do contexto não controlado | Limitar k + auditoria de tamanho dos chunks. |
| Dependência de assinatura Sonar sem necessidade | Provar ganho qualitativo antes de adotar. |

---
## 12. Resumo Executivo
O GPT-4o mini cobre de forma econômica (≤ US$ 3/mês) todos os cenários acadêmicos previstos. Sonar só se justifica se houver necessidade específica de capacidades diferenciadas e custo de assinatura for aceitável. A estratégia de geração de poucos chunks semânticos e retrieval focado mantém o consumo de tokens mínimo.

---
*Documento gerado automaticamente a partir das análises de custo realizadas nas iterações do projeto.*
