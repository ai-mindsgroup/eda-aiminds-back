# Integração LangChain - EDA AI Minds Backend

**Início:** 02/10/2025  
**Status:** 🚧 Em Progresso

---

## Visão Geral

Este diretório documenta a integração incremental do LangChain no sistema multiagente EDA AI Minds, seguindo as melhores práticas de engenharia de IA e arquitetura robusta.

---

## Fases de Implementação

### ✅ Fase 1: LLM Manager com LangChain
**Status:** Concluído  
**Arquivo:** [fase1-llm-manager.md](fase1-llm-manager.md)

- Refatoração do LLM Manager usando LangChain
- Suporte a múltiplos provedores (OpenAI, Google, Groq)
- Fallback automático
- Configuração completa de hiperparâmetros
- Testes unitários e de integração

**Benefícios:**
- ✅ Abstração padronizada
- ✅ Facilita integração de novos provedores
- ✅ Melhora rastreabilidade e logging
- ✅ Compatibilidade com sistema legado

---

### 🚧 Fase 2: Sistema de Memória LangChain
**Status:** Planejado  
**Previsão:** A definir

Objetivos:
- Migrar `SupabaseMemoryManager` para LangChain Memory
- Integração com Supabase para persistência
- Suporte a diferentes tipos de memória (buffer, summary, vector)
- Melhoria de contexto dinâmico

---

### 📋 Fase 3: Chunking com LangChain
**Status:** Planejado  
**Previsão:** A definir

Objetivos:
- Substituir chunking customizado por TextSplitters
- Usar DocumentLoaders oficiais
- Configurar chunk_size e overlap otimizados
- Suporte a diferentes tipos de documentos

---

### 📋 Fase 4: Retrieval com LangChain
**Status:** Planejado  
**Previsão:** A definir

Objetivos:
- Implementar retrievers LangChain
- Conectar com Supabase pgvector
- Otimizar busca vetorial
- Suporte a diferentes estratégias de retrieval

---

### 📋 Fase 5: Chains e Workflows
**Status:** Planejado  
**Previsão:** A definir

Objetivos:
- Estruturar workflows com Chains
- Orquestração multiagente reutilizável
- Componentes modulares e testáveis
- Integração com sistema de visualização

---

## Estrutura de Arquivos

```
docs/langchain/
├── README.md                    # Este arquivo
├── fase1-llm-manager.md         # ✅ Fase 1 completa
├── fase2-memoria.md             # 🚧 Em desenvolvimento
├── fase3-chunking.md            # 📋 Planejado
├── fase4-retrieval.md           # 📋 Planejado
└── fase5-chains.md              # 📋 Planejado

tests/langchain/
├── test_langchain_manager.py    # ✅ Testes Fase 1
├── test_langchain_memory.py     # 🚧 Em desenvolvimento
├── test_langchain_chunking.py   # 📋 Planejado
├── test_langchain_retrieval.py  # 📋 Planejado
└── test_langchain_chains.py     # 📋 Planejado

src/llm/
├── langchain_manager.py         # ✅ Novo LLM Manager
└── manager.py                   # 📦 Manager legado
```

---

## Princípios da Integração

1. **Incremental e Modular**
   - Cada fase é independente
   - Sistema legado continua funcionando
   - Migração gradual sem quebrar funcionalidades

2. **Testes Abrangentes**
   - Testes unitários para cada componente
   - Testes de integração com provedores reais
   - Validação de performance e precisão

3. **Documentação Detalhada**
   - Cada fase documentada em arquivo próprio
   - Exemplos práticos de uso
   - Guias de migração

4. **Logging e Monitoramento**
   - Rastreabilidade de todas as operações
   - Métricas de performance
   - Alertas de fallback e erros

5. **Compatibilidade**
   - Interfaces compatíveis com sistema legado
   - Migração suave para agentes existentes
   - Sem breaking changes

---

## Dependências

### Instalação

```bash
# Dependências core LangChain
pip install langchain langchain-core

# Integrações com provedores LLM
pip install langchain-openai langchain-google-genai langchain-groq

# Integrações com vectorstore (futuro)
pip install langchain-community

# Ferramentas auxiliares
pip install langchain-text-splitters
```

### Versões Recomendadas

```
langchain>=0.3.27
langchain-core>=0.3.76
langchain-community>=0.3.27
langchain-openai>=0.3.30
langchain-google-genai>=2.1.9
langchain-groq>=0.2.0
```

---

## Como Usar

### Para Desenvolvedores

1. **Consulte a documentação da fase específica**
   - Cada fase tem um arquivo `.md` detalhado
   - Exemplos práticos e guias de uso

2. **Execute os testes**
   ```bash
   # Testes de uma fase específica
   pytest tests/langchain/test_langchain_manager.py -v
   
   # Todos os testes LangChain
   pytest tests/langchain/ -v
   ```

3. **Integre gradualmente**
   - Comece usando novos componentes em código novo
   - Migre código legado aos poucos
   - Mantenha compatibilidade

### Para Novos Agentes

Use diretamente os componentes LangChain:

```python
from src.llm.langchain_manager import get_langchain_llm_manager, LLMConfig

# Inicializar manager
manager = get_langchain_llm_manager()

# Configurar parâmetros
config = LLMConfig(temperature=0.2, max_tokens=1024)

# Usar
response = manager.chat("Sua pergunta", config=config)
```

---

## Métricas de Sucesso

- [ ] Todos os agentes migrados para LangChain LLM Manager
- [ ] Sistema de memória integrado com LangChain
- [ ] Chunking e retrieval usando componentes oficiais
- [ ] Workflows estruturados com Chains
- [ ] Cobertura de testes > 80%
- [ ] Documentação completa e atualizada
- [ ] Performance mantida ou melhorada
- [ ] Zero breaking changes para usuários finais

---

## Referências

- [LangChain Documentation](https://python.langchain.com/)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangChain Community](https://github.com/langchain-ai/langchain/discussions)
- [Best Practices](https://python.langchain.com/docs/guides/)

---

## Contato e Suporte

Para dúvidas ou sugestões sobre a integração LangChain:

1. Consulte a documentação específica de cada fase
2. Revise os testes implementados
3. Verifique os exemplos práticos
4. Abra uma issue no repositório

---

**Última atualização:** 02/10/2025
