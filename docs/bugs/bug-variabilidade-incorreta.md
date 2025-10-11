# Relatório de Bug: Resposta Incorreta para Variabilidade de Dados

**Data:** 2025-10-04  
**Severidade:** Alta  
**Status:** Identificado  

---

## 📋 Resumo

O agente AI Minds respondeu incorretamente à pergunta "Qual a variabilidade dos dados (desvio padrão, variância)?", retornando intervalos (mínimo, máximo, amplitude) em vez de medidas de dispersão (desvio padrão e variância).

---

## 🔍 Detalhamento do Problema

### Pergunta do Usuário
```
Qual a variabilidade dos dados (desvio padrão, variância)?
```

### Resposta Esperada (Perplexity - CORRETO)
| Variável | Desvio Padrão | Variância |
|----------|---------------|-----------|
| Time     | 108.027       | 11669.830 |
| V1       | 1.363         | 1.859     |
| V2       | 1.240         | 1.537     |
| V3       | 1.046         | 1.093     |
| ...      | ...           | ...       |

### Resposta do Agente (AI Minds - INCORRETO)
| Variável | Mínimo     | Máximo     | Amplitude  |
|----------|------------|------------|------------|
| Time     | 0.00       | 32851.00   | 32851.00   |
| V1       | -28.344757 | 1.960497   | 30.305254  |
| V2       | -40.978852 | 13.208904  | 54.187757  |
| ...      | ...        | ...        | ...        |

---

## 💡 Causa Raiz

1. **Interpretação incorreta da pergunta:** O agente não identificou as palavras-chave "variabilidade", "desvio padrão" e "variância"
2. **Cálculo errado:** Executou `df.min()`, `df.max()` em vez de `df.std()`, `df.var()`
3. **Falta de mapeamento semântico:** O roteador semântico não possui regras explícitas para direcionar perguntas sobre dispersão estatística

---

## ✅ Validação

Testamos os valores do Perplexity com cálculo direto no dataset `creditcard_test_500.csv`:

| Variável | Std (Calculado) | Std (Perplexity) | Diferença |
|----------|-----------------|------------------|-----------|
| Time     | 108.027         | 108.027          | 0.00%     |
| V1       | 1.363           | 1.363            | 0.03%     |
| V2       | 1.240           | 1.240            | 0.02%     |
| V3       | 1.046           | 1.046            | 0.03%     |
| V4       | 1.255           | 1.255            | 0.02%     |

**Conclusão:** Os valores do Perplexity estão corretos (diferença < 0.1%).

---

## 🔧 Solução Proposta

### 1. Correção no Agente de Análise CSV

**Arquivo:** `src/agent/embeddings_analyzer.py`

Adicionar detecção de palavras-chave para variabilidade:

```python
def detect_variability_query(query: str) -> bool:
    """Detecta se a pergunta solicita medidas de dispersão."""
    keywords = ['variabilidade', 'desvio padrão', 'variância', 
                'dispersão', 'std', 'var', 'deviation']
    return any(kw in query.lower() for kw in keywords)

def calculate_variability(self, df: pd.DataFrame) -> str:
    """Calcula desvio padrão e variância para todas colunas numéricas."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    results = []
    for col in numeric_cols:
        results.append({
            'Variável': col,
            'Desvio Padrão': df[col].std(),
            'Variância': df[col].var()
        })
    
    df_result = pd.DataFrame(results)
    return df_result.to_markdown(index=False)
```

### 2. Atualização do Roteador Semântico

**Arquivo:** `src/router/semantic_router.py`

Adicionar intent para consultas de variabilidade:

```python
INTENT_PATTERNS = {
    'variability_analysis': [
        'variabilidade', 'desvio padrão', 'variância',
        'dispersão', 'std', 'var', 'spread'
    ],
    # ... outros intents
}
```

### 3. Teste Automatizado

**Arquivo:** `tests/test_variability_analysis.py`

```python
def test_variability_query():
    """Testa resposta correta para pergunta sobre variabilidade."""
    orchestrator = OrchestratorAgent()
    
    query = "Qual a variabilidade dos dados (desvio padrão, variância)?"
    response = orchestrator.process(query)
    
    # Verificar se resposta contém std e var
    assert 'Desvio Padrão' in response or 'std' in response.lower()
    assert 'Variância' in response or 'var' in response.lower()
    
    # Verificar se NÃO contém min/max
    assert 'Mínimo' not in response and 'Máximo' not in response
```

---

## 📊 Impacto

- **Usuários afetados:** Todos que perguntarem sobre variabilidade/dispersão
- **Gravidade:** Alta - resposta completamente incorreta
- **Prioridade:** Alta - afeta confiabilidade do sistema

---

## 🎯 Próximos Passos

1. [ ] Implementar correção no agente de análise CSV
2. [ ] Atualizar roteador semântico com intent de variabilidade
3. [ ] Criar testes automatizados para validar correção
4. [ ] Documentar novos intents no README
5. [ ] Testar com diferentes formulações da mesma pergunta

---

## 📝 Logs do Erro

```
2025-10-04 22:39:21,640 | INFO | agent.embeddings_analyzer | 📊 Calculando estatísticas reais dos dados via embeddings...
2025-10-04 22:39:26,330 | INFO | src.tools.python_analyzer | 📊 Colunas reconstruídas: ['Time', 'V1', 'V2', ...]
2025-10-04 22:39:26,334 | INFO | agent.embeddings_analyzer | ✅ DataFrame carregado: 20000 registros, 31 colunas
2025-10-04 22:39:26,423 | INFO | agent.orchestrator | ✅ Análise CSV concluída com sucesso

🤖 Resposta:
📊 **Intervalo de Cada Variável (Mínimo e Máximo)**  # ❌ ERRO: Retornou intervalo em vez de variabilidade
```

---

## 📚 Referências

- Dataset: `data/creditcard_test_500.csv`
- Script de validação: `debug/analise_rapida.py`
- Perplexity: Valores corretos confirmados por cálculo direto com pandas
