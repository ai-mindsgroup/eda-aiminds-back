"""
Agente de Análise de Dados via RAG Vetorial Puro.

Este agente NÃO usa keywords hardcoded.
Ele busca semanticamente nos dados carregados na tabela embeddings usando match_embeddings().
"""

from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from src.agent.base_agent import BaseAgent, AgentError
from src.vectorstore.supabase_client import supabase
from src.embeddings.generator import EmbeddingGenerator
from src.utils.logging_config import get_logger


class RAGDataAgent(BaseAgent):
    """
    Agente que responde perguntas sobre dados usando APENAS busca vetorial.
    
    Fluxo:
    1. Usuário faz pergunta (ex: "Qual a variabilidade dos dados?")
    2. Gera embedding da pergunta
    3. Busca chunks similares nos DADOS usando match_embeddings()
    4. Usa LLM para interpretar os chunks e gerar resposta
    
    SEM keywords hardcoded, SEM classificação manual, SEM listas fixas.
    """
    
    def __init__(self):
        super().__init__(
            name="rag_data_analyzer",
            description="Analisa dados usando busca vetorial semântica pura",
            enable_memory=True
        )
        self.logger = get_logger("agent.rag_data")
        self.embedding_gen = EmbeddingGenerator()
        
        self.logger.info("✅ RAGDataAgent inicializado - busca vetorial pura")
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processa query do usuário usando RAG vetorial.
        
        Args:
            query: Pergunta do usuário
            context: Contexto adicional (opcional)
            
        Returns:
            Resposta baseada em busca vetorial nos dados
        """
        try:
            self.logger.info(f"🔍 Processando query via RAG: {query[:80]}...")
            
            # 1. Gerar embedding da query
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
            
            # 2. Buscar chunks similares nos DADOS usando match_embeddings
            self.logger.debug("Buscando chunks similares nos dados...")
            similar_chunks = self._search_similar_data(
                query_embedding=query_embedding,
                threshold=0.5,  # Threshold permissivo para capturar contexto relevante
                limit=10
            )
            
            if not similar_chunks:
                return self._build_response(
                    "❌ Nenhum dado relevante encontrado na base vetorial. "
                    "Verifique se os dados foram carregados corretamente.",
                    metadata={"chunks_found": 0, "method": "rag_vectorial"}
                )
            
            self.logger.info(f"✅ Encontrados {len(similar_chunks)} chunks relevantes")
            
            # 3. Extrair textos dos chunks para contexto
            context_texts = [chunk['chunk_text'] for chunk in similar_chunks]
            context_str = "\n\n".join(context_texts[:5])  # Top 5 mais relevantes
            
            # 4. Usar LLM para interpretar e responder
            self.logger.debug("Usando LLM para gerar resposta...")
            response_text = self._generate_llm_response(
                query=query,
                context_data=context_str,
                chunks_metadata=similar_chunks
            )
            
            # 5. Retornar resposta com metadados
            return self._build_response(
                response_text,
                metadata={
                    "chunks_found": len(similar_chunks),
                    "chunks_used": min(5, len(similar_chunks)),
                    "avg_similarity": sum(c['similarity'] for c in similar_chunks) / len(similar_chunks),
                    "method": "rag_vectorial",
                    "top_similarity": similar_chunks[0]['similarity'] if similar_chunks else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar query: {str(e)}")
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
    
    def _generate_llm_response(
        self,
        query: str,
        context_data: str,
        chunks_metadata: List[Dict]
    ) -> str:
        """
        Gera resposta usando LLM baseado no contexto dos chunks encontrados.
        
        Args:
            query: Pergunta do usuário
            context_data: Dados dos chunks concatenados
            chunks_metadata: Metadados dos chunks
            
        Returns:
            Resposta gerada pelo LLM
        """
        try:
            # Preparar prompt para o LLM
            system_prompt = """Você é um especialista em análise de dados.
Analise os dados fornecidos e responda à pergunta do usuário de forma clara e precisa.

IMPORTANTE:
- Use APENAS os dados fornecidos no contexto
- Se os dados contiverem valores numéricos, calcule estatísticas quando apropriado
- Forneça números exatos sempre que possível
- Se não houver informação suficiente, diga isso claramente
- Formate a resposta em Markdown para melhor legibilidade
"""
            
            user_prompt = f"""**Pergunta do Usuário:**
{query}

**Dados Disponíveis (extraídos da base vetorial):**
{context_data}

**Instruções:**
1. Analise os dados fornecidos
2. Responda à pergunta de forma direta e objetiva
3. Inclua estatísticas e números quando relevante
4. Formate tabelas quando apropriado

**Resposta:**"""
            
            # Usar LLM manager para gerar resposta
            from src.llm.manager import LLMManager
            llm_manager = LLMManager()
            
            # Chamar método correto do LLM Manager
            llm_response = llm_manager.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            if not llm_response or 'error' in llm_response:
                # Fallback: retornar dados brutos se LLM falhar
                return self._format_raw_data_response(query, chunks_metadata)
            
            # Extrair texto da resposta
            response_text = llm_response.get('content', llm_response.get('response', llm_response.get('text', '')))
            
            if not response_text:
                return self._format_raw_data_response(query, chunks_metadata)
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta LLM: {str(e)}")
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
        
        response += f"\n_Nota: Resposta gerada diretamente dos dados vetoriais._"
        return response
    
    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Constrói resposta de erro padronizada."""
        return self._build_response(
            f"❌ {error_msg}",
            metadata={"error": True, "method": "rag_vectorial"}
        )
    
    def load_csv_to_embeddings(
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
