"""Base abstractions for multi-agent components.

This module defines a lightweight contract for agents participating in the
RAG-oriented backend. All agents exchange `AgentMessage` objects and expose
`run`/`handle` hooks to cooperate within an orchestrated pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.utils.logging_config import get_logger


@dataclass
class AgentMessage:
    """Canonical payload exchanged between agents."""

    sender: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, **extra: Any) -> "AgentMessage":
        """Return a copy of the message with additional metadata merged in."""
        merged = {**self.metadata, **extra}
        return AgentMessage(sender=self.sender, content=self.content, metadata=merged)


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__
        self.logger = get_logger(self.name)

    @abstractmethod
    def run(self, message: Optional[AgentMessage] = None) -> AgentMessage:
        """Execute the agent's main logic.

        Parameters
        ----------
        message: Optional[AgentMessage]
            Optional input message from a previous agent.

        Returns
        -------
        AgentMessage
            The resulting message to be consumed by downstream agents.
        """

    @abstractmethod
    def handle(self, message: AgentMessage) -> AgentMessage:
        """Process an incoming message, returning a transformed message."""

    def build_message(self, content: Any, **metadata: Any) -> AgentMessage:
        """Helper for producing a message stamped with the agent identity."""
        self.logger.debug("Building message", extra={"metadata": metadata})
        return AgentMessage(sender=self.name, content=content, metadata=metadata)

    def log_start(self, context: str, **details: Any) -> None:
        self.logger.info("Starting %s", context, extra={"details": details})

    def log_end(self, context: str, **details: Any) -> None:
        self.logger.info("Finished %s", context, extra={"details": details})
