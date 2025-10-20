"""Extensões V4.0 para RAGDataAgent com Prompts Dinâmicos e Parâmetros Otimizados

Este módulo fornece métodos de extensão para o RAGDataAgent existente,
integrando:
- Sistema de prompts dinâmicos (src/prompts/dynamic_prompts.py)
- Configurações LLM/RAG otimizadas (src/llm/optimized_config.py)
- Fallback inteligente para CSV direto
- Geração automática de visualizações

USAR ESTE MÓDULO EM VEZ DE MODIFICAR RAGDataAgent DIRETAMENTE.

Autor: EDA AI Minds Team
Data: 2025-10-18
Versão: 4.0.0
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List
import pandas as pd
from datetime import datetime

# Adicionar diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agent.rag_data_agent import RAGDataAgent
from src.prompts.dynamic_prompts import (
    DynamicPromptGenerator,
    DatasetContext,
    get_dynamic_prompt_generator
)
from src.llm.optimized_config import (
    get_configs_for_intent,
    AnalysisType,
    get_llm_config,
    get_rag_config
)
from src.analysis.intent_classifier import IntentClassifier, AnalysisIntent
from src.utils.logging_config import get_logger
from src.vectorstore.supabase_client import supabase

logger = get_logger(__name__)


class RAGDataAgentV4(RAGDataAgent):
    """
    RAGDataAgent V4.0 com prompts dinâmicos e parâmetros otimizados.
    
    Extensões sobre V2.0:
    - ✅ Prompts completamente dinâmicos (zero hardcoding)
    - ✅ Parâmetros LLM/RAG otimizados por tipo de análise
    - ✅ Fallback inteligente para CSV direto
    - ✅ Contexto de dataset em tempo real
    - ✅ Logs detalhados de configurações usadas
    
    USO:
        agent = RAGDataAgentV4()
        response = agent.query_v4("Quais são os tipos de dados?", session_id="123")
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa agente com extensões V4."""
        super().__init__(*args, **kwargs)
        
        # FORÇAR inicialização do LLM com GROQ se disponível
        self._init_llm_with_groq()
        
        # Inicializar gerador de prompts dinâmicos
        self.prompt_generator = get_dynamic_prompt_generator()
        
        # Cache de contexto do dataset
        self.current_dataset_context: Optional[DatasetContext] = None
        
        # Cache do CSV carregado
        self.cached_csv_df: Optional[pd.DataFrame] = None
        self.cached_csv_path: Optional[str] = None
        
        logger.info("✅ RAGDataAgent V4.0 inicializado com prompts dinâmicos e parâmetros otimizados")
    
    def _init_llm_with_groq(self):
        """
        Inicializa LLM dando prioridade ao GROQ (mais rápido e barato).
        
        Ordem de fallback:
        1. GROQ (llama-3.1-8b-instant) - super rápido
        2. Google Gemini (gemini-1.5-flash) - bom custo-benefício
        3. OpenAI (gpt-4o-mini) - fallback final
        """
        try:
            # 1️⃣ PRIORIDADE: GROQ
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
                    logger.info("✅ LLM V4.0: GROQ (llama-3.1-8b-instant) - SUPER RÁPIDO")
                    return
                except ImportError:
                    logger.warning("⚠️ langchain-groq não instalado, tentando próximo provedor...")
            
            # 2️⃣ Fallback: Google Gemini
            from src.settings import GOOGLE_API_KEY
            if GOOGLE_API_KEY:
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash",
                        temperature=0.3,
                        max_tokens=2048,
                        google_api_key=GOOGLE_API_KEY
                    )
                    logger.info("✅ LLM V4.0: Google Gemini (gemini-1.5-flash)")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Google Gemini falhou: {e}")
            
            # 3️⃣ Fallback final: OpenAI
            from src.settings import OPENAI_API_KEY
            if OPENAI_API_KEY:
                try:
                    from langchain_openai import ChatOpenAI
                    self.llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0.3,
                        max_tokens=2048,
                        openai_api_key=OPENAI_API_KEY
                    )
                    logger.info("✅ LLM V4.0: OpenAI (gpt-4o-mini)")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI falhou: {e}")
            
            # ❌ Nenhum LLM disponível
            self.llm = None
            logger.error("❌ ERRO CRÍTICO: Nenhum LLM disponível! Configure GROQ_API_KEY, GOOGLE_API_KEY ou OPENAI_API_KEY")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar LLM: {e}")
            self.llm = None
    
    def _load_csv_with_fallback(self) -> Optional[pd.DataFrame]:
        """
        Carrega CSV com fallback inteligente.
        
        Tenta:
        1. CSV cache (se já carregado)
        2. Procurar em data/processado/
        3. Buscar metadata.source nos embeddings do Supabase
        
        Returns:
            DataFrame ou None se não encontrado
        """
        # 1. Verificar cache
        if self.cached_csv_df is not None:
            logger.info(f"📦 Usando CSV do cache: {self.cached_csv_path}")
            return self.cached_csv_df
        
        # 2. Procurar em data/processado/
        processado_dir = Path("data/processado")
        if processado_dir.exists():
            csv_files = list(processado_dir.glob("*.csv"))
            if csv_files:
                csv_path = csv_files[0]  # Pegar primeiro CSV encontrado
                logger.info(f"📂 CSV encontrado em data/processado: {csv_path}")
                try:
                    df = pd.read_csv(csv_path)
                    self.cached_csv_df = df
                    self.cached_csv_path = str(csv_path)
                    return df
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar CSV de {csv_path}: {e}")
        
        # 3. Buscar metadata.source no Supabase
        try:
            result = supabase.table('embeddings').select('metadata').limit(1).execute()
            if result.data:
                source_path = result.data[0]['metadata'].get('source')
                if source_path:
                    # Corrigir path se for Windows
                    source_path = source_path.replace('\\', '/')
                    csv_path = Path(source_path)
                    if csv_path.exists():
                        logger.info(f"📊 CSV encontrado via metadata Supabase: {csv_path}")
                        df = pd.read_csv(csv_path)
                        self.cached_csv_df = df
                        self.cached_csv_path = str(csv_path)
                        return df
                    else:
                        # Tentar path relativo
                        csv_path = Path("data/processando") / csv_path.name
                        if csv_path.exists():
                            logger.info(f"📊 CSV encontrado (path relativo): {csv_path}")
                            df = pd.read_csv(csv_path)
                            self.cached_csv_df = df
                            self.cached_csv_path = str(csv_path)
                            return df
        except Exception as e:
            logger.error(f"❌ Erro ao buscar CSV via Supabase metadata: {e}")
        
        logger.warning("⚠️ CSV não encontrado em nenhuma localização")
        return None
    
    def _update_dataset_context(self, df: pd.DataFrame) -> DatasetContext:
        """
        Atualiza contexto do dataset atual.
        
        Args:
            df: DataFrame carregado
            
        Returns:
            DatasetContext atualizado
        """
        file_path = self.cached_csv_path or "unknown"
        context = DatasetContext.from_dataframe(df, file_path)
        self.current_dataset_context = context
        
        logger.info({
            'event': 'dataset_context_updated',
            'file': file_path,
            'shape': context.shape,
            'numeric_cols': len(context.numeric_columns),
            'categorical_cols': len(context.categorical_columns),
            'temporal_cols': len(context.temporal_columns)
        })
        
        return context
    
    def query_v4(
        self,
        query: str,
        session_id: Optional[str] = None,
        force_csv_fallback: bool = False
    ) -> Dict[str, Any]:
        """
        Método principal V4.0 com prompts dinâmicos e parâmetros otimizados.
        
        Args:
            query: Pergunta do usuário
            session_id: ID da sessão (para memória persistente)
            force_csv_fallback: Se True, força análise direta do CSV
            
        Returns:
            Resposta estruturada com metadata completa
        """
        start_time = datetime.now()
        
        try:
            # 1. Carregar CSV e atualizar contexto
            df = self._load_csv_with_fallback()
            if df is None:
                return {
                    'success': False,
                    'error': 'CSV não encontrado. Faça upload de um dataset primeiro.',
                    'metadata': {'timestamp': datetime.now().isoformat()}
                }
            
            dataset_context = self._update_dataset_context(df)
            
            # 2. Classificar intenção da pergunta
            classifier = IntentClassifier(llm=self.llm, logger=self.logger)
            
            context_info = {
                'available_columns': dataset_context.columns,
                'numeric_count': len(dataset_context.numeric_columns),
                'categorical_count': len(dataset_context.categorical_columns),
                'shape': dataset_context.shape
            }
            
            intent_result = classifier.classify(query, context=context_info)
            
            logger.info({
                'event': 'intent_classified',
                'query': query[:100],
                'primary_intent': intent_result.primary_intent.value,
                'confidence': intent_result.confidence
            })
            
            # 3. Obter configurações otimizadas baseadas na intenção
            llm_config, rag_config = get_configs_for_intent(intent_result.primary_intent.value)
            
            logger.info({
                'event': 'configs_selected',
                'llm_temperature': llm_config.temperature,
                'llm_max_tokens': llm_config.max_tokens,
                'rag_threshold': rag_config.similarity_threshold,
                'rag_chunk_size': rag_config.chunk_size,
                'rag_max_chunks': rag_config.max_chunks
            })
            
            # 4. Buscar contexto via RAG (se não for forçado fallback)
            rag_context = ""
            if not force_csv_fallback:
                try:
                    rag_context = self._search_rag_context(
                        query,
                        threshold=rag_config.similarity_threshold,
                        limit=rag_config.max_chunks
                    )
                    logger.info(f"📚 RAG context recuperado: {len(rag_context)} caracteres")
                except Exception as e:
                    logger.warning(f"⚠️ RAG search falhou, usando fallback: {e}")
                    force_csv_fallback = True
            
            # 5. Gerar prompt dinâmico baseado no dataset e intenção
            system_prompt = self.prompt_generator.generate_system_prompt(
                dataset_context=dataset_context,
                analysis_intent=intent_result.primary_intent.value,
                additional_capabilities=[]
            )
            
            # 6. Recuperar histórico conversacional (se houver session_id)
            history_context = ""
            if session_id:
                history_context = self._get_conversation_history(session_id)
            
            # 7. Construir prompt do usuário enriquecido
            user_prompt = self.prompt_generator.generate_user_prompt_enhancement(
                original_query=query,
                dataset_context=dataset_context,
                historical_context=history_context,
                retrieved_chunks=rag_context
            )
            
            # 8. Chamada LLM com parâmetros otimizados
            from langchain.schema import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # Aplicar configurações otimizadas ao LLM
            # Nota: Alguns parâmetros podem não ser suportados por todos os LLMs
            try:
                if hasattr(self.llm, 'temperature'):
                    self.llm.temperature = llm_config.temperature
                if hasattr(self.llm, 'max_tokens'):
                    self.llm.max_tokens = llm_config.max_tokens
                if hasattr(self.llm, 'top_p'):
                    self.llm.top_p = llm_config.top_p
            except Exception as e:
                logger.warning(f"⚠️ Alguns parâmetros LLM não puderam ser aplicados: {e}")
            
            response = self.llm.invoke(messages)
            answer = response.content
            
            # 9. Detectar se necessita visualização e gerar
            visualization_paths = []
            if self._requires_visualization(query, intent_result):
                logger.info("📊 Pergunta requer visualização, gerando gráficos...")
                visualization_paths = self._generate_visualizations(
                    df,
                    query,
                    intent_result.primary_intent
                )
            
            # 10. Salvar na memória persistente (se session_id fornecido)
            if session_id:
                self._save_to_memory(
                    session_id=session_id,
                    query=query,
                    response=answer,
                    metadata={
                        'intent': intent_result.primary_intent.value,
                        'llm_config': llm_config.description,
                        'rag_config': rag_config.description,
                        'visualizations': visualization_paths
                    }
                )
            
            # 11. Construir resposta final
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'answer': answer,
                'query': query,
                'intent': intent_result.primary_intent.value,
                'confidence': intent_result.confidence,
                'visualizations': visualization_paths,
                'metadata': {
                    'version': '4.0',
                    'dataset_file': dataset_context.file_path,
                    'dataset_shape': dataset_context.shape,
                    'llm_config': {
                        'temperature': llm_config.temperature,
                        'max_tokens': llm_config.max_tokens,
                        'description': llm_config.description
                    },
                    'rag_config': {
                        'threshold': rag_config.similarity_threshold,
                        'max_chunks': rag_config.max_chunks,
                        'description': rag_config.description
                    },
                    'used_csv_fallback': force_csv_fallback,
                    'rag_context_length': len(rag_context),
                    'processing_time_seconds': elapsed_time,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no query_v4: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'metadata': {
                    'version': '4.0',
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def _search_rag_context(
        self,
        query: str,
        threshold: float = 0.65,
        limit: int = 7
    ) -> str:
        """
        Busca contexto via RAG com parâmetros otimizados.
        
        Args:
            query: Query do usuário
            threshold: Threshold de similaridade
            limit: Número máximo de chunks
            
        Returns:
            Contexto concatenado
        """
        try:
            # Gerar embedding da query
            from src.embeddings.generator import EmbeddingGenerator
            emb_gen = EmbeddingGenerator()
            embedding_result = emb_gen.generate_embedding(query)  # Corrigido: generate_embedding
            query_embedding = embedding_result.embedding
            
            # Buscar chunks similares
            result = supabase.rpc(
                'match_embeddings',  # FIX: Usar função correta (sem _v2)
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            if not result.data:
                logger.warning(f"⚠️ Nenhum chunk encontrado com threshold={threshold}")
                return ""
            
            # Concatenar chunks
            chunks = [item['chunk_text'] for item in result.data]
            context = "\n\n---\n\n".join(chunks)
            
            logger.info(f"✅ RAG: {len(result.data)} chunks recuperados (threshold={threshold})")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Erro na busca RAG: {e}")
            return ""
    
    def _get_conversation_history(self, session_id: str, limit: int = 5) -> str:
        """
        Recupera histórico conversacional da memória persistente.
        
        Args:
            session_id: ID da sessão
            limit: Número de interações anteriores
            
        Returns:
            Histórico formatado
        """
        try:
            result = supabase.table('agent_conversations') \
                .select('*') \
                .eq('session_id', session_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            if not result.data:
                return ""
            
            history = []
            for conv in reversed(result.data):  # Ordem cronológica
                history.append(f"**Usuário:** {conv['query']}")
                history.append(f"**Assistente:** {conv['response'][:200]}...")
            
            if history:
                return "**Histórico Conversacional:**\n" + "\n\n".join(history) + "\n\n"
            
            return ""
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao recuperar histórico: {e}")
            return ""
    
    def _save_to_memory(
        self,
        session_id: str,
        query: str,
        response: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Salva interação na memória persistente.
        
        Args:
            session_id: ID da sessão
            query: Pergunta do usuário
            response: Resposta do agente
            metadata: Metadados adicionais
        """
        try:
            supabase.table('agent_conversations').insert({
                'session_id': session_id,
                'query': query,
                'response': response,
                'metadata': metadata,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            logger.info(f"💾 Interação salva na memória: session={session_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar na memória: {e}")
    
    def _requires_visualization(
        self,
        query: str,
        intent_result
    ) -> bool:
        """
        Determina se a pergunta requer visualização.
        
        Args:
            query: Pergunta do usuário
            intent_result: Resultado da classificação de intenção
            
        Returns:
            True se requer visualização
        """
        # Intent primário é visualização
        if intent_result.primary_intent == AnalysisIntent.VISUALIZATION:
            return True
        
        # Intent secundário contém visualização
        if AnalysisIntent.VISUALIZATION in intent_result.secondary_intents:
            return True
        
        # Keywords explícitas (fallback leve)
        viz_keywords = ['histograma', 'gráfico', 'grafico', 'distribuição', 'distribuicao', 
                        'visualizar', 'plotar', 'chart', 'plot']
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in viz_keywords):
            return True
        
        return False
    
    def _generate_visualizations(
        self,
        df: pd.DataFrame,
        query: str,
        intent: AnalysisIntent
    ) -> List[str]:
        """
        Gera visualizações apropriadas.
        
        Args:
            df: DataFrame
            query: Pergunta do usuário
            intent: Intenção detectada
            
        Returns:
            Lista de paths dos gráficos gerados
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            from pathlib import Path
            
            # Criar diretório de output
            output_dir = Path("static/histogramas")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            paths = []
            
            # Gerar histogramas para todas as colunas numéricas
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                logger.warning("⚠️ Nenhuma coluna numérica para visualizar")
                return []
            
            # Limitar a 10 colunas para não gerar muitos gráficos
            cols_to_plot = numeric_cols[:10]
            
            for col in cols_to_plot:
                try:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Histograma com KDE
                    df[col].hist(bins=50, ax=ax, alpha=0.7, edgecolor='black')
                    ax.set_title(f'Distribuição de {col}', fontsize=14, fontweight='bold')
                    ax.set_xlabel(col, fontsize=12)
                    ax.set_ylabel('Frequência', fontsize=12)
                    ax.grid(axis='y', alpha=0.3)
                    
                    # Salvar
                    filename = f"hist_{col}_{timestamp}.png"
                    filepath = output_dir / filename
                    plt.tight_layout()
                    plt.savefig(filepath, dpi=100, bbox_inches='tight')
                    plt.close()
                    
                    paths.append(str(filepath))
                    logger.info(f"📊 Histograma gerado: {filename}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao gerar histograma para {col}: {e}")
                    continue
            
            return paths
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar visualizações: {e}")
            return []


def create_agent_v4(**kwargs) -> RAGDataAgentV4:
    """
    Factory function para criar RAGDataAgent V4.0.
    
    Args:
        **kwargs: Argumentos para inicialização do agente
        
    Returns:
        Instância de RAGDataAgentV4
    """
    return RAGDataAgentV4(**kwargs)


if __name__ == "__main__":
    # Teste rápido
    print("=== RAGDataAgent V4.0 - Teste Rápido ===\n")
    
    agent = create_agent_v4()
    
    # Teste 1: Tipos de dados
    print("\n🔍 TESTE 1: Tipos de dados\n")
    result = agent.query_v4(
        query="Quais são os tipos de dados (numéricos, categóricos)?",
        session_id="test_session_001"
    )
    
    if result['success']:
        print(f"✅ Resposta:\n{result['answer'][:500]}...")
        print(f"\n📊 Metadata:")
        print(f"  - Intent: {result['intent']}")
        print(f"  - Temperature: {result['metadata']['llm_config']['temperature']}")
        print(f"  - Threshold: {result['metadata']['rag_config']['threshold']}")
        print(f"  - Processing Time: {result['metadata']['processing_time_seconds']:.2f}s")
    else:
        print(f"❌ Erro: {result['error']}")
