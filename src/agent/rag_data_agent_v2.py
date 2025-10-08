"""
Agente de Análise de Dados via RAG Vetorial Puro com Memória Persistente e LangChain.

VERSÃO 2.0 - REFATORADA:
- ✅ Memória persistente em Supabase (tabelas agent_sessions, agent_conversations, agent_context)
- ✅ LangChain integrado nativamente (ChatOpenAI, ChatGoogleGenerativeAI)
- ✅ Métodos async para performance
- ✅ Contexto conversacional entre interações
- ✅ Busca vetorial pura (sem keywords hardcoded)
"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime
import asyncio

from src.agent.base_agent import BaseAgent, AgentError
from src.vectorstore.supabase_client import supabase
from src.embeddings.generator import EmbeddingGenerator
from src.utils.logging_config import get_logger

# Imports LangChain
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    ChatGoogleGenerativeAI = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None
    print(f"⚠️ LangChain não disponível: {e}")


class RAGDataAgent(BaseAgent):
    """
    Agente que responde perguntas sobre dados usando RAG vetorial + memória persistente + LangChain.
    
    Fluxo V2.0:
    1. Inicializa sessão de memória (se não existir)
    2. Recupera contexto conversacional anterior
    3. Gera embedding da pergunta
    4. Busca chunks similares nos DADOS usando match_embeddings()
    5. Usa LangChain LLM para interpretar chunks + contexto histórico
    6. Salva interação na memória persistente
    7. Retorna resposta contextualizada
    
    SEM keywords hardcoded, SEM classificação manual, SEM listas fixas.
    COM memória persistente, COM LangChain, COM contexto conversacional.
    """
    
    def __init__(self):
        super().__init__(
            name="rag_data_analyzer",
            description="Analisa dados usando busca vetorial semântica pura com memória persistente",
            enable_memory=True  # ✅ CRÍTICO: Habilita memória persistente
        )
        self.logger = get_logger("agent.rag_data")
        self.embedding_gen = EmbeddingGenerator()
        
        # Inicializar LLM LangChain
        self._init_langchain_llm()
        
        self.logger.info("✅ RAGDataAgent V2.0 inicializado - RAG vetorial + memória + LangChain")
    
    def _init_langchain_llm(self):
        """Inicializa LLM do LangChain com fallback."""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("⚠️ LangChain não disponível - usando fallback")
            self.llm = None
            return
        
        try:
            # Tentar Google Gemini primeiro (melhor custo-benefício)
            from src.settings import GOOGLE_API_KEY
            if GOOGLE_API_KEY:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.3,
                    max_tokens=2000,
                    google_api_key=GOOGLE_API_KEY
                )
                self.logger.info("✅ LLM LangChain inicializado: Google Gemini")
                return
        except Exception as e:
            self.logger.warning(f"Google Gemini não disponível: {e}")
        
        try:
            # Fallback: OpenAI
            from src.settings import OPENAI_API_KEY
            if OPENAI_API_KEY:
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    max_tokens=2000,
                    openai_api_key=OPENAI_API_KEY
                )
                self.logger.info("✅ LLM LangChain inicializado: OpenAI GPT-4o-mini")
                return
        except Exception as e:
            self.logger.warning(f"OpenAI não disponível: {e}")
        
        self.llm = None
        self.logger.warning("⚠️ Nenhum LLM LangChain disponível - usando fallback manual")
    
    async def process(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa query do usuário usando RAG vetorial + memória persistente.
        
        VERSÃO ASYNC com memória persistente.
        
        Args:
            query: Pergunta do usuário
            context: Contexto adicional (opcional)
            session_id: ID da sessão para memória persistente
            
        Returns:
            Resposta baseada em busca vetorial + contexto histórico
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🔍 Processando query via RAG V2.0: {query[:80]}...")
            
            # ═══════════════════════════════════════════════════════════════
            # 1. INICIALIZAR MEMÓRIA PERSISTENTE
            # ═══════════════════════════════════════════════════════════════
            if not self._current_session_id:
                if session_id:
                    await self.init_memory_session(session_id)
                else:
                    session_id = await self.init_memory_session()
                self.logger.info(f"✅ Sessão de memória inicializada: {session_id}")
            
            # ═══════════════════════════════════════════════════════════════
            # 2. RECUPERAR CONTEXTO CONVERSACIONAL ANTERIOR
            # ═══════════════════════════════════════════════════════════════
            memory_context = {}
            if self.has_memory and self._current_session_id:
                memory_context = await self.recall_conversation_context()
                self.logger.debug(
                    f"✅ Contexto de memória recuperado: "
                    f"{len(memory_context.get('recent_conversations', []))} interações anteriores"
                )
            
            # ═══════════════════════════════════════════════════════════════
            # 3. GERAR EMBEDDING DA QUERY
            # ═══════════════════════════════════════════════════════════════
            self.logger.debug("Gerando embedding da query...")
            embedding_result = self.embedding_gen.generate_embedding(query)
            
            # Extrair lista de floats do resultado
            if isinstance(embedding_result, list):
                query_embedding = embedding_result
            elif hasattr(embedding_result, 'embedding'):
                query_embedding = embedding_result.embedding
            else:
                return self._build_error_response("Formato de embedding inválido")
            
            if not query_embedding or len(query_embedding) == 0:
                return self._build_error_response("Falha ao gerar embedding da query")
            
            # ═══════════════════════════════════════════════════════════════
            # 4. BUSCAR CHUNKS SIMILARES NOS DADOS
            # ═══════════════════════════════════════════════════════════════
            self.logger.debug("Buscando chunks similares nos dados...")
            similar_chunks = self._search_similar_data(
                query_embedding=query_embedding,
                threshold=0.5,  # Threshold permissivo para capturar contexto relevante
                limit=10
            )
            
            if not similar_chunks:
                response_text = (
                    "❌ Nenhum dado relevante encontrado na base vetorial. "
                    "Verifique se os dados foram carregados corretamente com: "
                    "`python load_csv_data.py <arquivo.csv>`"
                )
                
                # Salvar na memória mesmo com erro
                if self.has_memory:
                    await self.remember_interaction(
                        query=query,
                        response=response_text,
                        processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        confidence=0.0,
                        model_used="rag_vectorial_v2",
                        metadata={"chunks_found": 0, "error": True}
                    )
                
                return self._build_response(
                    response_text,
                    metadata={"chunks_found": 0, "method": "rag_vectorial_v2"}
                )
            
            self.logger.info(f"✅ Encontrados {len(similar_chunks)} chunks relevantes")
            
            # ═══════════════════════════════════════════════════════════════
            # 5. GERAR RESPOSTA COM LANGCHAIN + CONTEXTO HISTÓRICO
            # ═══════════════════════════════════════════════════════════════
            context_texts = [chunk['chunk_text'] for chunk in similar_chunks]
            context_str = "\n\n".join(context_texts[:5])  # Top 5 mais relevantes
            
            self.logger.debug("Usando LangChain LLM para gerar resposta...")
            response_text = await self._generate_llm_response_langchain(
                query=query,
                context_data=context_str,
                memory_context=memory_context,
                chunks_metadata=similar_chunks
            )
            
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            avg_similarity = sum(c['similarity'] for c in similar_chunks) / len(similar_chunks)
            
            # ═══════════════════════════════════════════════════════════════
            # 6. SALVAR INTERAÇÃO NA MEMÓRIA PERSISTENTE
            # ═══════════════════════════════════════════════════════════════
            if self.has_memory:
                await self.remember_interaction(
                    query=query,
                    response=response_text,
                    processing_time_ms=processing_time_ms,
                    confidence=avg_similarity,
                    model_used="langchain_gemini" if self.llm else "fallback",
                    metadata={
                        "chunks_found": len(similar_chunks),
                        "chunks_used": min(5, len(similar_chunks)),
                        "avg_similarity": avg_similarity,
                        "top_similarity": similar_chunks[0]['similarity'],
                        "has_history": len(memory_context.get('recent_conversations', [])) > 0
                    }
                )
                self.logger.debug("✅ Interação salva na memória persistente")
            
            # ═══════════════════════════════════════════════════════════════
            # 7. RETORNAR RESPOSTA COM METADADOS
            # ═══════════════════════════════════════════════════════════════
            return self._build_response(
                response_text,
                metadata={
                    "chunks_found": len(similar_chunks),
                    "chunks_used": min(5, len(similar_chunks)),
                    "avg_similarity": avg_similarity,
                    "method": "rag_vectorial_v2",
                    "top_similarity": similar_chunks[0]['similarity'] if similar_chunks else 0,
                    "processing_time_ms": processing_time_ms,
                    "has_memory": self.has_memory,
                    "session_id": self._current_session_id,
                    "previous_interactions": len(memory_context.get('recent_conversations', []))
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar query: {str(e)}", exc_info=True)
            return self._build_error_response(f"Erro no processamento: {str(e)}")
    
    def _search_similar_data(
        self,
        query_embedding: List[float],
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca chunks similares nos dados usando match_embeddings RPC.
        
        Args:
            query_embedding: Embedding da query
            threshold: Threshold de similaridade (0.0 - 1.0)
            limit: Número máximo de resultados
            
        Returns:
            Lista de chunks similares com metadata
        """
        try:
            # Chamar função RPC match_embeddings
            response = supabase.rpc(
                'match_embeddings',
                {
                    'query_embedding': query_embedding,
                    'similarity_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            if not response.data:
                self.logger.warning("Nenhum chunk similar encontrado")
                return []
            
            self.logger.debug(f"Encontrados {len(response.data)} chunks similares")
            return response.data
            
        except Exception as e:
            self.logger.error(f"Erro na busca vetorial: {str(e)}")
            return []
    
    async def _generate_llm_response_langchain(
        self,
        query: str,
        context_data: str,
        memory_context: Dict[str, Any],
        chunks_metadata: List[Dict]
    ) -> str:
        """
        Gera resposta usando LangChain LLM + contexto histórico.
        
        Args:
            query: Pergunta do usuário
            context_data: Dados dos chunks concatenados
            memory_context: Contexto de conversas anteriores
            chunks_metadata: Metadados dos chunks
            
        Returns:
            Resposta gerada pelo LLM LangChain
        """
        try:
            # Preparar contexto histórico
            history_context = ""
            if memory_context.get('recent_conversations'):
                history_context = "\n\n**Contexto da Conversa Anterior:**\n"
                for conv in memory_context['recent_conversations'][-3:]:  # Últimas 3 interações
                    history_context += f"- Usuário: {conv.get('query', '')[:100]}\n"
                    history_context += f"- Assistente: {conv.get('response', '')[:100]}\n"
            
            # Preparar prompt
            system_prompt = """Você é um especialista em análise de dados.
Analise os dados fornecidos e responda à pergunta do usuário de forma clara e precisa.

IMPORTANTE:
- Use APENAS os dados fornecidos no contexto
- Se houver histórico de conversa, considere-o para dar respostas mais contextualizadas
- Se os dados contiverem valores numéricos, calcule estatísticas quando apropriado
- Forneça números exatos sempre que possível
- Se não houver informação suficiente, diga isso claramente
- Formate a resposta em Markdown para melhor legibilidade
"""
            
            user_prompt = f"""{history_context}

**Pergunta do Usuário:**
{query}

**Dados Disponíveis (extraídos da base vetorial):**
{context_data}

**Instruções:**
1. Analise os dados fornecidos
2. Considere o histórico da conversa (se houver)
3. Responda à pergunta de forma direta e objetiva
4. Inclua estatísticas e números quando relevante
5. Formate tabelas quando apropriado

**Resposta:**"""
            
            # Usar LangChain LLM se disponível
            if self.llm and LANGCHAIN_AVAILABLE:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = await asyncio.to_thread(self.llm.invoke, messages)
                return response.content
            
            # Fallback: usar LLM Manager customizado
            else:
                from src.llm.manager import LLMManager
                llm_manager = LLMManager()
                
                llm_response = llm_manager.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                if not llm_response or 'error' in llm_response:
                    return self._format_raw_data_response(query, chunks_metadata)
                
                response_text = llm_response.get('content', llm_response.get('response', llm_response.get('text', '')))
                
                if not response_text:
                    return self._format_raw_data_response(query, chunks_metadata)
                
                return response_text
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta LLM: {str(e)}", exc_info=True)
            return self._format_raw_data_response(query, chunks_metadata)
    
    def _format_raw_data_response(
        self,
        query: str,
        chunks_metadata: List[Dict]
    ) -> str:
        """
        Fallback: formata resposta básica com dados brutos se LLM falhar.
        """
        response = f"## Resposta para: {query}\n\n"
        response += f"**Dados encontrados na base vetorial:**\n\n"
        
        for i, chunk in enumerate(chunks_metadata[:3], 1):
            similarity = chunk.get('similarity', 0)
            text = chunk.get('chunk_text', '')[:500]
            response += f"### Chunk {i} (similaridade: {similarity:.2f})\n"
            response += f"```\n{text}\n```\n\n"
        
        response += f"\n_Nota: Resposta gerada diretamente dos dados vetoriais (LLM indisponível)._"
        return response
    
    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Constrói resposta de erro padronizada."""
        return self._build_response(
            f"❌ {error_msg}",
            metadata={"error": True, "method": "rag_vectorial_v2"}
        )
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODO SÍNCRONO WRAPPER (para compatibilidade retroativa)
    # ═══════════════════════════════════════════════════════════════
    
    def process_sync(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Wrapper síncrono para compatibilidade com código legado.
        
        ⚠️ DEPRECATED: Use process() async quando possível.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process(query, context))
    
    # ═══════════════════════════════════════════════════════════════
    # MÉTODO DE CARREGAMENTO CSV (mantido da versão anterior)
    # ═══════════════════════════════════════════════════════════════
    
    async def load_csv_to_embeddings(
        self,
        csv_path: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> Dict[str, Any]:
        """
        Carrega CSV para a tabela embeddings.
        
        Args:
            csv_path: Caminho do arquivo CSV
            chunk_size: Tamanho dos chunks
            overlap: Overlap entre chunks
            
        Returns:
            Status do carregamento
        """
        try:
            self.logger.info(f"📂 Carregando CSV: {csv_path}")
            
            import pandas as pd
            from src.embeddings.chunker import CSVChunker
            
            # Ler CSV
            df = pd.read_csv(csv_path)
            self.logger.info(f"✅ CSV lido: {len(df)} linhas, {len(df.columns)} colunas")
            
            # Criar chunks
            chunker = CSVChunker(chunk_size=chunk_size, overlap=overlap)
            chunks = chunker.chunk_dataframe(df)
            self.logger.info(f"✅ Criados {len(chunks)} chunks")
            
            # Gerar embeddings e salvar
            inserted_count = 0
            for i, chunk in enumerate(chunks):
                try:
                    # Gerar embedding
                    embedding = self.embedding_gen.generate_embedding(chunk['text'])
                    
                    # Salvar na tabela embeddings
                    insert_data = {
                        'chunk_text': chunk['text'],
                        'embedding': embedding,
                        'metadata': {
                            'source': csv_path,
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'created_at': datetime.now().isoformat()
                        }
                    }
                    
                    result = supabase.table('embeddings').insert(insert_data).execute()
                    
                    if result.data:
                        inserted_count += 1
                        if (i + 1) % 10 == 0:
                            self.logger.info(f"Progresso: {i+1}/{len(chunks)} chunks inseridos")
                
                except Exception as chunk_error:
                    self.logger.warning(f"Erro no chunk {i}: {chunk_error}")
                    continue
            
            self.logger.info(f"✅ Carregamento concluído: {inserted_count}/{len(chunks)} chunks inseridos")
            
            return self._build_response(
                f"✅ CSV carregado com sucesso: {inserted_count} chunks inseridos na base vetorial",
                metadata={
                    'csv_path': csv_path,
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'chunks_created': len(chunks),
                    'chunks_inserted': inserted_count
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar CSV: {str(e)}")
            return self._build_error_response(f"Falha ao carregar CSV: {str(e)}")
