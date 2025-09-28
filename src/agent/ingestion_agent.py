"""CSV ingestion agent specialised for the credit card fraud dataset.

The agent encapsulates the ingestion + cleansing logic required to feed the
multi-agent analytics pipeline. It loads the CSV, performs structural
validations, cleans common data quality issues and returns a ready-to-use
DataFrame wrapped in the canonical ``AgentMessage`` structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import pandas as pd
from pandas.api import types as ptypes

from .base_agent import AgentMessage, BaseAgent
from src.utils.logging_config import get_logger


@dataclass
class CSVIngestionConfig:
    """Configuration for :class:`CSVIngestionAgent`.

    Attributes
    ----------
    csv_path:
        Default path to load when the incoming message does not provide one.
    essential_columns:
        Mapping between canonical names (time, amount, etc.) and candidate
        column names present in the CSV. The agent resolves the first match
        case-insensitively.
    dtype_expectations:
        Expected semantic type for the canonical column (``"numeric"`` or
        ``"categorical"``). Used to coerce/validate loaded data.
    drop_duplicates:
        Whether duplicated rows should be dropped during cleaning.
    dropna_subset:
        Canonical column names that must not have null values after cleaning.
    create_missing_id:
        When True, missing transaction identifiers will be synthesised with
        a sequential integer column.
    chunk_size:
        Number of rows to read per chunk when streaming the CSV from disk.
    chunk_overlap:
        Number of rows to overlap between consecutive chunks to preserve
        continuity (must be smaller than ``chunk_size``).
    """

    csv_path: Path
    essential_columns: Dict[str, Sequence[str]] = field(default_factory=dict)
    dtype_expectations: Dict[str, str] = field(default_factory=dict)
    drop_duplicates: bool = True
    dropna_subset: Sequence[str] = field(default_factory=lambda: ("transaction_id", "time", "amount", "fraud_label"))
    create_missing_id: bool = True
    chunk_size: int = 20_000
    chunk_overlap: int = 2_000
    chunk_token_min: int = 50
    chunk_token_target: int = 120
    chunk_token_max: int = 180
    chunk_column_sample: int = 12

    @staticmethod
    def default(project_root: Optional[Path] = None) -> "CSVIngestionConfig":
        root = project_root or Path(__file__).resolve().parents[2]
        return CSVIngestionConfig(
            csv_path=root / "data" / "creditcard.csv",
            essential_columns={
                "transaction_id": ("id", "transaction_id", "row_id"),
                "time": ("time", "tempo", "transaction_time", "timestamp"),
                "amount": ("amount", "valor", "transaction_amount"),
                "fraud_label": ("class", "fraude", "is_fraud", "fraud"),
            },
            dtype_expectations={
                "transaction_id": "numeric",
                "time": "numeric",
                "amount": "numeric",
                "fraud_label": "numeric",
            },
            chunk_size=20_000,
            chunk_overlap=2_000,
            chunk_token_min=50,
            chunk_token_target=120,
            chunk_token_max=180,
            chunk_column_sample=12,
        )


class CSVIngestionAgent(BaseAgent):
    """Agent that loads, validates and cleans the credit-card fraud dataset."""

    def __init__(self, name: Optional[str] = None, config: Optional[CSVIngestionConfig] = None) -> None:
        super().__init__(name=name or "CSVIngestionAgent")
        self.config = config or CSVIngestionConfig.default()
        self.logger = get_logger(self.name)

    # ------------------------------------------------------------------
    # BaseAgent API
    # ------------------------------------------------------------------
    def run(self, message: Optional[AgentMessage] = None) -> AgentMessage:
        return self.handle(message)

    def handle(self, message: Optional[AgentMessage]) -> AgentMessage:
        self.log_start("ingestion", source=message.sender if message else None)
        df, report, chunks = self._ingest(message)
        self.log_end("ingestion", rows=report["shape"]["after_rows"], columns=report["shape"]["after_columns"])
        payload = {"data": df, "report": report, "chunks": chunks}
        return self.build_message(payload, stage="ingestion")

    # ------------------------------------------------------------------
    # Ingestion pipeline
    # ------------------------------------------------------------------
    def _ingest(self, message: Optional[AgentMessage]) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        override = message.content if message else {}
        if override and not isinstance(override, dict):
            raise TypeError("CSVIngestionAgent expects dict payload with optional overrides (path/data/chunk).")

        report: Dict[str, Any] = {
            "path": None,
            "shape": {"before_rows": 0, "before_columns": 0, "after_rows": 0, "after_columns": 0},
            "issues": {},
            "cleaning_actions": [],
            "resolved_columns": {},
            "chunks_processed": [],
        }

        cleaned_chunks: List[pd.DataFrame] = []
        resolved_template: Optional[Dict[str, str]] = None
        synthetic_id_created = False
        raw_rows_total = 0

        if override.get("data") is not None:
            data = override["data"]
            if not isinstance(data, pd.DataFrame):
                raise TypeError("Override 'data' deve ser um pandas.DataFrame")
            report["path"] = "<in-memory>"
            report["shape"]["before_rows"] = int(data.shape[0])
            report["shape"]["before_columns"] = int(data.shape[1])

            processed_chunk, chunk_report, resolved_template, synthetic_flag = self._process_chunk(
                data.copy(), resolved_template, chunk_index=0, overlap_rows=0
            )
            synthetic_id_created = synthetic_id_created or synthetic_flag
            report["chunks_processed"].append(chunk_report)
            cleaned_chunks.append(processed_chunk)
        else:
            path = self._resolve_path(override or {})
            self._validate_chunk_parameters()
            report["path"] = str(path)

            if not path.exists():
                raise FileNotFoundError(f"Arquivo CSV não encontrado: {path}")

            for chunk_index, chunk_df, base_rows, overlap_rows in self._read_chunk_iterator(path):
                raw_rows_total += int(base_rows)
                if report["shape"]["before_columns"] == 0:
                    report["shape"]["before_columns"] = int(chunk_df.shape[1])

                processed_chunk, chunk_report, resolved_template, synthetic_flag = self._process_chunk(
                    chunk_df, resolved_template, chunk_index, overlap_rows
                )
                chunk_report["base_rows"] = int(base_rows)
                report["chunks_processed"].append(chunk_report)
                cleaned_chunks.append(processed_chunk)
                synthetic_id_created = synthetic_id_created or synthetic_flag

            report["shape"]["before_rows"] = raw_rows_total

        if not report["shape"]["before_rows"] and cleaned_chunks:
            report["shape"]["before_rows"] = int(sum(chunk.shape[0] for chunk in cleaned_chunks))

        if cleaned_chunks:
            df = pd.concat(cleaned_chunks, ignore_index=True)
        else:
            df = pd.DataFrame()

        if resolved_template is None and not df.empty:
            resolved_template = self._resolve_essential_columns(df)

        if not df.empty:
            txn_col = (resolved_template or {}).get("transaction_id")
            subset_cols = [col for col in df.columns if col != txn_col]
            before_concat_rows = int(df.shape[0])
            if subset_cols:
                df = df.drop_duplicates(subset=subset_cols).reset_index(drop=True)
            else:
                df = df.drop_duplicates().reset_index(drop=True)
            removed_overlap = before_concat_rows - int(df.shape[0])
            if removed_overlap:
                report["cleaning_actions"].append({"dropped_overlap_duplicates": removed_overlap})

            if synthetic_id_created and self.config.create_missing_id:
                txn_col = txn_col or "transaction_id"
                df[txn_col] = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)
                if resolved_template is None:
                    resolved_template = {}
                resolved_template["transaction_id"] = txn_col
                report["cleaning_actions"].append({"transaction_id_reassigned": len(df)})

        if resolved_template is None:
            resolved_template = {}

        if not df.empty:
            dtype_info, coercions = self._ensure_dtypes(df, resolved_template)
            issues = self._diagnose_issues(df, resolved_template, dtype_info)
            if coercions:
                report["cleaning_actions"].append({"coerced_columns_final": coercions})
        else:
            dtype_info = {}
            issues = {"null_counts": {}, "duplicate_rows": 0, "dtypes": {}, "invalid_numeric": {}}

        report["issues"] = issues
        report["resolved_columns"] = resolved_template
        report["shape"]["after_rows"] = int(df.shape[0])
        report["shape"]["after_columns"] = int(df.shape[1]) if not df.empty else report["shape"]["before_columns"]
        report["chunking"] = {
            "chunk_size": self.config.chunk_size,
            "chunk_overlap": self.config.chunk_overlap,
            "chunks": len(report["chunks_processed"]),
        }

        chunks = self._generate_chunks(df, resolved_template, report) if not df.empty else []
        report["chunks"] = [
            {"id": chunk["id"], "type": chunk["type"], "token_estimate": chunk["token_estimate"]} for chunk in chunks
        ]

        return df, report, chunks

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def _resolve_path(self, override: Dict[str, Any]) -> Path:
        if override and override.get("path"):
            return Path(override["path"]).resolve()
        if override and override.get("csv_path"):
            return Path(override["csv_path"]).resolve()
        return self.config.csv_path

    def _resolve_essential_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        resolved: Dict[str, str] = {}
        lowered = {col.lower(): col for col in df.columns}

        for canonical, candidates in self.config.essential_columns.items():
            actual = self._match_candidate(lowered, candidates)
            if actual:
                resolved[canonical] = actual
                continue

            if canonical == "transaction_id" and self.config.create_missing_id:
                new_col = "transaction_id"
                df[new_col] = pd.Series(range(1, len(df) + 1), index=df.index)
                resolved[canonical] = new_col
                self.logger.info("Coluna de ID sintetizada", extra={"column": new_col})
            else:
                raise ValueError(
                    f"Coluna essencial ausente: {canonical}. Procure por uma das opções: {', '.join(candidates)}"
                )

        return resolved

    def _match_candidate(self, lowered: Dict[str, str], candidates: Sequence[str]) -> Optional[str]:
        for candidate in candidates:
            ref = candidate.lower()
            if ref in lowered:
                return lowered[ref]
        return None

    def _ensure_dtypes(self, df: pd.DataFrame, resolved: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
        dtype_info: Dict[str, str] = {}
        coerced: List[str] = []
        for canonical, expected in self.config.dtype_expectations.items():
            column = resolved.get(canonical)
            if not column:
                continue
            series = df[column]
            if expected == "numeric":
                if not ptypes.is_numeric_dtype(series):
                    coerced_series = pd.to_numeric(series, errors="coerce")
                    coerced.append(column)
                    df[column] = coerced_series
            dtype_info[column] = str(df[column].dtype)
        return dtype_info, coerced

    def _diagnose_issues(
        self, df: pd.DataFrame, resolved: Dict[str, str], dtype_info: Dict[str, str]
    ) -> Dict[str, Any]:
        null_counts = df.isna().sum().to_dict()
        duplicate_rows = int(df.duplicated().sum())
        invalid_numeric: Dict[str, int] = {}

        for canonical, expected in self.config.dtype_expectations.items():
            column = resolved.get(canonical)
            if not column or expected != "numeric":
                continue
            series = df[column]
            invalid_numeric[column] = int(series.isna().sum())

        return {
            "null_counts": null_counts,
            "duplicate_rows": duplicate_rows,
            "dtypes": dtype_info,
            "invalid_numeric": invalid_numeric,
        }

    def _clean_dataframe(
        self, df: pd.DataFrame, resolved: Dict[str, str], issues: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        actions: List[Dict[str, Any]] = []
        before_rows = df.shape[0]

        if self.config.drop_duplicates:
            duplicates = issues.get("duplicate_rows", 0)
            if duplicates:
                df = df.drop_duplicates().reset_index(drop=True)
                actions.append({"dropped_duplicates": duplicates})

        subset = [resolved[key] for key in self.config.dropna_subset if resolved.get(key)]
        if subset:
            before_dropna = df.shape[0]
            df = df.dropna(subset=subset)
            dropped = before_dropna - df.shape[0]
            if dropped:
                actions.append({"dropped_null_rows": dropped, "subset": subset})

        df = df.reset_index(drop=True)
        after_rows = df.shape[0]
        actions.append({"rows_retained": after_rows, "rows_removed": before_rows - after_rows})

        return df, actions

    # ------------------------------------------------------------------
    # Chunk reading helpers
    # ------------------------------------------------------------------
    def _validate_chunk_parameters(self) -> None:
        if self.config.chunk_size <= 0:
            raise ValueError("chunk_size deve ser positivo")
        if self.config.chunk_overlap < 0:
            raise ValueError("chunk_overlap não pode ser negativo")
        if self.config.chunk_overlap >= self.config.chunk_size:
            raise ValueError("chunk_overlap precisa ser menor que chunk_size")

    def _read_chunk_iterator(self, path: Path) -> Iterator[Tuple[int, pd.DataFrame, int, int]]:
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        base_size = chunk_size - overlap if overlap else chunk_size
        reader = pd.read_csv(path, chunksize=base_size)
        overlap_buffer = pd.DataFrame()

        for index, base_chunk in enumerate(reader):
            base_chunk = base_chunk.reset_index(drop=True)
            if base_chunk.empty and overlap_buffer.empty:
                continue

            if overlap_buffer.empty:
                chunk_df = base_chunk
            else:
                chunk_df = pd.concat([overlap_buffer, base_chunk], ignore_index=True)

            overlap_rows = int(overlap_buffer.shape[0])
            if index == 0:
                self.logger.info(
                    "Lendo chunk do CSV",
                    extra={"path": str(path), "chunk_size": chunk_size, "overlap": overlap},
                )

            yield index, chunk_df, int(base_chunk.shape[0]), overlap_rows

            if overlap:
                overlap_buffer = chunk_df.tail(overlap).copy()
            else:
                overlap_buffer = pd.DataFrame()

    def _process_chunk(
        self,
        chunk_df: pd.DataFrame,
        resolved_template: Optional[Dict[str, str]],
        chunk_index: int,
        overlap_rows: int,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], Optional[Dict[str, str]], bool]:
        chunk = chunk_df.copy()
        chunk_report: Dict[str, Any] = {
            "chunk_index": chunk_index,
            "input_rows": int(chunk.shape[0]),
            "overlap_rows": int(overlap_rows),
            "issues": {},
            "cleaning_actions": [],
        }

        before_columns = set(chunk.columns)
        current_resolved = self._resolve_essential_columns(chunk)
        synthetic_id_created = False
        txn_col = current_resolved.get("transaction_id")
        if txn_col and txn_col not in before_columns:
            synthetic_id_created = True

        if resolved_template is not None:
            for canonical, column in resolved_template.items():
                if canonical == "transaction_id":
                    continue
                if current_resolved.get(canonical) != column:
                    raise ValueError(
                        f"Chunk {chunk_index} possui mapeamento divergente para '{canonical}': "
                        f"{current_resolved.get(canonical)} != {column}"
                    )

        resolved = resolved_template or current_resolved.copy()
        dtype_info, coercions = self._ensure_dtypes(chunk, resolved)
        if coercions:
            chunk_report["cleaning_actions"].append({"coerced_columns": coercions})

        issues = self._diagnose_issues(chunk, resolved, dtype_info)
        chunk_report["issues"] = issues
        chunk_report["dtype_info"] = dtype_info
        chunk_cleaned, cleaning_summary = self._clean_dataframe(chunk, resolved, issues)
        chunk_report["cleaning_actions"].extend(cleaning_summary)
        chunk_report["output_rows"] = int(chunk_cleaned.shape[0])
        chunk_report["resolved_columns"] = current_resolved

        return chunk_cleaned, chunk_report, resolved, synthetic_id_created

    # ------------------------------------------------------------------
    # Chunk generation helpers
    # ------------------------------------------------------------------
    def _generate_chunks(
        self, df: pd.DataFrame, resolved: Dict[str, str], report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        rows = int(df.shape[0])
        columns = int(df.shape[1])
        overview_columns = df.columns.tolist()
        amount_col = resolved.get("amount")
        time_col = resolved.get("time")
        fraud_col = resolved.get("fraud_label")

        time_span: Optional[Tuple[float, float]] = None
        if time_col and time_col in df.columns:
            time_series = pd.to_numeric(df[time_col], errors="coerce").dropna()
            if not time_series.empty:
                time_span = (float(time_series.min()), float(time_series.max()))

        amount_stats: Dict[str, float] = {}
        if amount_col and amount_col in df.columns:
            amount_series = pd.to_numeric(df[amount_col], errors="coerce").dropna()
            if not amount_series.empty:
                desc = amount_series.describe(percentiles=[0.25, 0.5, 0.75])
                amount_stats = {
                    "mean": float(desc["mean"]),
                    "std": float(desc["std"]),
                    "min": float(desc["min"]),
                    "max": float(desc["max"]),
                    "p25": float(desc["25%"]),
                    "p50": float(desc["50%"]),
                    "p75": float(desc["75%"]),
                }

        fraud_distribution: Dict[str, float] = {}
        if fraud_col and fraud_col in df.columns:
            counts = df[fraud_col].value_counts(normalize=True, dropna=True)
            fraud_distribution = {str(label): float(freq) for label, freq in counts.items()}

        null_counts = report.get("issues", {}).get("null_counts", {})
        top_missing = sorted(null_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        rows_removed = self._extract_rows_removed(report.get("cleaning_actions", []))
        coerced_columns = self._collect_coerced_columns(report.get("cleaning_actions", []))

        chunks: List[Dict[str, Any]] = []

        overview_text, overview_tokens = self._build_overview_chunk(
            rows, columns, overview_columns, time_span, rows_removed, coerced_columns
        )
        chunks.append(
            self._make_chunk(
                index=len(chunks) + 1,
                chunk_type="dataset_overview",
                content=overview_text,
                token_estimate=overview_tokens,
                metadata={
                    "rows": rows,
                    "columns": columns,
                    "time_span": time_span,
                    "rows_removed": rows_removed,
                    "coerced_columns": coerced_columns,
                },
            )
        )

        if amount_stats:
            amount_text, amount_tokens = self._build_amount_chunk(amount_col or "amount", amount_stats)
            chunks.append(
                self._make_chunk(
                    index=len(chunks) + 1,
                    chunk_type="amount_stats",
                    content=amount_text,
                    token_estimate=amount_tokens,
                    metadata={"column": amount_col, "stats": amount_stats},
                )
            )

        if fraud_distribution or top_missing:
            quality_text, quality_tokens = self._build_quality_chunk(
                fraud_col or "class", fraud_distribution, top_missing, rows
            )
            chunks.append(
                self._make_chunk(
                    index=len(chunks) + 1,
                    chunk_type="fraud_quality",
                    content=quality_text,
                    token_estimate=quality_tokens,
                    metadata={
                        "fraud_distribution": fraud_distribution,
                        "top_missing": top_missing,
                    },
                )
            )

        return chunks

    def _build_overview_chunk(
        self,
        rows: int,
        columns: int,
        overview_columns: Sequence[str],
        time_span: Optional[Tuple[float, float]],
        rows_removed: int,
        coerced_columns: Sequence[str],
    ) -> Tuple[str, int]:
        column_subset = self._format_list(overview_columns, limit=self.config.chunk_column_sample)
        sentences = [
            (
                "Visão geral do dataset de fraude em cartão de crédito, contendo "
                f"{rows} transações válidas e {columns} atributos após a etapa de higienização do agente de ingestão."
            ),
            (
                "Cada linha representa uma operação anonimizada; o conjunto preserva a estrutura original usada em benchmarks "
                "de detecção de fraude, o que facilita comparações com trabalhos anteriores e com as próximas fases do pipeline."
            ),
            (
                "As colunas monitoradas incluem "
                f"{column_subset}, entre outros campos derivados que ajudarão na extração de sinais semânticos."
            ),
        ]

        if time_span:
            start, end = time_span
            sentences.append(
                "A coluna temporal cobre o intervalo de "
                f"{start:.0f} a {end:.0f} segundos desde o início da coleta, permitindo análises de evolução temporal."
            )

        sentences.append(
            "A limpeza inicial removeu "
            f"{rows_removed} registros conflitantes e aplicou coerção de tipos nas colunas críticas para garantir consistência."
        )

        if coerced_columns:
            coerced = self._format_list(coerced_columns, limit=6)
            sentences.append(f"Colunas com coerção de tipo registrada: {coerced}.")

        fallback = [
            "O objetivo desses chunks é fornecer contexto textual rico porém compacto para o módulo de embeddings.",
            "Esse resumo permanecerá aderente ao intervalo recomendado de 50 a 180 tokens para balancear custo e expressividade.",
        ]

        return self._compose_chunk_text(sentences, fallback)

    def _build_amount_chunk(self, column: str, stats: Dict[str, float]) -> Tuple[str, int]:
        sentences = [
            (
                f"Resumo de comportamento monetário para a coluna {column}: média {stats['mean']:.2f}, "
                f"desvio padrão {stats['std']:.2f} e valores dentro do intervalo de {stats['min']:.2f} a {stats['max']:.2f}."
            ),
            (
                "Os quartis revelam distribuição assimétrica típica de pagamentos, com primeiros 25% abaixo de "
                f"{stats['p25']:.2f}, mediana em {stats['p50']:.2f} e 75% até {stats['p75']:.2f}."
            ),
            (
                "Esses números sugerem forte concentração de transações de baixo valor e presença de cauda pesada de compras elevadas, "
                "indicando a necessidade de normalização ou escalonamento antes de alimentar modelos supervisionados."
            ),
            (
                "O chunk registra também que valores extremos influenciam métricas agregadas; recomenda-se usar médias robustas ou log-transformações "
                "durante etapas analíticas subsequentes para evitar distorções."
            ),
        ]

        fallback = [
            "As estatísticas serão cruzadas com perfis de fraude para identificar ranges suspeitos e calibrar alertas automáticos.",
            "Manter o texto dentro do limite de tokens permite reuso em embeddings sem custo excessivo.",
        ]

        return self._compose_chunk_text(sentences, fallback)

    def _build_quality_chunk(
        self,
        fraud_column: str,
        fraud_distribution: Dict[str, float],
        top_missing: Sequence[Tuple[str, int]],
        total_rows: int,
    ) -> Tuple[str, int]:
        sentences = []
        if fraud_distribution:
            formatted = ", ".join(
                [f"classe {label}: {freq * 100:.2f}%" for label, freq in sorted(fraud_distribution.items())]
            )
            sentences.append(
                f"Distribuição da coluna de fraude ({fraud_column}): {formatted}. O forte desbalanceamento exige métodos de upsampling ou métricas sensíveis a recall."
            )
            sentences.append(
                "Além disso, o chunk documenta a taxa de fraude para contextualizar prompts e priorizar análises focadas em casos positivos."
            )

        if top_missing:
            formatted_missing = ", ".join([
                f"{col}: {count} nulos" for col, count in top_missing if count > 0
            ])
            if formatted_missing:
                sentences.append(
                    "Colunas com maior incidência de nulos: "
                    f"{formatted_missing}. Esses atributos requerem imputação ou exclusão antes de calibrar modelos."
                )

        sentences.append(
            "O agente registra o histórico de limpeza e os indicadores de qualidade para que estágios posteriores avaliem impacto de anomalias nos resultados."
        )

        fallback = [
            f"Total de linhas consideradas após limpeza: {total_rows}.",
            "A análise contínua desses indicadores garante que cada chunk mantenha contexto operacional relevante dentro do limite de tokens.",
        ]

        return self._compose_chunk_text(sentences, fallback)

    def _compose_chunk_text(self, sentences: Sequence[str], fallback: Sequence[str]) -> Tuple[str, int]:
        tokens_total = 0
        parts: List[str] = []
        for sentence in sentences:
            if not sentence:
                continue
            parts.append(sentence.strip())
        text = " ".join(parts)
        tokens_total = self._token_count(text)

        if tokens_total < self.config.chunk_token_min:
            for extra in fallback:
                if not extra:
                    continue
                parts.append(extra.strip())
                text = " ".join(parts)
                tokens_total = self._token_count(text)
                if tokens_total >= self.config.chunk_token_min:
                    break

        if tokens_total < self.config.chunk_token_min:
            deficit = self.config.chunk_token_min - tokens_total
            padding = "Contexto adicional sobre a preparação dos dados.".split()
            while deficit > 0:
                take = min(deficit, len(padding))
                parts.append(" ".join(padding[:take]))
                deficit -= take
            text = " ".join(parts)
            tokens_total = self._token_count(text)

        if tokens_total > self.config.chunk_token_max:
            token_list = text.split()
            token_list = token_list[: self.config.chunk_token_max]
            text = " ".join(token_list)
            tokens_total = len(token_list)

        return text, tokens_total

    def _make_chunk(
        self,
        *,
        index: int,
        chunk_type: str,
        content: str,
        token_estimate: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "id": f"{self.name.lower()}_{index:02d}",
            "type": chunk_type,
            "content": content,
            "token_estimate": token_estimate,
            "metadata": metadata,
        }

    def _token_count(self, text: str) -> int:
        return len(text.split())

    def _format_list(self, values: Sequence[Any], *, limit: int) -> str:
        cleaned = [str(value) for value in values if value is not None]
        if limit:
            cleaned = cleaned[:limit]
        if not cleaned:
            return ""
        if len(cleaned) == 1:
            return cleaned[0]
        return ", ".join(cleaned[:-1]) + f" e {cleaned[-1]}"

    def _extract_rows_removed(self, actions: Sequence[Dict[str, Any]]) -> int:
        removed = 0
        for action in actions:
            removed += int(action.get("rows_removed", 0))
        return removed

    def _collect_coerced_columns(self, actions: Sequence[Dict[str, Any]]) -> List[str]:
        coerced: List[str] = []
        for action in actions:
            columns = action.get("coerced_columns")
            if columns:
                coerced.extend(columns)
        return coerced


__all__ = ["CSVIngestionAgent", "CSVIngestionConfig"]
