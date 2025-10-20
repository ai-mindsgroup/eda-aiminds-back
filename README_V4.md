# Sistema EDA AI Minds V4.0 - Guia Rápido

## ✨ Novidades da Versão 4.0

- **Prompts Completamente Dinâmicos**: Zero hardcoding, adapta-se a qualquer dataset
- **Parâmetros Otimizados**: Temperatura 0.1-0.35, threshold 0.6-0.65, max_tokens 2048
- **Fallback Inteligente**: RAG + fallback para CSV direto
- **Visualizações Automáticas**: Gera histogramas quando necessário
- **Suite de Testes**: 17 perguntas do curso com validação automatizada

## 🚀 Início Rápido

### 1. Ativar Ambiente

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Testar Importações

```powershell
# Configurar console para UTF-8
chcp 65001

# Testar imports
python test_imports_v4.py
```

### 3. Executar Testes das 17 Perguntas

```powershell
# Configurar encoding
$env:PYTHONIOENCODING="utf-8"

# Rodar testes
python tests/test_17_perguntas_v4.py
```

### 4. Ver Resultados

Os resultados são salvos em:
- `outputs/teste_17_perguntas_v4_YYYYMMDD_HHMMSS.json` - Dados estruturados
- `outputs/teste_17_perguntas_v4_YYYYMMDD_HHMMSS.html` - Relatório visual

## 📝 Uso Programático

```python
from src.agent.rag_data_agent_v4 import create_agent_v4

# Criar agente
agent = create_agent_v4()

# Fazer pergunta
result = agent.query_v4(
    query="Quais são os tipos de dados?",
    session_id="user_123"  # Para memória persistente
)

# Acessar resposta
print(result['answer'])
print(f"Intent: {result['intent']}")
print(f"Configurações usadas:")
print(f"  - Temperature: {result['metadata']['llm_config']['temperature']}")
print(f"  - RAG Threshold: {result['metadata']['rag_config']['threshold']}")

# Visualizações geradas
if result['visualizations']:
    print(f"Gráficos: {result['visualizations']}")
```

## 🛠️ Solução de Problemas

### Erro: "ModuleNotFoundError: No module named 'src'"

```powershell
# Executar script de correção de imports
python fix_imports.py

# Testar novamente
python test_imports_v4.py
```

### Erro: "UnicodeEncodeError"

```powershell
# Configurar console para UTF-8
chcp 65001
$env:PYTHONIOENCODING="utf-8"
```

### Erro: "LLM não disponível"

O sistema funciona com qualquer uma dessas APIs configuradas em `configs/.env`:
- GROQ_API_KEY (recomendado - mais rápido)
- GOOGLE_API_KEY (Gemini)
- OPENAI_API_KEY

## 📚 Documentação Completa

Consulte `docs/RELATORIO_TECNICO_MELHORIAS_V4.md` para:
- Problemas identificados e soluções
- Benchmarks e referências científicas
- Arquitetura detalhada
- Próximos passos

## 🎯 17 Perguntas do Curso

1. **Descrição dos Dados** (5 perguntas)
   - Tipos de dados
   - Distribuição
   - Intervalos
   - Tendência central
   - Variabilidade

2. **Padrões e Tendências** (3 perguntas)
   - Padrões temporais
   - Frequências
   - Clusters

3. **Anomalias** (3 perguntas)
   - Detecção de outliers
   - Impacto
   - Tratamento

4. **Relações** (3 perguntas)
   - Relações entre variáveis
   - Correlação
   - Influência

5. **Complementares** (3 perguntas)
   - Missing values
   - Forma das distribuições
   - Resumo executivo

## 📊 Métricas de Qualidade

O sistema é avaliado automaticamente com base em:
- Cobertura de colunas (>90%)
- Geração de visualizações (quando apropriado)
- Precisão numérica (estatísticas determinísticas)
- Completude da resposta (>200 caracteres)
- Uso correto de configurações (temp, threshold, etc)

## 🔧 Arquivos Principais

```
src/
├── prompts/
│   └── dynamic_prompts.py           # Sistema de prompts dinâmicos (650 linhas)
├── llm/
│   └── optimized_config.py          # Configurações otimizadas (400 linhas)
├── agent/
│   ├── rag_data_agent.py            # V2.0 (base)
│   └── rag_data_agent_v4.py         # V4.0 (novos recursos - 600 linhas)
tests/
└── test_17_perguntas_v4.py          # Suite de testes (500 linhas)
docs/
└── RELATORIO_TECNICO_MELHORIAS_V4.md # Documentação técnica completa
```

## ✅ Status

- [x] Prompts dinâmicos implementados
- [x] Parâmetros otimizados configurados
- [x] Fallback CSV integrado
- [x] Visualizações automáticas
- [x] Suite de testes completa
- [x] Documentação técnica
- [ ] Integração com Orquestrador (próximo passo)

## 🎉 Pronto para Produção

O sistema V4.0 está pronto para:
- Responder as 17 perguntas do curso
- Adaptar-se a qualquer dataset CSV
- Gerar visualizações automaticamente
- Fornecer respostas completas e precisas
- Logging detalhado para auditoria

---

**Versão:** 4.0.0  
**Data:** 2025-10-18  
**Autor:** AI Minds Engineering Team
