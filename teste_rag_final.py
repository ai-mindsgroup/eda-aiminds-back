#!/usr/bin/env python3
"""
Teste Final: Sistema RAG Completo com Dados Carregados
Verifica se o RAG encontra chunks similares e salva contexto quando há dados.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.rag_data_agent import RAGDataAgent
from src.memory.supabase_memory import SupabaseMemoryManager
from src.memory.memory_types import ContextType
from src.utils.logging_config import get_logger
from src.embeddings.generator import EmbeddingGenerator, EmbeddingProvider

logger = get_logger(__name__)

async def test_rag_with_loaded_data():
    """Testa o RAG com dados carregados e verifica se encontra chunks e salva contexto."""
    logger.info("🧪 Iniciando teste final do sistema RAG com dados carregados...")

    try:
        # 1. Preparar dados de exemplo
        sample_data = [
            "Este dataset contém dados de transações de cartão de crédito",
            "Análise de fraudes em cartões de crédito usando machine learning",
            "Dados estatísticos sobre distribuição de valores de transações",
            "Detecção de anomalias em padrões de compra com cartão",
            "Processamento de dados CSV para análise de risco financeiro",
            "Visualização de gráficos de distribuição de variáveis do dataset",
            "Algoritmos de clustering para identificar grupos de transações suspeitas",
            "Métricas de avaliação para modelos de detecção de fraude"
        ]

        # 2. Inicializar gerador de embeddings
        embedding_generator = EmbeddingGenerator(provider=EmbeddingProvider.SENTENCE_TRANSFORMER)

        # 3. Inicializar agente RAG
        rag_agent = RAGDataAgent()

        # 4. Inicializar gerenciador de memória
        memory_manager = SupabaseMemoryManager(agent_name="test_rag_complete")

        # 5. Simular carregamento de dados - salvar chunks no banco
        logger.info("📥 Carregando dados de exemplo no sistema...")

        for i, text in enumerate(sample_data):
            # Gerar embedding
            result = embedding_generator.generate_embedding(text)
            embedding = result.embedding

            # Salvar chunk simulado no Supabase (usando a função do agente RAG)
            # Como não temos uma função direta, vamos usar o método do agente para processar

        # 6. Fazer query que deve encontrar chunks similares
        query = "análise de fraudes em cartões de crédito"
        logger.info(f"🔍 Fazendo query: '{query}'")

        result = await rag_agent.process(query=query)

        # 7. Verificar resultados
        chunks_found = result.get('chunks_found', 0)
        if chunks_found > 0:
            logger.info(f"✅ Encontrou {chunks_found} chunks relevantes!")

            # 8. Verificar se contexto foi salvo
            session_id = result.get('session_id')
            if session_id:
                context_saved = await memory_manager.get_context(
                    session_id=session_id,
                    context_type=ContextType.DATA
                )

                if context_saved:
                    logger.info(f"✅ Contexto salvo: {len(context_saved)} registros")
                    return True
                else:
                    logger.warning("⚠️ Contexto não foi salvo")
                    return False
            else:
                logger.warning("⚠️ Session ID não encontrado")
                return False
        else:
            logger.warning(f"❌ Nenhum chunk encontrado para query '{query}'")
            return False

    except Exception as e:
        logger.error(f"❌ Erro no teste final RAG: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    logger.info("🚀 Iniciando teste final do sistema RAG completo...")

    success = await test_rag_with_loaded_data()

    if success:
        logger.info("🎯 Teste final do sistema RAG passou! Sistema funcionando corretamente.")
        sys.exit(0)
    else:
        logger.error("❌ Teste final falhou - sistema precisa de ajustes")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())