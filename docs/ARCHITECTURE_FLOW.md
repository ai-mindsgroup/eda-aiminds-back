# Diagramas de Fluxo - Arquitetura V3.0

**Data:** 16 de outubro de 2025  
**Versão:** 3.0.0  

---

## 🔄 FLUXO PRINCIPAL DE EXECUÇÃO

```mermaid
graph TD
    A[Usuário: Query em linguagem natural] --> B[RAGDataAgent.process]
    B --> C[IntentClassifier.classify]
    C --> D{LLM classifica intenção}
    
    D -->|STATISTICAL| E1[StatisticalAnalyzer]
    D -->|FREQUENCY| E2[FrequencyAnalyzer]
    D -->|TEMPORAL| E3[TemporalAnalyzer]
    D -->|CLUSTERING| E4[ClusteringAnalyzer]
    D -->|CORRELATION| E5[CorrelationAnalyzer futuro]
    D -->|OUTLIERS| E6[OutliersAnalyzer futuro]
    D -->|MÚLTIPLAS| E7[Vários Analyzers em paralelo]
    
    E1 --> F[AnalysisOrchestrator.orchestrate]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F
    E6 --> F
    E7 --> F
    
    F --> G[Combinação de resultados]
    G --> H[LLM gera interpretação integrada]
    H --> I[Relatório Markdown consolidado]
    I --> J[Retorna para usuário]
    
    style A fill:#e1f5ff
    style D fill:#fff4e1
    style F fill:#e8f5e9
    style H fill:#f3e5f5
    style J fill:#e1f5ff
```

---

## 🎯 FLUXO DE CLASSIFICAÇÃO DE INTENÇÃO

```mermaid
sequenceDiagram
    participant U as Usuário
    participant R as RAGDataAgent
    participant IC as IntentClassifier
    participant LLM as LLM (GPT/Gemini)
    participant O as AnalysisOrchestrator
    
    U->>R: "Qual a dispersão dos dados?"
    R->>IC: classify(query)
    IC->>LLM: Prompt estruturado com contexto
    
    Note over LLM: Análise semântica:<br/>dispersão = variabilidade<br/>= desvio padrão
    
    LLM-->>IC: IntentClassificationResult:<br/>primary: STATISTICAL<br/>confidence: 0.90<br/>requires_code: true
    
    IC-->>R: Resultado classificação
    R->>O: orchestrate(query, intent)
    
    Note over O: Decide módulos necessários:<br/>StatisticalAnalyzer
    
    O-->>R: OrchestrationResult
    R-->>U: Relatório formatado
```

---

## 🔧 FLUXO DE ORQUESTRAÇÃO DE MÓDULOS

```mermaid
graph LR
    A[AnalysisOrchestrator.orchestrate] --> B{Verificar intenções}
    
    B -->|STATISTICAL| C1[StatisticalAnalyzer.analyze]
    B -->|FREQUENCY| C2[FrequencyAnalyzer.analyze]
    B -->|TEMPORAL| C3[TemporalAnalyzer.analyze]
    B -->|CLUSTERING| C4[ClusteringAnalyzer.analyze]
    
    C1 --> D1[StatisticalAnalysisResult]
    C2 --> D2[FrequencyAnalysisResult]
    C3 --> D3[TemporalAnalysisResult]
    C4 --> D4[ClusteringAnalysisResult]
    
    D1 --> E[Combinar resultados]
    D2 --> E
    D3 --> E
    D4 --> E
    
    E --> F[LLM: Gerar interpretação integrada]
    F --> G[OrchestrationResult consolidado]
    
    style A fill:#fff4e1
    style E fill:#e8f5e9
    style F fill:#f3e5f5
    style G fill:#e1f5ff
```

---

## 📊 FLUXO DE ANÁLISE ESTATÍSTICA DETALHADO

