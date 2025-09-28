"""Simple orchestration utilities for the multi-agent pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from src.agent.base_agent import AgentMessage, BaseAgent
from src.utils.logging_config import get_logger


@dataclass
class OrchestrationResult:
    """Container with the final message and the message history."""

    final_message: AgentMessage
    history: List[AgentMessage] = field(default_factory=list)


class AgentOrchestrator:
    """Sequential orchestrator that wires messages across agents."""

    def __init__(self, agents: Sequence[BaseAgent]) -> None:
        if not agents:
            raise ValueError("AgentOrchestrator requires at least one agent")
        self.agents = list(agents)
        self.logger = get_logger(self.__class__.__name__)

    def run(self, initial_message: AgentMessage) -> OrchestrationResult:
        self.logger.info("Starting orchestration", extra={"agents": self._agent_names})
        message = initial_message
        history: List[AgentMessage] = []
        for agent in self.agents:
            self.logger.debug(
                "Dispatching message", extra={"to": agent.name, "stage": message.metadata.get("stage")}
            )
            message = agent.run(message)
            history.append(message)
        self.logger.info("Finished orchestration", extra={"final_stage": message.metadata.get("stage")})
        return OrchestrationResult(final_message=message, history=history)

    @property
    def _agent_names(self) -> Iterable[str]:
        return [agent.name for agent in self.agents]

    @staticmethod
    def build_initial_message(content: object, *, stage: str = "ingestion") -> AgentMessage:
        """Helper to start a pipeline using the canonical message format."""
        return AgentMessage(sender="orchestrator", content=content, metadata={"stage": stage})


class MessageExchange:
    """Lightweight message history buffer shared across agents."""

    def __init__(self) -> None:
        self._buffer: List[AgentMessage] = []

    def publish(self, message: AgentMessage) -> None:
        self._buffer.append(message)

    def history(self) -> List[AgentMessage]:
        return list(self._buffer)

    def last(self) -> Optional[AgentMessage]:
        return self._buffer[-1] if self._buffer else None
