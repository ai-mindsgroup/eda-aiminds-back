"""Agent delegated to generate actionable tasks or prompts from insights."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_agent import AgentMessage, BaseAgent


class ExecutorAgent(BaseAgent):
    """Prepare execution plans or prompts based on upstream insights."""

    def __init__(self, name: Optional[str] = None, objectives: Optional[List[str]] = None) -> None:
        super().__init__(name=name)
        self.objectives = objectives or ["summarise", "highlight_anomalies", "prepare_llm_prompt"]

    def run(self, message: Optional[AgentMessage] = None) -> AgentMessage:
        if message is None:
            raise ValueError("ExecutorAgent requires insights to assemble execution plan")
        return self.handle(message)

    def handle(self, message: AgentMessage) -> AgentMessage:
        self.log_start("execution", source=message.sender)
        insights = self._extract_insights(message.content)
        plan = self._build_execution_plan(insights)
        self.log_end("execution", steps=len(plan.get("steps", [])))
        return self.build_message(plan, stage="execution")

    def _extract_insights(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict) and "insights" in payload:
            return payload["insights"]
        raise TypeError("ExecutorAgent expected payload containing 'insights'.")

    def _build_execution_plan(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        steps = []
        if insights.get("descriptive_stats"):
            steps.append("Validar estatísticas descritivas e gerar narrativa resumida.")
        if insights.get("top_missing"):
            steps.append("Recomendar tratamento para colunas com maior taxa de valores ausentes.")
        plan = {
            "objectives": self.objectives,
            "steps": steps,
            "context": insights,
        }
        return plan
