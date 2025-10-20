# Correções Urgentes Identificadas - Teste Pergunta 01

## Data: 2025-10-18 22:42
## Status: TESTE FALHOU - Correções necessárias

## Problema Identificado

### ERRO CRÍTICO: Sistema respondendo análise temporal para pergunta sobre tipos de dados

**Pergunta do usuário:** "Quais são os tipos de dados (numéricos, categóricos)?"

**Comportamento esperado:** Listar TODAS as 31 colunas com seus tipos reais (int64, float64)

**Comportamento atual:** Sistema detecta "Time" como coluna temporal e faz análise temporal completa em vez de responder sobre tipos de dados

### Log do Erro:
```json
{
  "event": "fallback_para_analise_temporal",
  "motivo": "Sistema detectou Time como temporal e executou TemporalAnalyzer",
  "resultado": "Resposta irrelevante para pergunta sobre tipos de dados"
}
```

## Root Cause Analysis

### 1. Fluxo Incorreto no `_analisar_completo_csv()`

**Código problemático (linhas 655-705):**
```python
# ETAPA 1: DETECÇÃO DE COLUNAS TEMPORAIS
detector = TemporalColumnDetector(config=detection_config)
detection_results = detector.detect(df, override_column=override_temporal_col)
temporal_cols = detector.get_detected_columns(detection_results)

# ETAPA 2: ANÁLISE TEMPORAL (se colunas detectadas)
if temporal_cols:
    logger.info(f"Executando análise temporal em {len(temporal_cols)} coluna(s)")
    analyzer = TemporalAnalyzer(logger=logger)
    # ... executa análise temporal
    return header + "\n\n---\n\n".join(respostas)  # RETORNA AQUI!

# ETAPA 3: FALLBACK - ANÁLISE ESTATÍSTICA GERAL
# (nunca chega aqui se temporal_cols detectado)
```

**Problema:** Sistema assume que se existe coluna temporal, a pergunta é sobre análise temporal. Mas a pergunta é sobre **TIPOS DE DADOS**, não análise temporal!

### 2. LLM LangChain Não Disponível

**Log:**
```
WARNING: "⚠️ Nenhum LLM LangChain disponível - usando fallback manual"
```

**Impacto:** Sem LLM LangChain, o sistema não consegue interpretar a pergunta corretamente via `_interpretar_pergunta_llm()`. O método `_analisar_completo_csv()` assume análise temporal por padrão.

### 3. Falta GROQ API Key para LangChain

**Problema:** O sistema tem `GROQ_API_KEY` configurado para embeddings, mas o método `_init_langchain_llm()` só tenta Google Gemini e OpenAI, não GROQ.

**Código atual (linhas 836-872):**
```python
def _init_langchain_llm(self):
    try:
        # Tentar Google Gemini primeiro
        from src.settings import GOOGLE_API_KEY
        if GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(...)
            return
    except Exception as e:
        logger.warning(f"Google Gemini não disponível: {e}")
    
    try:
        # Fallback: OpenAI
        from src.settings import OPENAI_API_KEY
        if OPENAI_API_KEY:
            self.llm = ChatOpenAI(...)
            return
    except Exception as e:
        logger.warning(f"OpenAI não disponível: {e}")
    
    self.llm = None  # ❌ NÃO TENTA GROQ!
```

## Correções Necessárias (Prioridade Crítica)

### CORREÇÃO 1: Adicionar GROQ ao `_init_langchain_llm()`

**Arquivo:** `src/agent/rag_data_agent.py` (linhas 836-872)

