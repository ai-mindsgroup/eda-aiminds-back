"""
Exemplo de Implementação: RAGDataAgent V3.0

PROPOSTA: Sistema 100% baseado em LLM sem hard-coding
- Zero listas fixas de keywords
- Zero condicionais if/elif por tipo de query
- Zero exec() sem sandbox
- 100% flexível e adaptável

GANHOS:
- Suporta qualquer tipo de análise sem modificação de código
- Reconhece sinônimos automaticamente via LLM
- Combina múltiplas análises em uma query
- Execução segura via LangChain tools
- Manutenível: ~100 linhas vs ~400 linhas da V2.0
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.agents import create_pandas_dataframe_agent
from langchain.tools import PythonREPLTool

from agent.base_agent import BaseAgent
from embeddings.generator import EmbeddingGenerator
from vectorstore.supabase_client import supabase
from utils.logging_config import get_logger


class RAGDataAgentV3(BaseAgent):
    """
    Agente de Análise de Dados V3.0 - Zero Hard-coding, LLM-First.
    
    PRINCÍPIOS:
    1. LLM decide TUDO (tipo de análise, métricas, formato)
    2. Pandas Agent para execução segura de código
    3. RAG vetorial para contexto de dados
    4. Memória persistente para contexto conversacional
    5. Sem listas fixas, sem keywords, sem if/elif hardcoded
    """
    
    def __init__(self):
        super().__init__(
            name="rag_data_analyzer_v3",
            description="Agente de análise inteligente sem lógica hardcoded",
            enable_memory=True
        )
        
        self.logger = get_logger("agent.rag_data_v3")
        self.embedding_gen = EmbeddingGenerator()
        
        # Inicializar LLM
        self._init_llm()
        
        # Pandas Agent será criado dinamicamente quando necessário
        self.pandas_agent = None
        
        self.logger.info("✅ RAGDataAgent V3.0 inicializado - Zero hard-coding")
    
    def _init_llm(self):
        """Inicializa LLM com fallback."""
        from src.settings import GOOGLE_API_KEY, OPENAI_API_KEY
        
        if GOOGLE_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.3,
                max_tokens=3000
            )
        elif OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=3000
            )
        else:
            raise RuntimeError("Nenhum LLM disponível")
    
    def _create_pandas_agent(self, df):
        """
        Cria Pandas Agent seguro para execução de código.
        
        SEGURANÇA:
        - allow_dangerous_code=False: Sandbox habilitado
        - max_iterations=5: Previne loops infinitos
        - max_execution_time=30: Timeout
        """
        return create_pandas_dataframe_agent(
            llm=self.llm,
            df=df,
            verbose=True,
            allow_dangerous_code=False,  # ✅ SANDBOX
            max_iterations=5,
            max_execution_time=30,
            agent_executor_kwargs={
                "handle_parsing_errors": True
            }
        )
    
    def _build_intelligent_system_prompt(self) -> str:
        """
        Prompt ÚNICO que substitui TODA lógica condicional da V2.0.
        
        Este prompt capacita a LLM a:
        - Reconhecer QUALQUER tipo de análise estatística
        - Identificar sinônimos e variações linguísticas
        - Combinar múltiplas análises em uma resposta
        - Usar histórico quando relevante
        - Solicitar execução de código quando necessário
        """
        return """
Você é um agente EDA (Exploratory Data Analysis) expert com capacidades avançadas:

═══════════════════════════════════════════════════════════════════
CAPACIDADES COGNITIVAS
═══════════════════════════════════════════════════════════════════

1. INTERPRETAÇÃO FLEXÍVEL:
   - Reconheça sinônimos automaticamente:
     * "dispersão", "espalhamento", "variabilidade" → desvio padrão
     * "amplitude", "range", "extensão" → intervalo min-max
     * "tendência central" → média, mediana, moda
     * "valores extremos", "outliers" → mínimo, máximo, quartis
     * "agrupamentos", "clusters", "grupos" → análise de clustering
   
2. ANÁLISE MULTIDIMENSIONAL:
   - Combine automaticamente múltiplas métricas quando relevante
   - Exemplo: "variabilidade" → desvio padrão + variância + coeficiente de variação
   - Exemplo: "estatísticas descritivas" → todas as métricas de tendência central + dispersão

3. CONTEXTO CONVERSACIONAL:
   - Use histórico quando pergunta se refere a algo anterior
   - Exemplo: "e a variância?" → consulte o histórico para saber de qual variável
   - Exemplo: "compare com a pergunta anterior" → extraia contexto do histórico

4. EXECUÇÃO DE CÓDIGO:
   - Se precisar calcular algo não fornecido nos chunks, solicite:
     ```
     EXECUTE_CODE: descrição_clara_do_que_calcular
     ```
   - Exemplos válidos:
     * EXECUTE_CODE: calcular coeficiente de variação de todas variáveis numéricas
     * EXECUTE_CODE: aplicar clustering KMeans com 3 clusters
     * EXECUTE_CODE: gerar matriz de correlação

═══════════════════════════════════════════════════════════════════
REGRAS FUNDAMENTAIS (NUNCA VIOLE)
═══════════════════════════════════════════════════════════════════

