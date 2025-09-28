"""Agente de ingestão genérico com suporte a chunking, inferência de tipos e
relatórios adaptativos para arquivos CSV.

O agente lê dados tabulares em streaming (ou via DataFrame in-memory), aplica
limpeza consistente, detecta drift de esquema e produz resumos textuais que
alimentam etapas subsequentes do pipeline multiagente.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import pandas as pd

from .base_agent import AgentMessage, BaseAgent
from src.utils.logging_config import get_logger


class ColumnType(str, Enum):
    """Categorias semânticas inferidas para cada coluna."""

    NUMERIC = "numeric"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class ColumnSchema:
    name: str
    inferred_type: ColumnType
    semantic_role: Optional[str] = None


@dataclass
class SchemaProfile:
    columns: Dict[str, ColumnSchema] = field(default_factory=dict)
    stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def ensure(self, schema: ColumnSchema) -> None:
        self.columns[schema.name] = schema

    def to_report(self) -> Dict[str, Any]:
        return {
            "columns": {
                name: {
                    "type": schema.inferred_type.value,
                    "semantic_role": schema.semantic_role,
                    "stats": self.stats.get(name, {}),
                }
                for name, schema in self.columns.items()
            }
        }


@dataclass
class TypeInferenceThresholds:
    numeric_ratio: float = 0.85
    datetime_ratio: float = 0.75
    categorical_unique_ratio: float = 0.5
    categorical_max_unique: int = 120
    text_min_unique: int = 20
    text_min_avg_length: float = 12.0


@dataclass
class CSVIngestionConfig:
    """Configurações do agente de ingestão."""

    csv_path: Path
    delimiter: str = ","
    encoding: str = "utf-8"
    chunk_size: int = 20_000
    chunk_overlap_ratio: float = 0.1
    chunk_overlap_rows: Optional[int] = None
    drop_duplicates: bool = True
    drop_rows_all_null: bool = True
    create_row_id: bool = True
    semantic_roles: Dict[str, Sequence[str]] = field(default_factory=dict)
    required_roles: Sequence[str] = field(default_factory=tuple)
    type_thresholds: TypeInferenceThresholds = field(default_factory=TypeInferenceThresholds)
    read_csv_kwargs: Dict[str, Any] = field(default_factory=dict)
    chunk_token_min: int = 50
    chunk_token_target: int = 120
    chunk_token_max: int = 180
    max_columns_listed: int = 15

    @staticmethod
    def default(project_root: Optional[Path] = None) -> "CSVIngestionConfig":
        root = project_root or Path(__file__).resolve().parents[2]
        return CSVIngestionConfig(
            csv_path=root / "data" / "creditcard.csv",
            semantic_roles={
                "record_id": ("transaction_id", "id", "row_id"),
                "timestamp": ("time", "transaction_time", "timestamp"),
                "amount": ("amount", "valor", "transaction_amount"),
                "target": ("class", "fraud", "is_fraud"),
            },
            required_roles=("record_id",),
            chunk_size=20_000,
            chunk_overlap_ratio=0.1,
        )

    def resolve_overlap(self) -> int:
        if self.chunk_overlap_rows is not None:
            overlap = int(self.chunk_overlap_rows)
        else:
            ratio = max(0.0, min(self.chunk_overlap_ratio, 0.5))
            overlap = int(round(self.chunk_size * ratio))
        if overlap < 0:
            return 0
        if overlap >= self.chunk_size:
            return max(self.chunk_size - 1, 0)
        return overlap


class CSVIngestionAgent(BaseAgent):
    """Agente que transforma CSVs genéricos em dados limpos e relatórios."""

    def __init__(self, name: Optional[str] = None, config: Optional[CSVIngestionConfig] = None) -> None:
        super().__init__(name=name or "CSVIngestionAgent")
        self.config = config or CSVIngestionConfig.default()
        self.logger = get_logger(self.name)
        self._schema_profile = SchemaProfile()
        self._schema_drift_events: List[Dict[str, Any]] = []
        self._row_id_counter = 1

    def run(self, message: Optional[AgentMessage] = None) -> AgentMessage:
        return self.handle(message)

    def handle(self, message: Optional[AgentMessage]) -> AgentMessage:
        payload = message.content if message else {}
        if payload and not isinstance(payload, dict):
            raise TypeError("CSVIngestionAgent espera payload dict com overrides opcionais.")

        self._schema_profile = SchemaProfile()
        self._schema_drift_events = []
        self._row_id_counter = 1

        dataframe, report, text_chunks = self._ingest(payload or {})
        return self.build_message({"data": dataframe, "report": report, "chunks": text_chunks}, stage="ingestion")

    def _ingest(self, override: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        in_memory_df = override.get("data")
        if in_memory_df is not None:
            raw_df = self._ensure_dataframe(in_memory_df)
            chunk_iter = self._dataframe_chunk_iter(raw_df)
            source_label = "<in-memory>"
        else:
            path = self._resolve_path(override)
            if not path.exists():
                raise FileNotFoundError(f"Arquivo CSV não encontrado: {path}")
            raw_df = self._read_csv(path)
            chunk_iter = self._dataframe_chunk_iter(raw_df)
            source_label = str(path)

        report: Dict[str, Any] = {
            "path": source_label,
            "shape": {
                "before_rows": int(raw_df.shape[0]),
                "before_columns": int(raw_df.shape[1]),
                "after_rows": 0,
                "after_columns": 0,
            },
            "cleaning_actions": [],
            "issues": {"schema_drift": []},
            "chunks_processed": [],
            "chunking": {
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": 0,
                "chunks": 0,
            },
        }

        cleaned_chunks: List[pd.DataFrame] = []
        for chunk_index, chunk_df, base_rows, overlap_rows in chunk_iter:
            cleaned_chunk, chunk_report, actions, drift = self._process_chunk(
                chunk_df, chunk_index, base_rows, overlap_rows
            )
            cleaned_chunks.append(cleaned_chunk)
            report["chunks_processed"].append(chunk_report)
            report["cleaning_actions"].extend(actions)
            if any(drift.values()):
                self._schema_drift_events.append({"chunk": chunk_index, **drift})

        combined = pd.concat(cleaned_chunks, ignore_index=True) if cleaned_chunks else pd.DataFrame()
        combined = self._deduplicate_post_concat(combined, report)
        null_counts = combined.isna().sum().astype(int).to_dict()

        numeric_cols = [
            name
            for name, schema in self._schema_profile.columns.items()
            if schema.inferred_type == ColumnType.NUMERIC and name in combined.columns
        ]
        fully_valid = combined.dropna(subset=numeric_cols) if numeric_cols else combined.dropna(how="any")

        report["shape"]["after_rows"] = int(fully_valid.shape[0])
        report["shape"]["after_columns"] = int(combined.shape[1])
        report["issues"].update({"null_counts": null_counts})
        report["issues"]["schema_drift"] = self._schema_drift_events
        report["chunking"]["chunks"] = len(report["chunks_processed"])
        overlap_value = self.config.resolve_overlap()
        report["chunking"]["chunk_overlap"] = overlap_value if len(report["chunks_processed"]) > 1 else 0

        self._populate_schema_statistics(combined)
        if self._schema_profile.columns:
            report["schema_profile"] = self._schema_profile.to_report()

        text_chunks = self._generate_text_chunks(combined)
        report["chunks"] = [
            {"id": chunk["id"], "type": chunk["type"], "token_estimate": chunk["token_estimate"]}
            for chunk in text_chunks
        ]

        return combined, report, text_chunks

    def _dataframe_chunk_iter(self, dataframe: pd.DataFrame) -> Iterator[Tuple[int, pd.DataFrame, int, int]]:
        total_rows = int(dataframe.shape[0])
        if total_rows == 0:
            yield from []
            return

        chunk_size = max(1, int(self.config.chunk_size))
        overlap = self.config.resolve_overlap()
        if overlap >= chunk_size:
            overlap = max(0, chunk_size - 1)
        step = chunk_size - overlap if chunk_size > overlap else chunk_size

        index = 0
        chunk_index = 0
        while index < total_rows:
            end = min(index + chunk_size, total_rows)
            chunk_df = dataframe.iloc[index:end].copy()
            base_rows = int(chunk_df.shape[0])
            overlap_rows = overlap if chunk_index > 0 else 0
            yield chunk_index, chunk_df, base_rows, overlap_rows
            chunk_index += 1
            if step == 0:
                break
            index += step

    def _process_chunk(
        self,
        chunk_df: pd.DataFrame,
        chunk_index: int,
        base_rows: int,
        overlap_rows: int,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
        drift = self._ensure_schema(chunk_df)
        cleaned_chunk, actions, issues = self._clean_chunk(chunk_df)

        chunk_report = {
            "chunk_index": chunk_index,
            "input_rows": base_rows,
            "overlap_rows": int(overlap_rows),
            "output_rows": int(cleaned_chunk.shape[0]),
            "issues": issues,
            "cleaning_actions": actions,
        }
        return cleaned_chunk, chunk_report, actions, drift

    def _ensure_schema(self, chunk: pd.DataFrame) -> Dict[str, Any]:
        drift = {"missing_columns": [], "new_columns": [], "type_mismatch": {}}

        if not self._schema_profile.columns:
            for name in chunk.columns:
                schema = self._build_schema_entry(name, chunk[name])
                self._schema_profile.ensure(schema)
            return {}

        existing_columns = set(self._schema_profile.columns.keys())
        current_columns = set(chunk.columns)

        for missing in sorted(existing_columns - current_columns):
            drift["missing_columns"].append(missing)

        for name in chunk.columns:
            schema = self._build_schema_entry(name, chunk[name])
            if name not in self._schema_profile.columns:
                self._schema_profile.ensure(schema)
                drift["new_columns"].append(name)
            else:
                previous = self._schema_profile.columns[name]
                if schema.inferred_type != ColumnType.UNKNOWN and schema.inferred_type != previous.inferred_type:
                    drift["type_mismatch"][name] = {
                        "expected": previous.inferred_type.value,
                        "observed": schema.inferred_type.value,
                    }
                    self._schema_profile.ensure(schema)
                elif schema.inferred_type == ColumnType.UNKNOWN:
                    # Mantém tipo anterior quando nenhuma informação adicional é obtida
                    continue
                else:
                    self._schema_profile.ensure(schema)

        return drift

    def _build_schema_entry(self, name: str, series: pd.Series) -> ColumnSchema:
        inferred_type = self._infer_column_type(series)
        semantic_role = self._match_role(name)
        return ColumnSchema(name=name, inferred_type=inferred_type, semantic_role=semantic_role)

    def _infer_column_type(self, series: pd.Series) -> ColumnType:
        thresholds = self.config.type_thresholds
        non_null = series.dropna()
        if non_null.empty:
            return ColumnType.UNKNOWN

        numeric_series = pd.to_numeric(non_null, errors="coerce")
        numeric_ratio = numeric_series.notna().sum() / len(non_null)
        if numeric_ratio >= thresholds.numeric_ratio:
            return ColumnType.NUMERIC

        datetime_series = pd.to_datetime(non_null, errors="coerce")
        datetime_ratio = datetime_series.notna().sum() / len(non_null)
        if datetime_ratio >= thresholds.datetime_ratio:
            return ColumnType.DATETIME

        as_str = non_null.astype(str)
        unique_count = as_str.nunique(dropna=True)
        unique_ratio = unique_count / len(non_null)
        avg_length = float(as_str.str.len().mean()) if len(as_str) else 0.0

        if avg_length >= thresholds.text_min_avg_length or unique_count >= thresholds.text_min_unique:
            return ColumnType.TEXT

        if unique_count <= thresholds.categorical_max_unique or unique_ratio <= thresholds.categorical_unique_ratio:
            return ColumnType.CATEGORICAL

        if avg_length >= thresholds.text_min_avg_length:
            return ColumnType.TEXT

        return ColumnType.CATEGORICAL

    def _match_role(self, column_name: str) -> Optional[str]:
        lowered = column_name.lower()
        for role, aliases in self.config.semantic_roles.items():
            if any(lowered == alias.lower() for alias in aliases):
                return role
        return None

    def _clean_chunk(self, chunk: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
        cleaned = chunk.copy()
        actions: List[Dict[str, Any]] = []

        for name, schema in self._schema_profile.columns.items():
            if name not in cleaned.columns:
                continue
            series = cleaned[name]
            if schema.inferred_type == ColumnType.NUMERIC:
                converted = pd.to_numeric(series, errors="coerce")
                coerced = int((series.notna() & converted.isna()).sum())
                cleaned[name] = converted
                if coerced:
                    actions.append({"coerced_numeric": {name: coerced}})
            elif schema.inferred_type == ColumnType.DATETIME:
                converted = pd.to_datetime(series, errors="coerce")
                invalid = int((series.notna() & converted.isna()).sum())
                cleaned[name] = converted
                if invalid:
                    actions.append({"coerced_datetime": {name: invalid}})
            elif schema.inferred_type == ColumnType.CATEGORICAL:
                cleaned[name] = series.astype(str).str.strip()
            elif schema.inferred_type == ColumnType.TEXT:
                cleaned[name] = series.astype(str).str.normalize("NFKC").str.strip()
            else:
                cleaned[name] = series

        if self.config.drop_rows_all_null:
            before = int(cleaned.shape[0])
            cleaned = cleaned.dropna(how="all")
            removed = before - int(cleaned.shape[0])
            if removed:
                actions.append({"dropped_all_null_rows": removed})

        if self.config.drop_duplicates:
            before = int(cleaned.shape[0])
            cleaned = cleaned.drop_duplicates()
            removed = before - int(cleaned.shape[0])
            if removed:
                actions.append({"dropped_duplicates": removed})

        cleaned = cleaned.reset_index(drop=True)
        if self.config.create_row_id:
            start = self._row_id_counter
            cleaned.insert(0, "row_id", range(start, start + int(cleaned.shape[0])))
            self._row_id_counter += int(cleaned.shape[0])

        issues = {"null_counts": cleaned.isna().sum().astype(int).to_dict()}
        return cleaned, actions, issues

    def _deduplicate_post_concat(self, dataframe: pd.DataFrame, report: Dict[str, Any]) -> pd.DataFrame:
        if dataframe.empty:
            return dataframe

        subset = [col for col in dataframe.columns if col != "row_id"]
        before = int(dataframe.shape[0])
        if subset:
            deduplicated = dataframe.drop_duplicates(subset=subset).reset_index(drop=True)
        else:
            deduplicated = dataframe.drop_duplicates().reset_index(drop=True)

        removed = before - int(deduplicated.shape[0])
        if removed:
            report["cleaning_actions"].append({"dropped_overlap_duplicates": removed})
        return deduplicated

    def _populate_schema_statistics(self, dataframe: pd.DataFrame) -> None:
        stats: Dict[str, Dict[str, Any]] = {}
        for name, schema in self._schema_profile.columns.items():
            if name not in dataframe.columns:
                continue
            series = dataframe[name]
            stat: Dict[str, Any] = {
                "non_null": int(series.notna().sum()),
                "null_fraction": float(series.isna().sum() / max(len(series), 1)) if len(series) else 0.0,
            }
            if schema.inferred_type == ColumnType.NUMERIC:
                numeric = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric.empty:
                    desc = numeric.describe(percentiles=[0.25, 0.5, 0.75])
                    stat.update(
                        {
                            "min": float(desc["min"]),
                            "max": float(desc["max"]),
                            "mean": float(desc["mean"]),
                            "std": float(desc["std"]),
                            "p25": float(desc["25%"]),
                            "p50": float(desc["50%"]),
                            "p75": float(desc["75%"]),
                        }
                    )
            elif schema.inferred_type == ColumnType.DATETIME:
                dt = pd.to_datetime(series, errors="coerce").dropna()
                if not dt.empty:
                    stat.update({"min": dt.min().isoformat(), "max": dt.max().isoformat()})
            elif schema.inferred_type == ColumnType.CATEGORICAL:
                counts = series.astype(str).value_counts().head(5)
                stat.update({"unique": int(series.nunique(dropna=True)), "top_values": counts.to_dict()})
            elif schema.inferred_type == ColumnType.TEXT:
                lengths = series.astype(str).str.len()
                if not lengths.empty:
                    stat.update({"avg_length": float(lengths.mean()), "max_length": int(lengths.max())})
            stats[name] = stat
        self._schema_profile.stats = stats

    # ------------------------------------------------------------------
    # Geração de chunks textuais
    # ------------------------------------------------------------------
    def _generate_text_chunks(self, dataframe: pd.DataFrame) -> List[Dict[str, Any]]:
        if dataframe.empty:
            return []

        profile = self._schema_profile
        numeric_cols = [name for name, schema in profile.columns.items() if schema.inferred_type == ColumnType.NUMERIC]
        categorical_cols = [
            name for name, schema in profile.columns.items() if schema.inferred_type == ColumnType.CATEGORICAL
        ]
        text_cols = [name for name, schema in profile.columns.items() if schema.inferred_type == ColumnType.TEXT]
        datetime_cols = [name for name, schema in profile.columns.items() if schema.inferred_type == ColumnType.DATETIME]

        chunks: List[Dict[str, Any]] = []

        overview_text, overview_tokens = self._compose_overview_chunk(
            dataframe, numeric_cols, categorical_cols, text_cols, datetime_cols
        )
        chunks.append(
            self._make_chunk(
                index=len(chunks) + 1,
                chunk_type="dataset_overview",
                content=overview_text,
                token_estimate=overview_tokens,
                metadata={
                    "rows": int(dataframe.shape[0]),
                    "columns": int(dataframe.shape[1]),
                    "column_types": dict(Counter(schema.inferred_type.value for schema in profile.columns.values())),
                },
            )
        )

        if numeric_cols:
            numeric_text, numeric_tokens = self._compose_numeric_chunk(dataframe, numeric_cols)
            chunks.append(
                self._make_chunk(
                    index=len(chunks) + 1,
                    chunk_type="numeric_statistics",
                    content=numeric_text,
                    token_estimate=numeric_tokens,
                    metadata={"columns": list(numeric_cols)},
                )
            )

        if categorical_cols:
            categorical_text, categorical_tokens = self._compose_categorical_chunk(dataframe, categorical_cols)
            chunks.append(
                self._make_chunk(
                    index=len(chunks) + 1,
                    chunk_type="categorical_patterns",
                    content=categorical_text,
                    token_estimate=categorical_tokens,
                    metadata={"columns": list(categorical_cols)},
                )
            )

        if text_cols:
            text_text, text_tokens = self._compose_textual_chunk(dataframe, text_cols)
            chunks.append(
                self._make_chunk(
                    index=len(chunks) + 1,
                    chunk_type="textual_overview",
                    content=text_text,
                    token_estimate=text_tokens,
                    metadata={"columns": list(text_cols)},
                )
            )

        return chunks

    def _compose_overview_chunk(
        self,
        dataframe: pd.DataFrame,
        numeric_cols: Sequence[str],
        categorical_cols: Sequence[str],
        text_cols: Sequence[str],
        datetime_cols: Sequence[str],
    ) -> Tuple[str, int]:
        rows = int(dataframe.shape[0])
        columns = int(dataframe.shape[1])
        listed_columns = ", ".join(list(dataframe.columns[: self.config.max_columns_listed]))
        sentences = [
            (
                "Visão geral de um dataset ingerido dinamicamente: "
                f"{rows} linhas disponíveis e {columns} colunas após deduplicação."
            ),
            "Colunas analisadas incluem " + listed_columns + ".",
        ]
        if numeric_cols:
            sentences.append(f"Detectadas {len(numeric_cols)} colunas numéricas com métricas agregadas.")
        if categorical_cols:
            sentences.append(f"{len(categorical_cols)} colunas categóricas apresentaram padrões relevantes de frequência.")
        if text_cols:
            sentences.append("Há colunas textuais que podem exigir vetorização ou limpeza adicional.")
        if datetime_cols:
            sentences.append("Campos temporais foram reconhecidos, permitindo análises de evolução no tempo.")
        sentences.append(
            "Linhas totalmente nulas e duplicatas foram removidas para garantir consistência ao pipeline multiagente."
        )

        fallback = [
            "O resumo é neutro e preparado para prompts de análise em domínios variados.",
            "Os tokens foram calibrados para caber dentro da janela sugerida para embeddings contextuais.",
        ]
        return self._compose_chunk_text(sentences, fallback)

    def _compose_numeric_chunk(self, dataframe: pd.DataFrame, numeric_cols: Sequence[str]) -> Tuple[str, int]:
        sentences: List[str] = []
        for column in list(numeric_cols)[:3]:
            numeric = pd.to_numeric(dataframe[column], errors="coerce").dropna()
            if numeric.empty:
                continue
            desc = numeric.describe(percentiles=[0.25, 0.5, 0.75])
            sentences.append(
                (
                    f"Coluna {column}: média {desc['mean']:.2f}, desvio padrão {desc['std']:.2f}, "
                    f"intervalo de {desc['min']:.2f} a {desc['max']:.2f}."
                )
            )
        if not sentences:
            sentences.append(
                "As colunas numéricas não possuem valores suficientes para estatísticas conclusivas, mas foram preservadas."
            )
        fallback = [
            "Sugere-se avaliar normalização ou tratamento de outliers antes de modelos quantitativos.",
            "Os indicadores numéricos ajudam a priorizar features para o agente executor.",
        ]
        return self._compose_chunk_text(sentences, fallback)

    def _compose_categorical_chunk(self, dataframe: pd.DataFrame, categorical_cols: Sequence[str]) -> Tuple[str, int]:
        sentences: List[str] = []
        for column in list(categorical_cols)[:3]:
            counts = dataframe[column].astype(str).value_counts().head(5)
            formatted = ", ".join(f"{value}: {count}" for value, count in counts.items()) or "sem categorias predominantes"
            sentences.append(f"Coluna {column} apresenta principais categorias {formatted}.")
        fallback = [
            "Categorias raras foram preservadas para avaliações futuras de agrupamento ou encoding.",
            "Esses sinais apoiam decisões sobre balanceamento e estratificação em análises posteriores.",
        ]
        return self._compose_chunk_text(sentences, fallback)

    def _compose_textual_chunk(self, dataframe: pd.DataFrame, text_cols: Sequence[str]) -> Tuple[str, int]:
        sentences: List[str] = []
        for column in list(text_cols)[:2]:
            lengths = dataframe[column].astype(str).str.len()
            if lengths.empty:
                continue
            sentences.append(
                f"Coluna {column} possui comprimento médio de {lengths.mean():.1f} caracteres e máximo de {int(lengths.max())}."
            )
        fallback = [
            "Os textos passaram por normalização básica para reduzir ruídos antes de embeddings contextuais.",
            "Amostras podem ser coletadas posteriormente para enriquecer prompts específicos.",
        ]
        return self._compose_chunk_text(sentences, fallback)

    def _compose_chunk_text(self, sentences: Sequence[str], fallback: Sequence[str]) -> Tuple[str, int]:
        parts = [sentence.strip() for sentence in sentences if sentence]
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
            padding = "Contexto adicional sobre a preparação genérica dos dados.".split()
            while tokens_total < self.config.chunk_token_min:
                take = min(len(padding), self.config.chunk_token_min - tokens_total)
                parts.append(" ".join(padding[:take]))
                text = " ".join(parts)
                tokens_total = self._token_count(text)

        if tokens_total > self.config.chunk_token_max:
            token_list = text.split()[: self.config.chunk_token_max]
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

    def _resolve_path(self, override: Dict[str, Any]) -> Path:
        if override.get("path"):
            return Path(override["path"]).expanduser().resolve()
        if override.get("csv_path"):
            return Path(override["csv_path"]).expanduser().resolve()
        return self.config.csv_path

    def _read_csv(self, path: Path) -> pd.DataFrame:
        kwargs = dict(self.config.read_csv_kwargs)
        kwargs.setdefault("encoding", self.config.encoding)
        kwargs.setdefault("sep", self.config.delimiter)
        return pd.read_csv(path, **kwargs)

    def _ensure_dataframe(self, data: Any) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            return data.copy()
        return pd.DataFrame(data)


__all__ = ["CSVIngestionAgent", "CSVIngestionConfig", "TypeInferenceThresholds", "ColumnType"]
