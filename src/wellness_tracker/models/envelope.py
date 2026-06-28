import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from wellness_tracker.models.objectives import WeeklyObjectives


class DailyEnvelope(BaseModel):
    envelope_id: str = Field(default="")
    date: str
    status: Literal["in_progress", "finalised"] = "in_progress"
    weekly_objectives: WeeklyObjectives

    def model_post_init(self, __context: Any) -> None:
        if not self.envelope_id:
            self.envelope_id = f"env_{self.date}_{uuid.uuid4().hex[:8]}"
