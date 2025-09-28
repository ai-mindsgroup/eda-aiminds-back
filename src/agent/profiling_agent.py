"""Agent responsible for initial data profiling and cleansing stubs."""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from .base_agent import AgentMessage, BaseAgent


class ProfilingAgent(BaseAgent):
    """Generate lightweight profiling metadata for tabular datasets."""

    def run(self, message: Optional[AgentMessage] = None) -> AgentMessage:
        if message is None:
            raise ValueError("ProfilingAgent requires an input message with data")
        return self.handle(message)

    def handle(self, message: AgentMessage) -> AgentMessage:
        self.log_start("profiling", source=message.sender)
        data = self._extract_dataframe(message.content)
        profile = self._build_profile(data)
        self.log_end("profiling", rows=profile.get("rows"), columns=profile.get("columns"))
        return self.build_message({"profile": profile, "raw": data}, stage="profiling")

    @staticmethod
    def _extract_dataframe(payload: Any) -> pd.DataFrame:
        if isinstance(payload, pd.DataFrame):
            return payload
        if isinstance(payload, dict) and "data" in payload:
            value = payload["data"]
            if isinstance(value, pd.DataFrame):
                return value
        raise TypeError("ProfilingAgent expected a pandas.DataFrame in the message content under 'data'.")

    def _build_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        profile: Dict[str, Any] = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "missing_values": df.isna().sum().to_dict(),
            "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
        }
        return profile