**Modificação:**
```python
def _init_langchain_llm(self):
    if not LANGCHAIN_AVAILABLE:
        self.logger.warning("⚠️ LangChain não disponível - usando fallback")
        self.llm = None
        return
    
    try:
        # 1️⃣ PRIORIDADE: GROQ (mais rápido e disponível)
        from src.settings import GROQ_API_KEY
        if GROQ_API_KEY:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="llama-3.1-8b-instant",
                    temperature=0.3,
                    max_tokens=2048,
                    groq_api_key=GROQ_API_KEY
                )
                self.logger.info("✅ LLM LangChain inicializado: GROQ (llama-3.1-8b-instant)")
                return
            except ImportError:
                self.logger.warning("langchain-groq não instalado")
    except Exception as e:
        self.logger.warning(f"GROQ não disponível: {e}")
    
    # 2️⃣ Fallback: Google Gemini
    try:
        from src.settings import GOOGLE_API_KEY
        if GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.3,
                max_tokens=2048,
                google_api_key=GOOGLE_API_KEY
            )
            self.logger.info("✅ LLM LangChain inicializado: Google Gemini")
            return
    except Exception as e:
        self.logger.warning(f"Google Gemini não disponível: {e}")
    
    # 3️⃣ Fallback final: OpenAI
    try:
        from src.settings import OPENAI_API_KEY
        if OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=2048,
                openai_api_key=OPENAI_API_KEY
            )
            self.logger.info("✅ LLM LangChain inicializado: OpenAI GPT-4o-mini")
            return
    except Exception as e:
        self.logger.warning(f"OpenAI não disponível: {e}")
    
    self.llm = None
    self.logger.warning("⚠️ Nenhum LLM LangChain disponível - usando fallback manual")
```

### CORREÇÃO 2: Modificar `_analisar_completo_csv()` para Interpretar Pergunta ANTES de Decidir Análise

**Arquivo:** `src/agent/rag_data_agent.py` (linha ~650)

**Modificação:**
```python
def _analisar_completo_csv(self, csv_path: str, pergunta: str, override_temporal_col: str = None,
                           temporal_col_names: list = None, accepted_types: tuple = None) -> str:
    import pandas as pd
    from src.analysis.temporal_detection import TemporalColumnDetector, TemporalDetectionConfig
    from src.analysis.temporal_analyzer import TemporalAnalyzer
    
    # Carregar dados
    df = pd.read_csv(csv_path)
    
    logger = self.logger if hasattr(self, 'logger') else logging.getLogger(__name__)
    logger.info({
        'event': 'inicio_analise_csv_v2',
        'csv_path': csv_path,
        'shape': df.shape,
        'dtypes': df.dtypes.to_dict(),
        'override_temporal_col': override_temporal_col
    })
    
    # ✅ V4.0: Atualizar contexto do dataset
    dataset_context = self._update_dataset_context(df, csv_path)
    
    # ═══════════════════════════════════════════════════════════════
    # ✅ V4.0: INTERPRETAR PERGUNTA PRIMEIRO (antes de decidir análise)
    # ═══════════════════════════════════════════════════════════════
    
    # Detectar se pergunta é sobre tipos de dados / descrição geral
    pergunta_lower = pergunta.lower()
    intent_keywords = {
        'tipos_dados': ['tipos de dados', 'tipos de variáveis', 'tipo de dado', 'numéricos', 'categóricos', 'dtypes'],
        'descricao': ['descreva', 'descrição', 'overview', 'visão geral', 'resumo'],
        'estatisticas': ['estatísticas', 'média', 'mediana', 'desvio', 'variância'],
        'temporal': ['temporal', 'tempo', 'tendência', 'séries temporais', 'sazonalidade']
    }
    
    detected_intent = None
    for intent, keywords in intent_keywords.items():
        if any(kw in pergunta_lower for kw in keywords):
            detected_intent = intent
            break
    
    # Se pergunta é sobre tipos de dados / descrição, NÃO fazer análise temporal
    if detected_intent in ['tipos_dados', 'descricao', 'estatisticas']:
        logger.info({
            'event': 'intent_detected_skip_temporal',
            'intent': detected_intent,
            'pergunta': pergunta[:80]
        })
        
        # ✅ V4.0: Usar PROMPTS DINÂMICOS para responder sobre tipos/descrição
        if self.current_dataset_context and self.llm:
            # Gerar prompt dinâmico
            system_prompt = self.prompt_generator.generate_system_prompt(
                dataset_context=self.current_dataset_context,
                analysis_intent=detected_intent
            )
            
            user_prompt = self.prompt_generator.generate_user_prompt_enhancement(
                query=pergunta,
                dataset_context=self.current_dataset_context
            )
            
            # Chamar LLM com prompt dinâmico
            # ... (implementar chamada LLM)
        else:
            # Fallback: gerar resposta sobre tipos diretamente do DataFrame
            return self._generate_data_types_response(df, dataset_context)
    
    # Continuar com análise temporal apenas se pergunta for sobre temporal
    # ...resto do código existente...
```

