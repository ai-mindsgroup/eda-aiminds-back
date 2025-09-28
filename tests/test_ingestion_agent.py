import pandas as pd
import pytest

from src.agent.base_agent import AgentMessage
from src.agent.ingestion_agent import CSVIngestionAgent, CSVIngestionConfig


def _build_config(csv_path):
    default_cfg = CSVIngestionConfig.default()
    return CSVIngestionConfig(
        csv_path=csv_path,
        essential_columns=default_cfg.essential_columns,
        dtype_expectations=default_cfg.dtype_expectations,
        drop_duplicates=default_cfg.drop_duplicates,
        dropna_subset=default_cfg.dropna_subset,
        create_missing_id=default_cfg.create_missing_id,
        chunk_size=3,
        chunk_overlap=1,
        chunk_token_min=default_cfg.chunk_token_min,
        chunk_token_target=default_cfg.chunk_token_target,
        chunk_token_max=default_cfg.chunk_token_max,
        chunk_column_sample=default_cfg.chunk_column_sample,
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

    assert "transaction_id" in cleaned.columns
    assert cleaned["Time"].dtype.kind in {"i", "u", "f"}
    assert cleaned.shape[0] == 3  # duplicate and null rows removed
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
    assert "transaction_id" in cleaned.columns
    assert cleaned.shape[0] == 2
    assert len(chunks) >= 1
    assert len(report["chunks"]) == len(chunks)
    assert report["chunking"]["chunks"] == 1
    assert report["chunking"]["chunks"] == len(report["chunks_processed"])
    assert report["chunks_processed"][0]["overlap_rows"] == 0
