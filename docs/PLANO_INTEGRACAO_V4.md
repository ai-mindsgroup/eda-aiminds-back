# Plano de Integração V4 ao Sistema Principal

## Data: 2025-10-18
## Status: EM EXECUÇÃO

## 1. ARQUITETURA DESCOBERTA

### Fluxo Atual do Sistema
```
interface_interativa.py (linha 240+)
    ↓
OrchestratorAgent.__init__() (linha 158+)
    ↓ inicializa
RAGDataAgent() (linha 90 em rag_data_agent.py)
    ↓ método principal
RAGDataAgent.process(query, context, session_id) (linha 986+)
    ↓ usa
IntentClassifier (para detecção de intenção)
LLMManager (JÁ existe - abstração para GROQ/Gemini/OpenAI)
EmbeddingGenerator
```

### Componentes V4 Isolados
- `src/agent/rag_data_agent_v4.py` - Classe separada (RAGDataAgentV4)
- `src/prompts/dynamic_prompts.py` - Prompts dinâmicos baseados em DataFrame real
- `src/llm/optimized_config.py` - Configurações otimizadas por tipo de análise

### Camada de Abstração LLM Existente
- ✅ `src/llm/manager.py` - LLMManager com fallback automático (GROQ → Gemini → OpenAI)
- ✅ Já implementa patterns: get_llm_manager(), LLMConfig, LLMResponse
- ✅ Usado em vários pontos do sistema

## 2. PROBLEMAS IDENTIFICADOS NO V4

### Violação de Arquitetura
❌ `RAGDataAgentV4._init_llm_with_groq()` reimplementa lógica que já existe no LLMManager
❌ V4 é classe separada em vez de integração ao RAGDataAgent principal
❌ Tests usam `create_agent_v4()` que cria instância isolada

### Problemas de Dados
❌ Sistema gera respostas com dados fictícios (colunas A1-A10, V29-V31)
❌ Não está usando DataFrame real carregado
❌ Hardcoding de "31 colunas" em vez de detecção dinâmica

## 3. ESTRATÉGIA DE INTEGRAÇÃO

### Fase 1: Integrar Prompts Dinâmicos (PRIORIDADE MÁXIMA)
**Arquivo alvo:** `src/agent/rag_data_agent.py`

**Ações:**
1. Importar `DynamicPromptGenerator` e `DatasetContext` no início do arquivo
2. Adicionar `self.prompt_generator = DynamicPromptGenerator()` no `RAGDataAgent.__init__()`
3. No método `process()` (linha 986+), após carregar CSV:
   - Extrair `DatasetContext.from_dataframe(df, csv_path)`
   - Usar `prompt_generator.generate_system_prompt(context, intent)`
   - Usar prompt dinâmico em vez de templates estáticos

**Impacto:** Elimina hardcoding, garante detecção automática de tipos/colunas

### Fase 2: Integrar Configurações Otimizadas
**Arquivo alvo:** `src/agent/rag_data_agent.py`

**Ações:**
1. Importar `get_configs_for_intent()` de `src.llm.optimized_config`
2. No método `process()`, após classificação de intent:
   ```python
   from src.llm.optimized_config import get_configs_for_intent
   llm_config, rag_config = get_configs_for_intent(intent_result.intent)
   ```
3. Usar `llm_config.temperature`, `llm_config.max_tokens` nas chamadas LLM
4. Usar `rag_config.threshold`, `rag_config.max_chunks` na busca vetorial

**Impacto:** Otimiza parâmetros automaticamente por tipo de análise

### Fase 3: Garantir Uso de DataFrame Real
**Arquivo alvo:** `src/agent/rag_data_agent.py`

**Ações:**
1. No método `_analisar_completo_csv()` (fallback global):
   - Garantir que `pd.read_csv()` carrega CSV completo
   - Adicionar logging: `logger.info(f"CSV carregado: shape={df.shape}, dtypes={df.dtypes.to_dict()}")`
   - Usar `df.describe().to_dict()` para estatísticas REAIS
   - Implementar detecção de categóricas binárias:
   ```python
   for col in df.columns:
       unique_vals = df[col].nunique()
       if unique_vals == 2 and set(df[col].unique()).issubset({0, 1, True, False}):
           # Coluna categórica binária
   ```

