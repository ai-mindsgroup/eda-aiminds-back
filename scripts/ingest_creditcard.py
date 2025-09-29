"""Ferramenta utilitária para ingestão do dataset de fraude em cartão de crédito.

Executa o pipeline RAG completo (chunking CSV, geração de embeddings e
armazenamento no vector store) utilizando os parâmetros recomendados para o projeto.

Uso básico:
    python scripts/ingest_creditcard.py

Parâmetros opcionais permitem alterar o caminho do CSV, fonte, chunking e
provedor de embeddings.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# Garantir que o diretório raiz do projeto esteja no PYTHONPATH quando o script
# for executado diretamente (python scripts/ingest_creditcard.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.rag_agent import RAGAgent
from src.embeddings.generator import EmbeddingProvider

DEFAULT_CSV_PATH = Path("data/creditcard.csv")
DEFAULT_SOURCE_ID = "creditcard_full"


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingesta o dataset de fraude em cartão de crédito para o vector store",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="Caminho para o arquivo CSV a ser ingerido.",
    )
    parser.add_argument(
        "--source-id",
        type=str,
        default=DEFAULT_SOURCE_ID,
        help="Identificador da fonte a ser armazenado no vector store.",
    )
    parser.add_argument(
        "--chunk-size-rows",
        type=int,
        default=20,
        help="Quantidade de linhas por chunk CSV (antes do overlap).",
    )
    parser.add_argument(
        "--overlap-rows",
        type=int,
        default=4,
        help="Quantidade de linhas de overlap entre chunks CSV consecutivos.",
    )
    parser.add_argument(
        "--chunk-size-chars",
        type=int,
        default=512,
        help="Tamanho do chunk textual em caracteres (para fontes não-CSV).",
    )
    parser.add_argument(
        "--chunk-overlap-chars",
        type=int,
        default=50,
        help="Overlap em caracteres entre chunks textuais (para fontes não-CSV).",
    )
    parser.add_argument(
        "--provider",
        choices=[provider.value for provider in EmbeddingProvider],
        default=EmbeddingProvider.SENTENCE_TRANSFORMER.value,
        help="Provedor de embeddings a ser utilizado.",
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf-8",
        help="Codificação usada para leitura do CSV.",
    )
    parser.add_argument(
        "--errors",
        type=str,
        default="ignore",
        help="Política de tratamento de erros de decodificação ao ler o CSV.",
    )
    return parser.parse_args(argv)


def _resolve_provider(value: str) -> EmbeddingProvider:
    for provider in EmbeddingProvider:
        if value == provider.value or value.lower() == provider.name.lower():
            return provider
    raise ValueError(f"Provedor de embeddings não suportado: {value}")


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    csv_path = args.csv_path.resolve()
    if not csv_path.exists():
        print(f"❌ Arquivo CSV não encontrado: {csv_path}", file=sys.stderr)
        return 1

    if args.chunk_size_rows <= 0:
        print("❌ chunk_size_rows deve ser maior que zero.", file=sys.stderr)
        return 1

    provider = _resolve_provider(args.provider)

    print("🚀 Iniciando ingestão do CSV...", flush=True)
    print(f"   • Arquivo: {csv_path}")
    print(f"   • Fonte (source_id): {args.source_id}")
    print(f"   • Chunk CSV: {args.chunk_size_rows} linhas (+{args.overlap_rows} overlap)")
    print(f"   • Provedor de embeddings: {provider.value}")

    agent = RAGAgent(
        embedding_provider=provider,
        chunk_size=args.chunk_size_chars,
        chunk_overlap=args.chunk_overlap_chars,
        csv_chunk_size_rows=args.chunk_size_rows,
        csv_overlap_rows=args.overlap_rows,
    )

    result = agent.ingest_csv_file(
        file_path=str(csv_path),
        source_id=args.source_id,
        encoding=args.encoding,
        errors=args.errors,
    )

    content = result.get("content", "")
    metadata = result.get("metadata", {}) or {}

    if metadata.get("error"):
        print("❌ Falha na ingestão:")
        print(f"   • Mensagem: {content}")
        if metadata:
            print(f"   • Detalhes: {metadata}")
        return 2

    print("✅ Ingestão concluída com sucesso!")
    if content:
        print("---")
        print(content)
        print("---")

    if metadata:
        print("📊 Estatísticas do processamento:")
        stats_lines = [
            f"   • Fonte: {metadata.get('source_id')}",
            f"   • Tipo da fonte: {metadata.get('source_type')}",
            f"   • Chunks gerados: {metadata.get('chunks_created')}",
            f"   • Embeddings gerados: {metadata.get('embeddings_generated')}",
            f"   • Embeddings armazenados: {metadata.get('embeddings_stored')}",
            f"   • Estratégia de chunking: {metadata.get('chunk_strategy')}",
            f"   • Tempo de processamento (s): {metadata.get('processing_time'):.2f}" if metadata.get('processing_time') is not None else None,
        ]
        for line in stats_lines:
            if line is not None:
                print(line)

        chunk_stats = metadata.get("chunk_stats") or {}
        if chunk_stats:
            print("   • CSV total de linhas processadas:", chunk_stats.get("total_csv_rows"))
            print("   • Média de linhas por chunk:", chunk_stats.get("avg_csv_rows"))
            print("   • Overlap total (linhas):", chunk_stats.get("total_csv_overlap_rows"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
