import pandas as pd
import pytest

from src.agent.base_agent import AgentMessage
from src.agent.ingestion_agent import CSVIngestionAgent, CSVIngestionConfig, ColumnType


def _build_config(csv_path):
    default_cfg = CSVIngestionConfig.default()
    return CSVIngestionConfig(
        csv_path=csv_path,
        chunk_size=3,
        chunk_overlap_ratio=0.2,
        semantic_roles=default_cfg.semantic_roles,
        required_roles=(),
        drop_duplicates=True,
        drop_rows_all_null=True,
        create_row_id=True,
        type_thresholds=default_cfg.type_thresholds,
        chunk_token_min=default_cfg.chunk_token_min,
        chunk_token_target=default_cfg.chunk_token_target,
        chunk_token_max=default_cfg.chunk_token_max,
        max_columns_listed=default_cfg.max_columns_listed,
    )


def test_ingestion_agent_loads_and_cleans(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_path = data_dir / "creditcard.csv"
    df = pd.DataFrame(
        {
            "Time": [0, 1, 1, 2, None],
            "Amount": [100.0, 200.5, 200.5, "300", "400"],
            "Class": [0, 0, 0, 1, 1],
        }
    )
    df.loc[2] = df.loc[1]  # duplicate row
    df.to_csv(csv_path, index=False)

    agent = CSVIngestionAgent(config=_build_config(csv_path))
    message = AgentMessage(sender="test", content={"path": str(csv_path)})

    result = agent.run(message)
    cleaned = result.content["data"]
    report = result.content["report"]
    chunks = result.content["chunks"]

    assert "row_id" in cleaned.columns
    assert cleaned["Time"].dtype.kind in {"i", "u", "f"}
    assert cleaned["Amount"].dtype.kind in {"i", "u", "f"}
    assert cleaned.shape[0] == 4
    assert report["shape"]["before_rows"] == 5
    assert report["shape"]["after_rows"] == 3
    assert report["shape"]["before_rows"] - report["shape"]["after_rows"] >= 2
    assert report["cleaning_actions"]  # non-empty log
    assert report["chunking"]["chunks"] == len(report["chunks_processed"])
    assert report["chunking"]["chunk_overlap"] == 1
    assert len(report["chunks_processed"]) >= 2
    assert report["chunks_processed"][0]["overlap_rows"] == 0
    assert report["chunks_processed"][1]["overlap_rows"] > 0
    assert len(report["chunks"]) == len(chunks)
    assert any("dropped_overlap_duplicates" in action for action in report["cleaning_actions"])
    assert len(chunks) >= 1
    for chunk in chunks:
        assert 50 <= chunk["token_estimate"] <= 180
        assert isinstance(chunk["content"], str)

    profile = report["schema_profile"]["columns"]
    assert profile["Time"]["type"] == "numeric"
    assert profile["Amount"]["type"] == "numeric"
    assert profile["Class"]["type"] == "numeric"
    assert report["issues"]["schema_drift"] == []


def test_ingestion_agent_handles_missing_file(tmp_path):
    csv_path = tmp_path / "missing.csv"
    agent = CSVIngestionAgent(config=_build_config(csv_path))

    message = AgentMessage(sender="test", content={})
    with pytest.raises(FileNotFoundError):
        agent.run(message)


def test_ingestion_agent_accepts_dataframe_override():
    df = pd.DataFrame({"Time": [0, 1], "Amount": [10.0, 20.0], "Class": [0, 1]})
    agent = CSVIngestionAgent()
    message = AgentMessage(sender="test", content={"data": df})

    result = agent.run(message)
    cleaned = result.content["data"]
    report = result.content["report"]
    chunks = result.content["chunks"]

    assert report["path"] == "<in-memory>"
    assert "row_id" in cleaned.columns
    assert cleaned.shape[0] == 2
    assert len(chunks) >= 1
    assert len(report["chunks"]) == len(chunks)
    assert report["chunking"]["chunks"] == 1
    assert report["chunking"]["chunks"] == len(report["chunks_processed"])
    assert report["chunks_processed"][0]["overlap_rows"] == 0


def test_type_inference_and_schema_profile():
    df = pd.DataFrame(
        {
            "numbers": ["1", "2", "3", "4"],
            "dates": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "categories": ["A", "B", "A", "C"],
            "text": [
                "primeiro registro",
                "segundo evento",
                "terceiro item",
                "quarto exemplo",
            ],
        }
    )
    agent = CSVIngestionAgent()
    message = AgentMessage(sender="test", content={"data": df})

    result = agent.run(message)
    cleaned = result.content["data"]
    profile = result.content["report"]["schema_profile"]["columns"]

    assert cleaned["numbers"].dtype.kind in {"f", "i"}
    assert str(cleaned["dates"].dtype).startswith("datetime")
    assert profile["numbers"]["type"] == ColumnType.NUMERIC.value
    assert profile["dates"]["type"] == ColumnType.DATETIME.value
    assert profile["categories"]["type"] == ColumnType.CATEGORICAL.value
    assert profile["text"]["type"] == ColumnType.TEXT.value


def test_detects_schema_drift_on_type_change():
    agent = CSVIngestionAgent()

    first_chunk = pd.DataFrame({"value": ["1", "2", "3"]})
    drift_initial = agent._ensure_schema(first_chunk)
    assert drift_initial == {}

    second_chunk = pd.DataFrame({"value": ["x", "y", "z"], "extra": [1, 2, 3]})
    drift = agent._ensure_schema(second_chunk)

    assert "value" in drift["type_mismatch"]
    assert "extra" in drift["new_columns"]
    assert agent._schema_profile.columns["value"].inferred_type == ColumnType.CATEGORICAL