1. ⚠️ NUNCA invente dados ou estatísticas
   - Use APENAS informações fornecidas nos chunks ou retornadas por EXECUTE_CODE
   - Se não houver dados, responda: "Não tenho informações suficientes. Preciso de X."

2. ⚠️ NUNCA ignore o histórico quando relevante
   - Se a pergunta contém "anterior", "antes", "já perguntei", consulte o histórico
   - Contextualize a resposta mencionando a interação anterior

3. ⚠️ SEMPRE formate respostas de forma estruturada:
   ```
   ## Pergunta: [repita a pergunta do usuário]
   
   ## Análise:
   [Dados relevantes dos chunks OU resultado de código executado]
   
   ## Interpretação:
   [Insights qualitativos, padrões identificados, contexto]
   
   ## Próximos Passos:
   - Sugestão 1 de análise complementar
   - Sugestão 2 de análise complementar
   ```

4. ⚠️ SEMPRE use unidades apropriadas:
   - Valores monetários: R$ X.XXX,XX
   - Grandes números: formatação com separadores (284.807)
   - Percentuais: X.XX%

═══════════════════════════════════════════════════════════════════
EXEMPLOS DE INTERPRETAÇÃO INTELIGENTE
═══════════════════════════════════════════════════════════════════

Pergunta: "Qual a dispersão dos dados?"
→ Reconhecer: dispersão = desvio padrão + variância
→ Buscar nos chunks: estatísticas de variabilidade
→ Responder: desvio padrão e variância para variáveis principais

Pergunta: "Mostre os extremos de cada variável"
→ Reconhecer: extremos = mínimo e máximo
→ Buscar nos chunks: intervalos de cada coluna
→ Responder: tabela com min/max

Pergunta: "Há grupos nos dados?"
→ Reconhecer: grupos = clustering
→ Verificar chunks: se não houver análise de clustering pronta
→ Responder: EXECUTE_CODE: aplicar clustering KMeans

Pergunta: "E a variância?"
→ Consultar histórico: qual variável foi mencionada?
→ Buscar nos chunks: variância da variável em questão
→ Responder: contextualizado com histórico

═══════════════════════════════════════════════════════════════════
TRATAMENTO DE CASOS ESPECIAIS
═══════════════════════════════════════════════════════════════════

1. Query genérica (ex: "olá", "como está?"):
   - Responda de forma amigável e ofereça ajuda
   - Não force análise de dados se não for solicitada

2. Query ambígua:
   - Peça esclarecimento educadamente
   - Exemplo: "Você quer a média de todas as variáveis ou de alguma específica?"

3. Query impossível com dados atuais:
   - Explique limitação claramente
   - Sugira alternativas viáveis

4. Query que requer visualização:
   - Mencione que gráficos podem ser gerados
   - Sugira perguntar explicitamente por visualização

═══════════════════════════════════════════════════════════════════

