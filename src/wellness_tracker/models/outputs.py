from typing import Literal

from pydantic import BaseModel, field_validator


class WhoopBriefOutput(BaseModel):
    agent_id: Literal["whoop_brief_agent"] = "whoop_brief_agent"
    version: str
    status: Literal["success", "partial", "unable_to_determine"]
    strain_target: float | None = None
    confidence: float
    notes: str | None = None
    requires_human_review: bool = False

    @field_validator("strain_target")
    @classmethod
    def strain_in_range(cls, v: float | None) -> float | None:
        if v is not None and (v < 0.0 or v > 21.0):
            raise ValueError("strain_target must be >= 0.0 and <= 21.0")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence must be >= 0.0 and <= 1.0")
        return v
