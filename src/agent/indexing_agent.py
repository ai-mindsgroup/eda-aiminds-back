"""Agent responsible for building statistical insights and index-ready chunks."""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from .base_agent import AgentMessage, BaseAgent


class IndexingAgent(BaseAgent):
    """Synthesise compact insights that will be later embedded/indexed."""

    def run(self, message: Optional[AgentMessage] = None) -> AgentMessage:
        if message is None:
            raise ValueError("IndexingAgent requires profiling output as input message")
        return self.handle(message)

    def handle(self, message: AgentMessage) -> AgentMessage:
        self.log_start("indexing", source=message.sender)
        payload = self._extract_payload(message.content)
        df = payload["raw"]
        insights = self._generate_insights(df, payload["profile"])
        self.log_end("indexing", insights_count=len(insights))
        return self.build_message({"insights": insights, "profile": payload["profile"]}, stage="indexing")

    def _extract_payload(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict) and "raw" in payload and "profile" in payload:
            raw = payload["raw"]
            if isinstance(raw, pd.DataFrame):
                return payload
        raise TypeError(
            "IndexingAgent expected a dict with 'raw' pandas.DataFrame and 'profile' metadata from ProfilingAgent."
        )

    def _generate_insights(self, df: pd.DataFrame, profile: Dict[str, Any]) -> Dict[str, Any]:
        numeric_df = df.select_dtypes(include=["number"])
        descriptives = numeric_df.describe().to_dict() if not numeric_df.empty else {}
        top_missing = sorted(profile["missing_values"].items(), key=lambda kv: kv[1], reverse=True)[:5]
        return {
            "descriptive_stats": descriptives,
            "top_missing": top_missing,
            "numeric_columns": profile.get("numeric_columns", []),
        }
