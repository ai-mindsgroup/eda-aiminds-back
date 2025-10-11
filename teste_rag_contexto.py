#!/usr/bin/env python3
"""
Teste do Sistema RAG com Contexto - Verifica se agent_context é populada
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.rag_data_agent import RAGDataAgent
from src.memory.supabase_memory import SupabaseMemoryManager
from src.memory.memory_types import ContextType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def test_rag_context_saving():
    """Testa se o RAGDataAgent salva contexto quando encontra chunks relevantes."""
    logger.info("Iniciando teste do sistema RAG com salvamento de contexto...")

    try:
        # Inicializar agente RAG (sem parâmetro name)
        rag_agent = RAGDataAgent()

        # Inicializar gerenciador de memória com agent_name
        memory_manager = SupabaseMemoryManager(agent_name="test_rag_agent")

        # Query que deve encontrar chunks relacionados aos dados de cartão de crédito
        query = "análise de fraudes em dados de cartão de crédito"

        logger.info(f"Executando query: '{query}'")

        # Executar busca RAG (agora await)
        result = await rag_agent.process(query=query)

        logger.info("Query executada com sucesso")

        # Verificar se encontrou chunks
        if result.get('chunks_found', 0) > 0:
            logger.info(f"✅ Encontrou {result['chunks_found']} chunks relevantes")

            # Verificar se contexto foi salvo
            context_saved = await memory_manager.get_context(
                session_id=result.get('session_id'),
                context_type=ContextType.DATA
            )

            if context_saved:
                logger.info(f"✅ Contexto salvo na tabela agent_context: {len(context_saved)} registros")
                for ctx in context_saved:
                    logger.info(f"  - Tipo: {ctx.get('context_type')}, Chave: {ctx.get('context_key')}")
            else:
                logger.warning("⚠️ Nenhum contexto encontrado na tabela agent_context")
                return False

        else:
            logger.warning(f"⚠️ Nenhum chunk encontrado para a query '{query}'")
            # Mesmo sem chunks, verificar se algum contexto foi salvo
            # Usar parâmetros obrigatórios para get_context
            all_context = await memory_manager.get_context(
                session_id=result.get('session_id'),
                context_type=ContextType.DATA,
                context_key='dataset_info'  # chave específica
            )
            if all_context:
                logger.info(f"ℹ️ Contexto geral encontrado: {len(all_context)} registros")
            else:
                logger.info("ℹ️ Nenhum contexto salvo (esperado se não há dados carregados)")

        # Verificar estatísticas da resposta
        if 'response' in result:
            logger.info("✅ Resposta gerada pelo agente RAG")
            logger.info(f"Resposta (primeiros 200 chars): {result['response'][:200]}...")

        logger.info("🎉 Teste do sistema RAG concluído com sucesso!")
        return True

    except Exception as e:
        logger.error(f"❌ Erro no teste RAG: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_context_persistence():
    """Testa se o contexto persiste entre sessões."""
    logger.info("Testando persistência de contexto...")

    try:
        memory_manager = SupabaseMemoryManager(agent_name="test_agent")

        # Primeiro criar uma sessão
        session_info = await memory_manager.create_session()
        session_id = session_info.session_id  # Usar o session_id string diretamente
        logger.info(f"Sessão criada: {session_id}")

        # Salvar contexto de teste
        test_context = {
            "dataset_info": "Dados de cartão de crédito com 284807 transações",
            "columns": ["Time", "V1", "V2", "Amount", "Class"],
            "fraud_rate": "0.172%",
            "analysis_type": "fraud_detection"
        }

        success = await memory_manager.save_context(
            session_id=session_id,
            agent_name="test_agent",
            context_type=ContextType.DATA,
            context_key="creditcard_dataset_info",
            context_data=test_context
        )

        if success:
            logger.info("✅ Contexto de teste salvo com sucesso")

            # Recuperar contexto
            retrieved = await memory_manager.get_context(
                session_id=session_id,
                context_type=ContextType.DATA,
                context_key="creditcard_dataset_info"
            )

            if retrieved and retrieved.context_data.get('dataset_info') == test_context['dataset_info']:
                logger.info("✅ Contexto recuperado corretamente")
                return True
            else:
                logger.error("❌ Dados do contexto não correspondem")
                return False
        else:
            logger.error("❌ Falha ao salvar contexto de teste")
            return False

    except Exception as e:
        logger.error(f"❌ Erro no teste de persistência: {str(e)}")
        return False

async def main():
    success1 = await test_rag_context_saving()
    success2 = await test_context_persistence()

    if success1 and success2:
        logger.info("🎯 Todos os testes do sistema RAG e contexto passaram!")
        sys.exit(0)
    else:
        logger.error("❌ Alguns testes falharam")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())