**Impacto:** Elimina dados fictícios, garante precisão

### Fase 4: Eliminar RAGDataAgentV4 Isolado
**Ações:**
1. Remover imports de `RAGDataAgentV4` de arquivos de teste
2. Criar função wrapper `create_agent_v4()` que retorna `RAGDataAgent()` com melhorias integradas
3. Manter arquivo v4 apenas como referência histórica

## 4. MODIFICAÇÕES NECESSÁRIAS

### Arquivo: `src/agent/rag_data_agent.py`

**Linha ~90 - Adicionar imports:**
```python
from src.prompts.dynamic_prompts import DynamicPromptGenerator, DatasetContext
from src.llm.optimized_config import get_configs_for_intent, LLMOptimizedConfig, RAGOptimizedConfig
```

**Linha ~810 - Modificar `__init__()`:**
```python
def __init__(self):
    super().__init__(...)
    # ... código existente ...
    
    # ✅ V4.0: Inicializar gerador de prompts dinâmicos
    self.prompt_generator = DynamicPromptGenerator()
    self.current_dataset_context: Optional[DatasetContext] = None
    
    self.logger.info("✅ RAGDataAgent V4.0 inicializado - prompts dinâmicos + parâmetros otimizados")
```

**Linha ~1050 - Modificar `process()` para usar configurações otimizadas:**
```python
# Após classificação de intent (já existe no código)
classification_result = classifier.classify(query=query, context=intent_context)

# ✅ V4.0: Obter configurações otimizadas
llm_config, rag_config = get_configs_for_intent(classification_result.primary_intent.value)

# Usar nas buscas
similar_chunks = self._search_similar_data(
    query_embedding=query_embedding,
    threshold=rag_config.threshold,  # 0.6-0.65 vs 0.3 original
    limit=rag_config.max_chunks  # 10 vs 10
)
```

**Novo método - Adicionar após `__init__()`:**
```python
def _update_dataset_context(self, df: pd.DataFrame, file_path: str) -> DatasetContext:
    """
    Atualiza contexto do dataset baseado no DataFrame real.
    
    Returns:
        DatasetContext com tipos, colunas e estatísticas reais
    """
    context = DatasetContext.from_dataframe(df, file_path)
    self.current_dataset_context = context
    
    self.logger.info({
        'event': 'dataset_context_updated',
        'file': file_path,
        'shape': df.shape,
        'numeric_cols': len(context.numeric_columns),
        'categorical_cols': len(context.categorical_columns),
        'temporal_cols': len(context.temporal_columns)
    })
    
    return context
```

### Arquivo: `src/agent/rag_data_agent.py` - Método `_analisar_completo_csv()`

**Adicionar após carregar DataFrame:**
```python
def _analisar_completo_csv(self, csv_path: str, pergunta: str) -> str:
    """Analisa CSV completo quando chunks não são suficientes."""
    try:
        # Carregar CSV
        df = pd.read_csv(csv_path)
        
        # ✅ V4.0: Atualizar contexto do dataset
        dataset_context = self._update_dataset_context(df, csv_path)
        
        # ✅ V4.0: Gerar prompt dinâmico baseado no DataFrame real
        if self.current_dataset_context and self.llm:
            # Classificar intent
            from src.analysis.intent_classifier import IntentClassifier
            classifier = IntentClassifier(self.llm, self.logger)
            intent_result = classifier.classify(pergunta)
            
            # Obter configurações otimizadas
            llm_config, rag_config = get_configs_for_intent(intent_result.primary_intent.value)
            
            # Gerar prompt dinâmico
            system_prompt = self.prompt_generator.generate_system_prompt(
                dataset_context=dataset_context,
                analysis_intent=intent_result.primary_intent.value
            )
            
            user_prompt = self.prompt_generator.generate_user_prompt_enhancement(
                query=pergunta,
                dataset_context=dataset_context
            )
            
            # Chamar LLM com temperatura otimizada
            # ... resto do código usando llm_config.temperature, llm_config.max_tokens
```