```mermaid
graph TD
    A[StatisticalAnalyzer.analyze] --> B[Selecionar colunas numéricas]
    B --> C{Para cada coluna}
    
    C --> D1[Calcular métricas de resumo]
    C --> D2[Calcular métricas de variabilidade]
    C --> D3[Calcular métricas de posição]
    C --> D4[Calcular características distribuição]
    
    D1 --> E1[mean, median, mode]
    D2 --> E2[std, variance, CV, IQR]
    D3 --> E3[Q1, Q2, Q3, min, max]
    D4 --> E4[skewness, kurtosis]
    
    E1 --> F[Consolidar resultados]
    E2 --> F
    E3 --> F
    E4 --> F
    
    F --> G[Gerar interpretações automáticas]
    G --> H[StatisticalAnalysisResult]
    
    style A fill:#fff4e1
    style F fill:#e8f5e9
    style H fill:#e1f5ff
```

---

## 🔍 FLUXO DE ANÁLISE DE CLUSTERING

```mermaid
graph TD
    A[ClusteringAnalyzer.analyze] --> B{Método escolhido?}
    
    B -->|kmeans| C1[KMeans n_clusters]
    B -->|dbscan| C2[DBSCAN eps/min_samples]
    B -->|hierarchical| C3[AgglomerativeClustering]
    
    C1 --> D[Executar clustering]
    C2 --> D
    C3 --> D
    
    D --> E[Calcular métricas qualidade]
    E --> F1[Silhouette Score]
    E --> F2[Davies-Bouldin Index]
    E --> F3[Calinski-Harabasz Index]
    
    F1 --> G[Analisar distribuição clusters]
    F2 --> G
    F3 --> G
    
    G --> H[Calcular centros/características]
    H --> I[ClusteringAnalysisResult]
    
    style A fill:#fff4e1
    style D fill:#e8f5e9
    style I fill:#e1f5ff
```

---

## 🌐 ARQUITETURA MODULAR COMPLETA

```mermaid
graph TB
    subgraph "Camada de Interface"
        A[RAGDataAgent]
    end
    
    subgraph "Camada de Classificação"
        B[IntentClassifier]
        C[LLM Provider]
    end
    
    subgraph "Camada de Orquestração"
        D[AnalysisOrchestrator]
    end
    
    subgraph "Camada de Análise Especializada"
        E1[StatisticalAnalyzer]
        E2[FrequencyAnalyzer]
        E3[TemporalAnalyzer]
        E4[ClusteringAnalyzer]
        E5[CorrelationAnalyzer]
        E6[OutliersAnalyzer]
    end
    
    subgraph "Camada de Dados"
        F1[DataFrame pandas]
        F2[Supabase Vectorstore]
        F3[Conversation Memory]
    end
    
    A --> B
    B --> C
    A --> D
    D --> E1
    D --> E2
    D --> E3
    D --> E4
    D --> E5
    D --> E6
    
    E1 --> F1
    E2 --> F1
    E3 --> F1
    E4 --> F1
    E5 --> F1
    E6 --> F1
    
    A --> F2
    A --> F3
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style D fill:#e8f5e9
    style E1 fill:#f3e5f5
    style E2 fill:#f3e5f5
    style E3 fill:#f3e5f5
    style E4 fill:#f3e5f5
    style E5 fill:#f3e5f5
    style E6 fill:#f3e5f5
```

---

## 🔄 COMPARAÇÃO FLUXO V2.0 vs V3.0

### V2.0 (Hard-coded)

```mermaid
graph TD
    A[Query] --> B{termo_para_acao dict lookup}
    B -->|Match keyword| C[if termo in query]
    C -->|Match| D[elif outro termo in query]
    D -->|Match| E[elif mais termo in query]
    E -->|240 linhas if/elif...| F[Executar análise hardcoded]
    F --> G[Resultado]
    
    B -->|No match| H[Erro: não reconhecido]
    
    style B fill:#ffcccc
    style C fill:#ffcccc
    style D fill:#ffcccc
    style E fill:#ffcccc
    style H fill:#ff6666
```

**Problemas:**
- ❌ 400+ linhas de if/elif
- ❌ Lista fixa de keywords
- ❌ Não reconhece sinônimos
- ❌ Difícil adicionar novos tipos
- ❌ Queries mistas processam só 1 parte

---

### V3.0 (LLM-driven)

