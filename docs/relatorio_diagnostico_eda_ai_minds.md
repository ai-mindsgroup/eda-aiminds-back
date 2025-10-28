# Relatório Técnico: Diagnóstico do Sistema EDA AI Minds

## 1. Listagem de Prompts Usados

### Prompt 01 (Resumo/Objetivo)
- **Arquivo:** `api_completa.py`
- **Local:** Função `analyze_csv_data`
- **Conteúdo:**
```python
filename = file_info.get('filename', 'arquivo.csv')
analysis.append(f"📊 **Análise do arquivo: {filename}**\n")
rows, cols = df.shape
analysis.append(f"📈 **Dimensões:** {rows:,} linhas x {cols} colunas\n")
analysis.append("📋 **Resumo Estatístico:**")
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 0:
    stats = df[numeric_cols].describe()
    for col in numeric_cols[:3]:  # Primeiras 3 colunas numéricas
        mean_val = stats.loc['mean', col]
        std_val = stats.loc['std', col]
        analysis.append(f"   • {col}: Média {mean_val:.2f}, Desvio {std_val:.2f}")
```
- **Observação:** Este bloco é sempre executado, independentemente da pergunta.

### Prompt 02 em diante (Fraude, Estatística, Colunas)
- **Arquivo:** `api_completa.py`
- **Local:** Função `analyze_csv_data`
- **Conteúdo:**
```python
message_lower = message.lower()
if 'fraude' in message_lower or 'fraud' in message_lower:
    analysis.append("🎯 **Resposta à sua pergunta sobre fraude:**")
    # ...detalhes de fraude...
elif 'estatística' in message_lower or 'média' in message_lower or 'resumo' in message_lower:
    analysis.append("🎯 **Estatísticas principais:**")
    # ...detalhes estatísticos...
elif 'colunas' in message_lower or 'variáveis' in message_lower:
    analysis.append("🎯 **Informações sobre colunas:**")
    # ...detalhes de colunas...
```
- **Observação:** Só são executados se a pergunta contiver palavras-chave específicas.

---

## 2. Parâmetros dos Agentes e LLMs

- **Temperatura:** Não explicitado no trecho analisado, mas geralmente padrão (0.7) se não configurado.
- **top_k, batch_size, chunk_overlap:** Não encontrados explicitamente no código analisado.
- **Prompts contextuais:** Dependem de keywords na mensagem.
- **Fallback:** Não há fallback entre LLMs no fluxo principal.
- **Roteamento:** Não há roteamento semântico, apenas por keywords.

**Adequação:**  
Os parâmetros atuais são inadequados para garantir flexibilidade e raciocínio semântico. O uso de keywords engessa o sistema e impede respostas completas para perguntas fora do padrão.

---

## 3. Diagnóstico dos Erros

- **Por que só a pergunta 01 é respondida corretamente?**
  - O bloco inicial da função `analyze_csv_data` sempre retorna um resumo do arquivo, independentemente da pergunta. Por isso, perguntas sobre o objetivo/descritivo do arquivo (como a 01) são sempre respondidas.
  - As demais perguntas dependem de keywords. Se a pergunta não contiver exatamente as palavras esperadas, o sistema não executa o bloco correspondente e retorna apenas o resumo.

- **Logs de execução recentes:**  
  - Não há logs detalhados de falha de LLM, apenas logs de carregamento de CSV e inicialização de agentes.
  - Não há registro de fallback ou de análise semântica da intenção do usuário.

- **Dependência do modelo:**  
  - O problema não está no modelo Groq/Gemini/GPT, mas sim na estrutura do prompt e na lógica de roteamento baseada em keywords.

---

## 4. Cobertura Analítica Obrigatória

### Teste de perguntas (exemplos):

- **Frequência dos dados:**  
  - Pergunta: "Qual a frequência dos valores na coluna X?"  
  - Resposta: Apenas o resumo do arquivo, pois não há keyword "frequência" mapeada.

- **Clusters:**  
  - Pergunta: "Identifique clusters nos dados."  
  - Resposta: Apenas o resumo do arquivo, pois não há keyword "cluster".

- **Outliers:**  
  - Pergunta: "Existem outliers na coluna Y?"  
  - Resposta: Apenas o resumo do arquivo, pois não há keyword "outlier".

- **Relações entre variáveis/correlação:**  
  - Pergunta: "Qual a correlação entre as variáveis A e B?"  
  - Resposta: Apenas o resumo do arquivo, pois não há keyword "correlação".

**Causa raiz:**  
O pipeline só responde corretamente se a pergunta contiver exatamente as keywords esperadas. Não há interpretação semântica real, nem geração dinâmica de código para análises avançadas.

---

## 5. Recomendações Técnicas

- **Alterações de prompt:**  
  - Remover dependência de keywords. Utilizar prompts que instruam a LLM a interpretar a intenção do usuário e gerar código Python/Pandas conforme a necessidade.
  - Exemplo de prompt dinâmico:  
    "Dada a pergunta do usuário e o DataFrame carregado, gere o código Python necessário para responder, execute e retorne o resultado (texto, tabela ou gráfico)."

- **Parâmetros:**  
  - Ajustar temperatura para 0.2–0.5 para maior precisão em tarefas analíticas.
  - Implementar fallback entre LLMs (Groq, GPT, Gemini) para garantir robustez.

- **Lógica:**  
  - Integrar LangChain com ferramentas Python REPL, Pandas e Matplotlib.
  - Modularizar prompts: um para entendimento da intenção, outro para geração de código, outro para execução e formatação do output.
  - Instrumentar logs detalhados para cada etapa (intenção, código gerado, execução, output).

- **Validação dos outputs:**  
  - Validar se o output contém o tipo de resposta esperado (gráfico, tabela, texto) e, se não, acionar fallback ou re-prompt.

---

## 6. Diferença entre APIs (Groq, Gemini, GPT-free)

- **Groq API free:**  
  - Pode rodar modelos open-source (Llama, Mixtral), que têm limitações em raciocínio matemático e geração de código.
  - Instabilidades podem ocorrer, mas o problema principal aqui é estrutural, não do modelo.

- **Gemini/GPT-free:**  
  - Mais robustos para análise de dados, geração de código e respostas analíticas.
  - Recomenda-se testes cruzados para isolar falha de modelo versus falha de pipeline.

---

## 7. Conclusão

O sistema responde corretamente apenas à pergunta 01 porque o fluxo sempre retorna um resumo fixo do arquivo, independentemente da pergunta. As demais perguntas dependem de keywords específicas, o que limita a flexibilidade e impede respostas completas para análises matemáticas, estatísticas e gráficas.

**O problema central está na estrutura do prompt e na lógica de roteamento, não no modelo LLM utilizado.**

---

### Recomendações Finais

- Refatore o pipeline para usar prompts dinâmicos e interpretação semântica.
- Modularize a análise: intenção → geração de código → execução → output.
- Implemente logs e validação de outputs.
- Considere fallback entre LLMs e ajuste de parâmetros.
- Elimine qualquer dependência de keywords ou hardcoding.

Assim, o sistema será flexível, robusto e capaz de responder a qualquer pergunta analítica, conforme o objetivo do projeto.
