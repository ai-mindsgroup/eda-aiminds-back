#!/usr/bin/env python3
"""
Script para limpeza seletiva - apenas embeddings do dataset creditcard.

Mantém todas as tabelas de memória (agent_sessions, agent_conversations, agent_context).
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main() -> int:
    print("🧹 LIMPEZA SELETIVA - APENAS DATASET CREDITCARD")
    print("=" * 60)

    # Source ID usado pelo script de ingestão
    source_id = "creditcard_full"

    print(f"🎯 Removendo apenas embeddings do source: {source_id}")
    print("📊 Mantendo tabelas de memória intactas...")
    print()

    try:
        # Criar agente RAG para usar o método clear_source
        agent = RAGAgent()

        # Limpar apenas o source específico
        result = agent.clear_source(source_id)

        if result.get("metadata", {}).get("error"):
            print(f"❌ Erro na limpeza: {result.get('content', 'Erro desconhecido')}")
            return 1

        deleted_count = result.get("metadata", {}).get("deleted_count", 0)
        print(f"✅ Sucesso! Removidos {deleted_count:,} embeddings do source '{source_id}'")

        if deleted_count == 0:
            print("ℹ️ Nenhum embedding encontrado para limpeza (base já limpa?)")

        print()
        print("📋 Tabelas de memória PRESERVADAS:")
        print("   • agent_sessions: mantidas")
        print("   • agent_conversations: mantidas")
        print("   • agent_context: mantidas")
        print()
        print("🚀 Pronto para nova ingestão!")

        return 0

    except Exception as e:
        logger.error(f"Erro durante limpeza: {e}")
        print(f"❌ Erro: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())