```mermaid
graph TD
    A[Query] --> B[IntentClassifier LLM]
    B --> C{Classificação semântica}
    C -->|Reconhece sinônimos| D[AnalysisOrchestrator]
    D -->|Decide módulos dinamicamente| E[Múltiplos analyzers em paralelo]
    E --> F[Combinar resultados]
    F --> G[Interpretação integrada LLM]
    G --> H[Resultado rico]
    
    style B fill:#ccffcc
    style C fill:#ccffcc
    style D fill:#ccffcc
    style G fill:#99ff99
    style H fill:#66ff66
```

**Vantagens:**
- ✅ Zero hard-coding
- ✅ Reconhece sinônimos automaticamente
- ✅ Suporta queries mistas
- ✅ Extensível sem modificar código
- ✅ Interpretação contextual inteligente

---

## 📈 FLUXO DE ADIÇÃO DE NOVO MÓDULO

```mermaid
graph LR
    A[Identificar necessidade] --> B[Criar novo Analyzer]
    B --> C[Implementar método analyze]
    C --> D[Criar dataclass Result]
    D --> E[Registrar no Orchestrator]
    E --> F[Adicionar Intent se necessário]
    F --> G[Criar testes unitários]
    G --> H[Documentar uso]
    
    H --> I[Módulo disponível automaticamente!]
    
    style A fill:#fff4e1
    style E fill:#e8f5e9
    style I fill:#66ff66
```

**Tempo estimado:** 2-4 horas (vs 2-3 dias em V2.0)

---

## 🧪 FLUXO DE TESTE E VALIDAÇÃO

```mermaid
graph TD
    A[Testes Unitários] --> B1[test_intent_classifier.py]
    A --> B2[test_statistical_analyzer.py]
    A --> B3[test_frequency_analyzer.py]
    A --> B4[test_clustering_analyzer.py]
    A --> B5[test_orchestrator.py]
    
    B1 --> C[Validar classificação semântica]
    B2 --> D[Validar cálculos estatísticos]
    B3 --> E[Validar análise frequência]
    B4 --> F[Validar clustering]
    B5 --> G[Validar orquestração]
    
    C --> H[Testes de Integração]
    D --> H
    E --> H
    F --> H
    G --> H
    
    H --> I[test_rag_data_agent.py]
    I --> J[Validar fluxo end-to-end]
    
    J --> K{Tudo passou?}
    K -->|Sim| L[Deploy aprovado]
    K -->|Não| M[Corrigir e re-testar]
    
    style H fill:#e8f5e9
    style K fill:#fff4e1
    style L fill:#66ff66
    style M fill:#ffcccc
```

---

## 🔐 FLUXO DE SEGURANÇA (Futuro)

```mermaid
graph TD
    A[Query com execução código] --> B[IntentClassifier]
    B --> C{requires_code_execution?}
    
    C -->|true| D[LangChain PythonREPLTool]
    C -->|false| E[Análise direta]
    
    D --> F[Sandbox isolado]
    F --> G[Validação imports]
    G --> H[Timeout automático]
    H --> I[Execução monitorada]
    
    I --> J{Exceção?}
    J -->|Sim| K[Log erro + fallback]
    J -->|Não| L[Retorna resultado seguro]
    
    K --> M[Resposta tratada]
    L --> M
    E --> M
    
    style D fill:#e8f5e9
    style F fill:#fff4e1
    style K fill:#ffcccc
    style L fill:#66ff66
```

**Status:** Planejado para Sprint 2

---

## 📚 LEGENDA DE CORES

- 🔵 **Azul claro** (#e1f5ff): Entrada/Saída do usuário
- 🟡 **Amarelo claro** (#fff4e1): Decisão/Classificação (LLM)
- 🟢 **Verde claro** (#e8f5e9): Processamento/Orquestração
- 🟣 **Roxo claro** (#f3e5f5): Módulos especializados
- 🟢 **Verde forte** (#66ff66): Sucesso/Aprovação
- 🔴 **Vermelho** (#ffcccc): Erro/Problema

---

**Diagramas criados por:** EDA AI Minds Team  
**Última atualização:** 16 de outubro de 2025  
**Ferramenta:** Mermaid.js  
**Renderização:** GitHub Markdown / VSCode Markdown Preview