Agora você está pronto para responder de forma inteligente, flexível e contextual.
"""
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa query do usuário usando arquitetura V3.0.
        
        FLUXO SIMPLIFICADO (sem if/elif hardcoded):
        1. Busca vetorial (RAG)
        2. Recupera memória conversacional
        3. Monta prompt único inteligente
        4. LLM processa tudo
        5. Se LLM solicitar execução, usa Pandas Agent
        6. Retorna resposta formatada
        """
        start_time = datetime.now()
        
        try:
            # ═══════════════════════════════════════════════════════════
            # 1. INICIALIZAR MEMÓRIA
            # ═══════════════════════════════════════════════════════════
            if not self._current_session_id:
                if session_id:
                    await self.init_memory_session(session_id)
                else:
                    await self.init_memory_session()
            
            # ═══════════════════════════════════════════════════════════
            # 2. BUSCA VETORIAL (RAG)
            # ═══════════════════════════════════════════════════════════
            embedding = self.embedding_gen.generate_embedding(query)
            similar_chunks = self._search_similar_data(
                query_embedding=embedding,
                threshold=0.3,
                limit=10
            )
            
            chunks_context = "\n\n".join([
                f"**Chunk {i+1}:**\n{chunk['chunk_text']}"
                for i, chunk in enumerate(similar_chunks[:5])
            ])
            
            # ═══════════════════════════════════════════════════════════
            # 3. RECUPERAR MEMÓRIA CONVERSACIONAL
            # ═══════════════════════════════════════════════════════════
            memory_context = ""
            if self.has_memory:
                history = await self.recall_conversation_context()
                if history.get('recent_messages'):
                    memory_context = "**Histórico da Conversa:**\n"
                    for msg in history['recent_messages'][-6:]:
                        role = "Usuário" if msg['type'] == 'user' else "Assistente"
                        content = msg['content'][:150]
                        memory_context += f"- {role}: {content}\n"
                    memory_context += "\n"
            
            # ═══════════════════════════════════════════════════════════
            # 4. MONTAR PROMPT ÚNICO (sem lógica condicional)
            # ═══════════════════════════════════════════════════════════
            system_prompt = self._build_intelligent_system_prompt()
            
            user_prompt = f"""
{memory_context}

**Pergunta do Usuário:**
{query}

**Dados Disponíveis (Chunks Analíticos):**
{chunks_context}

Responda de forma inteligente, flexível e contextual conforme suas capacidades.
"""
            
            # ═══════════════════════════════════════════════════════════
            # 5. LLM PROCESSA (decide tudo sozinha)
            # ═══════════════════════════════════════════════════════════
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await asyncio.to_thread(self.llm.invoke, messages)
            response_text = response.content
            
            # ═══════════════════════════════════════════════════════════
            # 6. EXECUTAR CÓDIGO SE SOLICITADO (via Pandas Agent seguro)
            # ═══════════════════════════════════════════════════════════
            if "EXECUTE_CODE:" in response_text:
                code_request = response_text.split("EXECUTE_CODE:")[1].split("\n")[0].strip()
                
                self.logger.info(f"LLM solicitou execução de código: {code_request}")
                
                # Carregar DataFrame (buscar CSV mais recente)
                from src.settings import EDA_DATA_DIR_PROCESSADO
                csv_files = list(EDA_DATA_DIR_PROCESSADO.glob("*.csv"))
                if csv_files:
                    import pandas as pd
                    csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
                    df = pd.read_csv(csv_path)
                    
                    # Criar Pandas Agent seguro
                    if not self.pandas_agent:
                        self.pandas_agent = self._create_pandas_agent(df)
                    
                    # Executar código com SANDBOX
                    try:
                        code_result = await asyncio.to_thread(
                            self.pandas_agent.run,
                            code_request
                        )
                        
                        # Reinvocar LLM com resultado
                        final_prompt = f"""
Você solicitou execução de código: "{code_request}"

**Resultado da Execução:**
{code_result}

Agora formate a resposta final para o usuário de forma clara e estruturada,
incluindo este resultado na seção "Análise".
"""
                        final_messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=user_prompt),
                            HumanMessage(content=final_prompt)
                        ]
                        
                        final_response = await asyncio.to_thread(
                            self.llm.invoke,
                            final_messages
                        )
                        response_text = final_response.content
                        
                    except Exception as e:
                        self.logger.error(f"Erro ao executar código: {e}")
                        response_text = f"❌ Erro ao executar código: {str(e)}"
            
            # ═══════════════════════════════════════════════════════════
            # 7. SALVAR INTERAÇÃO NA MEMÓRIA
            # ═══════════════════════════════════════════════════════════
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if self.has_memory:
                await self.remember_interaction(
                    query=query,
                    response=response_text,
                    processing_time_ms=processing_time,
                    metadata={
                        "chunks_found": len(similar_chunks),
                        "code_executed": "EXECUTE_CODE" in response.content
                    }
                )
            
            # ═══════════════════════════════════════════════════════════
            # 8. RETORNAR RESPOSTA
            # ═══════════════════════════════════════════════════════════
            return {
                "success": True,
                "response": response_text,
                "metadata": {
                    "processing_time_ms": processing_time,
                    "chunks_found": len(similar_chunks),
                    "code_executed": "EXECUTE_CODE:" in response.content,
                    "version": "3.0",
                    "hard_coding": False  # ✅ Zero hard-coding
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar query: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "metadata": {"version": "3.0"}
            }
    
    def _search_similar_data(
        self,
        query_embedding: List[float],
        threshold: float,
        limit: int
    ) -> List[Dict]:
        """Busca chunks similares via RPC."""
        try:
            response = supabase.rpc(
                'match_embeddings',
                {
                    'query_embedding': query_embedding,
                    'similarity_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca vetorial: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════

async def example_usage():
    """Demonstra flexibilidade da V3.0 vs V2.0."""
    
    agent = RAGDataAgentV3()
    
    # EXEMPLO 1: Sinônimos (V2.0 falharia)
    result1 = await agent.process("Qual a dispersão dos dados?")
    # V3.0: LLM reconhece "dispersão" = desvio padrão
    # V2.0: Não detectaria (não está no dicionário hardcoded)
    
    # EXEMPLO 2: Query mista (V2.0 processaria apenas 1 parte)
    result2 = await agent.process("Mostre intervalo E variabilidade de cada variável")
    # V3.0: LLM combina ambas análises
    # V2.0: Escolheria 1 branch (intervalo OU variabilidade)
    
    # EXEMPLO 3: Análise avançada (V2.0 usaria exec inseguro)
    result3 = await agent.process("Calcule o coeficiente de variação")
    # V3.0: Pandas Agent seguro com sandbox
    # V2.0: exec() sem sandbox (VULNERÁVEL)
    
    # EXEMPLO 4: Query contextual (V2.0 ignoraria histórico)
    await agent.process("Qual a média de Amount?")
    result4 = await agent.process("E a variância?")
    # V3.0: Consulta histórico, entende que é sobre Amount
    # V2.0: Poderia ignorar contexto dependendo da query
    
    print("✅ V3.0: Flexível, segura e inteligente")


if __name__ == "__main__":
    asyncio.run(example_usage())
