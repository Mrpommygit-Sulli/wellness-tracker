import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from wellness_tracker.models.objectives import WeeklyObjectives


class WhoopDayContext(BaseModel):
    strain_target: float
    strain_accumulated: float = 0.0
    strain_actual: float | None = None
    weight_kg: float | None = None

    @field_validator("strain_target", "strain_accumulated", "strain_actual")
    @classmethod
    def strain_in_range(cls, v: float | None) -> float | None:
        if v is not None and (v < 0.0 or v > 21.0):
            raise ValueError("strain values must be >= 0.0 and <= 21.0")
        return v

    @field_validator("weight_kg")
    @classmethod
    def weight_in_range(cls, v: float | None) -> float | None:
        if v is not None and (v <= 0 or v >= 300):
            raise ValueError("weight_kg must be > 0 and < 300")
        return v


class DailyEnvelope(BaseModel):
    envelope_id: str = Field(default="")
    date: str
    status: Literal["in_progress", "finalised"] = "in_progress"
    weekly_objectives: WeeklyObjectives
    whoop: WhoopDayContext | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.envelope_id:
            self.envelope_id = f"env_{self.date}_{uuid.uuid4().hex[:8]}"
