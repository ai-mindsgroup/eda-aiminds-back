import pandas as pd
import pytest

from src.agent.base_agent import AgentMessage
from src.agent.executor_agent import ExecutorAgent
from src.agent.indexing_agent import IndexingAgent
from src.agent.profiling_agent import ProfilingAgent
from src.rag.orchestrator import AgentOrchestrator


def dataframe_fixture():
    return pd.DataFrame(
        {
            "amount": [10.0, 20.5, 5.2],
            "fraud": [0, 0, 1],
            "score": [0.1, 0.3, 0.95],
        }
    )


def test_agents_pipeline_sequential_flow():
    df = dataframe_fixture()
    profiling = ProfilingAgent()
    indexing = IndexingAgent()
    executor = ExecutorAgent()

    orchestrator = AgentOrchestrator([profiling, indexing, executor])

    initial = orchestrator.build_initial_message({"data": df}, stage="ingestion")
    result = orchestrator.run(initial)

    assert len(result.history) == 3
    assert result.final_message.metadata["stage"] == "execution"

    plan = result.final_message.content
    assert "steps" in plan
    assert plan["context"]["numeric_columns"] == ["amount", "fraud", "score"]


def test_agent_message_helpers():
    agent = ProfilingAgent()
    msg = agent.build_message({"foo": "bar"}, stage="test")
    assert isinstance(msg, AgentMessage)
    assert msg.sender == agent.name
    assert msg.metadata["stage"] == "test"


def test_orchestrator_requires_agents():
    with pytest.raises(ValueError):
        AgentOrchestrator([])