### CORREÇÃO 3: Criar Método `_generate_data_types_response()`

**Arquivo:** `src/agent/rag_data_agent.py` (adicionar após `_update_dataset_context()`)

**Código:**
```python
def _generate_data_types_response(self, df: pd.DataFrame, dataset_context: DatasetContext) -> str:
    """
    Gera resposta sobre tipos de dados sem usar LLM.
    Usa dados REAIS do DataFrame e DatasetContext.
    
    ELIMINA HARDCODING:
    - Itera sobre df.dtypes (não assume 31 colunas)
    - Detecta categóricas binárias automaticamente
    - Usa estatísticas REAIS de df.describe()
    
    Returns:
        String em Markdown com resposta completa
    """
    resposta = f"# Tipos de Dados do Dataset\n\n"
    resposta += f"**Arquivo:** `{dataset_context.file_path}`\n"
    resposta += f"**Dimensões:** {dataset_context.num_rows:,} linhas × {dataset_context.num_columns} colunas\n"
    resposta += f"**Memória:** {dataset_context.memory_usage_mb:.2f} MB\n\n"
    
    resposta += "## 📊 Resumo por Tipo\n\n"
    resposta += f"- **Numéricas:** {len(dataset_context.numeric_columns)} colunas\n"
    resposta += f"- **Categóricas:** {len(dataset_context.categorical_columns)} colunas\n"
    resposta += f"- **Temporais:** {len(dataset_context.temporal_columns)} colunas\n\n"
    
    # Listar TODAS as colunas com tipos
    resposta += "## 📋 Detalhamento por Coluna\n\n"
    resposta += "| Coluna | Tipo Python | Tipo Pandas | Classificação |\n"
    resposta += "|--------|-------------|-------------|---------------|\n"
    
    for col in df.columns:
        dtype = df[col].dtype
        py_type = dtype.name
        
        # Classificar coluna
        if col in dataset_context.numeric_columns:
            classificacao = "Numérica"
        elif col in dataset_context.categorical_columns:
            # Verificar se é binária
            unique_vals = df[col].nunique()
            if unique_vals == 2:
                vals = sorted(df[col].unique())
                classificacao = f"Categórica Binária ({vals[0]}={_interpretar_valor(vals[0])}, {vals[1]}={_interpretar_valor(vals[1])})"
            else:
                classificacao = f"Categórica ({unique_vals} valores únicos)"
        elif col in dataset_context.temporal_columns:
            classificacao = "Temporal"
        else:
            classificacao = "Outro"
        
        resposta += f"| `{col}` | {py_type} | {dtype} | {classificacao} |\n"
    
    # Adicionar estatísticas básicas
    resposta += "\n## 📈 Estatísticas Gerais\n\n"
    desc = df.describe()
    resposta += desc.to_markdown() + "\n"
    
    return resposta

def _interpretar_valor(val):
    """Interpreta valores binários (ex: 0=não fraude, 1=fraude para coluna Class)"""
    if val == 0:
        return "não/false/normal"
    elif val == 1:
        return "sim/true/positivo"
    return str(val)
```

## Próximos Passos

1. ✅ Implementar CORREÇÃO 1 (adicionar GROQ ao `_init_langchain_llm()`)
2. ✅ Implementar CORREÇÃO 2 (interpretar pergunta antes de decidir análise)
3. ✅ Implementar CORREÇÃO 3 (criar `_generate_data_types_response()`)
4. ✅ Testar novamente com Pergunta 01
5. ✅ Validar que lista TODAS as 31 colunas com tipos corretos

## Impacto Estimado

- **Tempo de implementação:** ~30 minutos
- **Complexidade:** Média (requer refatoração de fluxo)
- **Risco:** Baixo (correções pontuais, não afetam outros fluxos)
- **Benefício:** CRÍTICO - Sistema passará a responder corretamente perguntas sobre tipos de dados
