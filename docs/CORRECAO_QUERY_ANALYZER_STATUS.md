# ✅ Correção QueryAnalyzer - Status Atualizado

**Data:** 2025-10-21 04:40 BRT  
**Iteração:** 2ª correção aplicada

---

## 📊 Progresso da Correção

### Erro Original (Teste 6)
```
AttributeError: 'dict' object has no attribute 'category'
```

### 1ª Correção Aplicada
- **Ação:** Converter `Dict` → `QueryAnalysis` (objeto tipado)
- **Resultado:** ✅ Erro original resolvido
- **Novo Erro:** `'str' object has no attribute 'value'`

### 2ª Correção Aplicada  
- **Ação:** Ajustar test_cases para usar strings em vez de enums
- **Resultado:** ✅ Erro `.value` resolvido
- **Novo Erro:** `AssertionError: Query simples classificada como complex`

---

## 🔍 Análise do Problema Atual

### Teste 6 - Execução Atual

```
📌 CASO 1: statistics
   ✅ 'Qual a média de Amount?...' → SIMPLE | statistics
   ✅ 'Me dá a média...' → SIMPLE | structure (⚠️ categoria errada, mas SIMPLE ok)
   ✅ 'Calcule o valor médio...' → SIMPLE | unknown (⚠️ categoria errada, mas SIMPLE ok)
   ✅ 'Quanto é a média...' → SIMPLE | statistics

📌 CASO 2: correlation
   ❌ 'Correlação entre Amount e Time' → COMPLEX | correlation
   ❌ ASSERTION FAILED: "Query simples classificada como complex"
```

**Causa Raiz:** Fallback heurístico classificando correlação como COMPLEX

---

## 💡 Solução Necessária

### Problema Identificado

No arquivo `query_analyzer.py`, linhas 261-281, o fallback heurístico usa:

```python
complex_indicators = [
    'quais', 'mostre', 'liste', 'filtr', 'específic', 'exat', 'precis',
    'detalh', 'linha', 'registro', 'transaç', 'acima', 'abaixo', 'maior', 'menor',
    'entre', 'gráfico', 'plot', 'visualiz', 'histograma'
]
```

A palavra **"correlação"** não está explicitamente na lista, mas é classificada como COMPLEX. 

Provável causa: Linha 281
```python
is_complex = any(indicator in query_lower for indicator in complex_indicators)
```

### Correção Recomendada

1. **Adicionar palavras de estatísticas simples à whitelist:**
```python
simple_indicators = [
    'média', 'mediana', 'moda', 'desvio', 'variância',
    'correlação', 'correlação de pearson', 'correlação de spearman',
    'mínimo', 'máximo', 'quartis', 'percentis'
]

# Primeiro verificar se é SIMPLE
is_simple = any(indicator in query_lower for indicator in simple_indicators)

if is_simple:
    is_complex = False  # Forçar simple
else:
    is_complex = any(indicator in query_lower for indicator in complex_indicators)
```

2. **Ou ajustar a lógica:**
```python
# Se query é curta E contém palavra estatística → SIMPLE
if len(query_lower.split()) < 10:  # Query curta
    if any(word in query_lower for word in ['média', 'mediana', 'correlação', 'mínimo', 'máximo']):
        is_complex = False
```

---

## 📝 Próximos Passos

### Opção A: Ajustar Fallback Heurístico (5 min)
```python
# src/agent/query_analyzer.py - linha ~261

# ANTES
complex_indicators = [...]
is_complex = any(indicator in query_lower for indicator in complex_indicators)

# DEPOIS
simple_stats = ['média', 'mediana', 'correlação', 'desvio', 'variância', 'quartis']
has_simple_stat = any(stat in query_lower for stat in simple_stats)

if has_simple_stat and len(query_lower.split()) < 12:
    is_complex = False
else:
    is_complex = any(indicator in query_lower for indicator in complex_indicators)
```

### Opção B: Melhorar Detecção no LLM (15 min)
- Ajustar prompt do LLM para distinguir melhor entre:
  * "Correlação entre X e Y" → SIMPLE (cálculo único)
  * "Mostre todas as correlações acima de 0.8" → COMPLEX (lista)

### Opção C: Relaxar Assertion do Teste (1 min - workaround)
```python
# test_hybrid_processor_v2_etapa2_completo.py - linha ~756

# ANTES
if case['expected_complexity'] == 'simple':
    assert analysis.complexity in ['simple', 'moderate'], \
        f"Query simples classificada como {analysis.complexity}"

# DEPOIS (mais flexível)
if case['expected_complexity'] == 'simple':
    # Permitir COMPLEX se LLM falhou (fallback heurístico pode variar)
    if not analysis.fallback_used:
        assert analysis.complexity in ['simple', 'moderate'], \
            f"Query simples classificada como {analysis.complexity}"
```

---

## 🎯 Recomendação

**Implementar Opção A (5 minutos)** - Ajustar fallback heurístico

**Motivo:**
- Rápido
- Resolve causa raiz
- Melhora classificação geral
- Não mascara problema (Opção C apenas oculta)

---

## ✅ Checklist de Correção

### Já Concluído
- [x] QueryAnalyzer retorna objetos tipados
- [x] Compatibilidade retroativa 100%
- [x] Erro `.value` corrigido
- [x] Test_cases ajustados para strings

### Pendente
- [ ] Ajustar fallback heurístico (correlação → SIMPLE)
- [ ] Re-executar Teste 6
- [ ] Validar taxa de sucesso 50%+

---

**Última atualização:** 2025-10-21 04:45 BRT  
**Status:** 🔄 Correção em andamento - 2ª iteração  
**Próxima ação:** Implementar Opção A (ajuste heurístico)