## 5. TESTES NECESSÁRIOS

### Teste 1: Pergunta 01 - Tipos de Dados
**Comando:**
```bash
python interface_interativa.py
# Perguntar: "Quais são os tipos de dados (numéricos, categóricos)?"
```

**Validação:**
- ✅ Lista TODAS as 31 colunas
- ✅ Detecta Class como categórica binária (0=não fraude, 1=fraude)
- ✅ Não menciona colunas fictícias (A1-A10, V29-V31)
- ✅ Usa dtypes reais do DataFrame

### Teste 2: Pergunta 03 - Intervalos
**Comando:**
```bash
python interface_interativa.py
# Perguntar: "Qual o intervalo de cada variável (mínimo, máximo)?"
```

**Validação:**
- ✅ Calcula min/max REAIS de TODAS as 31 colunas
- ✅ Não inventa valores
- ✅ Inclui Amount e Class
- ✅ Não menciona V29, V30, V31

### Teste 3: 17 Perguntas Completas
**Comando:**
```bash
# Modificar test_17_perguntas_v4.py para usar sistema principal
# Substituir: agent = create_agent_v4()
# Por: agent = RAGDataAgent()  # com melhorias integradas
python tests/test_17_perguntas_v4.py
```

**Validação:**
- ✅ 100% de aprovação
- ✅ Nenhum dado fictício
- ✅ Cobertura completa das 31 colunas

## 6. CHECKLIST DE IMPLEMENTAÇÃO

### Etapa 1: Preparação
- [ ] Fazer backup do rag_data_agent.py original
- [ ] Criar branch: `integrate-v4-improvements`
- [ ] Documentar estado atual

### Etapa 2: Integração de Prompts Dinâmicos
- [ ] Adicionar imports no rag_data_agent.py
- [ ] Modificar __init__() para incluir DynamicPromptGenerator
- [ ] Adicionar método _update_dataset_context()
- [ ] Modificar _analisar_completo_csv() para usar prompts dinâmicos
- [ ] Testar com Pergunta 01

### Etapa 3: Integração de Configurações Otimizadas
- [ ] Importar get_configs_for_intent
- [ ] Modificar process() para usar configurações otimizadas
- [ ] Ajustar parâmetros de busca RAG (threshold, max_chunks)
- [ ] Testar com Pergunta 03

### Etapa 4: Validação de DataFrame Real
- [ ] Adicionar logging detalhado do DataFrame carregado
- [ ] Implementar detecção de categóricas binárias
- [ ] Garantir uso de df.describe() real
- [ ] Testar todas as 17 perguntas

### Etapa 5: Limpeza e Documentação
- [ ] Remover RAGDataAgentV4 dos imports
- [ ] Atualizar README com V4.0 integrado
- [ ] Criar documento de migração
- [ ] Fazer merge na branch principal

## 7. RISCOS E MITIGAÇÕES

### Risco: Quebrar compatibilidade com código existente
**Mitigação:** Manter assinaturas de métodos existentes, apenas adicionar funcionalidade

### Risco: LLM Manager pode não ter método esperado
**Mitigação:** Validar interface do LLMManager antes de usar

### Risco: Performace degradada com prompts mais complexos
**Mitigação:** Usar parâmetros otimizados (temperature 0.1-0.35, max_tokens 2048)

## 8. MÉTRICAS DE SUCESSO

- ✅ Interface interativa responde Pergunta 01 com 100% de precisão
- ✅ 17 perguntas passam com score médio > 0.95
- ✅ Nenhum dado fictício gerado
- ✅ Tempo de resposta < 15s por pergunta
- ✅ Sistema detecta automaticamente qualquer CSV sem hardcoding
