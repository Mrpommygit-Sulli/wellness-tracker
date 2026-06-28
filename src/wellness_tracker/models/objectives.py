import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


class WeightGoal(BaseModel):
    direction: Literal["lose", "maintain", "gain"]
    target_weekly_deficit_kcal: int | None = None
    current_weight_kg: float

    @field_validator("current_weight_kg")
    @classmethod
    def weight_in_range(cls, v: float) -> float:
        if v <= 0 or v >= 300:
            raise ValueError("current_weight_kg must be > 0 and < 300")
        return v

    @model_validator(mode="after")
    def deficit_required_when_losing(self) -> "WeightGoal":
        if self.direction == "lose":
            deficit = self.target_weekly_deficit_kcal
            if not deficit or deficit <= 0:
                raise ValueError(
                    "target_weekly_deficit_kcal is required and must be > 0"
                    " when direction is 'lose'"
                )
        return self


class NutritionTargets(BaseModel):
    daily_calorie_target: int
    daily_protein_target_g: int

    @field_validator("daily_calorie_target")
    @classmethod
    def calorie_in_range(cls, v: int) -> int:
        if v < 1000 or v > 5000:
            raise ValueError("daily_calorie_target must be >= 1000 and <= 5000")
        return v

    @field_validator("daily_protein_target_g")
    @classmethod
    def protein_in_range(cls, v: int) -> int:
        if v < 0 or v > 500:
            raise ValueError("daily_protein_target_g must be >= 0 and <= 500")
        return v


class TrainingTarget(BaseModel):
    sessions: int
    min_duration_minutes: int

    @field_validator("sessions")
    @classmethod
    def sessions_in_range(cls, v: int) -> int:
        if v < 1 or v > 14:
            raise ValueError("sessions must be >= 1 and <= 14")
        return v

    @field_validator("min_duration_minutes")
    @classmethod
    def duration_in_range(cls, v: int) -> int:
        if v < 10 or v > 300:
            raise ValueError("min_duration_minutes must be >= 10 and <= 300")
        return v


class WeeklyObjectives(BaseModel):
    week_starting: str
    weight_goal: WeightGoal
    training_targets: dict[str, TrainingTarget]
    nutrition_targets: NutritionTargets
    constraints: list[str] = []

    @field_validator("week_starting")
    @classmethod
    def valid_iso_date(cls, v: str) -> str:
        datetime.date.fromisoformat(v)
        return v

    @field_validator("training_targets")
    @classmethod
    def at_least_one_activity(
        cls, v: dict[str, TrainingTarget]
    ) -> dict[str, TrainingTarget]:
        if not v:
            raise ValueError("training_targets must have at least one activity")
        return v
