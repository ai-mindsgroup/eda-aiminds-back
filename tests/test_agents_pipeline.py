import pandas as pd
import pytest

from src.agent.base_agent import AgentMessage
from src.agent.executor_agent import ExecutorAgent
from src.agent.ingestion_agent import CSVIngestionAgent
from src.agent.indexing_agent import IndexingAgent
from src.agent.profiling_agent import ProfilingAgent
from src.rag.orchestrator import AgentOrchestrator


def dataframe_fixture():
    return pd.DataFrame(
        {
            "time": [0, 1, 2],
            "amount": [10.0, 20.5, 5.2],
            "fraud": [0, 0, 1],
            "score": [0.1, 0.3, 0.95],
        }
    )


def test_agents_pipeline_sequential_flow():
    df = dataframe_fixture()
    ingestion = CSVIngestionAgent()
    profiling = ProfilingAgent()
    indexing = IndexingAgent()
    executor = ExecutorAgent()

    orchestrator = AgentOrchestrator([ingestion, profiling, indexing, executor])

    initial = orchestrator.build_initial_message({"data": df}, stage="ingestion")
    result = orchestrator.run(initial)

    assert len(result.history) == 4
    assert result.history[0].metadata["stage"] == "ingestion"
    ingestion_payload = result.history[0].content
    assert "chunks" in ingestion_payload
    assert "report" in ingestion_payload
    assert ingestion_payload["report"]["chunking"]["chunks"] == 1
    assert len(ingestion_payload["chunks"]) >= 1
    assert result.final_message.metadata["stage"] == "execution"

    plan = result.final_message.content
    assert "steps" in plan
    numeric_cols = plan["context"]["numeric_columns"]
    assert set(["amount", "fraud", "score"]).issubset(set(numeric_cols))


def test_agent_message_helpers():
    agent = ProfilingAgent()
    msg = agent.build_message({"foo": "bar"}, stage="test")
    assert isinstance(msg, AgentMessage)
    assert msg.sender == agent.name
    assert msg.metadata["stage"] == "test"


def test_orchestrator_requires_agents():
    with pytest.raises(ValueError):
        AgentOrchestrator([])
