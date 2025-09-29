"""Executa consultas simuladas ao agente RAG usando o dataset creditcard.

O objetivo é validar se o agente responde adequadamente às perguntas
utilizando os embeddings armazenados no Supabase.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider


QUESTIONS: List[str] = [
    "Quais os tipos de variáveis no arquivo e sua distribuição?",
    "Qual a média, mediana e desvio padrão do valor das transações?",
    "Como as fraudes estão distribuídas ao longo do tempo?",
    "Existe correlação entre o valor da transação e a chance de fraude?",
    "Quais são os outliers mais significativos?",
    "Quantas fraudes ocorreram na última janela do dataset?",
    "Quais as características comuns das transações fraudulentas?",
    "Quais clusters podem ser formados e o que indicam?",
    "Qual o impacto dos outliers na análise geral?",
    "Pode gerar um resumo das conclusões principais para um gestor entender?",
]


def format_metadata(metadata: Dict[str, Any]) -> str:
    if not metadata or metadata.get("error"):
        return "   • Nenhuma métrica disponível"

    parts = [
        f"   • Tempo de processamento: {metadata.get('processing_time', 0):.2f}s",
        f"   • Resultados: {metadata.get('search_results_count', 0)}",
        f"   • Fontes: {', '.join(metadata.get('sources_found', [])) or 'desconhecidas'}",
    ]

    source_stats = metadata.get("source_stats", {})
    if source_stats:
        stats_lines = [
            f"     - {source}: {stats['chunks']} chunks, sim. média {stats['avg_similarity']:.3f}"  # type: ignore[index]
            for source, stats in source_stats.items()
        ]
        parts.append("   • Estatísticas por fonte:\n" + "\n".join(stats_lines))

    return "\n".join(parts)


def main() -> int:
    print("🚀 Executando consultas ao agente RAG (creditcard)")

    try:
        agent = RAGAgent(
            embedding_provider=EmbeddingProvider.MOCK,
            chunk_size=512,
            chunk_overlap=50,
            csv_chunk_size_rows=20,
            csv_overlap_rows=4,
        )
    except Exception as exc:  # pragma: no cover - diagnóstico manual
        print(f"❌ Falha ao inicializar RAGAgent: {exc}")
        return 1

    context = {
        "similarity_threshold": 0.25,
        "max_results": 5,
        "include_context": True,
        "filters": {"source": "creditcard_v1"},
    }

    for idx, question in enumerate(QUESTIONS, start=1):
        print("\n" + "=" * 80)
        print(f"📝 Pergunta {idx}: {question}")
        print("-" * 80)

        try:
            result = agent.process(question, context=context)
        except Exception as exc:  # pragma: no cover - diagnóstico manual
            print(f"❌ Erro ao processar pergunta: {exc}")
            continue

        print(result.get("content", "(sem conteúdo retornado)"))
        metadata = result.get("metadata", {})
        print("\n📊 Metadados")
        print(format_metadata(metadata))

    print("\n✅ Consultas finalizadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
