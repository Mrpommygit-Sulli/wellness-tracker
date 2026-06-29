from typing import Any, Literal

from wellness_tracker.agents.base import BaseAgent
from wellness_tracker.models.outputs import WhoopBriefOutput


class WhoopBriefAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("whoop_brief_agent.yaml")

    def run(self, payload: dict[str, Any]) -> WhoopBriefOutput:
        raw_response = self._call_llm(payload["raw_text"])

        try:
            data = self._parse_json(raw_response)
        except ValueError:
            return WhoopBriefOutput(
                version=self.version,
                status="unable_to_determine",
                strain_target=None,
                confidence=0.0,
            )

        strain_target = data.get("strain_target")
        status: Literal["success", "unable_to_determine"] = (
            "success" if strain_target is not None else "unable_to_determine"
        )

        return WhoopBriefOutput(
            version=self.version,
            status=status,
            strain_target=strain_target,
            confidence=data.get("confidence", 0.0),
            notes=data.get("notes"),
        )
