# Diagrama do Pipeline Modular Multiagente (Mermaid)

```mermaid
graph TD
    subgraph Entrada
        A[API / Script / Teste]
    end
    A --> B[RAGDataAgentV4]
    B --> C[AnalysisOrchestrator]
    C --> D1[CodeGenerator]
    C --> D2[CodeExecutor]
    C --> D3[OutputFormatter]
    D1 --> D2
    D2 --> D3
    D3 --> E[Resposta Final]
    B -.->|Fallback| F[LLM Manager / Fallback LLM]
    B -->|Cache| G[Cache Local]
    B -->|Logging| H[Logger Estruturado]
    C -->|Chamada LLM| I[LangChain Manager]
    I --> J[GROQ / OpenAI / Gemini]
    subgraph Outros Agentes
        K[MemoryCleaner]
        L[OrchestratorAgent]
        M[CsvAnalysisAgent]
    end
    A --> K
    A --> L
    A --> M
```

> **Legenda:**
> - O fluxo principal utiliza o `RAGDataAgentV4` e o orquestrador para análise, geração, execução e formatação de código dinâmico.
> - Outros agentes especializados continuam disponíveis e podem ser acionados conforme o contexto multiagente.
> - Integração com múltiplos LLMs via LangChain Manager.
